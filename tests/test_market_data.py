import unittest
from datetime import datetime,timezone,timedelta
from af_core.market_data import quote_from_ibkr_snapshot,sec_latest_shares,validate_quote_and_shares
now=datetime(2026,10,22,12,12,tzinfo=timezone.utc)
class MarketQuote(unittest.TestCase):
 def test_realtime_and_market_cap(self):
  s={"conid":265598,"31":"343.75","6509":"RpB","_updated":int(now.timestamp()*1000)}
  q=quote_from_ibkr_snapshot(s,"AAPL",asof=now)
  self.assertEqual(q["market_status"],"REALTIME")
  fact={"facts":{"dei":{"EntityCommonStockSharesOutstanding":{"units":{"shares":[
   {"val":14594180000,"filed":"2026-07-30","end":"2026-07-17","form":"10-Q","accn":"0000320193-26-000020"}]}}}}}
  sh=sec_latest_shares(fact,cutoff_date="2026-10-22")
  self.assertEqual(sh["status"],"OFFICIAL")
  c=validate_quote_and_shares(q,sh)
  self.assertAlmostEqual(c["market_cap_usd"],343.75*14594180000)
 def test_delayed_frozen_rejected(self):
  for f in ("DpB","ZpB","YpB","NpB",""):
   with self.subTest(f=f),self.assertRaises(ValueError):
    quote_from_ibkr_snapshot({"conid":265598,"31":"10","6509":f,"_updated":int(now.timestamp()*1000)},"AAPL",asof=now)
 def test_stale_rejected(self):
  with self.assertRaisesRegex(ValueError,"Stale"):
   quote_from_ibkr_snapshot({"conid":265598,"31":"10","6509":"RpB","_updated":int((now-timedelta(hours=1)).timestamp()*1000)},"AAPL",asof=now)
 def test_halted_frozen_prefix_rejected(self):
  with self.assertRaises(ValueError):
   quote_from_ibkr_snapshot({"conid":265598,"31":"C343.75","6509":"RpB","_updated":int(now.timestamp()*1000)},"AAPL",asof=now)
 def test_wrong_conid_rejected(self):
  with self.assertRaises(ValueError):
   quote_from_ibkr_snapshot({"conid":1,"31":"10","6509":"RpB","_updated":int(now.timestamp()*1000)},"AAPL",asof=now)
 def test_future_shares_rejected(self):
  fact={"facts":{"dei":{"EntityCommonStockSharesOutstanding":{"units":{"shares":[{"val":100,"filed":"2026-10-30","end":"2026-10-25","form":"10-Q"}]}}}}}
  self.assertEqual(sec_latest_shares(fact,cutoff_date="2026-10-22")["status"],"BLOCKED")
 def test_not_eps_shares(self):
  fact={"facts":{"us-gaap":{"WeightedAverageNumberOfDilutedSharesOutstanding":{"units":{"shares":[{"val":200,"end":"2026-06-30","filed":"2026-07-30","form":"10-Q"}]}}}}}
  self.assertEqual(sec_latest_shares(fact,cutoff_date="2026-10-22")["status"],"BLOCKED")
if __name__=="__main__":unittest.main()
