import unittest
from af_core.narrative_semantics_v9 import period_change,is_valid_point_in_time,fixed_discount_cashflow,price_return
class NarrativeV9Tests(unittest.TestCase):
 def test_revenue_yoy(self):self.assertAlmostEqual(period_change(110,100)[0],10)
 def test_ebit_yoy_negative(self):self.assertAlmostEqual(period_change(75,100)[0],-25)
 def test_margin_in_pp(self):self.assertEqual(period_change(4.6,7.2,ratio=True)[1],"pp")
 def test_zero_is_not_valid_percent_base(self):self.assertIsNone(period_change(30,0))
 def test_negative_base_is_not_a_percent(self):self.assertIsNone(period_change(10,-20))
 def test_null_not_zero(self):self.assertIsNone(period_change(None,20))
 def test_no_filing_lookahead(self):self.assertFalse(is_valid_point_in_time("2025-02-10","2025-02-03","2026-02-02"))
 def test_filing_already_public(self):self.assertTrue(is_valid_point_in_time("2025-02-04","2025-02-10","2026-02-09",preceding_report_filed="2024-02-09"))
 def test_discount_rate_must_exceed_terminal(self):self.assertIsNone(fixed_discount_cashflow(100,0.03,0.02,0.025))
 def test_discount_formula(self):
  a=fixed_discount_cashflow(4000,0.16,0.14,0.03)
  self.assertAlmostEqual(a["value"],88639.40434116538,places=3)
 def test_price_return(self):self.assertAlmostEqual(price_return(100,120),20)
 def test_missing_price(self):self.assertIsNone(price_return(None,120))
