"""Regresión para el adaptador público; el motor privado se prueba fuera de GitHub."""
import unittest
from integrations.cic_runtime_adapter import execute, load_engine

class Result:
    def __init__(self,v,status="CÁLCULO",reason=""):
        self.value=v;self.status=status;self.reason=reason
    def to_dict(self):
        return {"value":self.value,"status":self.status,"reason":self.reason}

class FakeEngine:
    VERSION="0.2.0"
    @staticmethod
    def validate_document(doc):
        return {m["id"]:m for m in doc["metrics"]}
    @staticmethod
    def blocked(op,reason,ids):
        return Result(None,"BLOQUEADO",reason)
    @staticmethod
    def fcf_gross(a,b):
        return Result(a-b)
    @staticmethod
    def net_debt(a,b):
        return Result(a-b)

def sample():
    def m(mid,value,concept,kind="FLOW",period="FY",end="2025-12-31",scale=1e9):
        return dict(id=mid,value=value,concept=concept,basis="GAAP",
                    currency="USD",scale=scale,period=period,kind=kind,
                    start=end,end=end,status="OFICIAL")
    return {"version":"0.2.0","synthetic":True,"sources":[],
            "metrics":[m("cfo",20,"CFO"),m("capex",5,"CAPEX_CASH_OUTFLOW"),
                       m("cash",10,"CASH","STOCK","INSTANT"),
                       m("debt",40,"DEBT","STOCK","INSTANT")]}

class TestAdapter(unittest.TestCase):
    def calc(self,doc,op,ids):
        return execute(FakeEngine(),{"document":doc,"tasks":[{"id":"x","op":op,"input_ids":ids}]})["calculations"][0]
    def test_valid_fcf(self):
        r=self.calc(sample(),"fcf_gross",["cfo","capex"])
        self.assertEqual(r["result"]["value"],15)
    def test_null_rejected(self):
        d=sample();d["metrics"][0]["value"]=None
        self.assertEqual(self.calc(d,"fcf_gross",["cfo","capex"])["status"],"BLOQUEADO")
    def test_currency_mismatch_rejected(self):
        d=sample();d["metrics"][1]["currency"]="EUR"
        self.assertEqual(self.calc(d,"fcf_gross",["cfo","capex"])["status"],"BLOQUEADO")
    def test_stock_timestamp_mismatch_rejected(self):
        d=sample();d["metrics"][-1]["end"]="2025-11-30"
        self.assertEqual(self.calc(d,"net_debt",["debt","cash"])["status"],"BLOQUEADO")
    def test_stock_scale_mismatch_rejected(self):
        d=sample();d["metrics"][-1]["scale"]=1
        self.assertEqual(self.calc(d,"net_debt",["debt","cash"])["status"],"BLOQUEADO")
    def test_missing_engine_explicit(self):
        with self.assertRaises(RuntimeError):
            load_engine("/NONEXISTENT_PRIVATE_CIC_ENGINE")
    def test_unknown_operation_rejected(self):
        with self.assertRaises(ValueError):
            self.calc(sample(),"execute_trade",["cfo"])

if __name__=="__main__":
    unittest.main()
