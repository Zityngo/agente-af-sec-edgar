#!/usr/bin/env python3
"""READ-ONLY SEC + EODHD demo: pilot of AAPL/TSLA/AMZN.

Reuses the existing SEC normalizer, af_core SQLite and official FY2025 10-K
anchors; does not write Google Sheets or publish a vendor raw data dump.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request
from datetime import date
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"scripts")]
import pilot_5
from af_core.verification import capex_quality,attributable_quality,ebit_quality

TICKERS=("AAPL","TSLA","AMZN")
CIK={"AAPL":"0000320193","TSLA":"0001318605","AMZN":"0001018724"}
SEC_10K={
 "AAPL":"https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm",
 "TSLA":"https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm",
 "AMZN":"https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm"
}
# Published FY2025 10-K values (USD millions; EPS USD/share).
# Amazon cash CapEx 131819m is GROSS; management FCF uses NET 128320m.
GOLD={
 "AAPL":{"end":"2025-09-27","revenue":416161,"operating_income":133050,"net_income":112010,"cfo":111482,"capex":12715,"eps_diluted":7.46},
 "TSLA":{"end":"2025-12-31","revenue":94827,"operating_income":4355,"net_income":3794,"cfo":14747,"capex":8527,"eps_diluted":1.08},
 "AMZN":{"end":"2025-12-31","revenue":716924,"operating_income":79975,"net_income":77670,"cfo":139514,"capex":131819,"eps_diluted":7.17}
}
MOAT={
 "AAPL":("Marca y costes de sustitución (hipótesis)","Validar retención, peso de Servicios, márgenes y dependencia de iPhone"),
 "TSLA":("Marca, escala industrial y red de carga (hipótesis)","Validar márgenes de vehículo, costes, demanda y retorno del CapEx en IA"),
 "AMZN":("Escala logística y costes de sustitución AWS (hipótesis)","Validar márgenes AWS, CapEx de centros de datos y FCF recurrente")
}

def fetch(url,ua):
    req=urllib.request.Request(url,headers={"User-Agent":ua,"Accept":"application/json","Accept-Encoding":"identity"})
    with urllib.request.urlopen(req,timeout=80) as z:return json.loads(z.read().decode("utf-8"))

def number(v):
    try:return float(v) if v is not None and v!="" else None
    except (ValueError,TypeError):return None

def eodhd(t):
    url=f"https://eodhd.com/api/v1.1/fundamentals/{t}.US?api_token=demo&fmt=json"
    try:
        payload=fetch(url,"AFundamental-Research-Sprint/1.0")
        if not isinstance(payload,dict) or not isinstance(payload.get("Financials"),dict):
            return {"status":"UNAVAILABLE","reason":"No Financials in demo payload","url":url},{}
        return {"status":"AVAILABLE","url":url,"sections":list(payload.keys())},payload
    except Exception as e:
        return {"status":"UNAVAILABLE","url":url,"reason":str(e)[:190]},{}

def financial_year(payload,period_end):
    fs=payload.get("Financials") or {}
    def item(key):
        annual=(fs.get(key) or {}).get("yearly") or {}
        if not isinstance(annual,dict):return {}
        if period_end in annual:return annual[period_end] or {}
        exact=next((v for v in annual.values() if isinstance(v,dict) and v.get("date")==period_end),None)
        if exact is not None:return exact
        # Provider calendar labels can use a month-end close while the SEC
        # fiscal week ends a few days earlier. No more than 10 days of tolerance.
        target=date.fromisoformat(period_end)
        candidates=[]
        for k,v in annual.items():
            if not isinstance(v,dict):continue
            try:
                reported=date.fromisoformat(str(v.get("date") or k)[:10])
                delta=abs((reported-target).days)
                if delta<=10:candidates.append((delta,v))
            except ValueError:pass
        return sorted(candidates,key=lambda x:x[0])[0][1] if candidates else {}
    inc,cf=item("Income_Statement"),item("Cash_Flow")
    values={"revenue":inc.get("totalRevenue"),"operating_income":inc.get("operatingIncome"),
            "net_income":inc.get("netIncomeApplicableToCommonShares"),
            "eps_diluted":inc.get("epsDiluted"),
            "cfo":cf.get("totalCashFromOperatingActivities"),
            "capex":cf.get("capitalExpenditures")}
    return {k:(abs(number(v)) if k=="capex" and number(v) is not None else number(v)) for k,v in values.items()}

def latest_filings(cik,ua):
    url=f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        j=fetch(url,ua)["filings"]["recent"]
        v=[]
        for idx,form in enumerate(j["form"]):
            if form not in ("10-K","10-Q","8-K","DEF 14A","4","3","5","SC 13D","SC 13G","13F-HR"):continue
            acc=j["accessionNumber"][idx]
            v.append({"form":form,"date":j["filingDate"][idx],"accession":acc,
                "url":f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{j['primaryDocument'][idx]}"})
            if len(v)>=45:break
        return {"status":"AVAILABLE","url":url,"filings":v}
    except Exception as e:return {"status":"UNAVAILABLE","url":url,"filings":[],"reason":str(e)[:190]}

def reconcile(row,official):
    data={}
    for k,val in official.items():
        if k=="end":continue
        expected=val if k=="eps_diluted" else float(val)*1e6
        got=number(row.get(k)) if row else None
        diff=abs(got-expected)/max(abs(expected),1) if got is not None else None
        status="MISSING" if diff is None else "MATCH" if diff<= (.01 if k=="eps_diluted" else .005) else "DIVERGENCE"
        data[k]={"official":expected,"extracted":got,"relative_difference":diff,"status":status}
    return data

def compare_external(row,vals):
    data={}
    for k,ref in vals.items():
        sec=number(row.get(k)) if row else None
        delta=abs(ref-sec)/max(abs(sec),1) if ref is not None and sec is not None else None
        data[k]={"status":"UNAVAILABLE" if delta is None else "MATCH" if delta<=.01 else "REVIEW",
                 "relative_difference":delta}
    return data

def format_usd(v,eps=False):
    return "—" if v is None else f"{v:,.2f}" if eps else f"{v/1e6:,.0f}"

def report_markdown(result):
    lines=["# A.Fundamental · Apple, Tesla y Amazon","",
        "Versión de auditoría: NO certificada; no es recomendación personalizada.",
        f"Extracción (UTC): {result['generated_at']}.",
        "Fuente principal SEC EDGAR. EODHD demo es contraste opcional.","",
        "## Resumen","",
        "| Empresa | Conciliación del FY2025 | API EODHD |",
        "|---|---|---|"]
    for t,r in result["companies"].items():
        c=Counter(x["status"] for x in r["reconciliation"].values())
        lines.append(f"| {t} | {c['MATCH']} coinciden, {c['DIVERGENCE']} discrepancias, {c['MISSING']} no disponibles | {r['eodhd']['status']} |")
    for t,r in result["companies"].items():
        lines+=["",f"## {t} · ejercicio 2025","",
            f"10-K oficial: {SEC_10K[t]}",
            f"Período: {GOLD[t]['end']}; CIK: {CIK[t]}; accession extraído: {r['accession'] or 'SIN DATO'}.",
            "","### Resultados SEC vs 10-K publicado","","| Campo | 10-K | XBRL normalizado | Estado |",
            "|---|---:|---:|---|"]
        for metric,c in r["reconciliation"].items():
            lines.append(f"| {metric} | {format_usd(c['official'],metric=='eps_diluted')} | {format_usd(c['extracted'],metric=='eps_diluted')} | {c['status']} |")
        lines+=["","### Controles del motor",""]
        for metric,quality in r["quality"].items():lines.append(f"- {metric}: {quality[0]} — {quality[1]}")
        lines+=["","### Negocio, MOAT y tesis a contrastar","",
            f"- Hipótesis competitiva: {MOAT[t][0]}.",
            f"- Contraste exigido: {MOAT[t][1]}.",
            "- Un MOAT no se acredita únicamente con ratios históricos.",
            "","### Directiva, insiders y grandes accionistas","",
            f"Índice SEC de filings: {r['filings']['url']}.",
            "Formularios indexados en muestra: "+", ".join(f"{f}: {n}" for f,n in sorted(Counter(x["form"] for x in r["filings"]["filings"]).items()))+".",
            "PENDIENTE: parsear cada Form 4 con códigos P/S/M/A/F y planes 10b5-1; procesar 13D/G y cambios 13F. No se han inferido compras o ventas individuales.",
            "","### Eventos relevantes SEC",""]
        ev=[x for x in r["filings"]["filings"] if x["form"]=="8-K"][:4]
        lines.extend([f"- {x['date']}: 8-K pendiente de clasificación: {x['url']}" for x in ev] or ["- Sin 8-K en la muestra indexada."])
        if t=="AMZN":lines+=["","**Amazon:** FCF según empresa 11.194 MUSD (CapEx neto 128.320); FCF con CapEx bruto 7.695 MUSD. Distintos métodos."]
        if t=="TSLA":lines+=["","**Tesla:** beneficio neto consolidado 3.855 MUSD vs 3.794 MUSD atribuible a ordinarios; no intercambiables."]
        lines+=["","### Valoración y conclusión","",
                "PER y EV pendientes de precio/acciones fechados y fuente comercial adecuada; DCF y forward requieren hipótesis expresas.",
                "Bloquear toda cifra con estado DIVERGENCE, BLOCKED o NULL hasta revisar 10-K/10-Q.",
                "La tesis final queda ABIERTA; no presentar señal de compra/venta.",""]
    lines+=["","## Limitaciones","",
        "El informe es una auditoría de FY2025 con datos SEC y un proveedor demo; no cubre todavía todas las notas a los estados, el último 10-Q reconciliado, ni noticias externas.",
        "Los datos completos del proveedor demo no se guardan ni redistribuyen en el repositorio.",
        "La ejecución se realizó en una rama independiente. No modifica main, el Proyecto B ni Google Sheets."]
    return "\n".join(lines)+"\n"

def run(out,ua):
    pilot_5.TICKERS=list(TICKERS)
    con,errors=pilot_5.run(out,2021,2026,ua,sleep=.4)
    result={"generated_at":datetime.now(timezone.utc).isoformat(),"companies":{},"errors":errors}
    for t in TICKERS:
        cik=CIK[t]
        row=con.execute("SELECT * FROM periods WHERE cik=? AND period_type='FY' AND period_end=?",(cik,GOLD[t]["end"])).fetchone()
        row=dict(row) if row else None
        q={}
        if row:
            q={"EBIT":ebit_quality(row),"CapEx":capex_quality(row),
               "beneficio_atribuible":attributable_quality(row)}
        provider,payload=eodhd(t)
        external=financial_year(payload,GOLD[t]["end"]) if payload else {}
        financials=payload.get("Financials") or {}
        provider["fy_income_dates"]=list(((financials.get("Income_Statement") or {}).get("yearly") or {}).keys())[-8:]
        provider["fy_income_field_names"]=list(next(iter(((financials.get("Income_Statement") or {}).get("yearly") or {}).values()),{}).keys()) if financials else []
        provider["insider_section_type"]=type(payload.get("InsiderTransactions")).__name__ if payload else "missing"
        provider["holder_section_type"]=type(payload.get("Holders")).__name__ if payload else "missing"
        result["companies"][t]={
            "cik":cik,"accession":row["accession"] if row else None,
            "reconciliation":reconcile(row,GOLD[t]),"quality":q,
            "source_tags":json.loads(row["sources_json"] or "{}") if row else {},
            "eodhd":provider,"eodhd_comparison":compare_external(row,external),
            "eodhd_coverage":{k:v is not None for k,v in external.items()},
            "filings":latest_filings(cik,ua),
            "engine_fy":{z["metric"]:{"value":z["value"],"status":z["status"],"reason":z["reason"]}
                for z in con.execute("SELECT metric,value,status,reason FROM metrics WHERE cik=? AND scope='FY' AND period_end=?",
                (cik,GOLD[t]["end"]))}
        }
    out.mkdir(parents=True,exist_ok=True)
    (out/"auditoria_piloto_3.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    (out/"analisis_piloto_3.md").write_text(report_markdown(result),encoding="utf-8")
    summary={t:{"SEC":Counter(v["status"] for v in r["reconciliation"].values()),
                "EODHD":r["eodhd"]["status"]} for t,r in result["companies"].items()}
    print(json.dumps({"companies":summary,"download_errors":errors},ensure_ascii=False))
    return len(errors)==0 and len(result["companies"])==3

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,default=Path("publico/pilot3"))
    a=ap.parse_args()
    ua=os.environ.get("SEC_USER_AGENT","").strip()
    if not ua:raise SystemExit("Missing SEC_USER_AGENT")
    return 0 if run(a.out,ua) else 1

if __name__=="__main__":sys.exit(main())
