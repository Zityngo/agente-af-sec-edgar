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
    # Amazon etiqueta el coste de ventas en us-gaap:CostOfGoodsAndServicesSold.
    # El 'gross profit' es CALCULO revenue - cost, no campo GrossProfit observado.
    norm.TAG["amzn_cost_of_sales"] = ["CostOfGoodsAndServicesSold"]
    fys_all = norm.annual(facts, CIK, data.get("entityName", "Amazon.com"), "AMZN", 2020, 2026)
    annual = {r["fiscal_year"]: r for r in fys_all if r["fiscal_year"] in YEARS}
    q_all = norm.quarterly(facts, CIK, data.get("entityName","Amazon.com"), "AMZN", fys_all, 2021, 2026)
    quarterly = {(q["fiscal_year"], q["period_type"]): q for q in q_all if q["fiscal_year"] in YEARS}
    current = [q for q in q_all if q["fiscal_year"] == 2026 and q["period_type"] in ("Q1","Q2","Q3")]
    errors=[]
    # Restaurar BPA Q4 desde comunicados oficiales (nunca BPA FY - BPA 9M).
    regpath = ROOT / "data" / "amzn_q4_eps_official_2021_2025.json"
    registry = json.loads(regpath.read_text(encoding="utf-8"))
    if registry.get("schema_version") != 1 or registry.get("cik") != CIK or len(registry.get("rows", [])) != 5:
        raise ValueError("Registro oficial de EPS Q4 invalido")
    for datum in registry["rows"]:
        key=(datum["fiscal_year"],datum["period_type"])
        row=quarterly.get(key)
        if not row or row["period_end"]!=datum["period_end"]:
            raise ValueError(f"Q4 oficial no coincide con SEC {key}")
        if row.get("eps_diluted") is not None and abs(row["eps_diluted"]-datum["eps_diluted"])>.02:
            raise ValueError(f"Q4 oficial contradice EPS SEC {key}")
        if datum.get("published_at","")<=datum["period_end"] or not datum.get("source_url","").startswith("https://ir.aboutamazon.com/"):
            raise ValueError(f"EPS Q4 sin evidencia/fecha {key}")
        row["eps_diluted"]=datum["eps_diluted"]
        row.setdefault("sources",{})["eps_diluted"]={
            "tag":"IssuerReportedGAAPDilutedEPS","source":datum["source_url"],
            "published_at":datum["published_at"],"status":"OFFICIAL_MANUAL_SPLIT_ADJUSTED"}
    # Completar el margen bruto con etiquetas contables originales y procedencia.
    cost_key = "amzn_cost_of_sales"
    cost_annual = {}
    for year,r in annual.items():
        v,src = norm.select(facts,cost_key,r["period_end"],norm.ANNUAL_FORMS,
                            year,"FY",(320,390),r["filing_accession"])
        cost_annual[year]=(v,src)
        if v is None or r.get("revenue") is None:
            errors.append(f"FY {year}: cost of sales not found")
        else:
            r["gross_profit"] = r["revenue"] - v
    for (year,quarter),r in quarterly.items():
        if quarter != "Q4":
            v,src = norm.select(facts,cost_key,r["period_end"],norm.QUARTER_FORMS,
                                year,quarter,(70,112),r["filing_accession"])
        else:
            annual_cost,annual_src = cost_annual.get(year,(None,None))
            q3 = quarterly.get((year,"Q3"))
            ytd,ytd_src = ((None,None) if q3 is None else
                norm.select(facts,cost_key,q3["period_end"],norm.QUARTER_FORMS,
                            year,"Q3",(230,300),q3["filing_accession"]))
            v=annual_cost-ytd if annual_cost is not None and ytd is not None else None
            src={"derived_from":"FY_minus_9M","annual_source":annual_src,
                 "nine_month_source":ytd_src} if v is not None else None
        if v is None or r.get("revenue") is None:
            errors.append(f"{year} {quarter}: cost of sales not found")
        else:
            r["gross_profit"]=r["revenue"]-v
            r.setdefault("sources",{})["gross_profit"] = {"derived_from":"revenue_minus_cost_of_sales",
                "cost_of_sales":src,"revenue_source":r.get("sources",{}).get("revenue")}
    for r in current:
        year=r["fiscal_year"];period=r["period_type"]
        v,src=norm.select(facts,cost_key,r["period_end"],norm.QUARTER_FORMS,
                          year,period,(70,112),r["filing_accession"])
        if v is not None and r.get("revenue") is not None:
            r["gross_profit"]=r["revenue"]-v
            r.setdefault("sources",{})["gross_profit"]={"derived_from":"revenue_minus_cost_of_sales","cost_of_sales":src}

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
    # Fuente SEC 2026 Q1-Q3: conservar campos originales por trimestre en el artefacto,
    # incluidos accession y filed, para no degradar estos períodos a PROXY.
    current_rows=[]
    for r in sorted(current,key=lambda x:x["period_end"]):
        v={"year":r["fiscal_year"],"quarter":r["period_type"],
           "end":r["period_end"],"filed":r.get("filing_date"),
           "accession":r.get("filing_accession"),
           "values":{field:r.get(field) for field in FIELDS},
           "sources":r.get("sources",{}),
           "methods":{k:r.get(k) for k in ("operating_income_method","debt_method","da_method")}}
        current_rows.append(v)
    # Interval and accounting comparisons cannot be restricted to calendar-year stock dates.
    dates=sorted(date.fromisoformat(r["end"]) for r in rows)
    if any(not 70 <= (b-a).days <= 112 for a,b in zip(dates,dates[1:])):
        errors.append("quarter ending dates not consecutive")
    for c in compare:
        if c["status"]=="NULL" and c["metric"] in REQUIRED:
            errors.append(f"FY/4Q reconciliation missing: {c['fy']} {c['metric']}")
    coverage={k:sum(r["values"][k] is not None for r in rows) for k in FIELDS}
    sec_cost_tags = sorted(k for k in facts if "CostOf" in k or "CostOfGoods" in k)
    status="STRUCTURAL_PASS" if not errors and len(annual)==5 and len(rows)==20 else "REVIEW_REQUIRED"
    return {"status":status,"company":"Amazon.com, Inc.","cik":CIK,"sec_url":URL,
            "extracted_utc":datetime.now(timezone.utc).isoformat(),"FY":len(annual),
            "FY_years":sorted(annual.keys()),"quarters":len(rows),"sec_cost_tags":sec_cost_tags,
            "Q_2026":len(current),"current_q_rows":current_rows,"coverage":coverage,
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
