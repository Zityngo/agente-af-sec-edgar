"""Private three-issuer review pack: valuations stay explicitly illustrative."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_jons_review import discounted_cash_proxy, load_snapshot, render_html

class ReviewPack(unittest.TestCase):
    def setUp(self):
        self.reference=ROOT/"data/pilot_price_reference_2026-10-20.json"

    def test_three_prices_and_share_filings(self):
        p=load_snapshot(self.reference)
        self.assertEqual(set(p["companies"]),{"AAPL","TSLA","AMZN"})
        self.assertEqual(p["companies"]["AAPL"]["price_usd"],339.5)
        self.assertEqual(p["companies"]["TSLA"]["shares"],3949547394)

    def test_share_date_must_precede_quote(self):
        bad=json.loads(self.reference.read_text())
        bad["companies"]["AAPL"]["shares_date"]="2026-12-31"
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"p.json";path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):load_snapshot(path)

    def test_dcf_formula_terminal_weight(self):
        ans=discounted_cash_proxy(1000,100,0.03,0.1,0.025)
        self.assertIsNotNone(ans)
        self.assertGreater(ans["per_share"],10)
        self.assertLess(ans["terminal_pct"],100)

    def test_no_fcf_forecast_from_negative_fcf(self):
        self.assertIsNone(discounted_cash_proxy(-10,100,0.03,0.1,0.02))
        self.assertIsNone(discounted_cash_proxy(None,100,0.03,0.1,0.02))

    def test_discount_must_exceed_terminal(self):
        self.assertIsNone(discounted_cash_proxy(1000,100,0.03,0.02,0.04))

    def test_zero_shares_blocked(self):
        self.assertIsNone(discounted_cash_proxy(1000,0,0.03,0.1,0.02))

    def test_html_payload_sanitized(self):
        out=render_html({"company":"</script><script>alert('bad')</script>"},
                        ROOT/"app/jon_review_template.html")
        self.assertNotIn("</script><script>alert",out)
        self.assertIn("const DATA=",out)

    def test_fcf_to_dcf_same_math_for_growth_zero(self):
        result=discounted_cash_proxy(100,10,0.0,0.10,0.0,years=5)
        self.assertAlmostEqual(result["per_share"],100,places=8)
        self.assertEqual(result["method"],
                         "ILLUSTRATIVE_CFO_MINUS_GROSS_CAPEX_ZERO_NET_BORROWINGS_NOT_CERTIFIED")

if __name__=="__main__":unittest.main()
