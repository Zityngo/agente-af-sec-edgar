"""SEC XBRL historical 20-issuer as-filed fundamental evaluation sample.
No market prices, user data, or provider material in repository.
"""
import os,json,urllib.request,urllib.error,time,pathlib
CO={"AAPL":320193,"MSFT":789019,"GOOGL":1652044,"META":1326801,"NVDA":1045810,
"AMZN":1018724,"TSLA":1318605,"PEP":77476,"KO":21344,"PG":80424,"WMT":104169,
"COST":909832,"HD":354950,"CAT":18230,"DE":315189,"XOM":34088,"CVX":93410,
"JNJ":200406,"ABBV":1551152,"MCD":63908}
TAGS=set("""Revenues RevenueFromContractWithCustomerExcludingAssessedTax SalesRevenueNet
GrossProfit CostOfRevenue CostOfGoodsAndServicesSold OperatingIncomeLoss
NetIncomeLoss NetIncomeLossAvailableToCommonStockholdersBasic
EarningsPerShareDiluted WeightedAverageNumberOfDilutedSharesOutstanding
NetCashProvidedByUsedInOperatingActivities PaymentsToAcquirePropertyPlantAndEquipment
PaymentsToAcquireProductiveAssets PaymentsOfDividends PaymentsForRepurchaseOfCommonStock
ShareBasedCompensation DepreciationDepletionAndAmortization
DepreciationDepletionAndAmortizationPropertyPlantAndEquipment
IncomeTaxExpenseBenefit IncomeTaxesPaidNet InterestExpense InterestExpenseNonOperating
Assets AssetsCurrent Liabilities LiabilitiesCurrent StockholdersEquity
StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest
CashAndCashEquivalentsAtCarryingValue ShortTermInvestments AccountsReceivableNetCurrent
InventoryNet AccountsPayableCurrent LongTermDebt LongTermDebtCurrent DebtCurrent
ShortTermBorrowings LongTermDebtAndCapitalLeaseObligations OperatingLeaseLiabilityCurrent
OperatingLeaseLiabilityNoncurrent FinanceLeaseLiabilityCurrent
FinanceLeaseLiabilityNoncurrent PropertyPlantAndEquipmentNet
PaymentsToAcquireBusinessesNetOfCashAcquired
PaymentsToAcquireInvestments ProceedsFromIssuanceOfLongTermDebt RepaymentsOfLongTermDebt
OperatingExpenses ResearchAndDevelopmentExpense SellingGeneralAndAdministrativeExpense
CommonStockSharesOutstanding CommonStockDividendsPerShareDeclared
""".split())
def sec(cik):
 url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
 req=urllib.request.Request(url,headers={"User-Agent":os.environ["SEC_USER_AGENT"],
        "Accept":"application/json","Accept-Encoding":"identity"})
 for j in range(4):
  try:
   with urllib.request.urlopen(req,timeout=65) as fp:return json.load(fp)
  except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
   if j==3:raise
   time.sleep(2+j*2)
def main():
 o={"version":"1.0","snapshot_cutoff":"2026-10-25","source_url_template":"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json","companies":{},"errors":{}}
 for i,(tick,cik) in enumerate(CO.items()):
  try:
   raw=sec(cik); data={"cik":cik,"name":raw.get("entityName"),"us-gaap":{},"dei":{}}
   for ns in ("us-gaap","dei"):
    for tag,info in raw.get("facts",{}).get(ns,{}).items():
     if tag not in TAGS and tag!="EntityCommonStockSharesOutstanding":continue
     units={}
     for unit,items in info.get("units",{}).items():
      vals=[{k:item[k] for k in ("start","end","val","accn","fy","fp","form","filed","frame") if k in item}
        for item in items if item.get("end","")>="2018-01-01" and
        item.get("end","")<="2026-10-25" and item.get("filed","")<="2026-10-25" and
        item.get("form") in ("10-K","10-Q","10-K/A","10-Q/A")]
      if vals:units[unit]=vals
     if units:data[ns][tag]={"label":info.get("label"),"units":units}
   o["companies"][tick]=data
   print(tick,cik,len(data["us-gaap"]),"OK",flush=True)
  except Exception as e:
   o["errors"][tick]=str(e);print(tick,"ERROR",str(e),flush=True)
  time.sleep(0.23)
 p=pathlib.Path("publico/af_backtest20");p.mkdir(parents=True,exist_ok=True)
 (p/"sec_20_companyfacts_asfiled.json").write_text(json.dumps(o),encoding="utf-8")
 print("RESULT",len(o["companies"]),"SUCCESS",len(o["errors"]),"ERROR")
 if len(o["companies"])<16:raise RuntimeError("Too few companies (minimum 16)")
if __name__=="__main__":main()
