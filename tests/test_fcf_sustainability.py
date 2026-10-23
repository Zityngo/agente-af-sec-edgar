import unittest
from af_core.fcf_sustainability import CashPeriod,cash_bridge,fcf_stress,ttm_rollforward,wc_improvement_stress
class FCFTests(unittest.TestCase):
    def test_tesla_9m(self):
        r=cash_bridge(CashPeriod(14897,13014,debt_issuance=5834,debt_repayments=4954,finance_lease_principal=63))
        self.assertEqual((r["fcf_gross"],r["new_borrowings_net"],r["fcfe_financing_proxy"]),(1883,880,2700))
    def test_pepsi_distributions(self):
        r=cash_bridge(CashPeriod(7950,2182,5935,739))
        self.assertEqual((r["fcf_gross"],r["distributions"],r["surplus_after_distributions"]),(5768,6674,-906))
    def test_pepsi_ttm(self):
        r=ttm_rollforward(CashPeriod(12087,4415),CashPeriod(7950,2182),CashPeriod(5468,2499))
        self.assertEqual((r.cfo,r.capex_cash,cash_bridge(r)["fcf_gross"]),(14569,4098,10471))
    def test_tesla_yoy_wc_stress_is_sensitivity(self):
        self.assertEqual(wc_improvement_stress(CashPeriod(14897,13014),3510,1)["stressed_fcf_after_all_capex"],-1627)
        self.assertEqual(wc_improvement_stress(CashPeriod(14897,13014),3510,.5)["stressed_fcf_after_all_capex"],128)
    def test_no_issuer_maintenance_capex_split(self):
        r=fcf_stress(CashPeriod(7950,2182))
        self.assertIsNone(r["maintenance_capex"]);self.assertIn("BLOCKED",r["maintenance_status"])
    def test_maintenance_only_is_not_distributable(self):
        r=fcf_stress(CashPeriod(7950,2182),maintenance_share=.75)
        self.assertAlmostEqual(r["maintenance_capex"],1636.5);self.assertIn("HYPOTHESIS",r["maintenance_status"])
    def test_unavailable_borrowings_not_zero(self):
        self.assertIsNone(cash_bridge(CashPeriod(3,1))["fcfe_financing_proxy"])
    def test_rejects_bad_values(self):
        with self.assertRaises(ValueError):cash_bridge(CashPeriod(8,-3))
        with self.assertRaises(ValueError):fcf_stress(CashPeriod(8,3),maintenance_share=1.1)
        with self.assertRaises(ValueError):wc_improvement_stress(CashPeriod(8,3),3,2)
if __name__=="__main__": unittest.main()
