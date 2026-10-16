"""Offline tests of safe SEC->Google Sheets QA classification."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sec_sync_gate import validate, STAGING_HEADERS, sheet_date

SHA="a"*64
CIK="0000000123"
ACC="0000000123-26-000001"
SRC="https://www.sec.gov/Archives/edgar/data/123/000000012326000001/report.htm"

def input_record():
    return [f"{CIK}|FY|2025-12-31|{ACC}","DEMO",CIK,"10-K","FY","2025-12-31",
        "2026-02-20",ACC,1_000_000_000,200_000_000,100_000_000,150_000_000,50_000_000,
        100_000_000,"FY_CANDIDATO",'{"ebit":{"tag":"OperatingIncomeLoss"},"capex":{"tag":"PaymentsToAcquirePropertyPlantAndEquipment"}}',
        SRC,"https://data.sec.gov/api/xbrl/companyfacts/CIK0000000123.json",SHA,
        "2026-10-16T06:00:00Z","Candidate no certification"]

def historical():
    # SEC_FY_5Y column positions (header plus one data row).
    row=[""]*37
    row[0]="DEMO";row[1]=CIK;row[4]=46022 # 2025-12-31 Excel date serial
    row[8]=1_000_000_000;row[10]=200_000_000;row[11]=100_000_000
    row[13]=150_000_000;row[14]=50_000_000;row[15]=100_000_000;row[34]="PROVISIONAL"
    return [list(range(37)),row]

class TestGate(unittest.TestCase):
    def test_source_date_number(self):
        self.assertEqual(sheet_date(46022),"2025-12-31")
    def test_reconciled_is_proxy_not_certified(self):
        o=validate({"columns":STAGING_HEADERS,"rows":[input_record()]},historical(),[list(range(29))])[0]
        self.assertEqual(o[10],"COINCIDE_PROXY");self.assertEqual(o[8],6)
    def test_large_difference_block(self):
        r=input_record();r[8]*=2
        o=validate({"columns":STAGING_HEADERS,"rows":[r]},historical(),[list(range(29))])[0]
        self.assertEqual(o[10],"BLOQUEADO")
    def test_unknown_capex_tag_block(self):
        r=input_record();r[15]='{"capex":{"tag":"PaymentsToAcquireOtherPropertyPlantAndEquipment"}}'
        self.assertEqual(validate({"columns":STAGING_HEADERS,"rows":[r]},historical(),[list(range(29))])[0][10],"BLOQUEADO")
    def test_malformed_sha_block(self):
        r=input_record();r[18]="bad"
        self.assertEqual(validate({"columns":STAGING_HEADERS,"rows":[r]},historical(),[list(range(29))])[0][10],"BLOQUEADO")
    def test_missing_period_is_new_not_zero(self):
        r=input_record();r[5]="2024-12-31";r[0]=f"{CIK}|FY|2024-12-31|{ACC}"
        self.assertEqual(validate({"columns":STAGING_HEADERS,"rows":[r]},historical(),[list(range(29))])[0][10],"NUEVO_SIN_BASE")
    def test_duplicate_ids_fail(self):
        r=input_record()
        with self.assertRaises(ValueError):validate({"columns":STAGING_HEADERS,"rows":[r,r]},historical(),[list(range(29))])
    def test_staging_schema_change_blocks(self):
        with self.assertRaises(ValueError):validate({"columns":STAGING_HEADERS[:-1],"rows":[input_record()]},historical(),[list(range(29))])
    def test_manual_critical_blocks(self):
        r=input_record();r[1]="ADP"
        self.assertEqual(validate({"columns":STAGING_HEADERS,"rows":[r]},historical(),[list(range(29))])[0][10],"BLOQUEADO")

if __name__=="__main__":unittest.main()
