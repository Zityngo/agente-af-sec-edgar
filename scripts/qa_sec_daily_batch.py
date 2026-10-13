#!/usr/bin/env python3
"""Valida el lote diario SEC e identifica filings recientes. Sin precios ni agregadores.

Salida: JSON QA + CSV de revisión en publico/sec/. No cambia la base financiera
ni sincroniza Google Sheets: esa ingestión exige credenciales separadas y una
fase de comprobación contable/fiscal. Modo seguro por defecto.
"""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT=Path(os.environ.get('SEC_BATCH_ROOT','publico/sec'))
WINDOW_DAYS=int(os.environ.get('SEC_ALERT_DAYS','14'))
FORM_TYPES={'10-K','10-K/A','10-Q','10-Q/A','8-K','8-K/A','20-F','20-F/A','6-K'}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_snapshot(manifest_path: Path, cutoff_date: str) -> tuple[dict,list[dict]]:
    man=json.loads(manifest_path.read_text(encoding='utf-8'))
    if man.get('schema')!='SEC_SP500_BATCH_V1':
        raise ValueError('Unexpected SEC manifest schema; not safely ingestible')
    firms=man.get('companies',[])
    expected_count=len(firms)
    if not (1<=expected_count<=100):
        raise ValueError('Invalid batch size; refusing suspicious manifest')
    seen=set();events=[];errors=[];counts={}
    for f in firms:
        cik=f.get('cik','')
        if len(cik)!=10 or not cik.isdigit() or cik in seen:
            errors.append({'cik':cik,'reason':'invalid/duplicated CIK'});continue
        seen.add(cik)
        if f.get('status')!='OK':
            errors.append({'cik':cik,'reason':'download status not OK'});continue
        raw={}
        for typ in ('submissions','companyfacts'):
            path=manifest_path.parent / f'CIK{cik}' / f'{typ}.json.gz'
            try:
                compressed=path.read_bytes()
                obj_bytes=gzip.decompress(compressed)
                if sha(obj_bytes)!=f.get('sha256_'+typ):
                    raise ValueError('SHA256 mismatch')
                o=json.loads(obj_bytes)
                if str(o.get('cik','')).zfill(10)!=cik:
                    raise ValueError('SEC CIK mismatch')
                if typ=='submissions' and not isinstance(o.get('filings'),dict):
                    raise ValueError('Missing submissions filings')
                if typ=='companyfacts' and not isinstance(o.get('facts'),dict):
                    raise ValueError('Missing SEC facts')
                raw[typ]=o
            except (OSError,ValueError,EOFError,TypeError) as exc:
                errors.append({'cik':cik,'reason':str(exc),'source':typ})
        if len(raw)!=2:continue
        subs=raw['submissions']['filings'].get('recent',{})
        n=len(subs.get('form',[]))
        for key in ('accessionNumber','filingDate','primaryDocument','reportDate'):
            if len(subs.get(key,[])) != n:
                errors.append({'cik':cik,'reason':'recent filings column length mismatch: '+key})
                n=0;break
        sym='/'.join(f.get('symbols',[]))
        for i in range(n):
            form=subs['form'][i]
            filed=subs['filingDate'][i]
            if form not in FORM_TYPES or not (cutoff_date<=filed<=datetime.now(timezone.utc).date().isoformat()):continue
            acc=subs['accessionNumber'][i]
            primary=subs['primaryDocument'][i]
            item=subs.get('items',[])
            detail=item[i] if i<len(item) else ''
            filing_type='RESULTADOS_8K' if form.startswith('8-K') and '2.02' in detail else ('10K_10Q' if form.startswith(('10-K','10-Q')) else 'EVENTO')
            if not acc or not primary:
                errors.append({'cik':cik,'reason':'Missing accession or primary document'});continue
            events.append({
                'ticker':sym,'cik':cik,'form':form,'filing_date':filed,
                'period_end':subs['reportDate'][i], 'items':detail,
                'classification':filing_type,
                'accession':acc,
                'official_url':f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-", "")}/{primary}',
                'status':'PENDIENTE_VALIDAR_PERIODO_Y_METRICAS'
            })
        counts[cik]={'ticker':sym,'documents':n,'new_filings':sum(e['cik']==cik for e in events)}
    status='PASS' if not errors else 'FAIL_REVIEW'
    report={
        'status':status,'checked_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'source':'SEC official companyfacts + submissions','manifest':manifest_path.name,
        'window_days':WINDOW_DAYS,'cutoff_date':cutoff_date,
        'batch_companies':expected_count,'validated_companies':len(counts),
        'recent_filings':len(events),'errors':errors,
        'notice':'Daily batch, not all 500 companies. No direct Google Sheets update; accounting values remain subject to human/method audit.',
        'source_url':'https://data.sec.gov/'
    }
    return report,sorted(events,key=lambda e:(e['filing_date'],e['ticker']),reverse=True)


def main() -> None:
    if WINDOW_DAYS<1 or WINDOW_DAYS>90:raise SystemExit('SEC_ALERT_DAYS out of range')
    now=datetime.now(timezone.utc)
    cutoff=(now-timedelta(days=WINDOW_DAYS)).date().isoformat()
    path=ROOT/'sp500_batch_manifest.json'
    if not path.exists():raise SystemExit('Missing daily SEC batch manifest')
    report,events=verify_snapshot(path,cutoff)
    (ROOT/'sec_diario_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    columns=['ticker','cik','form','filing_date','period_end','items','classification','accession','official_url','status']
    with (ROOT/'sec_diario_nuevos_filings.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(events)
    print('SEC DAILY QA:',report['status'],'issuer',report['validated_companies'],'/',report['batch_companies'],
          'filings',len(events),'errors',len(report['errors']))
    if report['status']!='PASS':
        print('SEC DAILY QA BLOCKED: review errors in sec_diario_qa.json',file=sys.stderr)
        raise SystemExit(1)

if __name__=='__main__':main()