#!/usr/bin/env python3
"""Piloto SEC de 20 trimestres de PepsiCo (FY2021-FY2025), sin base de datos.

Reutiliza el extractor normalizador de A.FUNDAMENTAL. Sólo lee companyfacts oficial
SEC, valida períodos y conciliación FY = Q1+Q2+Q3+Q4; no modifica cartera/SQLite.
Puede recibir un JSON FMP privado como referencia opcional, sin distribuirlo.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen
from datetime import date, datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PEP_CIK = "0000077476"
SEC_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000077476.json"
FIRST, LAST = 2021, 2025
RAW_KEYS = ("revenue", "gross_profit", "operating_income", "net_income", "eps_diluted",
            "cfo", "capex", "cash", "debt_total", "equity", "assets", "da", "interest", "tax", "pretax")
FLOW_KEYS = ("revenue", "gross_profit", "operating_income", "net_income", "cfo", "capex")
REQUIRED_KEYS = ("revenue", "gross_profit", "operating_income", "net_income", "cfo", "capex")
FMP_KEYS = ("revenue", "operating_income", "net_income", "eps_diluted", "cfo", "capex")

def fetch_sec(ua: str) -> dict:
    if not ua or "@" not in ua or len(ua) < 14:
        raise ValueError("SEC_USER_AGENT debe incluir identidad y correo de contacto real")
    req = Request(SEC_URL, headers={"User-Agent": ua, "Accept": "application/json", "Accept-Encoding": "identity"})
    with urlopen(req, timeout=75) as resp:
        raw = resp.read()
    return json.loads(raw)

def ensure_facts(obj):
    if str(obj.get("cik", "")).zfill(10) != PEP_CIK:
        raise ValueError("CIK incorrecto; se bloquea la auditoría")
    if not isinstance(obj.get("facts", {}).get("us-gaap"), dict):
        raise ValueError("No se ha encontrado taxonomía us-gaap")

def ratio(n, d):
    return n / d if n is not None and d is not None and d != 0 else None

def source_state(r, key):
    """OK/proxy/blocked según procedencia; nunca promover falta de evidencia."""
    if r.get(key) is None:
        return "NULL"
    src = r.get("sources", {}).get(key)
    if not isinstance(src, dict):
        return "REVIEW_NO_SOURCE"
    if key == "operating_income" and r.get("operating_income_method") not in (
        "reported_OperatingIncomeLoss", "derived_Q4_FY_minus_9M"
    ):
        return "BLOCKED_EBIT_METHOD"
    if key == "capex" and r[key] < 0:
        return "BLOCKED_CAPEX_SIGN"
    if key in ("cfo", "capex") and r["period_type"] != "FY":
        method = src.get("derived_from")
        if method in ("ytd_delta", "FY_minus_9M"):
            fields = ["source"] if method == "ytd_delta" else ["annual_source", "nine_month_source"]
            if any(not isinstance(src.get(f), dict) for f in fields):
                return "BLOCKED_YTD_PROVENANCE"
            if method == "ytd_delta" and src.get("previous_ytd") is None:
                return "BLOCKED_YTD_PREVIOUS"
            return "PROXY_YTD_OR_FY_DELTA"
    return "PROXY" if src.get("derived_from") else "OK"

def sum_checked(rows, key):
    xs = [r.get(key) for r in rows]
    return sum(xs) if len(rows) == 4 and all(v is not None for v in xs) else None

def quarterly_rows(facts, norm):
    ensure_facts(facts)
    us = facts["facts"]["us-gaap"]
    norm._CACHE.clear()
    annual_all = norm.annual(us, PEP_CIK, facts.get("entityName", "PepsiCo"), "PEP", FIRST-1, LAST)
    q_all = norm.quarterly(us, PEP_CIK, facts.get("entityName", "PepsiCo"), "PEP", annual_all, FIRST, LAST)
    fy = [r for r in annual_all if FIRST <= r["fiscal_year"] <= LAST]
    q = [r for r in q_all if FIRST <= r["fiscal_year"] <= LAST]
    current_q = [r for r in q_all if r["fiscal_year"] == LAST+1 and r["period_type"] in ("Q1", "Q2", "Q3")]
    return annual_all, fy, q, current_q

def compare_fmp(years, quarters, reference, tolerance_usd=2_000_000, tolerance_eps=.015):
    """Los datos FMP son opcionales y privados; nunca se versionan como fixtures."""
    checks = []
    if reference is None:
        return checks
    keys = {(r["fiscal_year"], r["period_type"]): r for r in years + quarters}
    for r in reference.get("rows", []):
        key = (int(r["fiscal_year"]), r["period_type"])
        sec = keys.get(key)
        for k in FMP_KEYS:
            if k not in r:
                continue
            their = r[k]
            ours = sec.get(k) if sec else None
            tol = tolerance_eps if k == "eps_diluted" else tolerance_usd
            flag = "NOT_COMPARABLE" if their is None or ours is None else ("MATCH" if abs(their - ours) <= tol else "DIFFERENCE")
            checks.append({"year": key[0], "period": key[1], "metric": k,
                           "sec": ours, "fmp": their, "status": flag, "tolerance": tol})
    return checks

def audit(facts, norm, fmp_reference=None):
    annual_all, years, quarters, current_q = quarterly_rows(facts, norm)
    seen = {}
    defects = []
    year_reconciliations = []
    for r in quarters:
        k = (r["fiscal_year"], r["period_type"])
        if k in seen:
            defects.append(f"duplicado {k}")
        seen[k] = r
        if r.get("fiscal_year") != int(r["period_end"][:4]):
            defects.append(f"ejercicio/cierre incoherentes {k}")
        if r.get("filing_date") and r["filing_date"] < r["period_end"]:
            defects.append(f"filed anterior al cierre {k}")
        for metric in ("cfo", "capex"):
            if r.get(metric) is not None and source_state(r, metric).startswith("BLOCKED"):
                defects.append(f"{metric} sin procedencia FY/YTD válida: {k}")
    expected = {(yr, f"Q{q}") for yr in range(FIRST, LAST+1) for q in range(1, 5)}
    for k in sorted(expected - set(seen)):
        defects.append(f"trimestre ausente {k}")
    dates = [r["period_end"] for r in sorted(quarters, key=lambda x:x["period_end"])]
    calendar_exceptions = []
    for earlier, later in zip(dates, dates[1:]):
        days = (date.fromisoformat(later) - date.fromisoformat(earlier)).days
        # PepsiCo 2022 10-K, p. 66: 53-week fiscal year, Q4 has 17 weeks.
        # SEC: https://www.sec.gov/Archives/edgar/data/77476/000007747623000007/pep-20221231.htm
        documented_53_week_q4 = (earlier, later, days) == ("2022-09-03", "2022-12-31", 119)
        if documented_53_week_q4:
            calendar_exceptions.append({"year": 2022, "period": "Q4", "weeks": 17,
                                        "days": 119, "source": "SEC 2022 10-K p.66"})
        elif not 70 <= days <= 112:
            defects.append(f"fechas no consecutivas {earlier} -> {later} ({days} días)")
    annual_by_year = {r["fiscal_year"]: r for r in years}
    for yr in range(FIRST, LAST+1):
        a = annual_by_year.get(yr)
        blocks = [seen.get((yr, f"Q{k}")) for k in range(1, 5)]
        if not a or any(q is None for q in blocks):
            defects.append(f"faltan 10-K o trimestre en {yr}")
            continue
        if blocks[-1]["period_end"] != a["period_end"]:
            defects.append(f"cierre Q4 != FY {yr}")
        for fld in FLOW_KEYS:
            total = sum_checked(blocks, fld)
            ref = a.get(fld)
            status = "NULL" if total is None or ref is None else ("MATCH" if abs(total-ref) <= 2_000_000 else "DIFFERENCE")
            year_reconciliations.append({"fy": yr, "metric": fld, "fy_value": ref, "sum_quarters": total, "status": status})
            if status == "DIFFERENCE":
                defects.append(f"descuadre FY vs 4Q: {yr} {fld}")
    qrows = sorted(quarters + current_q, key=lambda x:x["period_end"])
    metrics = []
    for index, row in enumerate(qrows):
        w = qrows[index-3:index+1] if index >= 3 else []
        sums = {k: sum_checked(w, k) for k in ("revenue", "operating_income", "net_income", "cfo", "capex", "tax", "pretax", "da", "interest")}
        total_fcf = (sums["cfo"] - sums["capex"] if sums["cfo"] is not None and sums["capex"] is not None else None)
        fcf = (row["cfo"] - row["capex"] if row.get("cfo") is not None and row.get("capex") is not None else None)
        prev = qrows[index-4] if index >= 4 else None
        if prev is None and row["fiscal_year"] == FIRST and row["period_type"] == "Q4":
            prev = next((a for a in annual_all if a["fiscal_year"] == FIRST-1), None)
        roic = roe = None
        if prev is not None and len(w) == 4:
            current_ic = None if None in (row.get("equity"), row.get("debt_total"), row.get("cash")) else row["equity"]+row["debt_total"]-row["cash"]
            prev_ic = None if None in (prev.get("equity"), prev.get("debt_total"), prev.get("cash")) else prev["equity"]+prev["debt_total"]-prev["cash"]
            effective_t = ratio(sums["tax"], sums["pretax"]) if sums["pretax"] is not None and sums["pretax"] > 0 else None
            if (sums["operating_income"] is not None and effective_t is not None and 0 <= effective_t <= .6
                    and current_ic is not None and prev_ic is not None and current_ic+prev_ic > 0):
                roic = sums["operating_income"]*(1-effective_t)/((current_ic+prev_ic)/2)
            if (sums["net_income"] is not None and None not in (row.get("equity"), prev.get("equity"))
                    and row["equity"]+prev["equity"] > 0):
                roe = sums["net_income"]/((row["equity"]+prev["equity"])/2)
        metrics.append({"fy": row["fiscal_year"], "quarter": row["period_type"], "end": row["period_end"],
                        "values": {k: row.get(k) for k in RAW_KEYS},
                        "states": {k: source_state(row, k) for k in REQUIRED_KEYS},
                        "ratios": {"gross_margin": ratio(row.get("gross_profit"), row.get("revenue")),
                                   "ebit_margin": ratio(row.get("operating_income"), row.get("revenue")),
                                   "net_margin": ratio(row.get("net_income"), row.get("revenue")),
                                   "fcf_margin": ratio(fcf, row.get("revenue")),
                                   "fcf": fcf, "fcf_ttm": total_fcf,
                                   "roic_ttm_cic_proxy": roic, "roe_ttm": roe,
                                   "interest_coverage_ttm": ratio(sums["operating_income"], sums["interest"]),
                                   "net_debt": row["debt_total"]-row["cash"] if row.get("debt_total") is not None and row.get("cash") is not None else None},
                        "method_notes": ["ROIC proxy: EBIT TTM neto impuesto / media(equity+deuda-caja)",
                                         "No es ROIC core PepsiCo; sin ratios de cotización ni consenso"]})
    fmp_checks = compare_fmp(years, quarters+current_q, fmp_reference)
    coverage = {k: sum(r.get(k) is not None for r in quarters) for k in RAW_KEYS}
    for key in REQUIRED_KEYS:
        if coverage[key] != 20:
            defects.append(f"cobertura insuficiente {key}: {coverage[key]}/20")
    if any(x["status"] == "NULL" for x in year_reconciliations):
        defects.append("FY vs 4Q tiene conciliaciones incompletas")
    status = "REVIEW_REQUIRED" if defects or any(x["status"] == "DIFFERENCE" for x in fmp_checks) else "STRUCTURAL_PASS"
    return {"status": status, "audit_scope": "PEP 5FY + 20Q (2021-2025); Q 2026 opcionales",
            "official_source": SEC_URL, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "documented_fiscal_calendar_exceptions": calendar_exceptions,
            "fy_count": len(years), "quarter_count": len(quarters), "additional_current_quarters": len(current_q),
            "missing_quarters": [{"fiscal_year": fy, "quarter": q} for fy, q in sorted(expected-set(seen))],
            "coverage_count_by_metric_of_20": coverage, "fy_vs_quarters": year_reconciliations,
            "fmp_checks": fmp_checks, "defects": defects, "quarters": metrics,
            "limitations": ["STRUCTURAL_PASS no certifica 20 10-Q individuales ni bases GAAP/core",
                            "BPA Q4 nunca se obtiene restando BPA FY y 9M",
                            "CFO/CapEx Q2-Q4 se derivan de YTD/FY con trazabilidad",
                            "ROIC TTM es proxy pendiente de conciliar definiciones",
                            "PER, EV/EBITDA, FCF yield requieren precios y acciones fechados",
                            "Guidance/consenso requieren fuente externa (IR/8-K/FMP)"]}

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--companyfacts", type=Path, help="JSON SEC local para ejecutar sin red")
    ap.add_argument("--fmp", type=Path, help="JSON FMP privado opcional, NO versionar")
    ap.add_argument("--out", type=Path, default=Path("publico/pilot_pep_20q_qa.json"))
    args = ap.parse_args(argv)
    obj = json.loads(args.companyfacts.read_text(encoding="utf-8")) if args.companyfacts else fetch_sec(os.environ.get("SEC_USER_AGENT", ""))
    benchmark = json.loads(args.fmp.read_text(encoding="utf-8")) if args.fmp else None
    import normalize_sp500_v2 as nm
    report = audit(obj, nm, benchmark)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "fy_count", "quarter_count", "additional_current_quarters",
                                           "coverage_count_by_metric_of_20", "defects")}, ensure_ascii=False))
    return 0 if report["status"] == "STRUCTURAL_PASS" and report["fy_count"] == 5 and report["quarter_count"] == 20 else 2

if __name__ == "__main__":
    raise SystemExit(main())
