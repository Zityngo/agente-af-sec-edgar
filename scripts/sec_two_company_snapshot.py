import json, urllib.request, os, pathlib
CIKS={"TSLA":"0001318605","PEP":"0000077476"}
TAGS="Revenues RevenueFromContractWithCustomerExcludingAssessedTax SalesRevenueNet GrossProfit CostOfRevenue CostOfGoodsAndServicesSold OperatingIncomeLoss NetIncomeLoss NetIncomeLossAvailableToCommonStockholdersBasic EarningsPerShareDiluted WeightedAverageNumberOfDilutedSharesOutstanding NetCashProvidedByUsedInOperatingActivities PaymentsToAcquirePropertyPlantAndEquipment PaymentsToAcquireProductiveAssets PaymentsOfDividends PaymentsForRepurchaseOfCommonStock ShareBasedCompensation DepreciationDepletionAndAmortization DepreciationDepletionAndAmortizationPropertyPlantAndEquipment IncomeTaxExpenseBenefit IncomeTaxesPaidNet InterestExpense InterestExpenseNonOperating InterestPaidNet Assets AssetsCurrent Liabilities LiabilitiesCurrent StockholdersEquity CashAndCashEquivalentsAtCarryingValue ShortTermInvestments AccountsReceivableNetCurrent InventoryNet AccountsPayableCurrent LongTermDebt LongTermDebtCurrent DebtCurrent ShortTermBorrowings LongTermDebtAndCapitalLeaseObligations OperatingLeaseLiabilityCurrent OperatingLeaseLiabilityNoncurrent FinanceLeaseLiabilityCurrent FinanceLeaseLiabilityNoncurrent PropertyPlantAndEquipmentNet PaymentsToAcquireBusinessesNetOfCashAcquired PaymentsToAcquireInvestments ProceedsFromIssuanceOfLongTermDebt RepaymentsOfLongTermDebt OperatingExpenses ResearchAndDevelopmentExpense SellingGeneralAndAdministrativeExpense".split()
out={"source":"SEC Companyfacts public","cutoff":"2026-10-23","companies":{}}
for ticker,cik in CIKS.items():
 url="https://data.sec.gov/api/xbrl/companyfacts/CIK"+cik+".json"
 req=urllib.request.Request(url,headers={"User-Agent":os.environ["SEC_USER_AGENT"],"Accept-Encoding":"identity"})
 with urllib.request.urlopen(req,timeout=75) as r:raw=json.load(r)
 obj={"cik":cik,"entityName":raw.get("entityName"),"us-gaap":{},"dei":{}}
 for tx in ("us-gaap","dei"):
  for tag,info in raw.get("facts",{}).get(tx,{}).items():
   if tag not in TAGS and tag!="EntityCommonStockSharesOutstanding":continue
   units={}
   for unit,entries in info.get("units",{}).items():
    rows=[{k:e[k] for k in ("start","end","val","accn","fy","fp","form","filed","frame") if k in e} for e in entries if e.get("end","")>="2020-01-01" and e.get("end","")<="2026-10-24" and e.get("filed","")<="2026-10-24" and e.get("form") in ("10-K","10-Q","10-K/A","10-Q/A")]
    if rows:units[unit]=rows
   if units:obj[tx][tag]={"units":units,"label":info.get("label")}
 out["companies"][ticker]=obj
 print(ticker,len(obj["us-gaap"]))
p=pathlib.Path("publico/af_jon_current");p.mkdir(parents=True,exist_ok=True)
(p/"sec_financial_source_facts.json").write_text(json.dumps(out))
