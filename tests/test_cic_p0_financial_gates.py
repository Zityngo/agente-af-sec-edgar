"""Synthetic QA-gate regression; no FMP data or private engine distributed."""
import unittest
from types import SimpleNamespace
from integrations.cic_p0_financial_gates import fcf_bridge,debt_gate,roic_gate,dcf_gate,reconcile_fmp_debt_components

class DummyEngine:
    @staticmethod
    def fcf_gross(a,b):return SimpleNamespace(value=a-b,status="CÁLCULO")
    @staticmethod
    def net_debt(a,b):return SimpleNamespace(value=a-b,status="CÁLCULO")
class TestCicP0Gates(unittest.TestCase):
    def test_fcf_bridge_matches(self):
        self.assertEqual(fcf_bridge(DummyEngine(),168.3,215.192,-42.357,4.535).state,"CUMPLIDO")
    def test_fcf_missing_blocks(self):
        self.assertEqual(fcf_bridge(DummyEngine(),None,215,-42,4).state,"BLOQUEADO")
    def test_fcf_mismatch_detected(self):
        self.assertEqual(fcf_bridge(DummyEngine(),168.3,215.192,-30,4.535).state,"DIFERENCIA PENDIENTE DE CONCILIACIÓN")
    def test_debt_lease_not_approved_without_policy(self):
        self.assertEqual(debt_gate(DummyEngine(),180.332,55.783,14.495,100.288,271.949).state,"PARCIAL")
    def test_provider_field_reconciles_without_ev_claim(self):
        r=reconcile_fmp_debt_components(271.949,173.125,98.824,86.195,12.629)
        self.assertEqual(r.state,"CUMPLIDO_DESGLOSE_NO_EV")
        self.assertAlmostEqual(r.evidence["provider_residual"],0)
        self.assertAlmostEqual(r.evidence["sec_residual"],0)
    def test_roic_proxy_blocked_from_certification(self):
        self.assertEqual(roic_gate(60,300,400,False,False,False,False).state,"PARCIAL")
    def test_dcf_null_blocks(self):
        self.assertEqual(dcf_gate(list(range(2026,2031)),[1,None,3,4,5],.11,True,True,True,True,True).state,"BLOQUEADO")
    def test_dcf_more_than_five_years_blocked(self):
        self.assertEqual(dcf_gate(list(range(2026,2032)),[1]*6,.11,True,True,True,True,True).state,"BLOQUEADO")
if __name__=="__main__":unittest.main()
