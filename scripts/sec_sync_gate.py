#!/usr/bin/env python3
"""SEC -> Sheets: candidate-only quality gate, never writes to normalized financials.

Input is the already-verified output from scripts/sec_auto_staging.py.
Conservative classifications are NOT an audit or approval of a security.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

STAGING_HEADERS = ["clave","ticker","cik","form","periodo","cierre","filed", "accession",
    "ingresos_usd","ebit_operativo_usd","net_income_usd","cfo_usd","capex_usd",
    "fcf_proxy_usd","qa","trazas_xbrl","url_filing","url_companyfacts",
    "sha256_companyfacts","fecha_utc","observacion"]
QA_HEADERS = ["clave","ticker","cik","tipo","cierre","accession","qa_origen",
    "en_historico","metricas_contrastadas","desviacion_maxima","resultado_QA",
    "motivos","filing_sec","sha256","fecha_extraccion"]
SOURCE_FY = (8,10,11,13,14,15)
SOURCE_Q = (8,9,10,11,12,13)
CANDIDATE_METRICS = (8,9,10,11,12,13)
CRITICAL = {"ADP", "AEP", "ADM", "ABT", "ACN", "VYLR"}
ALLOWED_EBIT = {"OperatingIncomeLoss", "ProfitLossFromOperatingActivities"}
ALLOWED_CAPEX = {"PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsToAcquireProductiveAssets",
    "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"}


def sheet_date(value):
    if isinstance(value, (float, int)):
        return (datetime(1899,12,30,tzinfo=timezone.utc) + timedelta(days=value)).date().isoformat()
    return str(value or "")[:10]


def num(value):
    if value in (None, ""): return None
    try:
        f=float(value)
        return f if abs(f)<float('inf') else None
    except (TypeError,ValueError): return None


def master_index(data, kind):
    end_col=4 if kind=="FY" else 5
    indexed={}
    for row in data[1:]:
        if len(row)<=end_col: continue
        cik=str(row[1]).zfill(10)
        key=(cik, sheet_date(row[end_col]))
        if key in indexed: raise ValueError(f"duplicated {kind} master key: {key}")
        indexed[key]=row
    return indexed


def quality_row(row, fy, q, critical=CRITICAL):
    if len(row)!=len(STAGING_HEADERS):
        raise ValueError("Wrong candidate width: refusing update")
    key,ticker,cik,form,kind,period_end,filing_date,acc=row[:8]
    cik=str(cik).zfill(10)
    if kind not in ("FY","Q") or (kind=="FY" and form not in ("10-K","10-K/A","20-F","20-F/A")) or (kind=="Q" and form not in ("10-Q","10-Q/A")):
        raise ValueError("Unexpected SEC form or kind")
    if not re.fullmatch(r"[0-9]{10}",cik) or cik not in str(key) or str(acc) not in str(key):
        raise ValueError("candidate key/CIK/accession mismatch")
    reasons=[]
    baseline=(fy if kind=="FY" else q).get((cik,sheet_date(period_end)))
    matched=0
    maxdiff=None
    state="EN_REVISION"
    if not baseline:
        state="NUEVO_SIN_BASE"
        reasons.append("CIK y cierre ausentes del histórico: revisar antes de integrar")
    else:
        try: evidence=json.loads(row[15] or "{}")
        except (TypeError,ValueError):
            evidence={};reasons.append("Traza XBRL JSON inválida");state="BLOQUEADO"
        if str(row[14]).startswith("QA_"):
            state="BLOQUEADO";reasons.append("Extracción incompleta: "+str(row[14]))
        if any(t in critical for t in str(ticker).split(',')):
            state="BLOQUEADO";reasons.append("Emisor crítico pendiente del 10-K/10-Q")
        orig_status=str(baseline[34 if kind=="FY" else 26] if len(baseline)>=(35 if kind=="FY" else 27) else "")
        if any(x in orig_status.upper() for x in ("REVIEW","BLOCK","ERROR")):
            state="BLOQUEADO";reasons.append("Tabla maestra contiene alerta de calidad")
        for field,allowed in (("ebit",ALLOWED_EBIT),("capex",ALLOWED_CAPEX)):
            if field in evidence and evidence[field].get("tag") not in allowed:
                state="BLOQUEADO";reasons.append("Etiqueta SEC no aprobada: "+field)
        idx=SOURCE_FY if kind=="FY" else SOURCE_Q
        for name,ci,si in zip(("ingresos","EBIT","beneficio","CFO","CapEx","FCF"),CANDIDATE_METRICS,idx):
            candidate= num(row[ci]); historical=num(baseline[si] if len(baseline)>si else None)
            if candidate is None or historical is None: continue
            matched+=1
            diff=abs(candidate-historical)/max(abs(historical),1_000_000)
            maxdiff=diff if maxdiff is None else max(maxdiff,diff)
            if diff>0.02:
                state="BLOQUEADO";reasons.append(f"{name}: desviación {diff:.1%} (>2%)")
        if state=="EN_REVISION":
            if matched==0: state="SIN_COMPARABLE";reasons.append("Ninguna métrica comparable")
            elif maxdiff>0.005: state="AVISO_DIFERENCIA";reasons.append("Desviación >0,5%: revisión de etiquetas")
            else: state="COINCIDE_PROXY";reasons.append("Conciliación preliminar <=0,5%; no certificado")
    if str(row[14]).startswith("QA_") and state != "BLOQUEADO":
        state="BLOQUEADO";reasons.append("Extracción fuente incompleta: "+str(row[14]))
    if any(t in critical for t in str(ticker).split(",")) and state != "BLOQUEADO":
        state="BLOQUEADO";reasons.append("Emisor crítico pendiente del 10-K/10-Q")
    if not re.fullmatch(r"[0-9a-f]{64}",str(row[18])):
        state="BLOQUEADO";reasons.append("Sin SHA256 fiable")
    if not str(row[16]).startswith("https://www.sec.gov/Archives/edgar/data/"):
        state="BLOQUEADO";reasons.append("URL filing SEC inesperada")
    return [key,ticker,cik,kind,sheet_date(period_end),acc,row[14],
            "SI" if baseline else "NO",matched,maxdiff,state," | ".join(reasons),
            row[16],row[18],row[19]]


def validate(preview, fy_values, q_values):
    if preview.get("columns")!=STAGING_HEADERS:
        raise ValueError("SEC preview header mismatch: fail closed")
    fs,qs=master_index(fy_values,"FY"),master_index(q_values,"Q")
    rows=preview.get("rows")
    if not isinstance(rows,list) or not 1<=len(rows)<=200:
        raise ValueError("Unexpected candidate batch size")
    keys=set();out=[]
    for r in rows:
        if r[0] in keys: raise ValueError("Duplicate SEC accession key")
        keys.add(r[0]);out.append(quality_row(r,fs,qs))
    return out


def sheets_connection():
    import google.auth.transport.requests
    from google.oauth2 import service_account
    import requests
    sheet=os.environ.get("GOOGLE_SHEET_ID", "").strip()
    secret=os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not sheet or not secret: raise ValueError("Missing Google Sheets secrets")
    creds=service_account.Credentials.from_service_account_info(json.loads(secret),
        scopes=["https://www.googleapis.com/auth/spreadsheets"])
    http=google.auth.transport.requests.AuthorizedSession(creds)
    base="https://sheets.googleapis.com/v4/spreadsheets/"+quote(sheet,safe="")
    def request(method,route,**kw):
        response=getattr(http,method)(base+route,timeout=90,**kw)
        response.raise_for_status();return response.json()
    return request


def read_baseline(request):
    data=request("get","/values:batchGet",params={
        "ranges":["SEC_FY_5Y!A1:AK2452","SEC_Q_5Y!A1:AC10265"],
        "valueRenderOption":"UNFORMATTED_VALUE","dateTimeRenderOption":"SERIAL_NUMBER"})
    ranges=data.get("valueRanges",[])
    if len(ranges)!=2: raise ValueError("Incomplete source master read")
    return ranges[0].get("values",[]),ranges[1].get("values",[])


def upsert_qa(request,rows):
    tab="SEC_AUTO_QA"
    current=request("get","/values/"+quote(tab+"!A1:O",safe="")).get("values",[])
    if not current or current[0]!=QA_HEADERS:
        raise ValueError("SEC_AUTO_QA header missing/changed. Prepare tab before enabling writes")
    by_key={}
    for n,r in enumerate(current[1:],2):
        if not r: continue
        if r[0] in by_key: raise ValueError("Duplicate QA key: "+r[0])
        by_key[r[0]]=n
    updates=[];append=[];identical=0
    for r in rows:
        row=["" if x is None else x for x in r]
        prior=by_key.get(r[0])
        if prior:
            # Reconcile numeric formatted render safely; no update if effectively unchanged.
            updates.append({"range":f"{tab}!A{prior}:O{prior}","values":[row]})
        else: append.append(row)
    if updates:
        request("post","/values:batchUpdate",json={"valueInputOption":"RAW","data":updates})
    if append:
        request("post","/values/"+quote(tab+"!A:O",safe="")+":append",
            params={"valueInputOption":"RAW","insertDataOption":"INSERT_ROWS"},json={"values":append})
    return {"updated":len(updates),"added":len(append),"unchanged":identical}


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--preview",type=Path,default=Path("publico/sec/sec_staging_preview.json"))
    ap.add_argument("--out",type=Path,default=Path("publico/sec/sec_quality_gate.json"))
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args(argv)
    preview=json.loads(args.preview.read_text(encoding="utf-8"))
    request=sheets_connection()
    fy,q=read_baseline(request)
    rows=validate(preview,fy,q)
    counts={}
    for r in rows: counts[r[10]]=counts.get(r[10],0)+1
    result={"evaluated":len(rows),"counts":counts,"explanation":"Candidates only; never certified"}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps({**result,"headers":QA_HEADERS,"rows":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.write:result["sheets"]=upsert_qa(request,rows)
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":main()
