"""Public issuer facts only. Test Amazon 2026 SEC Q1-Q3 + Q4 IR guidance."""
import unittest
from test_cic_v06_consensus_bridge import cic_engine
from integrations.cic_consensus_guard import build_model

SEC10Q="https://www.sec.gov/Archives/edgar/data/1018724/000101872426000040/amzn-20260930.htm"
AMZN_IR="https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Third-Quarter-Results/default.aspx"

class TestAmazonOfficialAnchor(unittest.TestCase):
    def test_2026_actuals_plus_q4_guidance_take_priority(self):
        figures=[(1,181.519,23.852),(2,200.606,27.461),(3,201.944,28.076)]
        inp={
          "ticker":"AMZN","units":"USD billions","asof_date":"2026-11-07",
          "historical_quarters":[{"year":2026,"quarter":f"Q{q}",
               "revenue":revenue,"operating_income":operating,
               "source_type":"OFICIAL","source_url":SEC10Q,"filed":"2026-10-29"}
              for q,revenue,operating in figures],
          "guidance_q4":{"fiscal_year":2026,"basis":"OFICIAL",
               "source_url":AMZN_IR,
               "revenue_low":240.,"revenue_high":247.,
               "operating_income_low":28.5,"operating_income_high":33.5},
          "guidance_cash_capex_anchor_year":220.,
          "provider_anchor_year":{"revenue_avg":827.0,"ebit_avg":150.0},
          "forecasts":[{"year":y,"revenue_low":v-10,
                 "revenue_avg":v,"revenue_high":v+10,
                 "analyst_count_revenue":30,
                 "source_type":"PROVEEDOR","source":"Synthetic forward consensus",
                 "retrieved_at":"2026-11-07","source_url":"https://example.org/synthetic"}
                for y,v in zip(range(2027,2031),(960.,1110.,1300.,1450.))]
        }
        out=build_model(inp,engine=cic_engine)
        y=out["fiscal_years"][0]
        self.assertAlmostEqual(y["revenue_low"],824.069,places=3)
        self.assertAlmostEqual(y["revenue_high"],831.069,places=3)
        self.assertAlmostEqual(y["revenue_avg"],827.569,places=3)
        self.assertAlmostEqual(y["ebit_low"],107.889,places=3)
        self.assertAlmostEqual(y["ebit_high"],112.889,places=3)
        self.assertEqual(out["anchor_consensus_ebit_status"],"NO_COMPARABLE_PENDIENTE_DEFINICION")
        self.assertEqual(out["fiscal_years"][1]["data_status"],"PROVEEDOR_CONSENSO_SIN_GUIDANCE_ANUAL")
        self.assertIsNone(out["valuation"]["value_usd_per_share"])
        self.assertIsNone(out["fiscal_years"][-1]["fcff"])
if __name__ == "__main__": unittest.main()
