"""Offline tests; no API calls and no downloaded financial data."""
import gzip, hashlib, json, tempfile, unittest
from pathlib import Path
import os, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qa_sec_daily_batch_v75 import verify_snapshot

class TestDailyQA(unittest.TestCase):
    def test_valid_with_recent_filing_and_duplicate_guard(self):
        from datetime import datetime,timezone
        today=datetime.now(timezone.utc).date().isoformat()
        cik='0000789019'
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);sub={'cik':789019,'filings':{'recent':{
                'form':['10-Q','8-K'],'filingDate':[today,'2010-01-01'],
                'accessionNumber':['0001193125-26-123456','0001193125-10-111111'],
                'primaryDocument':['report.htm','old.htm'],
                'reportDate':[today,'2010-01-01'],'items':['','2.02']}}}
            facts={'cik':789019,'facts':{'us-gaap':{}}}
            expected={}
            for typ,raw in [('submissions',sub),('companyfacts',facts)]:
                b=json.dumps(raw).encode();p=root/f'CIK{cik}'/f'{typ}.json.gz';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(gzip.compress(b))
                expected['sha256_'+typ]=hashlib.sha256(b).hexdigest()
            record={'cik':cik,'symbols':['MSFT'],'status':'OK',**expected}
            manifest=root/'sp500_batch_manifest.json'
            manifest.write_text(json.dumps({'schema':'SEC_SP500_BATCH_V1','companies':[record]}))
            qa,events=verify_snapshot(manifest,today)
            self.assertEqual(qa['status'],'PASS')
            self.assertEqual(qa['recent_filings'],1)
            self.assertEqual(events[0]['ticker'],'MSFT')
            self.assertTrue(events[0]['official_url'].endswith('/report.htm'))
            # Negative: fail CLOSED on hash mismatch, never pretend to have checked data.
            record['sha256_companyfacts']='0'*64
            manifest.write_text(json.dumps({'schema':'SEC_SP500_BATCH_V1','companies':[record]}))
            qa,events=verify_snapshot(manifest,today)
            self.assertEqual(qa['status'],'FAIL_REVIEW')
            self.assertEqual(qa['validated_companies'],0)
            self.assertFalse(events)

if __name__=='__main__':unittest.main()