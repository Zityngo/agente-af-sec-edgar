import unittest
from af_core.sec_insiders import parse_form4_xml,fetch_recent_form4
BUY=b"""<?xml version="1.0"?><ownershipDocument>
<issuer><issuerTradingSymbol>AAPL</issuerTradingSymbol></issuer>
<reportingOwner><reportingOwnerId><rptOwnerName>Test Example</rptOwnerName></reportingOwnerId></reportingOwner>
<nonDerivativeTable>
<nonDerivativeTransaction><securityTitle><value>Common Stock</value></securityTitle>
<transactionDate><value>2026-10-14</value></transactionDate>
<transactionCoding><transactionCode>P</transactionCode></transactionCoding>
<transactionAmounts><transactionShares><value>200</value></transactionShares>
<transactionPricePerShare><value>100</value></transactionPricePerShare>
<transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode></transactionAmounts>
<ownershipNature><directOrIndirectOwnership><value>D</value></directOrIndirectOwnership></ownershipNature>
</nonDerivativeTransaction>
<nonDerivativeTransaction><transactionCoding><transactionCode>M</transactionCode></transactionCoding></nonDerivativeTransaction>
</nonDerivativeTable>
</ownershipDocument>"""
class InsiderChecks(unittest.TestCase):
 def test_p_is_buy_m_is_not_open_market(self):
  p=parse_form4_xml(BUY,"https://www.sec.gov/Archives/edgar/data/320193/example.xml","TEST")
  self.assertEqual(p["issuer"],"AAPL")
  self.assertEqual([r["open_market"] for r in p["transactions"]],[True,False])
  self.assertEqual(p["transactions"][0]["acq_disposal"],"A")
  self.assertIsNone(p["transactions"][0]["plan_10b5_1_confirmed"])
 def test_invalid_xml_is_rejected(self):
  with self.assertRaises(ValueError):parse_form4_xml(b"<html />")
 def test_no_form4_not_assumed_no_activity(self):
  self.assertEqual(fetch_recent_form4([{"form":"10-K"}],"AAPL",fetch=lambda u:BUY),[])
 def test_wrong_issuer_is_blocked(self):
  x=fetch_recent_form4([{"form":"4","url":"https://www.sec.gov/x.xml","accession":"A"}],
          "TSLA",fetch=lambda u:BUY)
  self.assertEqual(x[0]["status"],"BLOCKED_TICKER_MISMATCH")
 def test_missing_document_is_unavailable(self):
  x=fetch_recent_form4([{"form":"4","url":"https://www.sec.gov/x.xml","accession":"A"}],
          "AAPL",fetch=lambda u: (_ for _ in ()).throw(OSError("missing")))
  self.assertEqual(x[0]["status"],"UNAVAILABLE")
if __name__=="__main__": unittest.main()
