import sys, json, threading, tempfile, unittest, os, urllib.request, urllib.error
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path[:0] = [str(ROOT), str(ROOT / "tests"), str(ROOT / "scripts")]
import build_demo_db
from af_core.api import make_server

class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(); db = Path(cls.tmp) / "demo.db"; build_demo_db.main(db)
        cls.srv = make_server(db, ROOT / "app", port=0); cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()
    def get(self, path):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as r: return r.status, r.read().decode()
        except urllib.error.HTTPError as e: return e.code, e.read().decode()

    def test_search_company_and_quality(self):
        c, b = self.get("/api/search?q=SYN"); self.assertEqual(c, 200); tk = {x["ticker"]: x for x in json.loads(b)}
        self.assertGreater(tk["SYNADP"]["blocks"], 0); self.assertEqual(tk["SYNTEC"]["blocks"], 0)
        d = json.loads(self.get("/api/company?ticker=SYNADP")[1]); self.assertEqual(d["ttm"]["ebit_ttm"]["status"], "BLOCKED")
        self.assertTrue(any(x["check_id"] == "ebit_not_reported" for x in d["checks"]))

    def test_aapl_only_cfo_everything_else_null(self):
        d = json.loads(self.get("/api/company?ticker=AAPL")[1])
        self.assertEqual(d["ttm"]["cfo_ttm"]["value"], 146_724_000_000); self.assertEqual(d["ttm"]["revenue_ttm"]["status"], "NULL")
        self.assertIsNone(d["ttm"]["revenue_ttm"]["value"])

    def test_screener_excludes_blocked_null_and_na(self):
        rows = json.loads(self.get("/api/screener?metric=ebit_margin_ttm&scope=TTM")[1]); t = {r["ticker"] for r in rows}
        self.assertIn("SYNTEC", t); self.assertFalse(t & {"SYNADP", "SYNBANK", "AAPL"})

    def test_financial_valuation_not_applicable(self):
        d = json.loads(self.get("/api/company?ticker=SYNBANK")[1]); self.assertEqual(d["ttm"]["ev_ebitda"]["status"], "NA_SECTOR")

    def test_errors_and_static_and_traversal(self):
        self.assertEqual(self.get("/api/company?ticker=NOPE")[0], 404)
        self.assertEqual(self.get("/api/raw?ticker=SYNTEC&field=sqlite_master")[0], 400)
        c, b = self.get("/"); self.assertEqual(c, 200); self.assertIn("A.Fundamental", b)
        self.assertEqual(self.get("/../af_core/db.py")[0], 404)

    def test_provenance(self):
        p = json.loads(self.get("/api/provenance?ticker=AAPL&ptype=Q4&fy=2025")[1])
        self.assertEqual(p["derived"], 1); self.assertEqual(p["accession"], "0000320193-25-000079")

if __name__ == "__main__": unittest.main()
