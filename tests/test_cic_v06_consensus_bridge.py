"""Self-contained tests for installed plugin; no SEC/FMP copyrighted fixtures."""
import copy, unittest
from types import SimpleNamespace
class SyntheticEngine:
    VERSION='synthetic-only'
    @staticmethod
    def margin_percent(a,b):
        return SimpleNamespace(value=a/b*100)
    @staticmethod
    def growth_percent(a,b):
        return SimpleNamespace(value=(a/b-1)*100)
cic_engine=SyntheticEngine

from integrations.cic_consensus_guard import build_model

def data():
    return {
      'ticker':'TEST','units':'USD billions','asof_date':'2026-11-06',
      'historical_quarters': [
       {'year':2026,'quarter':f'Q{i}','revenue':100.0+i,'operating_income':10.0+i,
        'source_type':'OFICIAL','filed':f'2026-{i*3:02d}-30','source_url':'https://example.org/issuer'} for i in range(1,4)],
      'guidance_q4':{'fiscal_year':2026,'basis':'OFICIAL','source_url':'https://example.org/official',
        'revenue_low':100.0,'revenue_high':102.0,'operating_income_low':10.0,'operating_income_high':12.0},
      'guidance_cash_capex_anchor_year':50.0,
      'provider_anchor_year':{'revenue_avg':408.0,'ebit_avg':80.0},
      'forecasts':[{'year':y,'revenue_low':400.0+10*(y-2026),
         'revenue_avg':410.0+10*(y-2026),'revenue_high':420.0+10*(y-2026),
         'analyst_count_revenue':35,'source_type':'PROVEEDOR',
         'source':'Synthetic consensus','source_url':'https://example.org/vendor',
         'retrieved_at':'2026-11-06'} for y in range(2027,2031)]
    }

class TestGenericConsensus(unittest.TestCase):
 def test_five_years_and_value_blocked(self):
    v=build_model(data(),engine=cic_engine);self.assertEqual(len(v['fiscal_years']),5)
    self.assertIsNone(v['valuation']['value_usd_per_share'])
 def test_fmp_ebit_inconsistent_quarantined(self):
    v=build_model(data(),engine=cic_engine)
    self.assertEqual(v['anchor_consensus_ebit_status'],'NO_COMPARABLE_PENDIENTE_DEFINICION')
 def test_null_provider_revenue_rejected(self):
    d=data();d['forecasts'][0]['revenue_avg']=None
    with self.assertRaises(ValueError):build_model(d,engine=cic_engine)
 def test_low_consensus_count_rejected(self):
    d=data();d['forecasts'][2]['analyst_count_revenue']=10
    with self.assertRaises(ValueError):build_model(d,engine=cic_engine)
 def test_sixth_year_rejected(self):
    d=data();d['forecasts'].append(dict(d['forecasts'][3],year=2031))
    with self.assertRaises(ValueError):build_model(d,engine=cic_engine)
 def test_unit_conversion_not_silent(self):
    d=data();d['units']='EUR millions'
    with self.assertRaises(ValueError):build_model(d,engine=cic_engine)
 def test_positive_growth_calculated_with_engine(self):
    v=build_model(data(),engine=cic_engine)
    self.assertGreater(v['fiscal_years'][2]['revenue_growth_pct'],0)
if __name__=='__main__':unittest.main()
