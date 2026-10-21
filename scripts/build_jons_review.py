"""Build a private, source-labelled three-issuer review pack for Jon.

The SEC-derived SQLite database is the single source for accounting data.
This script NEVER downloads market prices or sends anything externally.
Frozen manual quote/share snapshots are only for noncommercial pilot review.
"""
from __future__ import annotations
import json
import math
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from af_core.earnings_audit import load_events

TICKERS=("AAPL","TSLA","AMZN")
COMPANY_NOTES={
"AAPL":{
"business":"Hardware de consumo, servicios y ecosistema de dispositivos.",
"moat":"HIPOTESIS: marca, distribución, servicios y coste de sustitución. Pendiente prueba de retención y precio/volumen.",
"catalysts":"Servicios; próximos resultados anuales y mix de márgenes.",
"risks":"Concentración iPhone; regulación; China; valor terminal elevado; recompras y divisa.",
"question":"¿Qué crecimiento sostenible del FCF justifica el precio sin extrapolar devoluciones arancelarias?"},
"TSLA":{
"business":"Vehículos eléctricos, almacenamiento de energía y opciones en autonomía/robótica.",
"moat":"HIPOTESIS: producción, red de carga, software y escala. No valorar Optimus/robotaxis sin datos auditables.",
"catalysts":"Márgenes automoción, energía, hoja de ruta de autonomía y CapEx.",
"risks":"Competencia; riesgo de ejecución; dilución; gasto de inversión; valor de negocios todavía no probados.",
"question":"¿Cuánto valor asignar a nuevas líneas aún sin FCF verificable y cuál es la invalidación?"},
"AMZN":{
"business":"Comercio electrónico, AWS, publicidad e infraestructura logística.",
"moat":"HIPOTESIS: logística, Marketplace y costes de cambio en AWS. Verificar retorno incremental del CapEx de IA.",
"catalysts":"AWS, publicidad, productividad logística y retorno de centros de datos.",
"risks":"Gasto en infraestructura; regulación; provisión de capacidad; beneficios GAAP distorsionados por inversiones.",
"question":"¿Cuánto CapEx es expansión recuperable y cuánto mantenimiento estructural?"}}
SCENARIOS=[
{"label":"Conservador","growth":-0.02,"discount":0.12,"terminal":0.02},
{"label":"Base ilustrativo","growth":0.03,"discount":0.10,"terminal":0.025},
{"label":"Optimista","growth":0.08,"discount":0.09,"terminal":0.03}]


def load_snapshot(path):
    doc=json.loads(path.read_text(encoding="utf-8"))
    if doc.get("purpose")!="PRIVATE_3_ISSUER_PILOT_2026_10_20":
        raise ValueError("Snapshot no autorizado para este piloto")
    refs=doc.get("companies")
    if not isinstance(refs,dict) or set(refs)!=set(TICKERS):
        raise ValueError("Precio y acciones deben existir para los tres emisores")
    for ticker,v in refs.items():
        for k in ("price_usd","shares","price_date","shares_date","price_url","shares_url","filing_accession"):
            if k not in v:
                raise ValueError(ticker+": falta "+k)
        if (not isinstance(v["price_usd"],(int,float)) or isinstance(v["price_usd"],bool)
            or not math.isfinite(v["price_usd"]) or v["price_usd"]<=0
            or not isinstance(v["shares"],int) or v["shares"]<=0):
            raise ValueError(ticker+": cotización o acciones inválidas")
        if any(not v[k].startswith("https://") for k in ("price_url","shares_url")):
            raise ValueError("Enlace de origen obligatorio")
        if (date.fromisoformat(v["shares_date"])>date.fromisoformat(v["price_date"])
            or (date.fromisoformat(v["price_date"])-date.fromisoformat(v["shares_date"])).days>180):
            raise ValueError("Snapshot de acciones temporalmente incompatible")
    return doc


def discounted_cash_proxy(fcf, shares, growth, discount, terminal, years=5):
    """Educational equity cash proxy only: CFO-CapEx, assumes zero net borrowing.

    NOT auditable FCFE or FCFF. Returns None for negative unsustainable baselines.
    """
    if (fcf is None or not isinstance(fcf,(int,float)) or not math.isfinite(fcf)
        or fcf<=0 or shares is None or shares<=0
        or not all(math.isfinite(x) for x in (growth,discount,terminal))
        or discount<=terminal or discount<=-1 or growth<=-1 or not 1<=years<=15):
        return None
    pv=0.0
    last=fcf
    for year in range(1,years+1):
        last=fcf*(1+growth)**year
        pv+=last/(1+discount)**year
    terminal_pv=(last*(1+terminal)/(discount-terminal))/(1+discount)**years
    return {"per_share":(pv+terminal_pv)/shares,
            "pv_forecast":pv,
            "pv_terminal":terminal_pv,
            "terminal_pct":100*terminal_pv/(pv+terminal_pv),
            "method":"ILLUSTRATIVE_CFO_MINUS_GROSS_CAPEX_ZERO_NET_BORROWINGS_NOT_CERTIFIED"}


def _rows(con,sql,args=()):
    return [dict(x) for x in con.execute(sql,args)]


def pack(db_path, audit_path, snapshot_path):
    snap=load_snapshot(snapshot_path)
    audits=json.loads(audit_path.read_text(encoding="utf-8"))
    con=sqlite3.connect("file:"+str(db_path.resolve())+"?mode=ro",uri=True)
    con.row_factory=sqlite3.Row
    out={"schema_version":"jon_review_private_v1",
         "generated_utc":datetime.now(timezone.utc).isoformat(),
         "price_date":snap["date"],
         "basis":"Fiscal FY2021-2025 and available FY2026 quarters / TTM from pilot SQLite",
         "scenarios":SCENARIOS,
         "definitions":{"fcf":"CFO - CapEx bruto: NO FCFF, NO FCFE certificado.",
             "eps":"BPA GAAP diluido; TTM por suma de cuatro trimestres PROXY.",
             "shares":"Acciones ordinarias en circulación, no media ponderada diluida.",
             "price":"Cotización de cierre Nasdaq del 20/10/2026, lectura manual verificada, no actualización automática.",
             "dcf":"Modelo formativo CFO-CapEx, deuda neta futura = 0 por HIPOTESIS. No calcular valor justo certificado.",
             "status":"OK = formula/fuente compatible; PROXY = limitación material; BLOCKED/NULL = no utilizable."},
         "companies":{}}
    for ticker in TICKERS:
        company=con.execute("SELECT * FROM companies WHERE ticker=?",(ticker,)).fetchone()
        if company is None:
            raise ValueError("No hay empresa SEC: "+ticker)
        cik=company["cik"]
        annual=_rows(con,"SELECT * FROM periods WHERE cik=? AND period_type='FY' ORDER BY fiscal_year",(cik,))
        qs=_rows(con,"SELECT * FROM periods WHERE cik=? AND period_type!='FY' ORDER BY period_end",(cik,))
        ttm_raw=_rows(con,"SELECT metric,value,status,reason,definition FROM metrics WHERE cik=? AND scope='TTM' ORDER BY period_end DESC,metric",(cik,))
        ttm={}
        for r in ttm_raw:
            ttm.setdefault(r["metric"],r)
        fym=_rows(con,"SELECT period_end,metric,value,status,reason FROM metrics WHERE cik=? AND scope='FY'",(cik,))
        fylookup={(x["period_end"],x["metric"]):x for x in fym}
        checks=_rows(con,"SELECT check_id,severity,period_ref,detail FROM checks WHERE cik=? ORDER BY severity,check_id",(cik,))
        if len(annual)<5 or len(qs)<4:
            raise ValueError(ticker+": falta histórico mínimo del motor")
        def rd(row,k):
            return row.get(k)
        history=[]
        for p in annual[-5:]:
            history.append({"fy":p["fiscal_year"],"end":p["period_end"],
                "accession":p["accession"],"filed":p["filed"],
                "revenue":rd(p,"revenue"),"ebit":rd(p,"operating_income"),
                "eps":rd(p,"eps_diluted"),"cfo":rd(p,"cfo"),"capex":rd(p,"capex"),
                "net_income":rd(p,"net_income"),"cash":rd(p,"cash"),
                "debt":rd(p,"debt_total"),"equity":rd(p,"equity"),
                "ebit_status":(fylookup.get((p["period_end"],"ebit")) or {}).get("status","NULL"),
                "fcf":(fylookup.get((p["period_end"],"fcf")) or {}).get("value"),
                "fcf_status":(fylookup.get((p["period_end"],"fcf")) or {}).get("status","NULL"),
                "roic":(fylookup.get((p["period_end"],"roic")) or {}).get("value"),
                "roic_status":(fylookup.get((p["period_end"],"roic")) or {}).get("status","NULL")})
        quarters=[]
        for p in qs[-12:]:
            sources=json.loads(p.get("sources_json") or "{}")
            quarters.append({"fy":p["fiscal_year"],"q":p["period_type"],
                "end":p["period_end"],"accession":p["accession"],
                "revenue":p["revenue"],"ebit":p["operating_income"],
                "eps":p["eps_diluted"],"cfo":p["cfo"],"capex":p["capex"],
                "fcf":p["cfo"]-p["capex"] if p["cfo"] is not None and p["capex"] is not None else None,
                "method":p["operating_income_method"],
                "cfo_origin":(sources.get("cfo") or {}).get("derived_from"),
                "capex_origin":(sources.get("capex") or {}).get("derived_from")})
        p=snap["companies"][ticker]
        mr=ttm.get("eps_ttm") or {}
        eps=mr.get("value") if mr.get("status") in ("OK","PROXY") else None
        fmr=ttm.get("fcf_ttm") or {}
        fcf=fmr.get("value") if fmr.get("status") in ("OK","PROXY") else None
        results=[{"scenario":s["label"],**s,
                  "result":discounted_cash_proxy(fcf,p["shares"],s["growth"],s["discount"],s["terminal"])}
                 for s in SCENARIOS]
        c_audit=audits["companies"][ticker]
        out["companies"][ticker]={
            "name":company["name"],"cik":cik,"sector":company["sector"],
            "notes":COMPANY_NOTES[ticker],
            "price":p,"market_cap_proxy":p["price_usd"]*p["shares"],
            "pe_gaap_ttm_proxy":p["price_usd"]/eps if eps is not None and eps>0 else None,
            "annual":history,"quarters":quarters,
            "ttm":ttm,"quality_checks":checks,
            "eps_audit":c_audit["eps_quarters"],
            "ttm_audit":c_audit["ttm_rollforward"],
            "earnings_events":c_audit["earnings_events"],
            "scenarios":results,
            "fcf_baseline":fcf,
            "fcf_baseline_status":fmr.get("status","NULL"),
            "valuation_status":"ILLUSTRATIVE_ONLY_NO_CERTIFIED_FCFE_FCFF_WACC",
            "proof":{"fy_reconciliations":c_audit["reconciliation"],
                     "eps_reference_count":4,
                     "ttm_rollforward_matches":sum(1 for x in c_audit["ttm_rollforward"]["metrics"].values()
                                                  if x["status"]=="MATCH")}}
    con.close()
    return out


def render_html(data,template_path):
    template=template_path.read_text(encoding="utf-8")
    payload=json.dumps(data,ensure_ascii=False,separators=(",",":"),allow_nan=False)
    # Prevent a filing or issuer name from prematurely closing a script element.
    payload=payload.replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    return template.replace("/*__AF_DATA__*/","const DATA="+payload+";")


def render_pdf(data,path):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    name="DejaVu"
    if Path(font).exists():
        pdfmetrics.registerFont(TTFont(name,font))
    else:name="Helvetica"
    st=getSampleStyleSheet()
    normal=ParagraphStyle("AFBody",parent=st["BodyText"],fontName=name,fontSize=8.4,leading=12,spaceAfter=7)
    h=ParagraphStyle("AFTitle",parent=normal,fontSize=18,leading=23,spaceAfter=13,textColor=colors.HexColor("#0d4060"))
    sh=ParagraphStyle("AFSection",parent=normal,fontSize=12,leading=16,spaceBefore=10,spaceAfter=9,textColor=colors.HexColor("#0d4060"))
    small=ParagraphStyle("AFSmall",parent=normal,fontSize=7,leading=10)
    def para(x,style=normal):
        from xml.sax.saxutils import escape
        return Paragraph(escape(str(x)),style)
    story=[para("A.FUNDAMENTAL | Paquete de revisión para Jon",h),
           para("Piloto PRIVADO. Apple, Tesla, Amazon. Fecha de precios: "+data["price_date"]+". Datos SEC: cierres FY2025 y TTM a 2026 Q2/Q3."),
           para("NO CERTIFICADO PARA INVERSIÓN. La valoración DCF se ilustra con FCF bruto; FCFE/FCFF, WACC y flujo sostenible permanecen pendientes."),
           para("Fuentes contables: SEC EDGAR companyfacts y 10-K/10-Q. Fuentes de mercado: referencias manuales de cierre con enlaces en JSON/HTML."),
           para("Criterios para la reunión",sh),
           para("1) Identificar si los valores originales coinciden con las cuentas. 2) Acordar flujo normalizado y deuda. 3) Decidir condiciones de MOAT y márgenes sectoriales. 4) Evaluar escenarios DCF como hipótesis. 5) Aceptar, corregir o bloquear por empresa."),
           para("Fuentes / estados y limitaciones",sh)]
    for k,v in data["definitions"].items():
        story.append(para(k.upper()+": "+v,small))
    story.append(PageBreak())
    def m(x,scale=1e6):
        return "N/D" if x is None else f"{x/scale:,.1f}".replace(","," ")
    for ticker,company in data["companies"].items():
        p=company["price"]
        story.extend([para(ticker+" | "+company["name"],h),
            para(company["notes"]["business"]),
            para("MOAT: "+company["notes"]["moat"],small),
            para("Precio (20/10/2026): "+str(p["price_usd"])+" USD | Acciones 10-Q: "+f'{p["shares"]:,}'+" | Capitalización PROXY: "+m(company["market_cap_proxy"],1e9)+" miles de millones USD."),
            para("PER TTM GAAP PROXY: "+(f'{company["pe_gaap_ttm_proxy"]:.1f}x' if company["pe_gaap_ttm_proxy"] else "N/D")+". Ganancias no recurrentes pueden distorsionarlo."),
            para("Histórico SEC FY (millones USD, salvo BPA)",sh)])
        headers=["FY/cierre","Ventas","EBIT","CFO","CapEx","FCF bruto","BPA","ROIC proxy"]
        rows=[list(map(lambda x:para(x,small),headers))]
        for y in company["annual"]:
            cells=[str(y["fy"]),m(y["revenue"]),m(y["ebit"]) if y["ebit_status"] in ("OK","PROXY") else "BLOQ.",
                   m(y["cfo"]),m(y["capex"]),
                   m(y["fcf"]) if y["fcf_status"] in ("OK","PROXY") else "BLOQ.",
                   str(round(y["eps"],2)) if y["eps"] is not None else "N/D",
                   str(round(100*y["roic"],1))+"%" if y["roic"] is not None and y["roic_status"]=="PROXY" else "N/D"]
            rows.append([para(x,small) for x in cells])
        tw=[28*mm,20*mm,20*mm,20*mm,20*mm,22*mm,14*mm,23*mm]
        table=Table(rows,colWidths=tw,repeatRows=1,hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e4edf3")),
            ("LINEBELOW",(0,0),(-1,0),0.8,colors.HexColor("#9bb1c4")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8fbfd")]),
            ("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        story.append(table)
        ttm=company["ttm"]
        story.append(para("Últimos doce meses (TTM) y estado",sh))
        for key in ("revenue_ttm","ebit_ttm","cfo_ttm","capex_ttm","fcf_ttm","eps_ttm"):
            z=ttm.get(key,{})
            v=z.get("value"); value=(f"{v:.2f} USD/acción" if key=="eps_ttm" and v is not None else m(v)+" MUSD")
            story.append(para(key+": "+value+" / "+z.get("status","NULL"),small))
        bridge=company["ttm_audit"]
        story.append(para("Puente SEC FY + YTD - YTD anterior: "+bridge["status"]+
                          " ("+str(company["proof"]["ttm_rollforward_matches"])+"/4 coincidencias).",small))
        story.append(para("Extraordinarios y BPA sostenible",sh))
        ev=company["earnings_events"]
        if ev["events"]:
            for e in ev["events"]:
                story.append(para(str(e["period_type"])+" "+str(e["period_end"])+": "+e["description"]+
                                  " ["+str(e["amount"])+", "+str(e["basis"])+"]",small))
        else:story.append(para("Sin eventos en catálogo parcial NO significa ausencia de extraordinarios.",small))
        story.append(para("BPA ajustado: BLOQUEADO hasta disponer de conciliación fiscal y acciones diluidas.",small))
        story.append(para("Escenarios DCF (HIPOTESIS, no precio objetivo)",sh))
        for s in company["scenarios"]:
            r=s["result"]
            story.append(para(s["scenario"]+": crecimiento "+str(s["growth"]*100)+"%, tasa "+str(s["discount"]*100)+
                               "%, terminal "+str(s["terminal"]*100)+"%; "+
                               (f'{r["per_share"]:.2f} USD/acción; terminal {r["terminal_pct"]:.1f}%' if r else "BLOQUEADO (FCF no positivo)."),small))
        story.append(para("RIESGO: "+company["notes"]["risks"],small))
        story.append(para("CATALIZADORES: "+company["notes"]["catalysts"],small))
        story.append(para("PREGUNTA CRÍTICA PARA JON: "+company["notes"]["question"],small))
        story.append(para("NO EMITIR COMPRAR/MANTENER/VENDER: FCFE/FCFF, tipos, deuda, sectores y márgenes de seguridad no certificados.",small))
        if ticker!=TICKERS[-1]:story.append(PageBreak())
    doc=SimpleDocTemplate(str(path),pagesize=(210*mm,297*mm),leftMargin=17*mm,rightMargin=17*mm,topMargin=16*mm,bottomMargin=15*mm,
                          title="A.FUNDAMENTAL - Piloto de revisión para Jon",author="A.FUNDAMENTAL")
    doc.build(story)


def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--db",type=Path,required=True)
    ap.add_argument("--audit",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--prices",type=Path,default=ROOT/"data/pilot_price_reference_2026-10-20.json")
    a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    data=pack(a.db,a.audit,a.prices)
    (a.out/"jon_review.json").write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    (a.out/"jon_review.html").write_text(render_html(data,ROOT/"app/jon_review_template.html"),encoding="utf-8")
    render_pdf(data,a.out/"jon_review.pdf")
    for ticker,d in data["companies"].items():
        print(json.dumps({"ticker":ticker,"fy_years":len(d["annual"]),
            "quarter_rows":len(d["quarters"]),"ttm":{k:(v["value"],v["status"]) for k,v in d["ttm"].items() if k in ("revenue_ttm","fcf_ttm","eps_ttm")},
            "price_usd":d["price"]["price_usd"],"shares":d["price"]["shares"],
            "pe_gaap_ttm_proxy":d["pe_gaap_ttm_proxy"],
            "rollforward":d["ttm_audit"]["status"]},ensure_ascii=False))
    return 0


if __name__=="__main__":sys.exit(main())
