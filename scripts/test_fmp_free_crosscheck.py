#!/usr/bin/env python3
"""Offline regression tests. No account, network, or FMP credits necessary."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE=Path(__file__).with_name('fmp_free_crosscheck.py')
spec=importlib.util.spec_from_file_location('fmp_free_crosscheck',MODULE)
fmp=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fmp)

class Tests(unittest.TestCase):
 def setUp(self):
  self.sec={'ticker':'AAPL','cik':'0000320193','fiscal_year':'2025',
            'period_type':'FY','period_end':'2025-09-27','currency':'USD',
            'revenue':'416161000000','operating_income':'133050000000',
            'gross_profit':'195201000000','net_income':'112010000000',
            'cfo':'111482000000','capex':'12715000000','fcf':'98767000000',
            'cash_unrestricted_v2':'35934000000','short_term_investments_v2':'18763000000',
            'equity':'73733000000','assets':'359241000000'}
  self.entry={'symbol':'AAPL','cik':'0000320193','fiscalYear':'2025',
              'period':'FY','date':'2025-09-27','reportedCurrency':'USD',
              'revenue':416161000000,'operatingIncome':133050000000}
 def test_apple_matching_period(self):
  rows=fmp.compare_one('AAPL','income-statement',self.entry,self.sec)
  x=next(r for r in rows if r['metric_fmp']=='revenue')
  self.assertEqual(x['status'],'MATCH')
 def test_no_ttm_fy_mixing(self):
  entry={**self.entry,'period':'Q3'}
  self.assertEqual(fmp.fiscal_match(entry,self.sec),'FMP_NOT_ANNUAL')
 def test_no_wrong_year(self):
  self.assertEqual(fmp.fiscal_match({**self.entry,'fiscalYear':'2026'},self.sec),'FISCAL_YEAR_MISMATCH')
 def test_no_wrong_currency(self):
  self.assertEqual(fmp.fiscal_match({**self.entry,'reportedCurrency':'EUR'},self.sec),'CURRENCY_MISMATCH')
 def test_no_wrong_cik(self):
  self.assertEqual(fmp.fiscal_match({**self.entry,'cik':'98765'},self.sec),'CIK_MISMATCH')
 def test_capex_sign_normalized(self):
  e={**self.entry,'capitalExpenditure':-12715000000,'operatingCashFlow':111482000000,'freeCashFlow':98767000000}
  rows=fmp.compare_one('AAPL','cash-flow-statement',e,self.sec)
  self.assertTrue(all(r['status']=='MATCH' for r in rows))
 def test_lease_differences_not_compared(self):
  self.assertNotIn('totalDebt',fmp.NUMERIC_FIELDS['balance-sheet-statement'])
  self.assertNotIn('netDebt',fmp.NUMERIC_FIELDS['balance-sheet-statement'])
  self.assertIn('totalDebt',fmp.NON_EQUIVALENT)
 def test_missing_sec_is_null_not_zero(self):
  rows=fmp.compare_one('AAPL','balance-sheet-statement',self.entry,{**self.sec,'cash_unrestricted_v2':''})
  self.assertEqual(next(r for r in rows if r['metric_fmp']=='cashAndCashEquivalents')['status'],'FMP_VALUE_MISSING')
 def test_restrict_api_stops_on_quota(self):
  def blocked(endpoint,ticker,key):raise fmp.APIError(429,'Rate limit')
  rows,events,calls=fmp.crosscheck(['AAPL','CSCO'],{},'FAKE',9,0,fetch=blocked)
  self.assertEqual(calls,1)
  self.assertEqual(events[0]['code'],'429')
 def test_no_key_dry_run(self):
  with patch.dict('os.environ',{},clear=True):
   self.assertEqual(fmp.run(['--dry-run','--tickers','AAPL,CSCO','--max-calls','4']),0)
 def test_qa_priority(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'queue.csv'
   with p.open('w',newline='') as o:
    w=csv.DictWriter(o,fieldnames=['priority','ticker']);w.writeheader();w.writerows([
      {'priority':'P2_VALIDATION','ticker':'MA'},
      {'priority':'P0_VALIDATION','ticker':'AAPL'},
      {'priority':'P1_VALIDATION','ticker':'CSCO'}])
   self.assertEqual(fmp.from_queue(p,2),['AAPL','CSCO'])
if __name__=='__main__':unittest.main()