#!/usr/bin/env python3
"""Auditoría SEC AMZN 2021-2025, 20 trimestres y YTD 2026; solo lectura.

Usa normalizador SEC existente; no crea base de datos, no cambia ratios
de producción, no almacena APIs comerciales ni claves.
"""
from __future__ import annotations
from pathlib import Path
from datetime import date, datetime, timezone
from urllib.request import Request, urlopen
import argparse
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
CIK = "0001018724"
URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"
YEARS = range(2021, 2026)
FIELDS = ("revenue","gross_profit","operating_income","net_income","eps_diluted",
          "cfo","capex","da","cash","debt_total","equity","assets","tax","pretax")
FLOWS = ("revenue","operating_income","net_income","cfo","capex")
REQUIRED = ("revenue","operating_income","net_income","cfo","capex")

def fetch(ua):
    if not ua or "@" not in ua or len(ua) < 14:
        raise ValueError("SEC_USER_AGENT debe identificar al solicitante")
    req = Request(URL, headers={"User-Agent": ua, "Accept": "application/json", "Accept-Encoding": "identity"})
    with urlopen(req, timeout=75) as stream:
        obj = json.loads(stream.read())
    return obj

def run(data, norm):
    if str(data.get("cik", "")).zfill(10) != CIK:
        raise ValueError("CIK Amazon incorrecto")
    facts = data.get("facts", {}).get("us-gaap")
    if not isinstance(facts, dict):
        raise ValueError("SEC JSON sin us-gaap")
    norm._CACHE.clear()
    fys_all = norm.annual(facts, CIK, data.get("entityName", "Amazon.com"), "AMZN", 2020, 2026)
    annual = {r["fiscal_year"]: r for r in fys_all if r["fiscal_year"] in YEARS}
    q_all = norm.quarterly(facts, CIK, data.get("entityName","Amazon.com"), "AMZN", fys_all, 2021, 2026)
    quarterly = {(q["fiscal_year"], q["period_type"]): q for q in q_all if q["fiscal_year"] in YEARS}
    current = [q for q in q_all if q["fiscal_year"] == 2026 and q["period_type"] in ("Q1","Q2","Q3")]
    errors=[]
    for year in YEARS:
        if year not in annual: errors.append(f"FY {year} absent")
        for ix in range(1, 5):
            if (year, f"Q{ix}") not in quarterly: errors.append(f"Q{ix} {year} absent")
    compare=[]
    for year in YEARS:
        if year not in annual or any((year, f"Q{ix}") not in quarterly for ix in range(1,5)):
            continue
        blocks = [quarterly[(year, f"Q{ix}")] for ix in range(1,5)]
        for metric in FLOWS:
            fval=annual[year].get(metric)
            qs=[v.get(metric) for v in blocks]
            qsum = sum(qs) if all(x is not None for x in qs) else None
            delta=(qsum-fval) if qsum is not None and fval is not None else None
            state="NULL" if delta is None else ("MATCH" if abs(delta)<=2_000_000 else "DIFFERENCE")
            compare.append({"fy":year,"metric":metric,"fy_value":fval,"sum_4q":qsum,
                            "delta":delta,"status":state})
            if state=="DIFFERENCE": errors.append(f"{year} {metric}: FY != sum four quarters")
    rows=[]
    for key, r in sorted(quarterly.items()):
        src=r.get("sources",{})
        # Never use FY - 9M for EPS, because weighted dilution varies.
        row={"year":key[0],"quarter":key[1],"end":r["period_end"],
             "filed":r.get("filing_date"),"accession":r.get("filing_accession"),
             "values":{field:r.get(field) for field in FIELDS},
             "sources":{k:src.get(k) for k in REQUIRED+("eps_diluted",)},
             "methods":{k:r.get(k) for k in ("operating_income_method","debt_method","da_method")}}
        for k in REQUIRED:
            if r.get(k) is None: errors.append(f"{key} missing {k}")
        for k in ("cfo","capex"):
            sf=src.get(k)
            if k in REQUIRED and r.get(k) is not None and not isinstance(sf,dict):
                errors.append(f"{key} {k} source unavailable")
            if isinstance(sf,dict) and sf.get("derived_from")=="FY_minus_9M":
                if not (isinstance(sf.get("annual_source"),dict) and isinstance(sf.get("nine_month_source"),dict)):
                    errors.append(f"{key} {k} invalid FY/YTD bridge")
        rows.append(row)
    # Interval and accounting comparisons cannot be restricted to calendar-year stock dates.
    dates=sorted(date.fromisoformat(r["end"]) for r in rows)
    if any(not 70 <= (b-a).days <= 112 for a,b in zip(dates,dates[1:])):
        errors.append("quarter ending dates not consecutive")
    for c in compare:
        if c["status"]=="NULL" and c["metric"] in REQUIRED:
            errors.append(f"FY/4Q reconciliation missing: {c['fy']} {c['metric']}")
    coverage={k:sum(r["values"][k] is not None for r in rows) for k in FIELDS}
    status="STRUCTURAL_PASS" if not errors and len(annual)==5 and len(rows)==20 else "REVIEW_REQUIRED"
    return {"status":status,"company":"Amazon.com, Inc.","cik":CIK,"sec_url":URL,
            "extracted_utc":datetime.now(timezone.utc).isoformat(),"FY":len(annual),
            "FY_years":sorted(annual.keys()),"quarters":len(rows),
            "Q_2026":len(current),"coverage":coverage,
            "fy_vs_q":compare,"defects":errors,"quarter_rows":rows,
            "fy_rows":[{"year":y,"end":r["period_end"],"filed":r["filing_date"],
                        "accession":r["filing_accession"],"values":{k:r.get(k) for k in FIELDS}}
                       for y,r in sorted(annual.items())],
            "limitations":["Q4 EPS not derived from FY minus 9M", 
                "FY=4Q may be tautological for Q4 reconstructed from FY-9M",
                "debt from financial tag normalizer is not necessarily lease-consistent",
                "provider FMP and price comparisons performed separately",
                "ROIC not certified without invested-capital reconciliation"]}

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--file",type=Path,help="SEC JSON local for reproducibility")
    p.add_argument("--out",type=Path,default=Path("publico/pilot_amzn20q/sec20q.json"))
    a=p.parse_args(argv)
    obj=json.loads(a.file.read_text()) if a.file else fetch(os.getenv("SEC_USER_AGENT", ""))
    import normalize_sp500_v2 as norm
    r=run(obj,norm)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:r[k] for k in ("status","FY","quarters","Q_2026","coverage","defects")},ensure_ascii=False))
    return 0 if r["status"]=="STRUCTURAL_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
