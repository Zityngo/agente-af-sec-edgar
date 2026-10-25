import unittest
from af_core.price_metric_context import price_mean_by_fiscal_window,roic_components,relative_difference,peg_screen,valuation_allowed
class ContextTest(unittest.TestCase):
 def test_mean(self):
  r=price_mean_by_fiscal_window([("2025-01-02",100),("2025-01-03",110),("2025-04-01",80)],"2025-01-01","2025-03-31")
  self.assertEqual(r["sessions"],2)
  self.assertEqual(r["mean_close"],105)
 def test_qtr_bounds(self):
  r=price_mean_by_fiscal_window([("2026-03-21",110),("2026-03-22",120)],"2026-03-22","2026-06-13")
  self.assertEqual(r["mean_close"],120)
 def test_no_quote(self):
  self.assertIsNone(price_mean_by_fiscal_window([("2024-01-01",10)],"2026-01-01","2026-12-31")["mean_close"])
 def test_duplicate(self):
  with self.assertRaises(ValueError):price_mean_by_fiscal_window([("2025-01-01",100),("2025-01-01",120)],"2025-01-01","2025-12-31")
 def test_invalid(self):
  with self.assertRaises(ValueError):price_mean_by_fiscal_window([("2025-01-01",0)],"2025-01-01","2025-12-31")
 def test_roic(self):self.assertAlmostEqual(roic_components(9670,67777),14.267375658)
 def test_missing_roic_is_null(self):self.assertIsNone(roic_components(None,67777))
 def test_ratios_in_pp(self):self.assertEqual(relative_difference(17.4,18.3,"ratio")["unit"],"pp")
 def test_price_yoy(self):self.assertAlmostEqual(relative_difference(143.3602,169.2791)["value"],-15.311340856609002)
 def test_peg_negative_not_bargain(self):self.assertIsNone(peg_screen(15.2,-1.2)["value"])
 def test_peg_growth_positive(self):self.assertAlmostEqual(peg_screen(15.8,2.1)["value"],7.5238095238)
 def test_no_auto_merge_roic(self):self.assertFalse(valuation_allowed(14.3,17.4,False))
if __name__=="__main__":unittest.main()
