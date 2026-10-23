import unittest
from scripts.inspect_q3_balance_sources import inspect
class InspectBalance(unittest.TestCase):
 def test_accession_strict(self):
  raw={"facts":{"us-gaap":{"OperatingLeaseLiabilityCurrent":{"units":{"USD":[{"val":100,"end":"2026-09-30","accn":"good","form":"10-Q"},{"val":200,"end":"2026-09-30","accn":"bad","form":"10-Q"}]}}}}}
  r=inspect(raw,"good","2026-09-30")
  self.assertEqual(r["OperatingLeaseLiabilityCurrent"][0]["val"],100)
 def test_missing_current_is_not_zero(self):
  raw={"facts":{"us-gaap":{"OperatingLeaseLiabilityCurrent":{"units":{"USD":[{"val":100,"end":"2025-12-31","filed":"2026-02-01","accn":"old","form":"10-K"}]}}}}}
  r=inspect(raw,"good","2026-09-30")
  self.assertEqual(r["OperatingLeaseLiabilityCurrent"]["status"],"NOT_IN_TARGET_FILING")
 def test_empty_input_does_not_claim_zero(self):
  self.assertEqual(inspect({}, "good", "2026-09-30"),{})
