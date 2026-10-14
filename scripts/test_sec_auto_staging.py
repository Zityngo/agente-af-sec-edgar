"""Offline QA of SEC -> staging. No network and no Google credentials."""
import gzip
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_auto_staging import verified, build, metric, write_staging, COLUMNS

def fixture(root, tamper=False):
    cik="0000320187"
    accession1="0000320187-25-000001"
    accession2="0000320187-25-000002"
    recent={"form":["10-K","10-Q"],"filingDate":["2025-07-10","2025-10-01"],
            "reportDate":["2025-05-31","2025-08-31"],
            "accessionNumber":[accession1,accession2],"primaryDocument":["fy.htm","q.htm"]}
    def fact(tag,values):
        return {tag:{"units":{"USD":values}}}
    def v(acc,form,start,end,value):
        return {"accn":acc,"form":form,"start":start,"end":end,"val":value}
    fy={"acc":accession1,"form":"10-K","start":"2024-06-01","end":"2025-05-31"}
    q={"acc":accession2,"form":"10-Q","start":"2025-06-01","end":"2025-08-31"}
    def both(a,b):
        return [v(fy["acc"],fy["form"],fy["start"],fy["end"],a),
                v(q["acc"],q["form"],q["start"],q["end"],b)]
    data={}
    data.update(fact("Revenues",both(1000,250)))
    data.update(fact("NetIncomeLoss",both(100,25)))
    data.update(fact("OperatingIncomeLoss",both(170,40)))
    data.update(fact("NetCashProvidedByUsedInOperatingActivities",both(200,60)))
    data.update(fact("PaymentsToAcquirePropertyPlantAndEquipment",both(50,10)))
    companyfacts={"cik":320187,"facts":{"us-gaap":data}}
    submissions={"cik":320187,"filings":{"recent":recent}}
    firm={"cik":cik,"symbols":["NKE"],"status":"OK"}
    for typ,obj in (("companyfacts",companyfacts),("submissions",submissions)):
        raw=json.dumps(obj).encode()
        folder=root/("CIK"+cik)
        folder.mkdir(parents=True,exist_ok=True)
        (folder/(typ+".json.gz")).write_bytes(gzip.compress(raw))
        firm["sha256_"+typ]=hashlib.sha256(raw).hexdigest()
    if tamper: firm["sha256_companyfacts"]="0"*64
    (root/"sp500_batch_manifest.json").write_text(json.dumps({
        "schema":"SEC_SP500_BATCH_V1","companies":[firm]}))
    return companyfacts

class StageQaTests(unittest.TestCase):
    def test_build_and_no_authorized_write(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fixture(root)
            rows=build(root)
            self.assertEqual(len(rows),2)
            self.assertEqual({row[4]:row[13] for row in rows},{"FY":150,"Q":50})
            self.assertEqual(len(COLUMNS),21)
            self.assertEqual(write_staging(rows,"","",False)["state"],"DRY_RUN")

    def test_hash_and_cik_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fixture(root,tamper=True)
            with self.assertRaisesRegex(ValueError,"SHA256"):
                list(verified(root))

    def test_ytd_cash_flow_not_quarterly(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            facts=fixture(root)["facts"]
            filing={"kind":"Q","form":"10-Q","end":"2025-11-30","acc":"X"}
            facts["us-gaap"]["NetCashProvidedByUsedInOperatingActivities"]["units"]["USD"].append(
                {"accn":"X","form":"10-Q","start":"2025-06-01",
                 "end":"2025-11-30","val":700})
            self.assertEqual(metric(facts,"cfo",filing),(None,None))

    def test_write_requires_credentials(self):
        with self.assertRaisesRegex(ValueError,"Faltan"):
            write_staging([],"","",True)

if __name__=="__main__":
    unittest.main()
