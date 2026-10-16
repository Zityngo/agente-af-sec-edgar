import sys, tempfile, unittest, sqlite3, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); sys.path.insert(0, str(Path(__file__).parent))
from af_core.db import connect_rw, connect_ro
from af_core import ingest, qa, query
from af_core.cli import recompute, load_prices
from fixtures import company_rows, write_csv

def build(tmp, specs, universe=None):
    ann, qr = [], []
    for s in specs:
        a, q = company_rows(**s); ann += a; qr += q
    pa, pq = os.path.join(tmp, "a.csv"), os.path.join(tmp, "q.csv"); write_csv(pa, ann); write_csv(pq, qr)
    con = connect_rw(os.path.join(tmp, "t.db")); run, n = ingest.ingest_csvs(con, pa, pq, universe); recompute(con)
    return con, run, n, (pa, pq)

def val(con, tk, scope, metric, pend=None):
    q = "SELECT value,status,reason FROM metrics m JOIN companies c ON c.cik=m.cik WHERE c.ticker=? AND scope=? AND metric=?"; a = [tk, scope, metric]
    if pend: q += " AND period_end=?"; a.append(pend)
    return con.execute(q + " ORDER BY period_end DESC LIMIT 1", a).fetchone()

class Core(unittest.TestCase):
    def setUp(self): self.t = tempfile.TemporaryDirectory(); self.tmp = self.t.name
    def tearDown(self): self.t.cleanup()

    def test_single_engine_values_and_ttm(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA")])
        self.assertAlmostEqual(val(con, "SYNA", "FY", "ebit_margin", "2025-12-31")["value"], 0.2)
        self.assertAlmostEqual(val(con, "SYNA", "FY", "fcf", "2025-12-31")["value"], 1200*0.22 - 1200*0.05)
        self.assertAlmostEqual(val(con, "SYNA", "FY", "revenue_yoy", "2025-12-31")["value"], 1200/1100-1)
        self.assertAlmostEqual(val(con, "SYNA", "TTM", "revenue_ttm")["value"], 1200.0)
        self.assertAlmostEqual(val(con, "SYNA", "TTM", "fcf_ttm")["value"], 1200*0.17)
        self.assertEqual(val(con, "SYNA", "FY", "roic", "2025-12-31")["status"], "PROXY")

    def test_roic_formula(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA")])
        r = val(con, "SYNA", "FY", "roic", "2025-12-31"); t = 1200*0.05/(1200*0.2); ic = lambda f: f*1.0 + f*0.5 - f*0.3
        self.assertAlmostEqual(r["value"], 1200*0.2*(1-t)/((ic(1200)+ic(1100))/2))

    def test_null_is_never_zero(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA", fy_over={2025: {"capex": None}})])
        r = val(con, "SYNA", "FY", "fcf", "2025-12-31")
        self.assertIsNone(r["value"]); self.assertEqual(r["status"], "NULL"); self.assertIn("capex", r["reason"])

    def test_adp_like_ebit_blocked_and_excluded_from_screener(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA"), dict(cik="0000000002", tk="SYNADP", oim="revenue_minus_OperatingCostsAndExpenses")])
        for m in ("ebit", "ebitda", "ebit_margin", "roic"):
            r = val(con, "SYNADP", "FY", m, "2025-12-31"); self.assertEqual(r["status"], "BLOCKED", m); self.assertIsNone(r["value"])
        self.assertEqual(val(con, "SYNADP", "TTM", "ebit_ttm")["status"], "BLOCKED")
        self.assertIn("ebit_not_reported", {c[1] for c in qa.run_checks(con, "0000000002")})
        names = [x["ticker"] for x in query.screener(con, "ebit_margin_ttm", scope="TTM")]
        self.assertIn("SYNA", names); self.assertNotIn("SYNADP", names)

    def test_financials_not_applicable(self):
        uni = os.path.join(self.tmp, "u.csv"); Path(uni).write_text("Symbol,Sector\nSYNB,Financials\nSYNA,Information Technology\n")
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA"), dict(cik="0000000003", tk="SYNB")], universe=uni)
        for m in ("ebitda", "net_debt", "debt_ebitda", "roic"): self.assertEqual(val(con, "SYNB", "FY", m, "2025-12-31")["status"], "NA_SECTOR", m)
        self.assertEqual(val(con, "SYNB", "FY", "roe_avg", "2025-12-31")["status"], "OK")
        self.assertNotEqual(val(con, "SYNA", "FY", "ebitda", "2025-12-31")["status"], "NA_SECTOR")

    def test_reconciliation_block_like_adm(self):
        over = {(2025, 2): {"operating_income": 1200*0.2*0.25 + 1200*0.2*0.04}}
        con, *_ = build(self.tmp, [dict(cik="0000000004", tk="SYNR", q_over=over)])
        self.assertIn(("recon_operating_income", "BLOCK"), {(x[1], x[2]) for x in qa.run_checks(con, "0000000004")})

    def test_clean_company_has_no_block(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA")])
        self.assertNotIn("BLOCK", [x[2] for x in qa.run_checks(con, "0000000001", as_of="2026-01-31")])

    def test_capex_tag_review_like_aep(self):
        con, *_ = build(self.tmp, [dict(cik="0000000005", tk="SYNC", capex_tag="PaymentsToAcquireOtherProductiveAssets")])
        self.assertIn("capex_tag_review", {c[1] for c in qa.run_checks(con, "0000000005")})
        con2, *_ = build(tempfile.mkdtemp(), [dict(cik="0000000006", tk="SYND", capex_tag="PaymentsToAcquirePropertyPlantAndEquipment")])
        self.assertNotIn("capex_tag_review", {c[1] for c in qa.run_checks(con2, "0000000006")})

    def test_ttm_needs_contiguous_quarters_and_eps_gap(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA", q_over={(2025, 3): {"revenue": None}})])
        r = val(con, "SYNA", "TTM", "revenue_ttm"); self.assertIsNone(r["value"]); self.assertEqual(r["status"], "NULL")
        con, *_ = build(tempfile.mkdtemp(), [dict(cik="0000000007", tk="SYNE", qyears=(2025,))])
        r = val(con, "SYNE", "TTM", "eps_ttm"); self.assertIsNone(r["value"]); self.assertIn("EPS", r["reason"])

    def test_valuation_needs_price_and_shares(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA")])
        self.assertIsNone(val(con, "SYNA", "VAL", "per_fy"))
        pf = os.path.join(self.tmp, "p.csv"); Path(pf).write_text("ticker,date,close,shares\nSYNA,2026-01-15,50,100\n")
        load_prices(con, pf, "SINTETICO", "solo test"); recompute(con)
        self.assertAlmostEqual(val(con, "SYNA", "VAL", "per_fy")["value"], 50/(1200*0.15/100))
        self.assertAlmostEqual(val(con, "SYNA", "VAL", "market_cap")["value"], 5000.0)
        self.assertAlmostEqual(val(con, "SYNA", "VAL", "fcf_yield")["value"], 1200*0.17/5000)
        self.assertIsNone(val(con, "SYNA", "VAL", "per_ttm")["value"])

    def test_ingest_idempotent_and_rollback(self):
        con, run1, n1, (pa, pq) = build(self.tmp, [dict(cik="0000000001", tk="SYNA")])
        self.assertEqual(ingest.ingest_csvs(con, pa, pq)[1], 0)
        before = con.execute("SELECT COUNT(*) FROM periods").fetchone()[0]
        a, q = company_rows(cik="0000000001", tk="SYNA", fy_over={2025: {"revenue": 9999.0}}); write_csv(pa, a); write_csv(pq, q)
        run3, n3 = ingest.ingest_csvs(con, pa, pq); self.assertEqual(n3, 1)
        rev = lambda: con.execute("SELECT revenue FROM periods WHERE period_type='FY' AND fiscal_year=2025").fetchone()[0]
        self.assertEqual(rev(), 9999.0); ingest.rollback_run(con, run3)
        self.assertEqual(rev(), 1200.0); self.assertEqual(con.execute("SELECT COUNT(*) FROM periods").fetchone()[0], before)
        ingest.rollback_run(con, run1); self.assertEqual(con.execute("SELECT COUNT(*) FROM periods").fetchone()[0], 0)

    def test_read_only_connection_cannot_write(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA")]); con.close()
        with self.assertRaises(sqlite3.OperationalError): connect_ro(os.path.join(self.tmp, "t.db")).execute("DELETE FROM periods")

    def test_provenance_and_derived_flag(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA")])
        p = query.provenance(con, "SYNA", "Q4", 2025); self.assertEqual(p["derived"], 1); self.assertEqual(p["cik"], "0000000001")
        self.assertEqual(query.provenance(con, "SYNA", "FY", 2025)["derived"], 0)

    def test_ticker_cik_mismatch_blocks_and_survives_recompute(self):
        con, *_ = build(self.tmp, [dict(cik="0000000001", tk="SYNA")])
        a, q = company_rows(cik="0000000001", tk="OTRO"); write_csv(os.path.join(self.tmp, "a2.csv"), a); write_csv(os.path.join(self.tmp, "q2.csv"), q)
        ingest.ingest_csvs(con, os.path.join(self.tmp, "a2.csv"), os.path.join(self.tmp, "q2.csv")); recompute(con)
        self.assertTrue(con.execute("SELECT 1 FROM checks WHERE check_id='ticker_cik_mismatch'").fetchone())

if __name__ == "__main__": unittest.main()
