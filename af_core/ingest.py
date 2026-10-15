"""Carga idempotente de la salida de scripts/normalize_sp500_v2.py (CSV anual/trimestral).
NO re-extrae XBRL. Cada carga lleva run_id, auditoría de filas sobrescritas y rollback_run()."""
from __future__ import annotations
import csv, json, uuid
from datetime import datetime, timezone

NUM = ["revenue","gross_profit","operating_income","net_income","eps_diluted","cfo","capex",
       "assets","equity","cash","debt_total","da","interest","tax","pretax"]
TXT = ["operating_income_method","debt_method","da_method"]
FIN_HINTS = ("financial","bank","insurance","reit","real estate")

def _f(x):
    if x is None: return None
    x = str(x).strip()
    if x == "" or x.lower() in ("none","null","nan"): return None
    try: return float(x)
    except ValueError: return None

def _sector_map(path):
    if not path: return {}
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as h:
        for r in csv.DictReader(h):
            low = {k.lower().strip(): v for k, v in r.items() if k}
            t = low.get("ticker") or low.get("symbol") or low.get("simbolo") or ""
            s = low.get("sector") or low.get("gics sector") or low.get("gics_sector") or ""
            if t: out[t.strip().upper()] = s.strip()
    return out

def _is_fin(sector):
    s = (sector or "").lower()
    return int(any(h in s for h in FIN_HINTS))

def _derived(ptype, sources):
    if ptype == "Q4": return 1
    return int(any(isinstance(v, dict) and "derived_from" in v for v in sources.values()))

def ingest_csvs(con, annual_csv, quarterly_csv, universe_csv=None, run_id=None, source="normalize_sp500_v2"):
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:6]
    sectors = _sector_map(universe_csv); n = 0
    con.execute("INSERT INTO ingest_runs VALUES(?,?,?,?,?)",
                (run_id, datetime.now(timezone.utc).isoformat(timespec="seconds"), source, 0, "RUNNING"))
    try:
        for path in (annual_csv, quarterly_csv):
            if not path: continue
            with open(path, encoding="utf-8", newline="") as h:
                for r in csv.DictReader(h):
                    cik = str(r["cik"]).zfill(10); tk = (r.get("ticker") or "").upper()
                    if not tk or not r.get("period_end") or not r.get("fiscal_year"): continue
                    sec = sectors.get(tk, "")
                    prev = con.execute("SELECT ticker FROM companies WHERE cik=?", (cik,)).fetchone()
                    if prev and prev["ticker"] != tk:
                        con.execute("INSERT OR REPLACE INTO checks VALUES(?,?,?,?,?)",
                                    (cik,"ticker_cik_mismatch","BLOCK","",f"{prev['ticker']} vs {tk}"))
                    con.execute("""INSERT INTO companies(cik,ticker,name,sector,is_financial) VALUES(?,?,?,?,?)
                        ON CONFLICT(cik) DO UPDATE SET name=excluded.name,
                        sector=CASE WHEN excluded.sector!='' THEN excluded.sector ELSE sector END,
                        is_financial=CASE WHEN excluded.sector!='' THEN excluded.is_financial ELSE is_financial END""",
                        (cik, tk, r.get("entity"), sec, _is_fin(sec)))
                    try: src = json.loads(r.get("source_tags_json") or "{}")
                    except json.JSONDecodeError: src = {}
                    ptype, fy = r["period_type"], int(r["fiscal_year"])
                    vals = [_f(r.get(k)) for k in NUM] + [r.get(k) or None for k in TXT]
                    old = con.execute("SELECT * FROM periods WHERE cik=? AND period_type=? AND fiscal_year=?",
                                      (cik, ptype, fy)).fetchone()
                    if old:
                        if all(old[k] == v for k, v in zip(NUM + TXT, vals)) and old["period_end"] == r["period_end"]:
                            continue
                        con.execute("INSERT INTO periods_audit(run_id,action,cik,period_type,fiscal_year,old_row_json) VALUES(?,?,?,?,?,?)",
                                    (run_id, "UPDATE", cik, ptype, fy, json.dumps(dict(old))))
                    else:
                        con.execute("INSERT INTO periods_audit(run_id,action,cik,period_type,fiscal_year,old_row_json) VALUES(?,?,?,?,?,NULL)",
                                    (run_id, "INSERT", cik, ptype, fy))
                    cols = ["cik","period_type","fiscal_year","period_end","accession","filed","currency","derived"] + NUM + TXT + ["sources_json","run_id"]
                    row = [cik, ptype, fy, r["period_end"], r.get("filing_accession"), r.get("filing_date"),
                           r.get("currency") or "USD", _derived(ptype, src)] + vals + [json.dumps(src), run_id]
                    con.execute(f"INSERT OR REPLACE INTO periods({','.join(cols)}) VALUES({','.join('?'*len(cols))})", row)
                    n += 1
        con.execute("UPDATE ingest_runs SET rows_in=?, status='OK' WHERE run_id=?", (n, run_id)); con.commit()
    except Exception:
        con.rollback(); con.execute("UPDATE ingest_runs SET status='FAILED' WHERE run_id=?", (run_id,)); con.commit(); raise
    return run_id, n

def rollback_run(con, run_id):
    cols = [c[1] for c in con.execute("PRAGMA table_info(periods)")]
    for a in con.execute("SELECT * FROM periods_audit WHERE run_id=? ORDER BY audit_id DESC", (run_id,)).fetchall():
        con.execute("DELETE FROM periods WHERE cik=? AND period_type=? AND fiscal_year=?", (a["cik"], a["period_type"], a["fiscal_year"]))
        if a["old_row_json"]:
            o = json.loads(a["old_row_json"])
            con.execute(f"INSERT INTO periods({','.join(cols)}) VALUES({','.join('?'*len(cols))})", [o[c] for c in cols])
    con.execute("DELETE FROM periods_audit WHERE run_id=?", (run_id,))
    con.execute("UPDATE ingest_runs SET status='ROLLED_BACK' WHERE run_id=?", (run_id,)); con.commit()
