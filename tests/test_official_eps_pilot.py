"""V3 fase 2a: el BPA Q4 debe proceder de una publicación identificable."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from official_eps_pilot import load_registry, apply


class Q4OfficialPilot(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry(ROOT / "data/q4_eps_official_pilot_2025.json")

    def rows(self):
        return [
            {"ticker":r["ticker"],"cik":r["cik"],"fiscal_year":r["fiscal_year"],
             "period_type":"Q4","period_end":r["period_end"],"eps_diluted":None,"sources":{}}
            for r in self.registry.values()
        ]

    def test_three_real_official_source_records(self):
        self.assertEqual(len(self.registry), 3)
        self.assertEqual({r["ticker"]:r["value"] for r in self.registry.values()},
                         {"AAPL":1.85,"TSLA":0.24,"AMZN":1.95})
        self.assertTrue(all(r["source_url"].startswith("https://") for r in self.registry.values()))

    def test_attach_official_q4_without_eps_subtraction(self):
        rows=self.rows()
        result=apply(rows,self.registry)
        self.assertEqual(result["eps_added"],3)
        for r in rows:
            self.assertEqual(r["sources"]["eps_diluted"]["derived_from"],"official_Q4_earnings_release")
            self.assertEqual(r["sources"]["eps_diluted"]["status"],"PILOT_SOURCED_NOT_AUTOMATED")
            self.assertIn("issuer_url",r["sources"]["eps_diluted"])

    def test_a_conflicting_sec_value_blocks_without_overwrite(self):
        rows=self.rows()
        rows[0]["eps_diluted"]=999.0
        with self.assertRaisesRegex(ValueError, "discrepantes"):
            apply(rows,self.registry)
        self.assertEqual(rows[0]["eps_diluted"],999.0)

    def test_missing_q4_blocks_instead_of_guessing(self):
        with self.assertRaisesRegex(ValueError, "Sin Q4"):
            apply(self.rows()[:2],self.registry)

    def test_present_eps_kept_and_only_corroborated(self):
        rows=self.rows()
        rows[0]["eps_diluted"]=1.85
        rows[0]["sources"]={"eps_diluted":{"tag":"EarningsPerShareDiluted","form":"10-K"}}
        result=apply(rows,self.registry)
        self.assertEqual(result["eps_added"],2)
        self.assertEqual(result["eps_corroborated"],1)
        self.assertEqual(rows[0]["sources"]["eps_diluted"]["tag"],"EarningsPerShareDiluted")
        self.assertIn("eps_official_confirmation",rows[0]["sources"])

    def test_invalid_registry_record_rejected(self):
        from official_eps_pilot import _valid
        r=dict(next(iter(self.registry.values())))
        r["metric"]="eps_non_gaap"
        with self.assertRaisesRegex(ValueError,"GAAP"):
            _valid(r)


if __name__=="__main__":
    unittest.main()
