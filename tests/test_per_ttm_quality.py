"""Pruebas de regresión del PER TTM: herencia de la calidad del BPA.

No contienen datos de empresas reales; entradas sintéticas para verificar estados.
"""
import unittest
from af_core.metrics import R, valuation_metrics


class TestPerTTMQuality(unittest.TestCase):
    def calculate(self, eps):
        # Sin shares: PER TTM es independiente de capitalización.
        return valuation_metrics({"close": 150.0, "shares": None}, {"eps_ttm": eps}, 10.0)["per_ttm"]

    def test_eps_proxy_must_keep_per_proxy(self):
        r = self.calculate(R(15.0, "PROXY", "Q4 trazado pero sin certificación plena"))
        self.assertEqual((r.v, r.s, r.why), (10.0, "PROXY", "Q4 trazado pero sin certificación plena"))

    def test_eps_ok_results_in_per_ok(self):
        r = self.calculate(R(15.0, "OK"))
        self.assertEqual((r.v, r.s), (10.0, "OK"))

    def test_missing_eps_gives_null_per(self):
        r = self.calculate(R(None, "NULL", "Falta EPS Q4"))
        self.assertIsNone(r.v)
        self.assertEqual((r.s, r.why), ("NULL", "Falta EPS Q4"))

    def test_blocked_eps_does_not_generate_per(self):
        r = self.calculate(R(15.0, "BLOCKED", "EPS no conciliado"))
        self.assertIsNone(r.v)
        self.assertEqual(r.s, "BLOCKED")

    def test_nonpositive_eps_does_not_generate_per(self):
        r = self.calculate(R(0.0, "OK"))
        self.assertIsNone(r.v)
        self.assertEqual(r.s, "NULL")
