#!/usr/bin/env python3
"""Low-cost FMP Basic cross-check for SEC S&P500 data, not a data replacement.

Usage:
  python scripts/fmp_free_crosscheck.py --dry-run --sec-csv datos/sp500_annual_5y.csv
  FMP_API_KEY=... python scripts/fmp_free_crosscheck.py --sec-csv datos/sp500_annual_5y.csv

Important: Every provider endpoint may be restricted under FMP Basic even with a key.
This script stops on quota errors, never assumes FMP and SEC metric definitions are
identical, never places an API key in logs, and never writes a provider raw-data dump.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib import error, parse, request

BASE = 'https://financialmodelingprep.com/stable/'
ENDPOINTS = ('income-statement', 'balance-sheet-statement', 'cash-flow-statement')
DEFAULT_SYMBOLS = ('AAPL', 'CSCO', 'MCK')
NUMERIC_FIELDS = {
    'income-statement': {
        'revenue': 'revenue',
        'grossProfit': 'gross_profit',
        'operatingIncome': 'operating_income',
        'netIncome': 'net_income',
        'incomeBeforeTax': 'pretax',
        'incomeTaxExpense': 'tax',
        'epsDiluted': 'eps_diluted',
    },
    'balance-sheet-statement': {
        'totalAssets': 'assets',
        'totalEquity': 'equity',
        'cashAndCashEquivalents': 'cash_unrestricted_v2',
        'shortTermInvestments': 'short_term_investments_v2',
    },
    'cash-flow-statement': {
        'operatingCashFlow': 'cfo',
        'capitalExpenditure': 'capex',
        'freeCashFlow': 'fcf',
    },
}
# The following must NOT be compared as same-definition quantities:
# - FMP totalDebt / netDebt vs SEC financial_debt_ex_leases_v2: lease inclusion differs.
# - FMP EBITDA vs derived SEC EBIT + D&A: definitions differ.
# - FMP ROIC vs our proxy ROIC: NOPAT and invested capital methods differ.
NON_EQUIVALENT = {
 'totalDebt': 'FMP debt may include lease obligations; SEC v2 financial debt explicitly excludes leases',
 'netDebt': 'FMP net debt is not necessarily SEC debt minus cash and short-term investments',
 'ebitda': 'FMP EBITDA is not necessarily SEC EBIT plus derived depreciation and amortization',
 'returnOnInvestedCapital': 'Provider ROIC methodology is not equivalent to either SEC v2 proxy',
}
class APIError(Exception):
    def __init__(self, code, reason):
        self.code, self.reason = code, str(reason)[:180]
        super().__init__(f'{code}: {reason}')


def safe_number(value):
    if value is None or value == '':
        return None
    try:
        n = float(value)
        return n if abs(n) < 1e18 and n == n else None
    except (ValueError, TypeError, OverflowError):
        return None


def sec_index(path):
    """Annual SEC rows indexed by uppercase ticker and fiscal year (FY only)."""
    if path is None:
        return {}
    out = {}
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row.get('period_type') != 'FY':
                continue
            key = (row.get('ticker', '').strip().upper(), str(row.get('fiscal_year', '')))
            if all(key):
                out[key] = row
    return out


def from_queue(path, count):
    if not path:
        return list(DEFAULT_SYMBOLS)[:count]
    priorities = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: (priorities.get(str(r.get('priority', '')).split('_')[0], 99), r.get('ticker', '')))
    tickers = []
    for row in rows:
        ticker = row.get('ticker', '').strip().upper()
        if ticker and ticker not in tickers:
            tickers.append(ticker)
        if len(tickers) >= count:
            break
    return tickers


def fiscal_match(record, sec):
    """No FY2025-to-TTM2026 comparisons; require matching CIK/date/currency."""
    if record.get('period') not in ('FY', 'annual'):
        return 'FMP_NOT_ANNUAL'
    if str(record.get('fiscalYear', '')) != str(sec.get('fiscal_year', '')):
        return 'FISCAL_YEAR_MISMATCH'
    if str(record.get('reportedCurrency') or '').upper() != str(sec.get('currency') or 'USD').upper():
        return 'CURRENCY_MISMATCH'
    if record.get('cik') and sec.get('cik'):
        if str(record['cik']).zfill(10) != str(sec['cik']).zfill(10):
            return 'CIK_MISMATCH'
    try:
        days = abs((date.fromisoformat(record['date']) - date.fromisoformat(sec['period_end'])).days)
    except (KeyError, TypeError, ValueError):
        return 'PERIOD_DATE_MISSING'
    if days > 7:
        return 'PERIOD_END_MISMATCH'
    return None


def fetch_fmp(endpoint, ticker, api_key, opener=request.urlopen):
    """Never include key-containing URL in any reported exception."""
    query = parse.urlencode({'symbol': ticker, 'period': 'annual', 'limit': 5, 'apikey': api_key})
    req = request.Request(BASE + endpoint + '?' + query, headers={'Accept': 'application/json', 'User-Agent': 'AgenteAFundamental-PrivateValidator/1.0'})
    try:
        with opener(req, timeout=20) as resp:
            data = resp.read(2_000_000)
    except error.HTTPError as exc:
        if exc.code == 429:
            raise APIError(429, 'Free plan rate limit reached') from None
        if exc.code in (401, 402, 403):
            raise APIError(exc.code, 'Endpoint/key not permitted for this subscription') from None
        raise APIError(exc.code, 'Provider HTTP error') from None
    except (error.URLError, TimeoutError, OSError):
        raise APIError('NETWORK', 'Provider connection unavailable') from None
    try:
        result = json.loads(data)
    except (ValueError, UnicodeDecodeError):
        raise APIError('INVALID', 'Response is not valid JSON') from None
    if isinstance(result, dict):
        # FMP often returns JSON errors even when HTTP status is 200.
        raise APIError('PROVIDER', 'Endpoint rejected, or returned an unexpected JSON object')
    if not isinstance(result, list):
        raise APIError('INVALID', 'Expected list of statement records')
    return result


def compare_one(ticker, endpoint, fmp_record, sec_row, tolerance=0.015):
    rows=[]
    mismatch = fiscal_match(fmp_record, sec_row) if sec_row else None
    for fmp_field, sec_field in NUMERIC_FIELDS[endpoint].items():
        fval=safe_number(fmp_record.get(fmp_field))
        sval=safe_number(sec_row.get(sec_field)) if sec_row else None
        if sec_row is None:
            status='SEC_YEAR_UNAVAILABLE'
        elif mismatch:
            status='PERIOD_OR_IDENTITY_UNMATCHED'
        elif fval is None:
            status='FMP_VALUE_MISSING'
        elif sval is None:
            status='SEC_VALUE_MISSING'
        else:
            # CAPEX expense is normally negative at FMP, while SEC stores spending positive.
            if fmp_field=='capitalExpenditure':fval=abs(fval)
            diff=abs(fval-sval)
            threshold=max(1e-6,tolerance*max(abs(fval),abs(sval)))
            status='MATCH' if diff<=threshold else 'REVIEW_DIFFERENCE'
        rows.append({'ticker':ticker,'fiscal_year':str(fmp_record.get('fiscalYear','')),
                     'period_end_fmp':fmp_record.get('date',''),
                     'period_end_sec':sec_row.get('period_end','') if sec_row else '',
                     'currency_fmp':fmp_record.get('reportedCurrency',''),
                     'fmp_endpoint':endpoint,'metric_fmp':fmp_field,'metric_sec':sec_field,
                     'value_fmp':fval,'value_sec':sval,
                     'status':status,'reason':mismatch or '',
                     'source':'FMP Basic comparison (not imported into SEC)'})
    return rows


def crosscheck(tickers, sec, api_key, max_calls, delay, fetch=fetch_fmp):
    report=[]; events=[]; calls=0; halt=False; restricted_endpoints=set()
    for ticker in tickers:
        if halt:break
        for endpoint in ENDPOINTS:
            if halt:
                break
            if endpoint in restricted_endpoints:
                events.append({'ticker':ticker,'endpoint':endpoint,'status':'SKIPPED_RESTRICTED_ENDPOINT'})
                continue
            if calls >= max_calls:
                events.append({'ticker':ticker,'endpoint':endpoint,'status':'CALL_BUDGET_REACHED'})
                halt=True;break
            calls+=1
            try:
                entries=fetch(endpoint,ticker,api_key)
            except APIError as exc:
                events.append({'ticker':ticker,'endpoint':endpoint,'status':'API_UNAVAILABLE','code':str(exc.code),'reason':exc.reason})
                if exc.code in (401, 429):halt=True
                if exc.code in (402, 403):restricted_endpoints.add(endpoint)
                if delay:time.sleep(delay)
                continue
            accepted=0
            for rec in entries:
                if not isinstance(rec,dict) or rec.get('period') not in ('FY','annual'):
                    continue
                key=(ticker,str(rec.get('fiscalYear','')))
                report.extend(compare_one(ticker,endpoint,rec,sec.get(key)))
                accepted+=1
            events.append({'ticker':ticker,'endpoint':endpoint,'status':'FETCHED','annual_periods':accepted})
            if delay:time.sleep(delay)
    return report,events,calls


def run(argv=None):
    parser=argparse.ArgumentParser(description='Read-only FMP Basic spot checks for SEC normalized fundamentals')
    parser.add_argument('--sec-csv',type=Path,help='Optional SEC normalized annual CSV; if omitted only connection/coverage is tested')
    parser.add_argument('--qa-queue',type=Path,help='Optional QA review queue, prioritized P0 to P3')
    parser.add_argument('--tickers',default='',help='Comma separated list; default AAPL,CSCO,MCK')
    parser.add_argument('--max-companies',type=int,default=3)
    parser.add_argument('--max-calls',type=int,default=9)
    parser.add_argument('--delay',type=float,default=0.4)
    parser.add_argument('--out-dir',type=Path,default=Path('fmp_qa_local'))
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(argv)
    if not 1<=args.max_companies<=10 or not 1<=args.max_calls<=30 or args.delay<0:
        parser.error('Safety limits: 1-10 companies, 1-30 calls, nonnegative delay')
    tickers=[s.strip().upper() for s in args.tickers.split(',') if s.strip()] if args.tickers else from_queue(args.qa_queue,args.max_companies)
    tickers=list(dict.fromkeys(tickers))[:args.max_companies]
    if not tickers or any(not re.fullmatch(r'[A-Z0-9.\-]{1,15}',t) for t in tickers):
        parser.error('Invalid ticker list')
    planned=min(args.max_calls,len(tickers)*len(ENDPOINTS))
    if args.dry_run:
        print(json.dumps({'mode':'dry_run','tickers':tickers,'endpoints':ENDPOINTS,'max_http_calls':planned,'price':'$0 if FMP Basic permits requested endpoints','will_not_modify_sec':True},ensure_ascii=False,indent=2))
        return 0
    key=os.environ.get('FMP_API_KEY','').strip()
    if not key:
        print('FMP_API_KEY not configured. Create a free FMP account, then set the secret FMP_API_KEY. Nothing was queried.',file=sys.stderr)
        return 2
    sec=sec_index(args.sec_csv)
    report,events,calls=crosscheck(tickers,sec,key,args.max_calls,args.delay)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    fields=['ticker','fiscal_year','period_end_fmp','period_end_sec','currency_fmp','fmp_endpoint','metric_fmp','metric_sec','value_fmp','value_sec','status','reason','source']
    with (args.out_dir/'fmp_sec_comparison.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(report)
    from collections import Counter
    overview={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'source':'FMP Basic (account-specific endpoint entitlement not yet verified)',
              'requested_tickers':tickers,'http_calls_consumed':calls,'quota_budget_configured':args.max_calls,
              'comparison_status_counts':dict(Counter(r['status'] for r in report)),
              'endpoint_events':events,'raw_provider_responses_stored':False,'sec_data_mutated':False,
              'limitations':['FMP netDebt/totalDebt may use other lease and liquidity definitions',
                             'Do not assume free access to all endpoints or five fiscal years',
                             'No automated SEC overwrite; manual methodology review required for mismatches',
                             'Results only for private analysis; redistribution requires license review']}
    (args.out_dir/'fmp_qa_summary.json').write_text(json.dumps(overview,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'http_calls':calls,'rows_compared':len(report),'statuses':overview['comparison_status_counts'],
                     'unavailable_endpoints':sum(e['status']=='API_UNAVAILABLE' for e in events),
                     'output_directory':str(args.out_dir)},ensure_ascii=False))
    return 0

if __name__=='__main__':sys.exit(run())