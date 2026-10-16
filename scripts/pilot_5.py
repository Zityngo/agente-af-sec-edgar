#!/usr/bin/env python3
"""Piloto de 5 emisores: SEC companyfacts -> normalize_sp500_v2 (extractor EXISTENTE) -> af_core (SQLite) -> informe.

NO inventa datos: todo procede de data.sec.gov. NO escribe en Google Sheets. NO certifica nada: genera un informe con
avisos de calidad y una tabla para conciliar a mano con los 10-K/10-Q originales.
Requiere SEC_USER_AGENT (descriptivo, con contacto) como exige la SEC. ESTADO: no ejecutado contra la SEC real al escribirlo.
"""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
TICKERS = ["AAPL", "MSFT", "JPM", "ADP", "AEP"]
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

def fetch_json(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def resolve_ciks(tickers, ua, fetch=fetch_json):
    table = fetch(TICKERS_URL, ua)
    by = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in table.values()}
    missing = [t for t in tickers if t not in by]
    if missing: raise SystemExit("Tickers no resueltos en la SEC: " + ",".join(missing))
    return {t: by[t] for t in tickers}

def run(out, first, last, ua, fetch=fetch_json, norm=None, sleep=0.25):
    import normalize_sp500_v2 as nm0
    nm = norm or nm0
    out.mkdir(parents=True, exist_ok=True)
    ciks = resolve_ciks(TICKERS, ua, fetch)
    ann_rows, q_rows, errors = [], [], []
    for tk, cik in ciks.items():
        try:
            d = fetch(FACTS_URL.format(cik=cik), ua); time.sleep(sleep)
            if str(d.get("cik", "")).zfill(10) != cik: raise ValueError("CIK de la fuente no coincide")
            (out / f"companyfacts_{tk}.json").write_text(json.dumps(d), encoding="utf-8")
            f = d.get("facts", {}).get("us-gaap", {}); nm._CACHE.clear()
            ann = nm.annual(f, cik, d.get("entityName", ""), tk, first, last)
            ann_rows += ann[-5:]; q_rows += nm.quarterly(f, cik, d.get("entityName", ""), tk, ann, first, last)[-21:]
        except Exception as e:
            errors.append({"ticker": tk, "cik": cik, "error": repr(e)})
    nm.write_csv(out / "pilot_annual.csv", ann_rows); nm.write_csv(out / "pilot_quarterly.csv", q_rows)
    from af_core.db import connect_rw
    from af_core import ingest
    from af_core.cli import recompute
    dbp = out / "pilot.db"
    if dbp.exists(): dbp.unlink()
    con = connect_rw(dbp)
    uni = ROOT / "universo_sp500.csv"   # sector -> NA_SECTOR para financieras; columnas no verificadas (si faltan, sector vacío)
    ingest.ingest_csvs(con, str(out / "pilot_annual.csv"), str(out / "pilot_quarterly.csv"), str(uni) if uni.exists() else None, source="pilot_5")
    recompute(con)
    write_report(con, out, errors)
    return con, errors

def write_report(con, out, errors):
    L = ["# Informe del piloto (5 emisores)", "",
         "Estado: **borrador automático, NADA está certificado**. Concilia cada cifra con el 10-K/10-Q original antes de darla por válida.", ""]
    if errors: L += ["## Errores de descarga/extracción", *[f"- {e['ticker']} ({e['cik']}): {e['error']}" for e in errors], ""]
    for c in con.execute("SELECT * FROM companies ORDER BY ticker").fetchall():
        L += [f"## {c['ticker']} · {c['name']} (CIK {c['cik']})", ""]
        n = con.execute("SELECT COUNT(*) n FROM periods WHERE cik=? AND period_type='FY'", (c["cik"],)).fetchone()["n"]
        m = con.execute("SELECT COUNT(*) n FROM periods WHERE cik=? AND period_type!='FY'", (c["cik"],)).fetchone()["n"]
        L += [f"Filas cargadas: {n} FY, {m} trimestrales.", "", "### Avisos de calidad"]
        ck = con.execute("SELECT severity,check_id,period_ref,detail FROM checks WHERE cik=? ORDER BY severity,check_id", (c["cik"],)).fetchall()
        L += [f"- **{k['severity']}** {k['check_id']} {k['period_ref']}: {k['detail']}" for k in ck] or ["- (sin avisos)"]
        L += ["", "### TTM (estado de cada métrica)", "", "| métrica | valor | estado | motivo |", "|---|---|---|---|"]
        for r in con.execute("SELECT metric,value,status,reason FROM metrics WHERE cik=? AND scope='TTM' ORDER BY metric", (c["cik"],)):
            v = r["value"]; vs = "NULL" if v is None else (f"{v:,.0f}" if abs(v) > 1000 else f"{v:.4g}")
            L.append(f"| {r['metric']} | {vs} | {r['status']} | {r['reason'] or ''} |")
        L += ["", "### Último ejercicio: cifras a conciliar a mano (USD)", "",
              "| FY | cierre | accession | ingresos | EBIT (método) | resultado neto | CFO | CapEx |", "|---|---|---|---|---|---|---|---|"]
        for p in con.execute("SELECT * FROM periods WHERE cik=? AND period_type='FY' ORDER BY fiscal_year DESC LIMIT 2", (c["cik"],)):
            g = lambda k: "NULL" if p[k] is None else f"{p[k]:,.0f}"
            L.append(f"| {p['fiscal_year']} | {p['period_end']} | {p['accession']} | {g('revenue')} | {g('operating_income')} ({p['operating_income_method']}) | {g('net_income')} | {g('cfo')} | {g('capex')} |")
        L.append("")
    (out / "informe_piloto.md").write_text("\n".join(L), encoding="utf-8")

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, default=Path("publico/pilot"))
    ap.add_argument("--first-year", type=int, default=2020); ap.add_argument("--last-year", type=int, default=2026)
    a = ap.parse_args(argv); ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua: raise SystemExit("Falta SEC_USER_AGENT (descriptivo, con contacto), requerido por la SEC.")
    con, errors = run(a.out, a.first_year, a.last_year, ua)
    print(json.dumps({"companies": con.execute("SELECT COUNT(*) FROM companies").fetchone()[0], "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0

if __name__ == "__main__": sys.exit(main())
