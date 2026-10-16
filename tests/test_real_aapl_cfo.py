"""Validación con datos SEC REALES de Apple (solo CFO). Procedencia en tests/aapl_real.py."""
import sys, unittest, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); sys.path.insert(0, str(Path(__file__).parent))
from scripts.sec_quarterly_cashflow import isolate_ytd_flow      # original del repo (scripts/)
from af_core.db import connect_rw
from af_core import ingest
from af_core.cli import recompute
from fixtures import row, write_csv
import aapl_real as A
M = A.M

class RealAapl(unittest.TestCase):
    def test_isolate_q2_q3_fy26_from_ytd(self):
        q2, s2 = isolate_ytd_flow(A.FACTS, A.TAGS, dict(kind="Q", form="10-Q", end="2026-03-28", filed="2026-05-01", acc="0000320193-26-000013"), "cfo")
        q3, s3 = isolate_ytd_flow(A.FACTS, A.TAGS, dict(kind="Q", form="10-Q", end="2026-06-27", filed="2026-07-31", acc="0000320193-26-000020"), "cfo")
        self.assertEqual(q2, (82627 - 53925) * M); self.assertEqual(q3, (116996 - 82627) * M)
        self.assertEqual(s3["previous"]["accn"], "0000320193-26-000013")

    def test_ttm_cfo_engine_equals_independent_identity(self):
        rows = [row("0000320193", "AAPL", q, int(y), end, cfo=v * M, accn=acc, entity="Apple Inc.") for y, q, end, v, acc in A.quarterly_rows()]
        t = tempfile.mkdtemp(); a, qf = os.path.join(t, "a.csv"), os.path.join(t, "q.csv")
        write_csv(a, []); write_csv(qf, rows)
        con = connect_rw(os.path.join(t, "x.db")); ingest.ingest_csvs(con, a, qf); recompute(con)
        got = con.execute("SELECT value FROM metrics WHERE scope='TTM' AND metric='cfo_ttm'").fetchone()["value"]
        self.assertEqual(got, (111482 + 116996 - 81754) * M)   # identidad independiente: FY25 + 9M26 - 9M25
        self.assertEqual(got, 146_724 * M)
        self.assertEqual(con.execute("SELECT status FROM metrics WHERE scope='TTM' AND metric='revenue_ttm'").fetchone()["status"], "NULL")

if __name__ == "__main__": unittest.main()
