import unittest
from af_core.balance_reconciliation import Balance,reconcile,enterprise_value
class DebtLeaseReconciliation(unittest.TestCase):
 def test_tesla_fin_and_operating_lease(self):
  b=Balance(17853,27594,1311,7956,76,180,1075,5847,"EXCLUDED")
  a=reconcile(b)
  self.assertEqual(a["gross_financial_debt"],9267)
  self.assertEqual(a["net_debt_strict"],-8586)
  self.assertEqual(a["net_debt_liquid_assets"],-36180)
  self.assertEqual(a["finance_lease_obligation"],256)
  self.assertEqual(a["operating_lease_obligation"],6922)
  self.assertEqual(a["net_debt_all_leases"],-29002)
 def test_pepsi_q3_no_leasing_value(self):
  b=Balance(10675,488,9223,42658,finance_lease_mode="UNKNOWN")
  a=reconcile(b)
  self.assertEqual(a["gross_financial_debt"],51881)
  self.assertEqual(a["net_debt_strict"],41206)
  self.assertEqual(a["net_debt_liquid_assets"],40718)
  self.assertIsNone(a["net_debt_all_leases"])
  self.assertEqual(a["lease_adjustment_status"],"BLOCKED_INCOMPLETE_Q3_LEASES")
 def test_included_finance_not_counted_twice(self):
  b=Balance(10,2,20,10,3,4,5,6,"INCLUDED")
  a=reconcile(b);self.assertEqual(a["net_debt_all_leases"],29)
 def test_unknown_finance_not_counted_as_zero(self):
  b=Balance(10,2,20,10,3,4,5,6,"UNKNOWN")
  self.assertIsNone(reconcile(b)["net_debt_all_leases"])
 def test_partial_operating_lease_blocks(self):
  b=Balance(10,2,20,10,1,1,5,None,"EXCLUDED")
  self.assertIsNone(reconcile(b)["net_debt_all_leases"])
 def test_missing_value_is_not_zero(self):
  b=Balance(10,2,20,10,None,None,None,None,"EXCLUDED")
  self.assertIsNone(reconcile(b)["net_debt_all_leases"])
 def test_ev_no_fabrication(self):
  self.assertIsNone(enterprise_value(200,None))
  self.assertEqual(enterprise_value(200,-29),171)
 def test_negative_cash_and_lease_rejected(self):
  with self.assertRaises(ValueError):reconcile(Balance(-1,0,0,0))
  with self.assertRaises(ValueError):reconcile(Balance(10,0,0,0,operating_lease_current=-2))
 def test_bools_rejected(self):
  with self.assertRaises(ValueError):reconcile(Balance(True,1,0,0))
