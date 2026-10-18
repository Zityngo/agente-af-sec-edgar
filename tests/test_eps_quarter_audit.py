"""Controles de trazabilidad Q1-Q4 del BPA diluido sin inventar TTM."""
import json
import unittest
from af_core.eps_audit import audit_company

ENDS=["2025-09-30","2025-12-31","2026-03-31","2026-06-30"]
Q=["Q3","Q4","Q1","Q2"]

class FakeDB:
    def __init__(self, rows): self.rows=rows
    def execute(self, query, args): return self
    def fetchall(self): return self.rows[::-1]  # SQL uses ORDER BY period_end DESC

def fixture():
    rows=[]
    for i,(typ,end) in enumerate(zip(Q,ENDS)):
        acc=f"0001318605-26-0000{i+11:02d}"
        if typ=="Q4":
            source={"tag":"IssuerReportedGAAPDilutedEPS","status":"PILOT_SOURCED_NOT_AUTOMATED",
                    "derived_from":"official_Q4_earnings_release","issuer_url":"https://ir.tesla.com/report",
                    "period_start":"2025-10-01","period_end":end}
        else:
            start={0:"2025-07-01",2:"2026-01-01",3:"2026-04-01"}[i]
            source={"tag":"EarningsPerShareDiluted","form":"10-Q","accession":acc,
                    "start":start,"end":end}
        rows.append({"period_type":typ,"period_end":end,"fiscal_year":2025 if i<2 else 2026,
                    "accession":acc,"filed":end,"eps_diluted":[.39,.24,.13,.32][i],
                    "sources_json":json.dumps({"eps_diluted":source})})
    return rows

class TestEPSQuarterAudit(unittest.TestCase):
    def test_four_quarters_traceable_proxies(self):
        x=audit_company(FakeDB(fixture()),"0001318605")
        self.assertEqual(x["status"],"PROXY")
        self.assertEqual(x["eps_sum"],1.08)
        self.assertEqual(len(x["quarters"]),4)
    def test_missing_provenance_blocks(self):
        rows=fixture()
        rows[0]["sources_json"]="{}"
        x=audit_company(FakeDB(rows),"0001318605")
        self.assertEqual(x["status"],"BLOCKED")
        self.assertIsNone(x["eps_sum"])
    def test_conflicting_accession_needs_review(self):
        rows=fixture()
        data=json.loads(rows[0]["sources_json"])
        data["eps_diluted"]["accession"]="0001318605-25-999999"
        rows[0]["sources_json"]=json.dumps(data)
        x=audit_company(FakeDB(rows),"0001318605")
        self.assertEqual(x["status"],"REVIEW")
        self.assertEqual(x["eps_sum"],1.08)
    def test_q4_not_from_issuer_blocks(self):
        rows=fixture()
        data=json.loads(rows[1]["sources_json"])
        data["eps_diluted"]["issuer_url"]=""
        rows[1]["sources_json"]=json.dumps(data)
        x=audit_company(FakeDB(rows),"0001318605")
        self.assertEqual(x["status"],"BLOCKED")
    def test_nonconsecutive_dates_block(self):
        rows=fixture()
        rows[2]["period_end"]="2026-02-15"
        x=audit_company(FakeDB(rows),"0001318605")
        self.assertEqual(x["status"],"BLOCKED")
    def test_missing_quarter_blocks(self):
        x=audit_company(FakeDB(fixture()[:3]),"0001318605")
        self.assertEqual(x["status"],"BLOCKED")
