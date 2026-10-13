#!/usr/bin/env python3
"""Generate a reproducible 5-FY Apple reference directly from public SEC companyfacts.

The output contains SEC data only; no FMP raw responses are published.
SEC_USER_AGENT is required for live download; --input enables offline tests.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

CIK = '0000320193'
SEC_URL = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json'
TAGS = {
    'revenue': ('RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues', 'SalesRevenueNet'),
    'gross_profit': ('GrossProfit',),
    'operating_income': ('OperatingIncomeLoss',),
    'net_income': ('NetIncomeLoss',),
    'pretax': ('IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',),
    'tax': ('IncomeTaxExpenseBenefit',),
    'eps_diluted': ('EarningsPerShareDiluted',),
    'assets': ('Assets',),
    'equity': ('StockholdersEquity',),
    'cash_unrestricted_v2': ('CashAndCashEquivalentsAtCarryingValue',),
    'short_term_investments_v2': ('ShortTermInvestments', 'MarketableSecuritiesCurrent'),
    'cfo': ('NetCashProvidedByUsedInOperatingActivities',),
    'capex': ('PaymentsToAcquirePropertyPlantAndEquipment',),
}
INSTANT = {'assets', 'equity', 'cash_unrestricted_v2', 'short_term_investments_v2'}

def annual(item):
    if not item.get('start'):
        return False
    try:
        days = (date.fromisoformat(item['end']) - date.fromisoformat(item['start'])).days
        return 330 <= days <= 400
    except (TypeError, ValueError, KeyError):
        return False

def pick(facts, tags, end, instant=False):
    for tag in tags:
        units=facts.get(tag,{}).get('units',{})
        matches=[]
        for unit in ('USD','USD/shares'):
            matches.extend(v for v in units.get(unit,[]) if
                v.get('form') in ('10-K','10-K/A') and v.get('end')==end and
                v.get('val') is not None and (instant or annual(v)))
        if matches:
            return sorted(matches,key=lambda v:(v.get('filed',''),v.get('accn','')))[-1]['val']
    return ''

def build(payload, num_years=5):
    if str(payload.get('cik')).zfill(10) != CIK:
        raise ValueError('SEC CIK mismatch (expected Apple)')
    facts=payload['facts']['us-gaap']
    ends=set()
    for tag in TAGS['revenue']:
        for vals in facts.get(tag,{}).get('units',{}).values():
            ends.update(v['end'] for v in vals if v.get('form') in ('10-K','10-K/A') and v.get('end') and annual(v))
    valid=sorted((end for end in ends if int(end[:4])<=date.today().year),reverse=True)[:num_years]
    rows=[]
    for end in sorted(valid):
        row={'ticker':'AAPL','cik':CIK,'period_type':'FY','fiscal_year':end[:4],
             'period_end':end,'currency':'USD','source_sec_url':SEC_URL}
        for name,tags in TAGS.items():
            row[name]=pick(facts,tags,end,name in INSTANT)
        if row['revenue']=='': continue
        row['fcf']=row['cfo']-row['capex'] if row['cfo']!='' and row['capex']!='' else ''
        rows.append(row)
    if len(rows)!=num_years:
        raise ValueError(f'Expected {num_years} SEC annual years, got {len(rows)}')
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path,help='Optional SEC companyfacts JSON for offline testing')
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--years',type=int,default=5)
    args=ap.parse_args()
    if args.input:
        data=json.loads(args.input.read_text(encoding='utf-8'))
    else:
        user_agent=os.environ.get('SEC_USER_AGENT','').strip()
        if '@' not in user_agent:
            raise SystemExit('SEC_USER_AGENT unavailable; SEC validation not performed')
        req=Request(SEC_URL,headers={'User-Agent':user_agent,'Accept':'application/json'})
        with urlopen(req,timeout=35) as resp:
            data=json.loads(resp.read(12_000_000))
    rows=build(data,args.years)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print('SEC public reference:',len(rows),'years',rows[0]['period_end'],'through',rows[-1]['period_end'])
    print('FMP provider data not stored; output limited to local runner')

if __name__=='__main__':
    main()
