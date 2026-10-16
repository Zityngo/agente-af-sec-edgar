"""Offline regression for known CIK revenue tags and amendment fallback."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sec_tag_resolution import preferred_tags,recover_amendment

class SecTagResolution(unittest.TestCase):
    def test_wynn_including_tax(self):
        self.assertEqual(preferred_tags('0001174922','revenue',[('us-gaap','Revenues')])[0],
                         ('us-gaap','RevenueFromContractWithCustomerIncludingAssessedTax'))
    def test_exr_consolidated(self):
        self.assertEqual(preferred_tags('0001289490','revenue',[('us-gaap','RevenueFromContractWithCustomerExcludingAssessedTax')])[0],
                         ('us-gaap','Revenues'))
    def test_ibkr_net_interest(self):
        self.assertEqual(preferred_tags('0001381197','revenue',[('us-gaap','Revenues')])[0],
                         ('us-gaap','RevenuesNetOfInterestExpense'))
    def test_unknown_company_keeps_default(self):
        source=[('us-gaap','Revenues'),('us-gaap','SalesRevenueNet')]
        self.assertEqual(preferred_tags('0000012345','revenue',source),source)
    def test_amendment_must_remain_pending(self):
        mod={"form":"10-K/A","filed":"2026-04-30","end":"2025-12-31","acc":"A","doc":"am.htm","kind":"FY"}
        subs={"filings":{"recent":{"form":["10-K/A","10-K"],"reportDate":["2025-12-31"]*2,
            "filingDate":["2026-04-30","2026-01-29"],"accessionNumber":["A","O"],
            "primaryDocument":["am.htm","orig.htm"]}}}
        def metric(facts,name,filing,cik):return (100,None) if filing['acc']=='O' else (None,None)
        orig,metadata=recover_amendment(subs,{},mod,'0001318605',metric)
        self.assertEqual(orig['acc'],'O');self.assertEqual(metadata['amendment_accession'],'A')
    def test_no_amendment_means_no_fallback(self):
        f={"form":"10-K","end":"2025-12-31","acc":"O"}
        self.assertEqual(recover_amendment({}, {}, f, '0001318605',lambda *a:(None,None)),(f,None))

if __name__=='__main__':unittest.main()
