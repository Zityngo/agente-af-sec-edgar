"""Lotes diarios del S&P 500: descarga hechos contables públicos desde SEC EDGAR.

Se ejecuta DESPUÉS de descargar_sec.py y guarda resultados en el mismo
artefacto temporal. El importador de ChatGPT conserva ese artefacto en Drive.

Una compañía financiera equivale a un CIK único, aunque tenga varias clases
de acciones en el S&P 500. La composición usa un snapshot versionado de
una fuente comunitaria, no una lista certificada por S&P Dow Jones Indices.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
import time
import urllib.error
import urllib.request

BASE = Path(__file__).resolve().parent
OUT = BASE / "publico" / "sec"
UNIVERSE = BASE / "universo_sp500.csv"
BATCH_SIZE = int(os.environ.get('SP500_BATCH_SIZE', '40'))
if not (10 <= BATCH_SIZE <= 100):
    raise SystemExit('SP500_BATCH_SIZE debe estar entre 10 y 100')
USER_AGENT = os.environ.get("SEC_USER_AGENT", "").strip()
if len(USER_AGENT) < 12 or "@" not in USER_AGENT:
    raise SystemExit("No está configurado SEC_USER_AGENT como secreto en GitHub")

def http_json(url: str, ticker: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent":USER_AGENT, "Accept":"application/json",
                      "Accept-Encoding":"identity"}
    )
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                payload = resp.read()
                if resp.status != 200:
                    raise ValueError(f"HTTP {resp.status}")
                test = json.loads(payload)
                if not isinstance(test, dict): raise ValueError("JSON no es un objeto")
                time.sleep(0.7)
                return payload
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                raise RuntimeError(f"{ticker}: SEC HTTP 403; IP bloqueada; sin eludir controles") from exc
            if exc.code not in (429,500,502,503,504) or i == 3:
                raise RuntimeError(f"{ticker}: HTTP {exc.code}") from exc
            time.sleep(2 + i * 4)
    raise RuntimeError(f"{ticker}: solicitud SEC fallida")

def companies() -> list[dict[str, str]]:
    companies_by_cik = {}
    with UNIVERSE.open(encoding="utf-8-sig",newline="") as fp:
        for row in csv.DictReader(fp):
            symbol = row["Symbol"].strip()
            cik_raw = row["CIK"].strip()
            if not cik_raw.isdigit() or not symbol:
                raise ValueError("Símbolo o CIK inválido en universo_sp500.csv")
            cik = cik_raw.zfill(10)
            item=companies_by_cik.setdefault(cik, {
                "cik": cik,
                "company_name": row["Security"],
                "sector": row["GICS Sector"],
                "symbols": []
            })
            item["symbols"].append(symbol)
    companies_list=sorted(companies_by_cik.values(),key=lambda a:a["cik"])
    if not (490<=len(companies_list)<=510):
        raise ValueError(f"Unidades legales inesperadas: {len(companies_list)}; abortar")
    return companies_list

def save(path:Path, data:bytes)->str:
    path.parent.mkdir(parents=True,exist_ok=True)
    zipped=gzip.compress(data,mtime=0,compresslevel=9)
    path.write_bytes(zipped)
    return hashlib.sha256(data).hexdigest()

def main():
    all_firms=companies()
    batch_total=math.ceil(len(all_firms)/BATCH_SIZE)
    now=datetime.now(timezone.utc)
    selected = os.environ.get('SP500_BATCH_INDEX', '').strip()
    batch_id = int(selected) if selected else now.toordinal()%batch_total
    if not (0 <= batch_id < batch_total):
        raise SystemExit(f'Índice de lote no válido: {batch_id}; máximo {batch_total-1}')
    start=batch_id*BATCH_SIZE
    batch=all_firms[start:start+BATCH_SIZE]
    index={
        "schema":"SEC_SP500_BATCH_V1",
        "created_utc":now.isoformat(timespec="seconds"),
        "source":"datasets/s-and-p-500-companies from Wikipedia",
        "source_ref":"universo_sp500.csv (snapshotted in GitHub)",
        "memberships": sum(len(c["symbols"]) for c in all_firms),
        "unique_cik":len(all_firms),
        "batch_size":BATCH_SIZE,
        "batch_index_zero_based":batch_id,
        "batch_total":batch_total,
        "companies":[],
        "errors":[]
    }
    print(f"SP500 lote {batch_id+1}/{batch_total}: {len(batch)} CIK de {len(all_firms)}",flush=True)
    for company in batch:
        cik=company["cik"]
        ticker="/".join(company["symbols"])
        entry={"cik":cik,"symbols":company["symbols"],"sector":company["sector"]}
        try:
            base=OUT / f"CIK{cik}"
            for kind,url in (
                ("submissions",f"https://data.sec.gov/submissions/CIK{cik}.json"),
                ("companyfacts",f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"),
            ):
                raw=http_json(url,ticker)
                obj=json.loads(raw)
                expected="filings" if kind=="submissions" else "facts"
                if not obj.get(expected):
                    raise ValueError(f"{ticker}: {kind} no contiene {expected}")
                entry["sha256_"+kind]=save(base/(kind+".json.gz"),raw)
                entry["bytes_"+kind]=len(raw)
            entry["status"]="OK"
            print(f"{ticker} CIK {cik}: OK",flush=True)
        except Exception as e:
            entry["status"]="ERROR"
            entry["error"]=str(e)
            index["errors"].append(entry)
            print(f"{ticker} CIK {cik}: ERROR {e}",flush=True)
        index["companies"].append(entry)
    OUT.mkdir(parents=True,exist_ok=True)
    manifest_path = (OUT / "batches" / f"sp500_batch_{batch_id:02d}.json") if os.environ.get("SP500_BOOTSTRAP") == "1" else OUT / "sp500_batch_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    successes=sum(x["status"]=="OK" for x in index["companies"])
    print(f"SP500 lote: {successes}/{len(batch)} empresas OK; "+
          f"{len(index['errors'])} errores; "+
          f"total de {batch_total} lotes; este lote #{batch_id+1}.",flush=True)
    if successes==0:raise SystemExit("NINGUNA empresa recuperada: revisar fuente y permisos")
    if index["errors"]:
        print("WARNING: lote parcial. No atribuir cobertura total a fallos.",flush=True)

if __name__=="__main__":
    main()
