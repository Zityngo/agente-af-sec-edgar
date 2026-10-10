"""Verificación reproducible de cobertura del S&P 500 tras unir lotes SEC."""
from __future__ import annotations
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE / "publico" / "sec"

def main():
    if "--check" in sys.argv:
        summary = json.loads((ROOT / "bootstrap_summary.json").read_text(encoding="utf-8"))
        if not summary["complete"]:
            raise SystemExit(
                f"Bootstrap INCOMPLETO: {summary['downloaded_company_count']}/"
                f"{summary['expected_company_count']} CIK, "
                f"{len(summary['failed_ciks'])} fallos."
            )
        print(f"BOOTSTRAP VALIDADO: {summary['downloaded_company_count']}/"
              f"{summary['expected_company_count']} CIK.", flush=True)
        return

    firms = {}
    with (BASE / "universo_sp500.csv").open(encoding="utf-8-sig", newline="") as fp:
        for r in csv.DictReader(fp):
            cik=r["CIK"].zfill(10)
            firms.setdefault(cik,[]).append(r["Symbol"])
    expected=set(firms)
    manifests=sorted((ROOT / "batches").glob("sp500_batch_*.json"))
    seen={}
    failed={}
    for manifest in manifests:
        data=json.loads(manifest.read_text(encoding="utf-8"))
        for c in data["companies"]:
            cik=c["cik"]
            p=ROOT / f"CIK{cik}"
            if c["status"]=="OK" and (p/"submissions.json.gz").is_file() and (p/"companyfacts.json.gz").is_file():
                seen[cik]={"symbols":c["symbols"],"status":"OK"}
            else:
                failed[cik]={"symbols":c["symbols"],"error":c.get("error","archivos no encontrados")}
    missing=expected-set(seen)
    report={
        "schema":"SEC_SP500_BOOTSTRAP_REPORT_V1",
        "created_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source":"universo_sp500.csv",
        "expected_company_count":len(expected),
        "expected_stock_count":sum(map(len,firms.values())),
        "downloaded_company_count":len(expected & set(seen)),
        "manifest_count":len(manifests),
        "missing_ciks":sorted(missing),
        "failed_ciks":{k:failed.get(k,{"symbols":firms[k], "error":"sin manifiesto"}) for k in sorted(missing)},
        "complete":set(seen)==expected
    }
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/"bootstrap_summary.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("SEC SP500 BOOTSTRAP:",report["downloaded_company_count"],"/",
          report["expected_company_count"],"CIK; ",
          len(manifests),"manifiestos; ",
          len(missing),"faltantes.",flush=True)
    if missing:
        print("CIK pendientes:",",".join(sorted(missing)),flush=True)

if __name__=="__main__":
    main()
