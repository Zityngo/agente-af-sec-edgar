"""Capa de consulta de SOLO LECTURA (la app solo usa esto)."""
from __future__ import annotations
import json
OK_STATES = ("OK", "PROXY")
RAW = {"revenue","gross_profit","operating_income","net_income","eps_diluted","cfo","capex","assets","equity","cash","debt_total","da","interest","tax","pretax"}

def _co(con, ticker):
    r = con.execute("SELECT * FROM companies WHERE ticker=?", (ticker.upper(),)).fetchone()
    if not r: raise KeyError(ticker)
    return r

def search(con, q, limit=20):
    like = f"%{q.strip().upper()}%"
    rows = con.execute("""SELECT c.ticker,c.name,c.sector,c.is_financial,q.blocks,q.warns,
        (SELECT MAX(period_end) FROM periods p WHERE p.cik=c.cik) AS last_period
        FROM companies c JOIN company_quality q ON q.cik=c.cik
        WHERE UPPER(c.ticker) LIKE ? OR UPPER(c.name) LIKE ? ORDER BY c.ticker LIMIT ?""", (like, like, limit)).fetchall()
    return [dict(r) for r in rows]

def company(con, ticker):
    c = _co(con, ticker)
    checks = [dict(r) for r in con.execute("SELECT check_id,severity,period_ref,detail FROM checks WHERE cik=? ORDER BY severity,check_id", (c["cik"],))]
    ttm = {r["metric"]: dict(r) for r in con.execute(
        "SELECT metric,value,status,reason,definition,period_end FROM metrics WHERE cik=? AND scope IN('TTM','VAL')", (c["cik"],))}
    return {"company": dict(c), "checks": checks, "ttm": ttm}

def series(con, ticker, metric, scope="FY"):
    c = _co(con, ticker)
    return [dict(r) for r in con.execute("""SELECT period_end,fiscal_year,value,status,reason FROM metrics
        WHERE cik=? AND scope=? AND metric=? ORDER BY period_end""", (c["cik"], scope, metric))]

def compare(con, tickers, metric, scope="FY"):
    return {t.upper(): series(con, t, metric, scope) for t in tickers}

def raw_series(con, ticker, field, ptype="FY"):
    if field not in RAW: raise ValueError("campo no permitido")
    c = _co(con, ticker); cond = "period_type='FY'" if ptype == "FY" else "period_type!='FY'"
    return [dict(r) for r in con.execute(f"SELECT period_end,fiscal_year,period_type,{field} AS value,derived FROM periods WHERE cik=? AND {cond} ORDER BY period_end", (c["cik"],))]

def screener(con, metric, min_value=None, max_value=None, sector=None, scope="TTM", include_proxy=True, limit=100):
    """Excluye NULL, BLOCKED y NA_SECTOR; PROXY va marcado."""
    states = OK_STATES if include_proxy else ("OK",)
    sql = f"""SELECT c.ticker,c.name,c.sector,m.value,m.status,m.period_end FROM metrics m
        JOIN companies c ON c.cik=m.cik WHERE m.scope=? AND m.metric=? AND m.value IS NOT NULL
        AND m.status IN ({','.join('?'*len(states))})"""
    args = [scope, metric, *states]
    if min_value is not None: sql += " AND m.value>=?"; args.append(min_value)
    if max_value is not None: sql += " AND m.value<=?"; args.append(max_value)
    if sector: sql += " AND c.sector=?"; args.append(sector)
    sql += " ORDER BY m.value DESC LIMIT ?"; args.append(limit)
    return [dict(r) for r in con.execute(sql, args)]

def provenance(con, ticker, period_type, fiscal_year):
    c = _co(con, ticker)
    r = con.execute("""SELECT period_type,fiscal_year,period_end,accession,filed,derived,sources_json,
        operating_income_method,debt_method,da_method FROM periods WHERE cik=? AND period_type=? AND fiscal_year=?""",
        (c["cik"], period_type, fiscal_year)).fetchone()
    if not r: return None
    d = dict(r); d["sources"] = json.loads(d.pop("sources_json") or "{}"); d["cik"] = c["cik"]
    d["filing_url_hint"] = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={int(c['cik'])}&type=10-&dateb=&owner=include&count=40"
    return d
