#!/usr/bin/env python3
"""Build normalized annual fundamental metrics from SEC companyfacts JSON."""
import argparse,csv,json
from pathlib import Path
TAGS={
"revenue":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet"],
"gross_profit":["GrossProfit"],"operating_income":["OperatingIncomeLoss"],"net_income":["NetIncomeLoss"],
"cfo":["NetCashProvidedByUsedInOperatingActivities"],"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],
"assets":["Assets"],"equity":["StockholdersEquity","StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
"cash":["CashAndCashEquivalentsAtCarryingValue","CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
"debt_current":["LongTermDebtCurrent","ShortTermBorrowings"],"debt_long":["LongTermDebtNoncurrent","LongTermDebt"],
"interest":["InterestExpenseNonOperating","InterestExpense"],"da":["DepreciationDepletionAndAmortization","DepreciationDepletionAndAmortizationPropertyPlantAndEquipment"],
"eps":["EarningsPerShareDiluted"]}
def pick(facts,tags,year,instant=False):
 for tag in tags:
  for unit,vals in facts.get(tag,{}).get("units",{}).items():
   c=[v for v in vals if v.get("val") is not None and v.get("form") in ("10-K","10-K/A") and str(v.get("fy"))==str(year) and (instant or v.get("fp")=="FY")]
   if c:
    v=sorted(c,key=lambda x:(x.get("filed",""),x.get("end","")))[-1]; return float(v["val"])
 return None
def div(a,b): return a/b if a is not None and b not in (None,0) else None
def main():
 ap=argparse.ArgumentParser();ap.add_argument("directory",type=Path);ap.add_argument("--out",type=Path,default=Path("fundamentals.csv"));ap.add_argument("--start",type=int,default=2016);ap.add_argument("--end",type=int,default=2026);a=ap.parse_args(); rows=[]
 for p in a.directory.rglob("*.json"):
  try:d=json.loads(p.read_text())
  except:continue
  if "facts" not in d or "cik" not in d:continue
  f=d["facts"].get("us-gaap",{})
  for y in range(a.start,a.end+1):
   m={k:pick(f,v,y,k in ("assets","equity","cash","debt_current","debt_long")) for k,v in TAGS.items()}
   if not any(v is not None for v in m.values()):continue
   debt=(m["debt_current"] or 0)+(m["debt_long"] or 0); fcf=m["cfo"]-m["capex"] if m["cfo"] is not None and m["capex"] is not None else None
   ebitda=m["operating_income"]+m["da"] if m["operating_income"] is not None and m["da"] is not None else None
   rows.append({"cik":str(d["cik"]).zfill(10),"entity":d.get("entityName",""),"fy":y,**m,"debt_total":debt,"net_debt":debt-m["cash"] if m["cash"] is not None else None,"fcf":fcf,"ebitda_derived":ebitda,"gross_margin":div(m["gross_profit"],m["revenue"]),"operating_margin":div(m["operating_income"],m["revenue"]),"net_margin":div(m["net_income"],m["revenue"]),"fcf_margin":div(fcf,m["revenue"]),"roe_simple":div(m["net_income"],m["equity"]),"roa_simple":div(m["net_income"],m["assets"]),"interest_coverage":div(m["operating_income"],m["interest"]),"debt_ebitda":div(debt,ebitda)})
 if not rows: raise SystemExit("No companyfacts found")
 with a.out.open("w",newline="",encoding="utf-8") as h:
  w=csv.DictWriter(h,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 print(f"{len(rows)} company-years -> {a.out}")
if __name__=="__main__":main()
