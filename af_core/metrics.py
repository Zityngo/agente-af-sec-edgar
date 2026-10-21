"""MOTOR ÚNICO de métricas. Toda fórmula vive aquí; la app y Sheets solo leen/proyectan.
Estados: OK | PROXY | BLOCKED | NA_SECTOR | NULL (dato no disponible; nunca 0)."""
from __future__ import annotations
from datetime import date
from .verification import capex_quality, attributable_quality, ebit_quality

ENGINE_VERSION = "0.1.0"
EBIT_OK_METHOD = "reported_OperatingIncomeLoss"
CAPEX_TAG_WHITELIST = {"PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"}
FIN_ONLY_NA = {"ebit","ebit_margin","ebitda","gross_margin","net_debt","debt_ebitda","interest_coverage","roic",
               "ebit_ttm","ebitda_ttm","ebit_margin_ttm","debt_ebitda_ttm","ev_ebitda","ev"}

DEFS = {
 "gross_margin":"gross_profit / revenue",
 "ebit":"OperatingIncomeLoss reportado (no derivado). Si el método no es 'reported_OperatingIncomeLoss' se bloquea.",
 "ebit_margin":"ebit / revenue", "ebitda":"ebit + da (da = D&A de la fuente; ver da_method)",
 "net_margin":"net_income / revenue", "fcf":"cfo - capex (capex en positivo; ver check capex_tag)",
 "fcf_margin":"fcf / revenue", "net_debt":"debt_total - cash",
 "debt_ebitda":"debt_total / ebitda (solo ebitda>0)", "interest_coverage":"ebit / interest (solo interest>0)",
 "roe_avg":"net_income / media(equity_t, equity_t-1)",
 "roic":"ebit*(1-t) / media(equity+debt-cash); t=tax/pretax en [0,0.6]. Proxy, no auditado.",
 "revenue_yoy":"revenue_t / revenue_t-1 - 1",
 "revenue_ttm":"suma 4 trimestres consecutivos", "ebit_ttm":"suma 4 trimestres (todos con ebit OK)",
 "ebitda_ttm":"ebit_ttm + da_ttm", "net_income_ttm":"suma 4 trimestres", "cfo_ttm":"suma 4 trimestres",
 "capex_ttm":"suma 4 trimestres", "fcf_ttm":"cfo_ttm - capex_ttm",
 "eps_ttm":"suma de 4 EPS diluidos trimestrales (NULL si falta alguno, p.ej. Q4)",
 "ebit_margin_ttm":"ebit_ttm / revenue_ttm", "fcf_margin_ttm":"fcf_ttm / revenue_ttm",
 "debt_ebitda_ttm":"debt_total(último Q) / ebitda_ttm",
 "market_cap":"close * shares (shares procede de prices.shares, fuente externa fechada)",
 "ev":"market_cap + net_debt", "per_fy":"close / eps_diluted último FY (eps>0)",
 "per_ttm":"close / eps_ttm (eps>0)", "fcf_yield":"fcf_ttm / market_cap", "ev_ebitda":"ev / ebitda_ttm (ebitda>0)",
}

class R:
    __slots__ = ("v","s","why")
    def __init__(s, v=None, st="NULL", why=""): s.v, s.s, s.why = v, st, why

def _div(n, d, nname, dname="revenue", status="OK"):
    miss = [x for x, v in ((nname, n), (dname, d)) if v is None]
    if miss: return R(None, "NULL", "falta " + ",".join(miss))
    if d == 0: return R(None, "NULL", "denominador 0")
    return R(n / d, status)

def _ebit(p):
    status,why=ebit_quality(p)
    if status in ("BLOCKED","NULL"): return R(None,status,why)
    return R(p["operating_income"],status)

def _fcf(p):
    miss = [k for k in ("cfo","capex") if p[k] is None]
    if miss: return R(None, "NULL", "falta " + ",".join(miss))
    status,why=capex_quality(p)
    if status=="BLOCKED": return R(None,status,why)
    return R(p["cfo"]-p["capex"],status,why)

def period_metrics(p, prev_fy=None):
    out = {}
    out["gross_margin"] = _div(p["gross_profit"], p["revenue"], "gross_profit")
    e = _ebit(p); out["ebit"] = e
    out["ebit_margin"] = R(None, e.s, e.why) if e.v is None else _div(e.v, p["revenue"], "ebit",status=e.s)
    if e.v is None: out["ebitda"] = R(None, e.s, e.why)
    elif p["da"] is None: out["ebitda"] = R(None, "NULL", "falta da")
    else: out["ebitda"] = R(e.v + p["da"], "PROXY" if e.s=="PROXY" or (p["da_method"] or "").startswith(("depreciation_only","unavailable")) else "OK")
    ni_status,ni_why=attributable_quality(p)
    out["net_margin"] = R(None,ni_status,ni_why) if ni_status in ("BLOCKED","NULL") else _div(p["net_income"],p["revenue"],"net_income",status=ni_status)
    f = _fcf(p); out["fcf"] = f
    out["fcf_margin"] = R(None, f.s, f.why) if f.v is None else _div(f.v, p["revenue"], "fcf", status=f.s)
    if p["debt_total"] is None or p["cash"] is None: out["net_debt"] = R(None, "NULL", "falta debt_total/cash")
    else: out["net_debt"] = R(p["debt_total"] - p["cash"], "PROXY" if p["debt_method"] and "proxy" in p["debt_method"] else "OK")
    if p["period_type"] == "FY":
        eb = out["ebitda"]
        out["debt_ebitda"] = R(None, eb.s, eb.why) if eb.v is None else (R(None,"NULL","ebitda<=0 o falta deuda") if eb.v <= 0 or p["debt_total"] is None else R(p["debt_total"]/eb.v, eb.s))
        out["interest_coverage"] = R(None, e.s, e.why) if e.v is None else (R(None,"NULL","interest<=0 o ausente") if not (p["interest"] or 0) > 0 else R(e.v/p["interest"], "OK"))
        out["roe_avg"] = R(None, "NULL", "sin FY previo contiguo")
        out["roic"] = R(None, "NULL", "sin FY previo contiguo")
        out["revenue_yoy"] = R(None, "NULL", "sin FY previo contiguo")
        if prev_fy is not None and prev_fy["fiscal_year"] == p["fiscal_year"] - 1:
            if p["net_income"] is not None and p["equity"] is not None and prev_fy["equity"] is not None:
                avg = (p["equity"] + prev_fy["equity"]) / 2
                out["roe_avg"] = R(p["net_income"]/avg, "OK") if avg > 0 else R(None, "NULL", "patrimonio medio <=0")
            else: out["roe_avg"] = R(None, "NULL", "falta net_income/equity")
            if p["revenue"] is not None and prev_fy["revenue"]:
                out["revenue_yoy"] = R(p["revenue"]/prev_fy["revenue"]-1, "OK")
            def ic(x): return None if None in (x["equity"], x["debt_total"], x["cash"]) else x["equity"]+x["debt_total"]-x["cash"]
            if e.v is None: out["roic"] = R(None, e.s, e.why)
            elif None in (p["tax"], p["pretax"]) or not p["pretax"] or p["pretax"] <= 0: out["roic"] = R(None, "NULL", "falta tax/pretax>0")
            else:
                t = p["tax"] / p["pretax"]; a, b = ic(p), ic(prev_fy)
                if not 0 <= t <= 0.6: out["roic"] = R(None, "BLOCKED", f"tasa efectiva fuera de rango ({t:.2f})")
                elif a is None or b is None or a + b <= 0: out["roic"] = R(None, "NULL", "capital invertido no disponible")
                else: out["roic"] = R(e.v*(1-t)/((a+b)/2), "PROXY", "proxy: no auditado")
    return out

def _days(a, b): return (date.fromisoformat(b) - date.fromisoformat(a)).days

def last4_quarters(qrows):
    qs = sorted(qrows, key=lambda r: r["period_end"])
    if len(qs) < 4: return None
    w = qs[-4:]
    for a, b in zip(w, w[1:]):
        if not 70 <= _days(a["period_end"], b["period_end"]) <= 112: return None
    return w

def ttm_metrics(w):
    out = {}
    def tsum(key):
        vals = [r[key] for r in w]
        return None if any(v is None for v in vals) else sum(vals)
    rev, ni, cfo, cap, da = (tsum(k) for k in ("revenue","net_income","cfo","capex","da"))
    for name, v in (("revenue_ttm",rev),("net_income_ttm",ni),("cfo_ttm",cfo),("capex_ttm",cap)):
        out[name] = R(v, "OK") if v is not None else R(None,"NULL",f"falta {name[:-4]} en algún trimestre")
    # SEC cash-flow quarters commonly come from YTD deltas, not direct 3M figures.
    # Sum reconciles via FY+YTD-YTD; keep derivation quality visible.
    import json
    def cfo_is_derived(q):
        try:
            raw=json.loads(q.get("sources_json") or "{}")
            entry=raw.get("cfo")
            return isinstance(entry,dict) and entry.get("derived_from") in ("FY_minus_9M","ytd_delta")
        except (ValueError,TypeError,AttributeError):
            return True
    if cfo is not None and any(cfo_is_derived(q) for q in w):
        out["cfo_ttm"]=R(cfo,"PROXY","CFO trimestral reconstruido de acumulados YTD/FY, contrastar puente SEC")
    capchecks=[capex_quality(q) for q in w]
    if cap is not None:
        if any(status=="BLOCKED" for status,_ in capchecks):
            out["capex_ttm"]=R(None,"BLOCKED","CapEx trimestral con etiqueta/origen no aprobado")
        elif any(status=="PROXY" for status,_ in capchecks):
            out["capex_ttm"]=R(cap,"PROXY","CapEx trimestral por diferencias YTD/FY")
    ni_checks=[attributable_quality(q) for q in w]
    if any(st=="BLOCKED" for st,_ in ni_checks):
        out["net_income_ttm"]=R(None,"BLOCKED","beneficio consolidado/no atribuible en trimestre")
    elif ni is not None and any(st=="PROXY" for st,_ in ni_checks):
        out["net_income_ttm"]=R(ni,"PROXY","beneficio de matriz; preferentes pendientes")
    if cfo is None or cap is None: out["fcf_ttm"] = R(None,"NULL","falta cfo/capex")
    else:
        qchecks=capchecks
        if any(st=="BLOCKED" for st,_ in qchecks):out["fcf_ttm"]=R(None,"BLOCKED","CapEx trimestral no conciliado")
        else:out["fcf_ttm"]=R(cfo-cap,"PROXY" if any(st=="PROXY" for st,_ in qchecks) or out["cfo_ttm"].s=="PROXY" else "OK","FCF bruto CFO - CapEx; alguno de los trimestres procede de YTD/FY, NO FCF ajustado corporativo")
    ebs = [_ebit(r) for r in w]; blocked = [x for x in ebs if x.s == "BLOCKED"]
    if blocked: out["ebit_ttm"] = R(None, "BLOCKED", blocked[0].why)
    elif any(x.v is None for x in ebs): out["ebit_ttm"] = R(None, "NULL", "falta ebit en algún trimestre")
    else: out["ebit_ttm"] = R(sum(x.v for x in ebs), "PROXY" if any(x.s=="PROXY" for x in ebs) else "OK", "incluye Q4 FY-9M" if any(x.s=="PROXY" for x in ebs) else "")
    et = out["ebit_ttm"]
    da_proxy = any((q.get("da_method") or "").startswith(("depreciation_only","unavailable")) for q in w)
    out["ebitda_ttm"] = (R(None, et.s, et.why) if et.v is None else
                         R(None, "NULL", "falta da en algún trimestre") if da is None else
                         R(et.v + da, "PROXY" if et.s == "PROXY" or da_proxy else "OK",
                           "D&A parcial o EBIT Q4 derivado" if da_proxy or et.s == "PROXY" else ""))
    out["ebit_margin_ttm"] = R(None, et.s, et.why) if et.v is None else _div(et.v, rev, "ebit",status=et.s)
    f = out["fcf_ttm"]; out["fcf_margin_ttm"] = R(None, f.s, f.why) if f.v is None else _div(f.v, rev, "fcf", status=f.s)
    eps = [r["eps_diluted"] for r in w]
    out["eps_ttm"] = R(sum(eps),"PROXY","EPS trimestral sumado; splits/pesos por trimestre pendientes") if all(x is not None for x in eps) else R(None,"NULL","falta EPS Q4 expresamente reportado; prohibido FY - 9M EPS")
    last = w[-1]
    if last["debt_total"] is None or last["cash"] is None: out["net_debt"] = R(None,"NULL","falta debt_total/cash")
    else: out["net_debt"] = R(last["debt_total"]-last["cash"],
                              "PROXY" if "proxy" in (last.get("debt_method") or "").lower() else "OK",
                              "Deuda financiera basada en proxy" if "proxy" in (last.get("debt_method") or "").lower() else "")
    eb = out["ebitda_ttm"]
    out["debt_ebitda_ttm"] = (R(None, eb.s, eb.why) if eb.v is None else
                              R(None, "NULL", "ebitda<=0 o falta deuda") if last["debt_total"] is None or eb.v <= 0 else
                              R(last["debt_total"]/eb.v,
                                "PROXY" if "PROXY" in (eb.s, out["net_debt"].s) else "OK",
                                "EBITDA o deuda proxy" if "PROXY" in (eb.s, out["net_debt"].s) else ""))
    return out

def valuation_metrics(price, ttm, fy_eps):
    out = {}; close = price["close"]; sh = price.get("shares")
    out["per_fy"] = R(close/fy_eps, "OK") if fy_eps and fy_eps > 0 else R(None,"NULL","EPS FY ausente o <=0")
    e = ttm.get("eps_ttm")
    if e is None:
        out["per_ttm"] = R(None, "NULL", "EPS TTM no disponible")
    elif e.s not in ("OK", "PROXY"):
        status = e.s if e.s in ("NULL", "BLOCKED", "NA_SECTOR") else "BLOCKED"
        out["per_ttm"] = R(None, status, e.why or "EPS TTM sin calidad aceptable")
    elif e.v is None:
        out["per_ttm"] = R(None, "NULL", e.why or "EPS TTM no disponible")
    elif e.v <= 0:
        out["per_ttm"] = R(None, "NULL", "EPS TTM <=0")
    else:
        out["per_ttm"] = R(close/e.v, e.s, e.why)
    if not sh:
        for k in ("market_cap","ev","fcf_yield","ev_ebitda"): out[k] = R(None,"NULL","falta shares en prices")
        return out
    mc = close*sh; out["market_cap"] = R(mc,"OK")
    nd, f, eb = ttm.get("net_debt"), ttm.get("fcf_ttm"), ttm.get("ebitda_ttm")
    # No ratio is more reliable than the metric feeding it.
    def usable(r):
        return r is not None and r.v is not None and r.s in ("OK", "PROXY")
    if usable(nd):
        out["ev"] = R(mc + nd.v, nd.s, nd.why)
    else:
        out["ev"] = R(None, nd.s if nd else "NULL", nd.why if nd else "falta net_debt")
    if usable(f):
        out["fcf_yield"] = R(f.v / mc, f.s, f.why) if mc > 0 else R(None, "NULL", "market cap <=0")
    else:
        out["fcf_yield"] = R(None, f.s if f else "NULL", f.why if f else "falta fcf_ttm")
    if not usable(eb):
        out["ev_ebitda"] = R(None, eb.s if eb else "NULL", eb.why if eb else "falta ebitda_ttm")
    elif not usable(out["ev"]):
        out["ev_ebitda"] = R(None, out["ev"].s, out["ev"].why)
    elif eb.v <= 0:
        out["ev_ebitda"] = R(None, "NULL", "ebitda<=0")
    else:
        status = "PROXY" if "PROXY" in (out["ev"].s, eb.s) else "OK"
        out["ev_ebitda"] = R(out["ev"].v / eb.v, status,
                              "EV o EBITDA TTM proxy" if status == "PROXY" else "")
    return out

def compute_company(con, cik):
    comp = con.execute("SELECT * FROM companies WHERE cik=?", (cik,)).fetchone()
    is_fin = bool(comp["is_financial"]); rows = []
    def put(scope, pend, fy, name, r):
        if is_fin and name in FIN_ONLY_NA: r = R(None, "NA_SECTOR", "no aplica a financieras: usar ROE, P/B, BPA")
        rows.append((cik, scope, pend, fy, name, r.v, r.s, r.why, DEFS.get(name,""), ENGINE_VERSION))
    fys = [dict(x) for x in con.execute("SELECT * FROM periods WHERE cik=? AND period_type='FY' ORDER BY fiscal_year", (cik,))]
    prev = None
    for p in fys:
        for k, r in period_metrics(p, prev).items(): put("FY", p["period_end"], p["fiscal_year"], k, r)
        prev = p
    qs = [dict(x) for x in con.execute("SELECT * FROM periods WHERE cik=? AND period_type!='FY' ORDER BY period_end", (cik,))]
    for p in qs:
        for k, r in period_metrics(p).items():
            if k in ("ebit","ebit_margin","ebitda","net_margin","fcf","fcf_margin","gross_margin"): put(p["period_type"], p["period_end"], p["fiscal_year"], k, r)
    w = last4_quarters(qs); ttm = {}
    if w:
        ttm = ttm_metrics(w)
        for k, r in ttm.items(): put("TTM", w[-1]["period_end"], w[-1]["fiscal_year"], k, r)
    pr = con.execute("SELECT * FROM prices WHERE ticker=? ORDER BY price_date DESC LIMIT 1", (comp["ticker"],)).fetchone()
    if pr and ttm:
        fy_eps = fys[-1]["eps_diluted"] if fys else None
        for k, r in valuation_metrics(dict(pr), ttm, fy_eps).items(): put("VAL", pr["price_date"], None, k, r)
    with con:
        con.execute("DELETE FROM metrics WHERE cik=?", (cik,))
        con.executemany("INSERT INTO metrics VALUES(?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)
