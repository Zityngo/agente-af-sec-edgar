#!/usr/bin/env python3
"""SEC EDGAR companyfacts -> auditable annual and quarterly S&P 500 fundamentals.

Source: immutable companyfacts/submissions JSON snapshots stored as zipped GitHub
artifacts. Do not use 'fy' alone to identify the period: SEC comparative periods
may have the filing fiscal year rather than the represented fiscal year.
Missing values are null, not zero. P/E requires a separate market-price source.
"""
import argparse, csv, gzip, json, zipfile
from collections import Counter
from datetime import date
from pathlib import Path

TAG = {
 'revenue':['RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet','RevenueFromContractWithCustomerIncludingAssessedTax','RevenuesNetOfInterestExpense'],
 'gross_profit':['GrossProfit'],
 'operating_income':['OperatingIncomeLoss'],
 'operating_costs_and_expenses':['OperatingCostsAndExpenses'],
 'operating_expenses':['OperatingExpenses'],
 'selling_general_admin':['SellingGeneralAndAdministrativeExpense'],
 'research_development':['ResearchAndDevelopmentExpense'],
 'net_income':['NetIncomeLossAvailableToCommonStockholdersBasic','NetIncomeLoss','ProfitLoss'],
 'eps_diluted':['EarningsPerShareDiluted'],
 'cfo':['NetCashProvidedByUsedInOperatingActivities'],
 'capex':['PaymentsToAcquirePropertyPlantAndEquipment','PaymentsToAcquireProductiveAssets','PaymentsToAcquireOtherPropertyPlantAndEquipment','PaymentsToAcquireOtherProductiveAssets'],
 'assets':['Assets'],
 'equity':['StockholdersEquity','StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
 'cash':['CashAndCashEquivalentsAtCarryingValue','CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'],
 'debt_current':['LongTermDebtCurrent','LongTermDebtAndCapitalLeaseObligationsCurrent','DebtCurrent','NotesPayableCurrent'],
 'debt_noncurrent':['LongTermDebtNoncurrent'],
 'debt_reported':['LongTermDebt','LongTermDebtAndCapitalLeaseObligations'],
 'debt_total_direct':['DebtLongtermAndShorttermCombinedAmount','LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities'],
 'short_borrowings':['ShortTermBorrowings','CommercialPaper'],
 'da':['DepreciationDepletionAndAmortization','DepreciationAndAmortization','DepreciationDepletionAndAmortizationPropertyPlantAndEquipment','DepreciationAmortizationAndAccretionNet'],
 'depreciation':['Depreciation'],
 'amortization_intangibles':['AmortizationOfIntangibleAssets'],
 'interest':['InterestExpenseNonOperating','InterestExpense','InterestAndDebtExpense','InterestExpenseDebt','InterestExpenseDebtExcludingAmortization'],
 'tax':['IncomeTaxExpenseBenefit'],
 'pretax':['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
           'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments']
}
INSTANT={'assets','equity','cash','debt_current','debt_noncurrent','debt_reported','debt_total_direct','short_borrowings'}
FINANCIAL={'revenue','gross_profit','operating_income','ebit','net_income','eps_diluted','cfo','capex','assets','equity','cash','debt_total','net_debt','da','ebitda_derived','fcf','gross_margin','operating_margin','ebit_margin','net_margin','fcf_margin','roe_avg','roa_avg','roic_estimated','interest_coverage','debt_ebitda','revenue_yoy','per'}
ANNUAL_FORMS={'10-K','10-K/A','20-F','20-F/A'}
QUARTER_FORMS={'10-Q','10-Q/A'}
_CACHE={}

def ratio(n,d): return n/d if n is not None and d is not None and d!=0 else None
def dur(v):
    try: return (date.fromisoformat(v['end'])-date.fromisoformat(v['start'])).days
    except (KeyError,ValueError,TypeError): return -1
def raw(f,tag,unit):
    key=(id(f),tag,unit)
    if key not in _CACHE:
        _CACHE[key]=[v for v in f.get(tag,{}).get('units',{}).get(unit,[]) if v.get('val') is not None and v.get('end')]
    return _CACHE[key]

def select(f,key,end,forms,fy,fp=None,days=None,accn=None,instant=None):
    if instant is None: instant=key in INSTANT
    unit='USD/shares' if key=='eps_diluted' else 'USD'
    chosen=[]
    for tag in TAG[key]:
        opts=[]
        for v in raw(f,tag,unit):
            if v['end']!=end or v.get('form') not in forms: continue
            if instant:
                if v.get('start'): continue
            elif days and not(days[0]<=dur(v)<=days[1]): continue
            opts.append(v)
        if opts:
            v=max(opts,key=lambda v:(v.get('accn')==accn,v.get('fy')==fy and (fp is None or v.get('fp')==fp),v.get('filed','')))
            chosen.append((tag,v))
            if key!='revenue': break
    if not chosen: return None,None
    if key=='revenue':
        excluding=[x for x in chosen if x[0]!='RevenueFromContractWithCustomerIncludingAssessedTax']
        if excluding: chosen=excluding
        tag,v=max(chosen,key=lambda x:float(x[1]['val']))
    else: tag,v=chosen[0]
    return float(v['val']),{'tag':tag,'accession':v.get('accn'),'filed':v.get('filed'),'start':v.get('start'),'end':end,'form':v.get('form'),'selection':'max_positive_revenue_tag_proxy' if key=='revenue' and len(chosen)>1 else 'preferred_tag'}

def annual_anchor(f,y):
    c=Counter();items={}
    for tag in TAG['revenue']+TAG['assets']:
        for v in raw(f,tag,'USD'):
            if v.get('form') not in ANNUAL_FORMS or v.get('fy')!=y or v.get('fp')!='FY' or v['end'][:4]!=str(y): continue
            if tag in TAG['revenue']:
                if not 320<=dur(v)<=390: continue
                weight=5
            else:
                if v.get('start'): continue
                weight=1
            c[v['end']]+=weight
            if v['end'] not in items or v.get('filed','')>items[v['end']].get('filed',''): items[v['end']]=v
    if not c: return None
    end=max(c,key=lambda e:(c[e],e))
    rv=[]
    for tag in TAG['revenue']:
        rv += [v for v in raw(f,tag,'USD') if v['end']==end and v.get('fy')==y and v.get('fp')=='FY' and v.get('form') in ANNUAL_FORMS and 320<=dur(v)<=390]
    a=max(rv,key=lambda v:v.get('filed','')) if rv else items[end]
    return end,a

def quarter_anchor(f,fy,q):
    pool=Counter();meta={}
    for tag in TAG['revenue']+TAG['assets']:
        for v in raw(f,tag,'USD'):
            if v.get('form') not in QUARTER_FORMS or v.get('fy')!=fy or v.get('fp')!='Q'+str(q): continue
            if tag in TAG['revenue']:
                if not 70<=dur(v)<=112: continue
                weight=4
            else:
                if v.get('start'): continue
                weight=1
            pool[v['end']]+=weight
            if v['end'] not in meta or v.get('filed','')>meta[v['end']].get('filed',''): meta[v['end']]=v
    if not pool: return None
    end=max(pool,key=lambda e:(pool[e],e))
    return end,meta[end]

def gather(f,year,end,accn,formset,fp=None,days=(320,390)):
    m={};sources={}
    for key in TAG:
        m[key],s=select(f,key,end,formset,year,fp,days,accn)
        if s: sources[key]=s
    return m,sources

def debt(m,sources=None):
    sources=sources or {}
    direct=m.get('debt_total_direct')
    if direct is not None: return direct,'reported_total_debt_direct'
    cur,non,total,short=[m.get(k) for k in ('debt_current','debt_noncurrent','debt_reported','short_borrowings')]
    cur_tag=(sources.get('debt_current') or {}).get('tag')
    extra_short=0 if cur_tag=='DebtCurrent' else (short or 0)
    if cur is not None and non is not None: return cur+non+extra_short,'current+noncurrent+short_if_distinct'
    if total is not None: return total+(short or 0),'reported_long_term+short_proxy'
    if non is not None and short is not None: return non+short,'noncurrent+short_proxy'
    return None,'missing_debt_components'

def derived(m,sources=None):
    sources=sources or {}
    if m['operating_income'] is None:
        if m.get('revenue') is not None and m.get('operating_costs_and_expenses') is not None:
            m['operating_income']=m['revenue']-m['operating_costs_and_expenses'];m['operating_income_method']='revenue_minus_OperatingCostsAndExpenses'
        elif m['gross_profit'] is not None and m['operating_expenses'] is not None:
            m['operating_income']=m['gross_profit']-m['operating_expenses'];m['operating_income_method']='gross_profit_minus_total_operating_expenses'
        elif m['gross_profit'] is not None and m['selling_general_admin'] is not None and m['research_development'] is None:
            m['operating_income']=m['gross_profit']-m['selling_general_admin'];m['operating_income_method']='gross_profit_minus_SG&A_proxy'
        else: m['operating_income_method']='unavailable'
    else:
        evidence=sources.get('operating_income') or {}
        m['operating_income_method']='derived_Q4_FY_minus_9M' if evidence.get('derived_from')=='FY_minus_9M' else 'reported_OperatingIncomeLoss'
    if m.get('da') is not None:
        m['da_method']='reported_combined_D&A:'+str((sources.get('da') or {}).get('tag',''))
    elif m.get('depreciation') is not None and m.get('amortization_intangibles') is not None:
        m['da']=m['depreciation']+m['amortization_intangibles'];m['da_method']='reported_depreciation_plus_intangible_amortization'
    elif m.get('depreciation') is not None:
        m['da']=m['depreciation'];m['da_method']='depreciation_only_proxy'
    else: m['da_method']='unavailable'
    if m.get('operating_income') is not None:
        m['ebit']=m['operating_income']
        m['ebit_method']='reported_OperatingIncomeLoss' if m.get('operating_income_method')=='reported_OperatingIncomeLoss' else 'derived_operating_income_UNVERIFIED'
    elif m.get('pretax') is not None and m.get('interest') is not None:
        m['ebit']=m['pretax']+m['interest'];m['ebit_method']='pretax_plus_interest_proxy'
    else:
        m['ebit']=None;m['ebit_method']='unavailable'
    m['interest_method']='reported:'+str((sources.get('interest') or {}).get('tag','')) if m.get('interest') is not None else 'unavailable'
    d,method=debt(m,sources);m['debt_total']=d;m['debt_method']=method
    m['net_debt']=d-m['cash'] if d is not None and m['cash'] is not None else None
    m['fcf']=m['cfo']-m['capex'] if m['cfo'] is not None and m['capex'] is not None else None
    m['ebitda_derived']=m['ebit']+m['da'] if m.get('ebit') is not None and m.get('da') is not None else None
    m['ebitda_method']='EBIT_plus_D&A_proxy:'+m['da_method'] if m['ebitda_derived'] is not None else 'unavailable'
    for name,num in [('gross_margin','gross_profit'),('operating_margin','operating_income'),('ebit_margin','ebit'),('net_margin','net_income'),('fcf_margin','fcf')]:
        m[name]=ratio(m.get(num),m['revenue'])
    m['interest_coverage']=ratio(m['ebit'],m['interest']) if (m.get('interest') or 0)>0 else None
    m['debt_ebitda']=ratio(d,m['ebitda_derived']) if (m['ebitda_derived'] or 0)>0 else None
    m['roe_avg']=m['roa_avg']=m['roic_estimated']=m['revenue_yoy']=None
    m['roic_method']='unavailable';m['per']=None
    return m

def annual(f,cik,entity,ticker,first,last):
    out=[]
    for year in range(first,last+1):
        found=annual_anchor(f,year)
        if not found: continue
        end,a=found
        m,src=gather(f,year,end,a.get('accn'),ANNUAL_FORMS,'FY',(320,390))
        row={'cik':cik,'ticker':ticker,'entity':entity,'period_type':'FY','fiscal_year':year,'period_end':end,'filing_accession':a.get('accn'),'filing_date':a.get('filed'),'currency':'USD',**m}
        derived(row,src);row['sources']=src;out.append(row)
    for i in range(1,len(out)):
        r,p=out[i],out[i-1]
        if r['fiscal_year']!=p['fiscal_year']+1: continue
        for k,den in [('roe_avg','equity'),('roa_avg','assets')]:
            if r[den] is not None and p[den] is not None: r[k]=ratio(r['net_income'],(r[den]+p[den])/2)
        if p['revenue'] not in (None,0) and r['revenue'] is not None: r['revenue_yoy']=r['revenue']/p['revenue']-1
        taxrate=ratio(r['tax'],r['pretax']) if (r['pretax'] or 0)>0 else None
        if taxrate is not None and 0<=taxrate<=0.6 and r.get('ebit') is not None:
            def ic(x): return x['equity']+x['debt_total']-x['cash'] if all(x[k] is not None for k in ('equity','debt_total','cash')) else None
            n,o=ic(r),ic(p)
            if n is not None and o is not None and n+o>0:
                r['roic_estimated']=r['ebit']*(1-taxrate)/((n+o)/2);r['roic_method']='NOPAT_over_avg_equity_plus_debt_minus_cash'
    return out

def quarterly(f,cik,entity,ticker,annual_rows,first,last):
    out=[];cash_ytd={};annual_by_year={r['fiscal_year']:r for r in annual_rows}
    for year in range(first,last+2):
        for q in (1,2,3):
            found=quarter_anchor(f,year,q)
            if not found: continue
            end,a=found;accn=a.get('accn')
            m,src=gather(f,year,end,accn,QUARTER_FORMS,'Q'+str(q),(70,112))
            for k in ('cfo','capex','da','depreciation','amortization_intangibles'):
                ytd,s=select(f,k,end,QUARTER_FORMS,year,'Q'+str(q),((65,110) if q==1 else (145,215) if q==2 else (230,320)),accn)
                if ytd is not None:
                    old=cash_ytd.get((year,q-1,k));m[k]=ytd-old if q>1 and old is not None else (ytd if q==1 else None)
                    src[k]={'derived_from':'ytd_delta' if q>1 else 'ytd_Q1','source':s,'previous_ytd':old};cash_ytd[(year,q,k)]=ytd
            row={'cik':cik,'ticker':ticker,'entity':entity,'period_type':'Q'+str(q),'fiscal_year':year,'period_end':end,'filing_accession':accn,'filing_date':a.get('filed'),'currency':'USD',**m}
            derived(row,src);row['sources']=src;out.append(row)
        a=annual_by_year.get(year)
        if not a: continue
        found=quarter_anchor(f,year,3)
        if not found: continue
        q3_end,q3a=found;end=a['period_end'];m={k:None for k in TAG};src={}
        for k in TAG:
            if k in INSTANT:
                m[k]=a[k]
                if k in a['sources']: src[k]={'from':'FY','source':a['sources'][k]}
            elif k=='eps_diluted':
                # A Q4 EPS figure may only be used if explicitly reported for ~90 days.
                # Weighted-average diluted EPS cannot be backed out as FY minus 9M.
                explicit,proof=select(f,k,end,ANNUAL_FORMS,year,'FY',(70,112),a.get('filing_accession'))
                if explicit is not None and proof and proof.get('start'):
                    m[k]=explicit
                    src[k]={'derived_from':'reported_Q4_90day','source':proof}
                continue
            else:
                ytd,s=select(f,k,q3_end,QUARTER_FORMS,year,'Q3',(230,300),q3a.get('accn'))
                if a[k] is not None and ytd is not None:
                    m[k]=a[k]-ytd;src[k]={'derived_from':'FY_minus_9M','annual_source':a['sources'].get(k),'nine_month_source':s}
        row={'cik':cik,'ticker':ticker,'entity':entity,'period_type':'Q4','fiscal_year':year,'period_end':end,'filing_accession':a['filing_accession'],'filing_date':a['filing_date'],'currency':'USD',**m}
        derived(row,src);row['sources']=src;out.append(row)
    return out

def write_csv(path,rows):
    meta=['cik','ticker','entity','period_type','fiscal_year','period_end','filing_accession','filing_date','currency']
    methods=['operating_income_method','ebit_method','da_method','ebitda_method','interest_method','debt_method','roic_method']
    keys=meta+list(TAG)+['debt_total','net_debt','fcf','ebit','ebitda_derived','gross_margin','operating_margin','ebit_margin','net_margin','fcf_margin','roe_avg','roa_avg','roic_estimated','revenue_yoy','per','interest_coverage','debt_ebitda']+methods+['source_tags_json','missing_metrics']
    with open(path,'w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=keys);w.writeheader()
        for row in rows:
            clean={k:row.get(k) for k in keys};clean['source_tags_json']=json.dumps(row['sources'],separators=(',',':'))
            clean['missing_metrics']=';'.join(k for k in FINANCIAL if row.get(k) is None);w.writerow(clean)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);ap.add_argument('--out-dir',type=Path,default=Path('/mnt/data/normalized_sp500'))
    ap.add_argument('--first-year',type=int,default=2020);ap.add_argument('--last-year',type=int,default=2026)
    args=ap.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    zips=sorted(args.directory.glob('SEC_EDGAR_SP500_BATCH_*.zip'))
    if len(zips)!=13: raise SystemExit('Expected 13 official SEC S&P500 batch archives; got '+str(len(zips)))
    annual_rows=[];quarter_rows=[];seen=set();errors=[]
    for path in zips:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if not name.endswith('/companyfacts.json.gz'): continue
                try:
                    d=json.loads(gzip.decompress(z.read(name)));cik=str(d['cik']).zfill(10)
                    if cik in seen: continue
                    seen.add(cik);f=d.get('facts',{}).get('us-gaap',{});_CACHE.clear()
                    subname=name.replace('companyfacts.json.gz','submissions.json.gz')
                    subs=json.loads(gzip.decompress(z.read(subname))) if subname in z.namelist() else {}
                    tickers=subs.get('tickers',[]);ticker=tickers[0] if tickers else '';entity=d.get('entityName','')
                    ann=annual(f,cik,entity,ticker,args.first_year,args.last_year)
                    annual_rows.extend(ann[-5:]);quarter_rows.extend(quarterly(f,cik,entity,ticker,ann,args.first_year,args.last_year)[-21:])
                except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e: errors.append({'path':str(path),'entry':name,'error':str(e)})
    write_csv(args.out_dir/'sp500_annual_5y.csv',annual_rows);write_csv(args.out_dir/'sp500_quarterly_5y.csv',quarter_rows)
    def coverage(rows):
        return {k:{'count':sum(r.get(k) is not None for r in rows),'pct':round(100*sum(r.get(k) is not None for r in rows)/len(rows),1) if rows else 0} for k in sorted(FINANCIAL)}
    report={'source':'SEC EDGAR companyfacts via archived GitHub batch run 38072477497 (snapshot 2026-10-10)','companies_raw':len(seen),'companies_with_annual':len({r['cik'] for r in annual_rows}),'companies_with_quarterly':len({r['cik'] for r in quarter_rows}),'annual_rows':len(annual_rows),'quarterly_rows':len(quarter_rows),'annual_coverage':coverage(annual_rows),'quarter_coverage':coverage(quarter_rows),'errors':errors}
    (args.out_dir/'quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if len(seen)!=500: raise SystemExit('Raw coverage is not 500 distinct companies')
if __name__=='__main__': main()
