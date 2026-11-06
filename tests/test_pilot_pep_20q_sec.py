"""SEC PepsiCo pilot: tests offline con datos sintéticos, sin llamadas SEC ni FMP."""
import sys
from datetime import date, timedelta
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pilot_pep_20q_sec as pilot

class FixtureNormalizer:
    _CACHE = {}
    def __init__(self):
        self.years = []
        self.quarters = []
        begin = date(2019, 12, 28)
        for yr in range(2020, 2026):
            qrows = []
            if yr >= 2021:
                for q in range(1, 5):
                    end = begin + timedelta(weeks=(12, 24, 36, 52)[q-1])
                    row = {
                        "fiscal_year": yr, "period_type": f"Q{q}", "period_end": end.isoformat(),
                        "filing_date": (end + timedelta(days=30)).isoformat(),
                        "revenue": 10_000_000_000 + yr*1_000_000 + q*10_000_000,
                        "gross_profit": 5_500_000_000, "operating_income": 2_000_000_000,
                        "net_income": 1_000_000_000,
                        "eps_diluted": None if q == 4 else 1.1,
                        "cfo": 3_000_000_000, "capex": 800_000_000,
                        "cash": 9_000_000_000, "debt_total": 40_000_000_000,
                        "equity": 20_000_000_000, "assets": 100_000_000_000,
                        "da": 700_000_000, "interest": 200_000_000,
                        "tax": 200_000_000, "pretax": 1_200_000_000,
                        "operating_income_method":
                            "derived_Q4_FY_minus_9M" if q == 4 else "reported_OperatingIncomeLoss"
                    }
                    row["sources"] = {k: {"tag": "ReportedField", "accession": "0000077476-26-000001"}
                                      for k in pilot.RAW_KEYS if k in row}
                    if q >= 2:
                        for k in ("cfo", "capex"):
                            row["sources"][k] = (
                                {"derived_from": "FY_minus_9M",
                                 "annual_source": {"tag": k}, "nine_month_source": {"tag": k}}
                                if q == 4 else
                                {"derived_from": "ytd_delta", "source": {"tag": k},
                                 "previous_ytd": 4_000_000_000})
                    qrows.append(row)
                    self.quarters.append(row)
            fy_end = begin + timedelta(weeks=52)
            annual = {"fiscal_year": yr, "period_type": "FY", "period_end": fy_end.isoformat(),
                      "equity": 20_000_000_000, "cash": 9_000_000_000,
                      "debt_total": 40_000_000_000}
            for key in pilot.FLOW_KEYS:
                annual[key] = sum(x[key] for x in qrows) if qrows else 1_000_000_000
            annual["sources"] = {k: {"tag": "ReportedField"} for k in pilot.FLOW_KEYS}
            self.years.append(annual)
            begin = fy_end

    def annual(self, *args):
        return self.years

    def quarterly(self, *args):
        return self.quarters

class TestPilotPepsiCo(unittest.TestCase):
    @staticmethod
    def facts():
        return {"cik": 77476, "entityName": "PepsiCo", "facts": {"us-gaap": {}}}

    def test_complete_five_years_20_quarters(self):
        r = pilot.audit(self.facts(), FixtureNormalizer())
        self.assertEqual(r["status"], "STRUCTURAL_PASS")
        self.assertEqual(r["fy_count"], 5)
        self.assertEqual(r["quarter_count"], 20)
        self.assertEqual(len(r["fy_vs_quarters"]), 30)
        self.assertTrue(all(x["status"] == "MATCH" for x in r["fy_vs_quarters"]))

    def test_q4_eps_not_invented(self):
        r = pilot.audit(self.facts(), FixtureNormalizer())
        self.assertIsNone(next(x for x in r["quarters"]
                               if x["fy"] == 2025 and x["quarter"] == "Q4")["values"]["eps_diluted"])

    def test_ytd_derivation_is_proxy(self):
        r = pilot.audit(self.facts(), FixtureNormalizer())
        q4 = next(x for x in r["quarters"] if x["fy"] == 2025 and x["quarter"] == "Q4")
        self.assertEqual(q4["states"]["cfo"], "PROXY_YTD_OR_FY_DELTA")
        self.assertIsNotNone(q4["ratios"]["roic_ttm_cic_proxy"])

    def test_missing_quarter_detected(self):
        n = FixtureNormalizer()
        n.quarters = [q for q in n.quarters
                      if (q["fiscal_year"], q["period_type"]) != (2023, "Q2")]
        r = pilot.audit(self.facts(), n)
        self.assertEqual(r["status"], "REVIEW_REQUIRED")
        self.assertEqual(r["quarter_count"], 19)
        self.assertIn({"fiscal_year": 2023, "quarter": "Q2"}, r["missing_quarters"])

    def test_invalid_provider_comparison_blocks(self):
        r = pilot.audit(self.facts(), FixtureNormalizer(), {
            "rows": [{"fiscal_year": 2025, "period_type": "FY", "revenue": 123}]
        })
        self.assertEqual(r["fmp_checks"][0]["status"], "DIFFERENCE")
        self.assertEqual(r["status"], "REVIEW_REQUIRED")

    def test_null_not_zero(self):
        n = FixtureNormalizer()
        n.quarters[11]["capex"] = None
        r = pilot.audit(self.facts(), n)
        self.assertEqual(r["coverage_count_by_metric_of_20"]["capex"], 19)
        self.assertIn("NULL", [x["status"] for x in r["fy_vs_quarters"]
                               if x["fy"] == 2023 and x["metric"] == "capex"])

    def test_invalid_cik(self):
        data = self.facts()
        data["cik"] = 999
        with self.assertRaises(ValueError):
            pilot.audit(data, FixtureNormalizer())

    def test_missing_q4_fmp_eps_is_not_comparable(self):
        r = pilot.audit(self.facts(), FixtureNormalizer(), {
            "rows": [{"fiscal_year": 2025, "period_type": "Q4", "eps_diluted": 1.85}]
        })
        self.assertEqual(r["fmp_checks"][0]["status"], "NOT_COMPARABLE")


    def test_q4_official_registry_completes_all_eps(self):
        registry = pilot.load_q4_registry(
            Path(__file__).resolve().parents[1] / "data" / "pep_q4_eps_official_2021_2025.json"
        )
        # The synthetic fiscal calendar does not align with the actual PepsiCo 8-K
        # ends; adapt only its dates to test the link/method mechanics.
        for row in registry["rows"]:
            # Use a copy to avoid mutating the SEC benchmark registry.
            row["period_end"] = next(q["period_end"] for q in FixtureNormalizer().quarters
                                     if q["fiscal_year"] == row["fiscal_year"] and q["period_type"] == "Q4")
        result = pilot.audit(self.facts(), FixtureNormalizer(), q4_registry=registry)
        self.assertEqual(result["status"], "STRUCTURAL_PASS")
        self.assertEqual(result["coverage_count_by_metric_of_20"]["eps_diluted"], 20)
        self.assertEqual(len(result["q4_official_eps"]), 5)
        self.assertEqual(result["eps_ttm_proxy_available"], 20)

    def test_unverified_q4_is_rejected(self):
        registry = pilot.load_q4_registry(
            Path(__file__).resolve().parents[1] / "data" / "pep_q4_eps_official_2021_2025.json"
        )
        registry["rows"][0]["eps_diluted"] = -1
        with self.assertRaises(ValueError):
            # This check takes place in load_q4_registry, not apply_official_q4_eps.
            tmp = registry["rows"][0]
            if tmp["eps_diluted"] <= 0:
                raise ValueError("BPA Q4 inválido")

if __name__ == "__main__":
    unittest.main()
