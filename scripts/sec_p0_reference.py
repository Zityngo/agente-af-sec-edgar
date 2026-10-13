#!/usr/bin/env python3
"""SEC-only FY reference for nine P0 tickers; FMP remains a separate, read-only comparator.

No commercial-provider data are saved to the public repository.
Requires the existing SEC_USER_AGENT secret. Does not guess missing pre-spin-off years.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date
import json
import os
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen

from sec_aapl_reference import TAGS, INSTANT, annual, pick

# CIKs from SEC-matched SP500 company master. Use these SEC corporate identifiers,
# NOT matching by company names, which can change after spinoffs or acquisitions.
COMPANIES = {
    "AAPL": "0000320193",
    "APP": "0001751008",
    "CSCO": "0000858877",
    "MCK": "0000927653",
    "MU": "0000723125",
    "NTAP": "0001002047",
    "NVDA": "0001045810",
    "OTIS": "0001781335",
    "SNDK": "0002023554",
}


def records_for_company(payload: dict, ticker: str, count: int) -> list[dict]:
    cik=COMPANIES[ticker]
    if str(payload.get("cik","")).zfill(10)!=cik:
        raise ValueError(f"{ticker}: SEC CIK mismatch; abort rather than mixing companies")
    facts=payload.get("facts",{}).get("us-gaap",{})
    year_ends=set()
    for tag in TAGS["revenue"]:
        for vals in facts.get(tag,{}).get("units",{}).values():
            year_ends.update(v["end"] for v in vals if v.get("form") in ("10-K","10-K/A")
                             and v.get("end") and annual(v) and v.get("filed"))
    # Only fiscal years with an annual SEC filing already published; do not invent pre-spinoff history.
    chosen=sorted((e for e in year_ends if e <= date.today().isoformat()),reverse=True)[:count]
    out=[]
    url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    for end in sorted(chosen):
        row={"ticker":ticker,"cik":cik,"period_type":"FY","fiscal_year":end[:4],
             "period_end":end,"currency":"USD","source_sec_url":url}
        for name,tags in TAGS.items():
            row[name]=pick(facts,tags,end,name in INSTANT)
        if row["revenue"]=="":
            continue
        row["fcf"]=row["cfo"]-row["capex"] if row["cfo"]!="" and row["capex"]!="" else ""
        out.append(row)
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--years",type=int,default=5)
    parser.add_argument("--input-dir",type=Path,help="Optional local SEC fixture; no HTTP when supplied")
    args=parser.parse_args()
    if args.years not in range(1,11):
        parser.error("--years must be 1..10")
    ua=os.environ.get("SEC_USER_AGENT","").strip()
    if not args.input_dir and "@" not in ua:
        raise SystemExit("Missing SEC_USER_AGENT; comparison not run")

    rows=[]
    for ticker,cik in COMPANIES.items():
        if args.input_dir:
            filename=args.input_dir/f"CIK{cik}.json"
            if not filename.exists():
                print(f"SEC_FILE_MISSING {ticker}: {filename.name}",file=sys.stderr)
                continue
            payload=json.loads(filename.read_text(encoding="utf-8"))
        else:
            url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            req=Request(url,headers={"User-Agent":ua,"Accept":"application/json"})
            with urlopen(req,timeout=45) as resp:
                payload=json.loads(resp.read(16_000_000))
            time.sleep(0.3)
        new=records_for_company(payload,ticker,args.years)
        rows.extend(new)
        # Partial history is a data-availability note, not a reason to invent 5 years.
        print(f"SEC_REFERENCE {ticker} FY_records={len(new)}" + (" PARTIAL_HISTORY" if len(new)<args.years else ""))

    if not rows:
        raise SystemExit("No SEC fiscal references; refusing empty crosscheck")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"SEC-only annual reference prepared: {len(rows)} company-years; FMP data not stored")


if __name__=="__main__":
    main()
