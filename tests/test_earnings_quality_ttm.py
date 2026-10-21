"""Quality inheritance and issuer-documented atypical earnings: synthetic tests."""
import json
import tempfile
import unittest
from pathlib import Path

from af_core.metrics import R, valuation_metrics, ttm_metrics
from af_core.earnings_audit import load_events, audit_window, SCOPE

ROOT = Path(__file__).resolve().parents[1]


class QualityPropagation(unittest.TestCase):
    def test_fcf_yield_does_not_promote_proxy(self):
        r = valuation_metrics({"close": 100, "shares": 10},
                              {"fcf_ttm": R(60, "PROXY", "CapEx YTD"),
                               "net_debt": R(30, "PROXY", "leasing"),
                               "ebitda_ttm": R(100, "PROXY", "EBIT Q4")}, None)
        self.assertEqual(r["fcf_yield"].s, "PROXY")
        self.assertEqual(r["ev"].s, "PROXY")
        self.assertEqual(r["ev_ebitda"].s, "PROXY")

    def test_fcf_blocked_cannot_create_yield(self):
        r = valuation_metrics({"close": 100, "shares": 10},
                              {"fcf_ttm": R(None, "BLOCKED", "CapEx tag"),
                               "net_debt": R(None, "BLOCKED", "deuda"),
                               "ebitda_ttm": R(80, "OK")}, None)
        self.assertIsNone(r["fcf_yield"].v)
        self.assertEqual(r["fcf_yield"].s, "BLOCKED")
        self.assertIsNone(r["ev_ebitda"].v)
        self.assertEqual(r["ev_ebitda"].s, "BLOCKED")

    def test_ttm_fcf_margin_keeps_derived_capex_proxy(self):
        quarters = []
        for i in range(4):
            source = {"operating_income": {"tag": "OperatingIncomeLoss"},
                      "net_income": {"tag": "NetIncomeLossAvailableToCommonStockholdersBasic"},
                      "capex": {"tag": "PaymentsToAcquirePropertyPlantAndEquipment"}}
            if i == 3:
                source["capex"] = {"derived_from": "FY_minus_9M",
                    "annual_source": {"tag": "PaymentsToAcquirePropertyPlantAndEquipment"},
                    "nine_month_source": {"tag": "PaymentsToAcquirePropertyPlantAndEquipment"}}
            quarters.append({"revenue":100,"net_income":10,"cfo":20,"capex":5,
                             "da":3,"da_method":"depreciation_only",
                             "operating_income":15,"operating_income_method":"reported_OperatingIncomeLoss",
                             "sources_json":json.dumps(source),"eps_diluted":1,
                             "debt_total":30,"debt_method":"proxy_bonds","cash":5})
        r = ttm_metrics(quarters)
        for name in ("fcf_ttm","fcf_margin_ttm","ebitda_ttm","debt_ebitda_ttm","net_debt"):
            self.assertEqual(r[name].s, "PROXY", name)


class ExceptionalEarningsAudit(unittest.TestCase):
    def setUp(self):
        self.events = load_events(ROOT / "data/earnings_events_pilot_2026q2.json")

    def test_three_events_with_original_units(self):
        self.assertEqual(len(self.events), 3)
        self.assertEqual([e["amount"] for e in self.events if e["ticker"] == "AMZN"], [16800, 53400])
        self.assertEqual([e["amount"] for e in self.events if e["ticker"] == "AAPL"], [0.11])

    def test_amazon_window_is_review_not_eps_normalized(self):
        a = audit_window("AMZN", ["2025-09-30","2025-12-31","2026-03-31","2026-06-30"], self.events)
        self.assertEqual(a["status"], "REVIEW_NONRECURRING")
        self.assertEqual(len(a["events"]), 2)
        self.assertIsNone(a["adjusted_eps"])

    def test_absent_flag_is_not_clean_certification(self):
        a = audit_window("TSLA", ["2025-09-30","2025-12-31","2026-03-31","2026-06-30"], self.events)
        self.assertEqual(a["status"], "NOT_FULLY_SCREENED")
        self.assertIsNone(a["adjusted_eps"])

    def test_missing_quarter_cannot_pass(self):
        a = audit_window("AAPL", ["2026-06-27"] * 4, self.events)
        self.assertEqual(a["status"], "INSUFFICIENT_QUARTERS")

    def test_invalid_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            data = {"schema_version": 1, "scope": SCOPE, "events": [
                dict(self.events[0], source_url="")]}
            p = Path(folder) / "bad.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inválidos"):
                load_events(p)


if __name__ == "__main__":
    unittest.main()
