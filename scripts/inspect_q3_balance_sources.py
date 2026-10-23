"""Inspect official SEC Companyfacts financial balance and lease facts for two Q3 filers.

Read-only official request, accession strict. Values in original USD.
Run in GitHub Actions with SEC_USER_AGENT; never infer missing liabilities as zero.
"""
import json, os, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIRMS={"TSLA":{"cik":"0001318605","accession":"0001628280-26-066775","end":"2026-09-30"},
       "PEP":{"cik":"0000077476","accession":"0000077476-26-000048","end":"2026-09-05"}}
TAGS=[
"CashAndCashEquivalentsAtCarryingValue","ShortTermInvestments","ShortTermBorrowings",
"ShortTermDebtCurrent","LongTermDebtCurrent","LongTermDebtNoncurrent","LongTermDebt",
"DebtCurrent","LongTermDebtAndCapitalLeaseObligations",
"OperatingLeaseLiability","OperatingLeaseLiabilityCurrent","OperatingLeaseLiabilityNoncurrent",
"FinanceLeaseLiability","FinanceLeaseLiabilityCurrent","FinanceLeaseLiabilityNoncurrent",
"OperatingLeaseRightOfUseAsset","FinanceLeaseRightOfUseAsset","FinanceLeaseLiabilityPaymentsDue",
"CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents","RestrictedCashAndCashEquivalents",
"CommercialPaper","DebtLongtermAndShorttermCombinedAmount",
]
def fetch(cik, ua):
    url="https://data.sec.gov/api/xbrl/companyfacts/CIK"+cik+".json"
    req=urllib.request.Request(url,headers={"User-Agent":ua,"Accept":"application/json",
        "Accept-Encoding":"identity"})
    with urllib.request.urlopen(req,timeout=50) as h:
        return json.loads(h.read().decode("utf-8"))
def inspect(raw, accession,end):
    data=raw.get("facts",{}).get("us-gaap",{})
    report={}
    for tag in TAGS:
        v=data.get(tag)
        if not v:continue
        matched=[]
        for unit,entries in v.get("units",{}).items():
            for e in entries:
                if e.get("end")==end and e.get("accn")==accession and e.get("form") in ("10-Q","10-Q/A"):
                    matched.append({"tag":tag,"unit":unit,"val":e["val"],"filed":e.get("filed"),
                       "start":e.get("start"),"accession":e["accn"],"form":e["form"],
                       "period_end":e["end"]})
        if matched:
            report[tag]=matched
        elif any(x in tag for x in ("Lease","Debt","Cash","CommercialPaper")):
            # Diagnostic only - NEVER report prior period as current.
            earlier=[]
            for unit,entries in v.get("units",{}).items():
                for e in entries:
                    if e.get("end","")<=end and e.get("filed","")<= "2026-10-23":
                        earlier.append({"unit":unit,"value":e.get("val"),"end":e.get("end"),"accn":e.get("accn")})
            if earlier:
                latest=max(earlier,key=lambda o:o["end"])
                report[tag]={"status":"NOT_IN_TARGET_FILING","last_historical_fact":latest}
    return report

def main():
    ua=os.environ.get("SEC_USER_AGENT","").strip()
    if not ua:raise RuntimeError("SEC_USER_AGENT required")
    out={"source":"SEC companyfacts","fetched":"at GitHub Actions runtime","companies":{}}
    for t,p in FIRMS.items():
        raw=fetch(p["cik"],ua)
        if str(raw["cik"]).zfill(10)!=p["cik"]:raise ValueError("Wrong CIK")
        r=inspect(raw,p["accession"],p["end"])
        out["companies"][t]={"asof":p["end"],"accession":p["accession"],
            "url":"https://www.sec.gov/Archives/edgar/data/"+str(int(p["cik"]))+"/"+p["accession"].replace("-","")+
                ("/tsla-20260930.htm" if t=="TSLA" else "/pep-20260905.htm"),
            "facts":r}
        print(json.dumps({"ticker":t,"matched":{k:v for k,v in r.items() if isinstance(v,list)},
            "missing_in_q3":{k:v["last_historical_fact"] for k,v in r.items()
                if isinstance(v,dict) and v.get("status")=="NOT_IN_TARGET_FILING"}},
            ensure_ascii=False))
    target=Path("publico/balance_q3_2026");target.mkdir(parents=True,exist_ok=True)
    (target/"companyfacts_balance_lease_diagnostic.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
