"""2026-11-07 guidance-first regression, all data synthetic."""
import copy
import unittest
from test_cic_v06_consensus_bridge import data, cic_engine
from integrations.cic_consensus_guard import build_model

class TestGuidancePriority(unittest.TestCase):
    @staticmethod
    def official2027():
        return {
          "year": 2027, "source_type": "OFICIAL",
          "source_url": "https://issuer.example/ir/guidance",
          "published_at": "2026-10-29",
          "revenue_low": 470., "revenue_high": 490.,
          "operating_income_low": 45., "operating_income_high": 55.,
          "cash_capex": None
        }
    def test_no_guidance_means_consensus_not_official(self):
        v=build_model(data(),engine=cic_engine)
        y=v["fiscal_years"][1]
        self.assertEqual(y["data_status"],"PROVEEDOR_CONSENSO_SIN_GUIDANCE_ANUAL")
        self.assertEqual(y["source_priority"],"PROVEEDOR_SIN_GUIDANCE")
    def test_guidance_overrides_provider_for_same_year(self):
        d=data();d["official_guidance_years"]=[self.official2027()]
        v=build_model(d,engine=cic_engine)
        y=v["fiscal_years"][1]
        self.assertEqual(y["revenue_avg"],480.)
        self.assertEqual(y["source_priority"],"OFICIAL")
        self.assertEqual(y["ebit_low"],45.)
        self.assertIsNone(y["fcff"])
        self.assertTrue(any(x["metric"]=="revenue_avg_2027" for x in v["discrepancies"]))
    def test_annual_guidance_works_even_if_provider_low_coverage(self):
        d=data();d["official_guidance_years"]=[self.official2027()]
        d["forecasts"][0]["analyst_count_revenue"]=5
        v=build_model(d,engine=cic_engine)
        self.assertEqual(v["fiscal_years"][1]["revenue_avg"],480.)
        self.assertIsNone(v["fiscal_years"][1]["consensus_revenue_avg"])
    def test_future_dated_guidance_rejected(self):
        d=data();g=self.official2027();g["published_at"]="2027-01-12"
        d["official_guidance_years"]=[g]
        with self.assertRaises(ValueError):
            build_model(d,engine=cic_engine)
    def test_wrong_period_guidance_rejected(self):
        d=data();g=self.official2027();g["year"]=2031
        d["official_guidance_years"]=[g]
        with self.assertRaises(ValueError):build_model(d,engine=cic_engine)
    def test_missing_guidance_but_low_vendor_count_rejected(self):
        d=data();d["forecasts"][0]["analyst_count_revenue"]=5
        with self.assertRaises(ValueError):build_model(d,engine=cic_engine)
    def test_invalid_guidance_range_rejected(self):
        d=data();g=self.official2027();g["revenue_high"]=300.
        d["official_guidance_years"]=[g]
        with self.assertRaises(ValueError):build_model(d,engine=cic_engine)
    def test_missing_cashflow_never_becomes_zero(self):
        d=data();d["official_guidance_years"]=[self.official2027()]
        y=build_model(d,engine=cic_engine)["fiscal_years"][1]
        self.assertIsNone(y["capex"])
        self.assertIsNone(y["operating_cash_flow"])
        self.assertIsNone(y["fcff"])
if __name__ == "__main__":unittest.main()
