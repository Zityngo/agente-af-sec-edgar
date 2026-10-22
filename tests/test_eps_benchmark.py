"""Comparación auditable de BPA piloto contra referencias del emisor."""
import unittest
from pathlib import Path
from af_core.eps_benchmark import load_benchmark,compare
ROOT=Path(__file__).resolve().parents[1]


class EPSBenchmark(unittest.TestCase):
    def setUp(self):
        self.refs=load_benchmark(ROOT/"data/eps_benchmarks_pilot_2026q2.json")
        self.audits={}
        for t in ("AAPL","TSLA","AMZN"):
            self.audits[t]={"quarters":[{"quarter":r["period_type"],"period_end":r["period_end"],
                "eps":r["eps_diluted_gaap"],"provenance":"TRACEABLE"}
                for r in sorted((x for x in self.refs if x["ticker"]==t),key=lambda x:x["period_end"])[-4:]]}

    def test_twelve_source_urls(self):
        self.assertGreaterEqual(len(self.refs),12)
        self.assertEqual({r["ticker"] for r in self.refs},{"AAPL","TSLA","AMZN"})

    def test_twelve_match(self):
        result=compare(self.audits,self.refs)
        self.assertEqual(sum(len(x["quarters"]) for x in result.values()),12)

    def test_wrong_eps_is_blocked(self):
        self.audits["AMZN"]["quarters"][-1]["eps"]+=0.10
        with self.assertRaisesRegex(ValueError,"Discrepancia"):
            compare(self.audits,self.refs)

    def test_untraceable_eps_is_blocked(self):
        self.audits["TSLA"]["quarters"][0]["provenance"]="REVIEW"
        with self.assertRaisesRegex(ValueError,"Discrepancia"):
            compare(self.audits,self.refs)
