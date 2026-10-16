from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
from .db import connect_rw
from . import ingest, metrics, qa

def recompute(con):
    ciks = [r["cik"] for r in con.execute("SELECT cik FROM companies").fetchall()]
    for c in ciks: metrics.compute_company(con, c); qa.run_checks(con, c)
    for c in ciks: qa.run_checks(con, c)       # 2ª pasada: checks que leen métricas frescas (p.ej. ROIC)
    return len(ciks)

def load_prices(con, path, source, license_note=""):
    n = 0
    with open(path, encoding="utf-8-sig", newline="") as h:
        for r in csv.DictReader(h):
            con.execute("INSERT OR REPLACE INTO prices VALUES(?,?,?,?,?,?,?)",
                        (r["ticker"].upper(), r["date"], float(r["close"]), float(r["shares"]) if r.get("shares") else None,
                         r.get("currency") or "USD", source, license_note)); n += 1
    con.commit(); return n

def main(argv=None):
    ap = argparse.ArgumentParser(prog="af_core"); sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--db", default="data/af.db"); b.add_argument("--annual", required=True)
    b.add_argument("--quarterly", required=True); b.add_argument("--universe")
    c = sub.add_parser("recompute"); c.add_argument("--db", default="data/af.db")
    p = sub.add_parser("prices"); p.add_argument("--db", default="data/af.db"); p.add_argument("--csv", required=True)
    p.add_argument("--source", required=True); p.add_argument("--license-note", default="")
    k = sub.add_parser("check"); k.add_argument("--db", default="data/af.db"); k.add_argument("--ticker", required=True)
    r = sub.add_parser("rollback"); r.add_argument("--db", default="data/af.db"); r.add_argument("--run-id", required=True)
    s = sub.add_parser("serve"); s.add_argument("--db", default="data/af.db"); s.add_argument("--port", type=int, default=8000)
    s.add_argument("--web", default=str(Path(__file__).resolve().parents[1] / "app"))
    a = ap.parse_args(argv)
    if a.cmd == "serve":
        from .api import serve; print(f"http://127.0.0.1:{a.port}"); serve(a.db, a.web, port=a.port); return 0
    con = connect_rw(a.db)
    if a.cmd == "build":
        run, n = ingest.ingest_csvs(con, a.annual, a.quarterly, a.universe); print(f"run_id={run} filas={n} empresas={recompute(con)}")
    elif a.cmd == "recompute": print(f"empresas={recompute(con)}")
    elif a.cmd == "prices": print(f"precios={load_prices(con, a.csv, a.source, a.license_note)}"); recompute(con)
    elif a.cmd == "rollback": ingest.rollback_run(con, a.run_id); print(f"rollback {a.run_id}; empresas={recompute(con)}")
    elif a.cmd == "check":
        for row in con.execute("""SELECT c.ticker,k.check_id,k.severity,k.period_ref,k.detail FROM checks k JOIN companies c ON c.cik=k.cik
                                  WHERE c.ticker=? ORDER BY k.severity""", (a.ticker.upper(),)): print(tuple(row))
    return 0
if __name__ == "__main__": sys.exit(main())
