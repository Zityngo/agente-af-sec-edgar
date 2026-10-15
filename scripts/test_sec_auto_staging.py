"""Offline QA of SEC -> staging. No network and no Google credentials."""
import gzip
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_auto_staging import verified, build, metric, write_staging, COLUMNS, same_accounting_candidate
from sec_quarterly_cashflow import isolate_ytd_flow

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

    def test_ytd_delta_Q2_Q3_and_evidence(self):
        tag="NetCashProvidedByUsedInOperatingActivities"
        def obs(acc, filing, start, end, filed, value):
            return {"accn":acc, "form":filing, "start":start, "end":end, "filed":filed, "val":value}
        facts={"us-gaap":{tag:{"units":{"USD":[
            obs("Q1","10-Q","2026-01-01","2026-03-31","2026-04-29",100),
            obs("Q2","10-Q","2026-01-01","2026-06-30","2026-07-29",240),
            obs("Q3","10-Q","2026-01-01","2026-09-30","2026-10-10",400),
        ]}}}}
        preferred=[("us-gaap",tag)]
        q2={"acc":"Q2","form":"10-Q","kind":"Q","end":"2026-06-30","filed":"2026-07-29"}
        q3={"acc":"Q3","form":"10-Q","kind":"Q","end":"2026-09-30","filed":"2026-10-10"}
        val, provenance = isolate_ytd_flow(facts,preferred,q2,"cfo")
        self.assertEqual(val,140)
        self.assertEqual(provenance["derived_from"],"SAME_TAG_YTD_MINUS_PREVIOUS_YTD")
        self.assertEqual(provenance["previous"]["accn"],"Q1")
        self.assertEqual(isolate_ytd_flow(facts,preferred,q3,"cfo")[0],160)

    def test_ytd_rejects_different_tags_fiscal_years_and_future_publication(self):
        tag="PaymentsToAcquirePropertyPlantAndEquipment"
        current={"accn":"Q2","form":"10-Q","start":"2026-01-01","end":"2026-06-30","filed":"2026-07-29","val":100}
        prior={"accn":"Q1","form":"10-Q","start":"2026-01-01","end":"2026-03-31","filed":"2026-08-01","val":30}
        facts={"us-gaap":{tag:{"units":{"USD":[current,prior]}}}}
        filing={"acc":"Q2","form":"10-Q","kind":"Q","end":"2026-06-30","filed":"2026-07-29"}
        preferred=[("us-gaap",tag)]
        self.assertEqual(isolate_ytd_flow(facts,preferred,filing,"capex"),(None,None))
        prior["filed"]="2026-04-29"
        prior["start"]="2026-01-02"
        self.assertEqual(isolate_ytd_flow(facts,preferred,filing,"capex"),(None,None))
        prior["start"]="2026-01-01"
        self.assertEqual(isolate_ytd_flow(facts,preferred,filing,"capex")[0],70)
        current["val"]=20
        self.assertEqual(isolate_ytd_flow(facts,preferred,filing,"capex"),(None,None))

    def test_staging_upsert_does_not_ignore_extractor_fixes(self):
        row=["x"]*21
        previous=row.copy()
        row[19]="new timestamp"
        self.assertTrue(same_accounting_candidate(previous,row))
        row[11]="200"
        self.assertFalse(same_accounting_candidate(previous,row))
        row[11]=previous[11]
        row[14]="Q_CANDIDATO"
        self.assertFalse(same_accounting_candidate(previous,row))

    def test_write_requires_credentials(self):
        with self.assertRaisesRegex(ValueError,"Faltan"):
            write_staging([],"","",True)

if __name__=="__main__":
    unittest.main()
