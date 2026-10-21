"""SEC FY+YTD-YTD bridge independent of quarterly sum, using synthetic XBRL."""
import sqlite3
import unittest
from datetime import date, timedelta
from af_core.ttm_rollforward import audit_ttm

CIK = "0000000001"
ACC = {"fy":"0000000001-25-000100",
       "prior":"0000000001-25-000020",
       "current":"0000000001-26-000020"}


def fixture(q="Q2"):
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript("""
    CREATE TABLE periods(cik TEXT,period_type TEXT,fiscal_year INT,period_end TEXT,
      accession TEXT,currency TEXT);
    CREATE TABLE metrics(cik TEXT,scope TEXT,metric TEXT,period_end TEXT,
      value REAL,status TEXT,reason TEXT);
    """)
    def period(qtype, fy, end, accession):
        c.execute("INSERT INTO periods VALUES (?,?,?,?,?,?)",(CIK,qtype,fy,end,accession,"USD"))
    if q=="Q2":
        period("Q3",2025,"2025-09-30","other")
        period("Q4",2025,"2025-12-31","other")
        period("Q1",2026,"2026-03-31","other")
        period("Q2",2026,"2026-06-30",ACC["current"])
        period("Q2",2025,"2025-06-30",ACC["prior"])
    else:
        period("Q4",2025,"2025-12-31","other")
        period("Q1",2026,"2026-03-31","other")
        period("Q2",2026,"2026-06-30","other")
        period("Q3",2026,"2026-09-30",ACC["current"])
        period("Q3",2025,"2025-09-30",ACC["prior"])
    period("FY",2025,"2025-12-31",ACC["fy"])
    cur_end="2026-06-30" if q=="Q2" else "2026-09-30"
    # FY + current YTD - previous YTD
    for metric,value in (("ebit_ttm",130.0),("cfo_ttm",260.0),
                         ("capex_ttm",80.0),("fcf_ttm",180.0)):
        c.execute("INSERT INTO metrics VALUES (?,?,?,?,?,?,?)",
                  (CIK,"TTM",metric,cur_end,value,"PROXY","synthetic"))
    records={}
    tag_value={"OperatingIncomeLoss":(110,80,100),
               "NetCashProvidedByUsedInOperatingActivities":(220,160,200),
               "PaymentsToAcquirePropertyPlantAndEquipment":(70,50,60)}
    for tag,(fyvalue,prior,current) in tag_value.items():
        if q=="Q2":
            values=[("2025-01-01","2025-12-31",ACC["fy"],"10-K",fyvalue),
                    ("2025-01-01","2025-06-30",ACC["prior"],"10-Q",prior),
                    ("2026-01-01","2026-06-30",ACC["current"],"10-Q",current)]
        else:
            values=[("2025-01-01","2025-12-31",ACC["fy"],"10-K",fyvalue),
                    ("2025-01-01","2025-09-30",ACC["prior"],"10-Q",prior),
                    ("2026-01-01","2026-09-30",ACC["current"],"10-Q",current)]
        records[tag]={"units":{"USD":[dict(start=s,end=e,accn=a,form=f,val=v,filed="2026-01-01")
                                     for s,e,a,f,v in values]}}
    return c, {"facts":{"us-gaap":records}}


class RollForward(unittest.TestCase):
    def test_q2_four_matches(self):
        db,raw=fixture()
        out=audit_ttm(db,CIK,raw)
        self.assertEqual(out["status"],"MATCH")
        self.assertEqual(set(out["metrics"]),{"ebit_ttm","cfo_ttm","capex_ttm","fcf_ttm"})
        self.assertEqual(out["metrics"]["fcf_ttm"]["reference"],180.0)

    def test_q3_four_matches(self):
        db,raw=fixture("Q3")
        self.assertEqual(audit_ttm(db,CIK,raw)["status"],"MATCH")

    def test_detects_wrong_engine_fcf(self):
        db,raw=fixture()
        db.execute("UPDATE metrics SET value=200 WHERE metric='fcf_ttm'")
        out=audit_ttm(db,CIK,raw)
        self.assertEqual(out["status"],"DIVERGENCE")
        self.assertEqual(out["metrics"]["fcf_ttm"]["status"],"DIVERGENCE")

    def test_different_tag_does_not_mix(self):
        db,raw=fixture()
        raw["facts"]["us-gaap"]["PaymentsToAcquirePropertyPlantAndEquipment"]["units"]["USD"][1]["accn"]="wrong"
        out=audit_ttm(db,CIK,raw)
        self.assertEqual(out["status"],"PARTIAL_BLOCKED")
        self.assertEqual(out["metrics"]["capex_ttm"]["status"],"BLOCKED")

    def test_wrong_duration_rejected(self):
        db,raw=fixture()
        raw["facts"]["us-gaap"]["OperatingIncomeLoss"]["units"]["USD"][2]["start"]="2026-06-01"
        out=audit_ttm(db,CIK,raw)
        self.assertEqual(out["metrics"]["ebit_ttm"]["status"],"BLOCKED")

    def test_missing_prior_fiscal_period(self):
        db,raw=fixture()
        db.execute("DELETE FROM periods WHERE fiscal_year=2025 AND period_type='FY'")
        self.assertEqual(audit_ttm(db,CIK,raw)["status"],"BLOCKED")

    def test_blocked_engine_metric_not_certified(self):
        db,raw=fixture()
        db.execute("UPDATE metrics SET status='BLOCKED' WHERE metric='ebit_ttm'")
        out=audit_ttm(db,CIK,raw)
        self.assertEqual(out["metrics"]["ebit_ttm"]["status"],"BLOCKED")
        self.assertEqual(out["status"],"PARTIAL_BLOCKED")

    def test_fcf_rollforward_preserves_definition(self):
        db,raw=fixture()
        out=audit_ttm(db,CIK,raw)
        self.assertIn("no es FCFF",out["metrics"]["fcf_ttm"]["reason"])


if __name__=="__main__":
    unittest.main()
