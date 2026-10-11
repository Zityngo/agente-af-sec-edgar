#!/usr/bin/env python3
"""Audit SEC companyfacts JSON files in an extracted archive. No network or credentials.

Usage: python scripts/audit_sec_coverage.py /path/to/extracted --out coverage.csv
Outputs coverage per CIK and year for audited annual income/balance/cashflow concepts.
A populated concept is NOT proof that a full annual report has been archived.
"""
import argparse, csv, json
from pathlib import Path

CONCEPTS = {
    "revenue": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"),
    "net_income": ("NetIncomeLoss",),
    "assets": ("Assets",),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment",),
}
def inspect(path, start, end):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict) or "facts" not in data or "cik" not in data:
        return []
    facts = data.get("facts", {})
    taxonomies = [facts.get("us-gaap", {}), facts.get("ifrs-full", {})]
    rows = []
    for year in range(start, end + 1):
        found = {}
        for metric, tags in CONCEPTS.items():
            found[metric] = False
            for taxonomy in taxonomies:
                for tag in tags:
                    for values in taxonomy.get(tag, {}).get("units", {}).values():
                        if any(str(v.get("fy")) == str(year) and v.get("form") in ("10-K", "10-K/A", "20-F", "20-F/A") and v.get("val") is not None for v in values):
                            found[metric] = True
                            break
                    if found[metric]: break
                if found[metric]: break
        rows.append({"cik": str(data["cik"]).zfill(10), "entity": data.get("entityName", ""), "year": year, **{k: int(v) for k,v in found.items()}, "metrics_present": sum(found.values()), "source_file": str(path)})
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", type=Path)
    ap.add_argument("--out", type=Path, default=Path("coverage.csv"))
    ap.add_argument("--start", type=int, default=2016)
    ap.add_argument("--end", type=int, default=2026)
    args = ap.parse_args()
    if not args.directory.is_dir() or args.start > args.end:
        ap.error("Provide an existing directory and valid year interval")
    rows = []
    for path in args.directory.rglob("*.json"):
        rows.extend(inspect(path, args.start, args.end))
    keys = ["cik","entity","year",*CONCEPTS,"metrics_present","source_file"]
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Audited {len(set(r['cik'] for r in rows))} CIKs; {len(rows)} company-years; output {args.out}")
    print("Caution: missing values may reflect taxonomy differences, not absent financial statements.")
if __name__ == "__main__":
    main()
