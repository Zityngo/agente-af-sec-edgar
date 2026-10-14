#!/usr/bin/env python3
"""SEC EDGAR verified batch -> candidate-only staging within existing master Sheet.

Source SHA256/CIK/accession controls; no FY/Q mixing and no guessed YTD cash flow.
No writes without explicit --write and Google service-account credentials.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

TAB = "SEC_AUTO_STAGING"
COLUMNS = ["clave", "ticker", "cik", "form", "periodo", "cierre", "filed",
           "accession", "ingresos_usd", "ebit_operativo_usd", "net_income_usd",
           "cfo_usd", "capex_usd", "fcf_proxy_usd", "qa", "trazas_xbrl",
           "url_filing", "url_companyfacts", "sha256_companyfacts",
           "fecha_utc", "observacion"]
TAGS = {
    "revenue": [("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
                ("us-gaap", "Revenues"), ("us-gaap", "SalesRevenueNet"),
                ("ifrs-full", "RevenueFromContractsWithCustomers"),
                ("ifrs-full", "Revenue")],
    "ebit": [("us-gaap", "OperatingIncomeLoss"),
             ("ifrs-full", "ProfitLossFromOperatingActivities")],
    "ni": [("us-gaap", "NetIncomeLoss"), ("ifrs-full", "ProfitLoss")],
    "cfo": [("us-gaap", "NetCashProvidedByUsedInOperatingActivities"),
            ("ifrs-full", "CashFlowsFromUsedInOperatingActivities")],
    "capex": [("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),
              ("ifrs-full", "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities")],
}
FY_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A"}
Q_FORMS = {"10-Q", "10-Q/A"}

def verified(root):
    manifest = json.loads((root / "sp500_batch_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != "SEC_SP500_BATCH_V1":
        raise ValueError("Manifest SEC incompatible")
    companies = manifest.get("companies", [])
    if not 1 <= len(companies) <= 100:
        raise ValueError("Lote SEC fuera de límites")
    seen = set()
    for company in companies:
        cik = str(company.get("cik", ""))
        if len(cik) != 10 or not cik.isdigit() or cik in seen:
            raise ValueError("CIK duplicado o inválido")
        seen.add(cik)
        if company.get("status") != "OK":
            raise ValueError("Lote parcial SEC: " + cik)
        loaded = {}
        for typ in ("submissions", "companyfacts"):
            raw = gzip.decompress((root / ("CIK" + cik) / (typ + ".json.gz")).read_bytes())
            sha = hashlib.sha256(raw).hexdigest()
            if sha != company.get("sha256_" + typ):
                raise ValueError("SHA256 inválido: " + cik + " " + typ)
            obj = json.loads(raw)
            if str(obj.get("cik", "")).zfill(10) != cik:
                raise ValueError("CIK fuente discordante: " + cik)
            loaded[typ] = (obj, sha)
        sub = loaded["submissions"][0]
        facts = loaded["companyfacts"][0]
        if not isinstance(sub.get("filings", {}).get("recent"), dict) or not isinstance(facts.get("facts"), dict):
            raise ValueError("Estructura SEC incompleta: " + cik)
        yield company, sub, facts, loaded["companyfacts"][1]

def recent_forms(sub):
    filings = sub["filings"]["recent"]
    keys = ("form", "filingDate", "reportDate", "accessionNumber", "primaryDocument")
    count = len(filings.get("form", []))
    if not count or any(len(filings.get(k, [])) != count for k in keys):
        raise ValueError("Índice filings SEC inconsistente")
    today = date.today().isoformat()
    eligible = []
    for i in range(count):
        form = filings["form"][i]
        if form not in FY_FORMS | Q_FORMS:
            continue
        row = {"form": form, "filed": filings["filingDate"][i],
               "end": filings["reportDate"][i], "acc": filings["accessionNumber"][i],
               "doc": filings["primaryDocument"][i],
               "kind": "FY" if form in FY_FORMS else "Q"}
        if any(not row[k] for k in ("filed", "end", "acc", "doc")):
            continue
        if row["filed"] > today or row["end"] > today:
            continue
        eligible.append(row)
    latest = {}
    for row in sorted(eligible, key=lambda r: (r["end"], r["filed"], r["acc"]), reverse=True):
        latest.setdefault(row["kind"], row)
    return list(latest.values())

def metric(facts, name, filing):
    for taxonomy, tag in TAGS[name]:
        for v in facts.get(taxonomy, {}).get(tag, {}).get("units", {}).get("USD", []):
            if (v.get("val") is None or v.get("form") != filing["form"]
                or v.get("accn") != filing["acc"] or v.get("end") != filing["end"]
                or not v.get("start")):
                continue
            try:
                days = (date.fromisoformat(v["end"]) - date.fromisoformat(v["start"])).days
            except (ValueError, TypeError, KeyError):
                continue
            if filing["kind"] == "FY" and not (330 <= days <= 390):
                continue
            if filing["kind"] == "Q" and not (70 <= days <= 112):
                continue
            return v["val"], {"taxonomy": taxonomy, "tag": tag,
                              "start": v["start"], "end": v["end"],
                              "accn": v["accn"], "days": days}
    return None, None

def build(root):
    rows = []
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for company, subs, cf, sha in verified(root):
        cik = company["cik"]
        for filing in recent_forms(subs):
            values = {}
            evidence = {}
            for name in TAGS:
                values[name], source = metric(cf["facts"], name, filing)
                if source is not None:
                    evidence[name] = source
            cfo, capex = values["cfo"], values["capex"]
            fcf = cfo - abs(capex) if cfo is not None and capex is not None else None
            status = "FY_CANDIDATO" if filing["kind"] == "FY" else "Q_CANDIDATO"
            if values["revenue"] is None or values["ni"] is None:
                status = "QA_TAGS_INCOMPLETOS"
            if filing["kind"] == "Q" and fcf is None:
                status = "QA_FCF_TRIMESTRAL_FALTANTE"
            note = ("Datos sin auditar concepto/ajustes. No recalcular TTM/ROIC/PER. "
                    "Nunca interpretar CFO acumulado 6M/9M como un único trimestre.")
            source_url = (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                          f"{filing['acc'].replace('-', '')}/{filing['doc']}")
            key = "|".join((cik, filing["kind"], filing["end"], filing["acc"]))
            rows.append([key, ",".join(company.get("symbols", [])), cik,
                         filing["form"], filing["kind"], filing["end"],
                         filing["filed"], filing["acc"], values["revenue"],
                         values["ebit"], values["ni"], cfo, capex, fcf, status,
                         json.dumps(evidence, ensure_ascii=False, separators=(",", ":")),
                         source_url, f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                         sha, timestamp, note])
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError("Claves SEC duplicadas")
    return rows

def write_staging(rows, sheet_id, service_account_json, enabled=False):
    if not enabled:
        return {"state": "DRY_RUN", "count": len(rows)}
    if not sheet_id or not service_account_json:
        raise ValueError("Faltan GOOGLE_SHEET_ID/GOOGLE_SERVICE_ACCOUNT_JSON")
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(service_account_json), scopes=["https://www.googleapis.com/auth/spreadsheets"])
    http = AuthorizedSession(credentials)
    base = f"https://sheets.googleapis.com/v4/spreadsheets/{quote(sheet_id, safe='')}"
    def request(method, route, **kwargs):
        response = getattr(http, method)(base + route, timeout=45, **kwargs)
        response.raise_for_status()
        return response.json()
    current = request("get", "/values/" + quote(TAB + "!A1:U5000", safe="")).get("values", [])
    if current and current[0] != COLUMNS:
        raise ValueError("Cabeceras staging cambiadas; bloqueo preventivo")
    if len(current) >= 4999:
        raise ValueError("Limite staging 5000 filas")
    if not current:
        request("put", "/values/" + quote(TAB + "!A1:U1", safe=""),
                params={"valueInputOption": "RAW"}, json={"values": [COLUMNS]})
        current = [COLUMNS]
    ids = {}
    for rownum, old in enumerate(current[1:], start=2):
        if old:
            if old[0] in ids:
                raise ValueError("Claves staging duplicadas: " + old[0])
            ids[old[0]] = rownum
    changed, new, ignored = [], [], 0
    for record in rows:
        vals = ["" if x is None else x for x in record]
        if record[0] in ids:
            n = ids[record[0]]
            old = current[n-1]
            if len(old) >= 19 and old[18] == record[18]:
                ignored += 1
                continue
            changed.append({"range": f"{TAB}!A{n}:U{n}", "values": [vals]})
        else:
            new.append(vals)
    if changed:
        request("post", "/values:batchUpdate",
                json={"valueInputOption": "RAW", "data": changed})
    if new:
        request("post", "/values/" + quote(TAB + "!A:U", safe="") + ":append",
                params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
                json={"values": new})
    return {"state": "STAGING_UPDATED", "added": len(new), "updated": len(changed), "unchanged": ignored}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("publico/sec"))
    parser.add_argument("--preview", type=Path, default=Path("publico/sec/sec_staging_preview.json"))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    rows = build(args.root)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.preview.write_text(json.dumps({"columns": COLUMNS, "rows": rows}, ensure_ascii=False, indent=2)
                            + "\n", encoding="utf-8")
    result = write_staging(rows, os.environ.get("GOOGLE_SHEET_ID", ""),
                           os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", ""), args.write)
    print(json.dumps({"companies": len({r[2] for r in rows}), "filings": len(rows),
                      "result": result}, ensure_ascii=False))

if __name__ == "__main__":
    main()
