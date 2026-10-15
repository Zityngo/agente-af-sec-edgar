"""Controles de calidad. Un dato descargado NO está validado: aquí se decide qué se bloquea."""
from __future__ import annotations
import json
from datetime import date
from .metrics import CAPEX_TAG_WHITELIST, EBIT_OK_METHOD, last4_quarters

WARN_PCT, BLOCK_PCT = 0.005, 0.02       # umbrales PROVISIONALES de conciliación trimestres vs FY
FLOWS = ("revenue","operating_income","net_income","cfo","capex")
STALE_DAYS = 200

def run_checks(con, cik, as_of=None):
    as_of = as_of or date.today().isoformat(); out = []
    def add(cid, sev, ref, detail): out.append((cik, cid, sev, ref, detail))
    P = [dict(r) for r in con.execute("SELECT * FROM periods WHERE cik=? ORDER BY period_end", (cik,))]
    comp = con.execute("SELECT * FROM companies WHERE cik=?", (cik,)).fetchone()
    fy = {p["fiscal_year"]: p for p in P if p["period_type"] == "FY"}
    qs = [p for p in P if p["period_type"] != "FY"]
    for y, p in fy.items():
        if p["operating_income"] is not None and p["operating_income_method"] != EBIT_OK_METHOD and not comp["is_financial"]:
            add("ebit_not_reported", "BLOCK", f"FY{y}", f"método={p['operating_income_method']}: EBIT/ROIC/EV-EBITDA bloqueados")
        try: tag = json.loads(p["sources_json"] or "{}").get("capex", {}).get("tag")
        except json.JSONDecodeError: tag = None
        if tag and tag not in CAPEX_TAG_WHITELIST:
            add("capex_tag_review", "WARN", f"FY{y}", f"capex usa {tag}: verificar que es adquisición de inmovilizado, no obra en curso/otros")
        if p["capex"] is not None and p["capex"] < 0: add("capex_negative", "BLOCK", f"FY{y}", "capex negativo")
        for k in ("revenue","assets"):
            if p[k] == 0: add("zero_instead_of_null", "WARN", f"FY{y}", f"{k}=0: ¿dato ausente tratado como 0?")
    ys = sorted(fy)
    for a, b in zip(ys, ys[1:]):
        if b != a + 1: add("fy_gap", "WARN", f"FY{a}-FY{b}", "ejercicios no contiguos: crecimiento/medias no calculados")
    for y in ys:
        q = {p["period_type"]: p for p in qs if p["fiscal_year"] == y}
        if not all(k in q for k in ("Q1","Q2","Q3","Q4")): continue
        for k in FLOWS:
            vals = [q[t][k] for t in ("Q1","Q2","Q3","Q4")]
            if any(v is None for v in vals) or fy[y][k] in (None, 0): continue
            d = abs(sum(vals) - fy[y][k]) / abs(fy[y][k])
            if d > BLOCK_PCT: add(f"recon_{k}", "BLOCK", f"FY{y}", f"suma trimestres difiere {d:.2%} del FY")
            elif d > WARN_PCT: add(f"recon_{k}", "WARN", f"FY{y}", f"suma trimestres difiere {d:.2%} del FY")
    if P:
        last = max(p["period_end"] for p in P)
        age = (date.fromisoformat(as_of) - date.fromisoformat(last)).days
        if age > STALE_DAYS: add("stale_data", "WARN", last, f"último cierre hace {age} días: ¿hay 10-Q/10-K nuevo?")
    if qs and last4_quarters(qs) is None: add("ttm_unavailable", "INFO", "", "no hay 4 trimestres contiguos para TTM")
    m = con.execute("SELECT value FROM metrics WHERE cik=? AND scope='FY' AND metric='roic' AND value IS NOT NULL", (cik,)).fetchall()
    if any(abs(r["value"]) > 0.6 for r in m): add("roic_outlier_review", "WARN", "", "ROIC proxy >60%: revisar capital invertido/recompras/impuestos (no es necesariamente error)")
    if comp["is_financial"]: add("financial_sector", "INFO", "", "EBITDA/EV-EBITDA/deuda neta no aplican: usar ROE, P/B, BPA")
    with con:
        con.execute("DELETE FROM checks WHERE cik=? AND check_id!='ticker_cik_mismatch'", (cik,))
        con.executemany("INSERT OR REPLACE INTO checks VALUES(?,?,?,?,?)", out)
    return out
