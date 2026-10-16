"""Crea la base de demo: AAPL (CFO REAL verificado, resto NULL) + empresas SINTÉTICAS (SYN*) para casos límite."""
import sys, os, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from af_core.db import connect_rw
from af_core import ingest
from af_core.cli import recompute, load_prices
from fixtures import company_rows, write_csv, row
import aapl_real as A

def main(out=ROOT / "data" / "demo.db"):
    out = Path(out); out.parent.mkdir(exist_ok=True)
    if out.exists(): out.unlink()
    t = tempfile.mkdtemp(); ann, qr = [], []
    for s in [dict(cik="0000000001", tk="SYNTEC"), dict(cik="0000000002", tk="SYNADP", oim="revenue_minus_OperatingCostsAndExpenses"),
              dict(cik="0000000003", tk="SYNBANK", base=5000.0),
              dict(cik="0000000004", tk="SYNUTIL", capex_tag="PaymentsToAcquireOtherProductiveAssets", base=2500.0),
              dict(cik="0000000005", tk="SYNREC", base=800.0, q_over={(2025, 2): {"operating_income": 960*0.2*0.25 + 960*0.2*0.05}})]:
        a, q = company_rows(**s); ann += a; qr += q
    qr += [row("0000320193", "AAPL", q, int(y), end, cfo=v * A.M, accn=acc, entity="Apple Inc.") for y, q, end, v, acc in A.quarterly_rows()]
    ann.append(row("0000320193", "AAPL", "FY", 2025, "2025-09-27", cfo=111482 * A.M, accn="0000320193-25-000079", entity="Apple Inc."))
    uni = os.path.join(t, "u.csv"); Path(uni).write_text("Symbol,Sector\nSYNBANK,Financials\nAAPL,Information Technology\nSYNTEC,Information Technology\n")
    pa, pq = os.path.join(t, "a.csv"), os.path.join(t, "q.csv"); write_csv(pa, ann); write_csv(pq, qr)
    con = connect_rw(out); run, n = ingest.ingest_csvs(con, pa, pq, uni, source="DEMO: sintetico + AAPL CFO real SEC"); recompute(con)
    pf = os.path.join(t, "p.csv"); Path(pf).write_text("ticker,date,close,shares\nSYNTEC,2026-10-15,60,100\nSYNBANK,2026-10-15,300,100\n")
    load_prices(con, pf, "SINTETICO", "no real"); recompute(con); con.close(); print("demo listo", run, n)

if __name__ == "__main__": main()
