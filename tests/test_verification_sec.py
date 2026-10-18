"""Regression tests for SEC metric lineage and documented FY2025 case studies."""
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"scripts")]
from af_core.verification import capex_quality,attributable_quality,ebit_quality
from af_core.metrics import _fcf, _ebit, ttm_metrics
import normalize_sp500_v2 as nm

def sec_period(**kw):
    p={"period_type":"FY","accession":"0000320193-25-000079",
       "operating_income_method":"reported_OperatingIncomeLoss",
       "operating_income":100.0,"cfo":150.0,"capex":50.0,
       "net_income":100.0,"sources_json":json.dumps({
           "operating_income":{"tag":"OperatingIncomeLoss"},
           "capex":{"tag":"PaymentsToAcquirePropertyPlantAndEquipment"},
           "net_income":{"tag":"NetIncomeLossAvailableToCommonStockholdersBasic"}})}
    p.update(kw);return p

class TestSECGates(unittest.TestCase):
    def test_ebit_reported_ok(self):
        p=sec_period();self.assertEqual(ebit_quality(p)[0],"OK")
        self.assertEqual(_ebit(p).v,100)
    def test_ebit_derived_blocked(self):
        self.assertEqual(_ebit(sec_period(operating_income_method="revenue_minus_OperatingCostsAndExpenses")).s,"BLOCKED")
    def test_ebit_wrong_sec_tag_blocked(self):
        p=sec_period(sources_json=json.dumps({"operating_income":{"tag":"PretaxIncome"}}))
        self.assertEqual(_ebit(p).s,"BLOCKED")
    def test_capex_other_productive_assets_blocked(self):
        p=sec_period(sources_json=json.dumps({"capex":{"tag":"PaymentsToAcquireOtherProductiveAssets"}}))
        self.assertEqual(_fcf(p).s,"BLOCKED")
        self.assertIsNone(_fcf(p).v)
    def test_capex_pp_e_allowed(self):
        self.assertEqual(_fcf(sec_period()).v,100)
    def test_capex_derived_no_9m_origin_blocked(self):
        p=sec_period(sources_json=json.dumps({"capex":{"derived_from":"FY_minus_9M",
               "annual_source":{"tag":"PaymentsToAcquirePropertyPlantAndEquipment"}}}))
        self.assertEqual(capex_quality(p)[0],"BLOCKED")
    def test_capex_derived_both_sources(self):
        ok={"tag":"PaymentsToAcquirePropertyPlantAndEquipment"}
        p=sec_period(sources_json=json.dumps({"capex":{"derived_from":"FY_minus_9M",
                        "annual_source":ok,"nine_month_source":ok}}))
        self.assertEqual(capex_quality(p)[0],"OK")
    def test_sec_without_capex_provenance_block(self):
        p=sec_period(sources_json="{}")
        self.assertEqual(_fcf(p).s,"BLOCKED")
    def test_consolidated_profit_loss_blocked(self):
        p=sec_period(sources_json=json.dumps({"net_income":{"tag":"ProfitLoss"}}))
        self.assertEqual(attributable_quality(p)[0],"BLOCKED")
    def test_parent_profit_proxy(self):
        p=sec_period(sources_json=json.dumps({"net_income":{"tag":"NetIncomeLoss"}}))
        self.assertEqual(attributable_quality(p)[0],"PROXY")
    def test_common_profit_ok(self):
        self.assertEqual(attributable_quality(sec_period())[0],"OK")
    def test_no_inferred_q4_eps(self):
        # A genuine Q4 EPS must have a reporting start/end and an acceptable form.
        self.assertNotIn("FY_minus_9M",nm.TAG["eps_diluted"])
        self.assertIsNone(nm.select({},"eps_diluted","2025-12-31",nm.ANNUAL_FORMS,2025,days=(70,112))[0])
    def test_fcf_ttm_blocks_unapproved_quarter(self):
        q=[]
        for t in range(4):
            p=sec_period(period_type=f"Q{t+1}",revenue=250,da=10,eps_diluted=None,debt_total=0,cash=0)
            if t==2:p["sources_json"]=json.dumps({"capex":{"tag":"PaymentsToAcquireOtherProductiveAssets"}})
            q.append(p)
        self.assertEqual(ttm_metrics(q)["fcf_ttm"].s,"BLOCKED")

class BenchmarksFY2025(unittest.TestCase):
    """Hand-verified against 2025 Form 10-K, USD millions; metadata test, not SEC API proof."""
    def test_apple_10k_formula(self):
        self.assertEqual(111_482-12_715,98_767)
        self.assertAlmostEqual(133_050/416_161,.319705,places=4)
    def test_tesla_net_income_attribution(self):
        self.assertEqual(3_855-61,3_794)
        self.assertEqual(14_747-8_527,6_220)
    def test_amazon_distinct_fcf_methods(self):
        self.assertEqual(139_514-131_819,7_695)
        self.assertEqual(139_514-128_320,11_194)
        self.assertNotEqual(7_695,11_194)

if __name__=="__main__":unittest.main()
