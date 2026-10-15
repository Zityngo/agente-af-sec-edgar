"""API JSON mínima (stdlib) sobre SQLite en solo lectura + servidor de la web estática."""
from __future__ import annotations
import json, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from . import query
from .db import connect_ro

def route(con, path, qs):
    g = lambda k, d=None: (qs.get(k) or [d])[0]
    if path == "/api/search": return query.search(con, g("q", ""))
    if path == "/api/company": return query.company(con, g("ticker", ""))
    if path == "/api/series": return query.series(con, g("ticker",""), g("metric",""), g("scope","FY"))
    if path == "/api/raw": return query.raw_series(con, g("ticker",""), g("field",""), g("ptype","FY"))
    if path == "/api/compare": return query.compare(con, [t for t in g("tickers","").split(",") if t][:5], g("metric",""), g("scope","FY"))
    if path == "/api/screener":
        f = lambda k: float(g(k)) if g(k) not in (None, "") else None
        return query.screener(con, g("metric",""), f("min"), f("max"), g("sector"), g("scope","TTM"))
    if path == "/api/provenance": return query.provenance(con, g("ticker",""), g("ptype","FY"), int(g("fy","0")))
    raise LookupError(path)

def make_handler(db_path, web_dir):
    web_dir = Path(web_dir)
    class H(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            b = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code); self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        def do_GET(self):
            u = urlparse(self.path)
            if u.path.startswith("/api/"):
                con = connect_ro(db_path)
                try: self._send(200, json.dumps(route(con, u.path, parse_qs(u.query)), ensure_ascii=False))
                except KeyError as e: self._send(404, json.dumps({"error": f"no existe {e}"}))
                except (LookupError, ValueError) as e: self._send(400, json.dumps({"error": str(e)}))
                finally: con.close()
                return
            f = (web_dir / ("index.html" if u.path in ("/", "") else u.path.lstrip("/"))).resolve()
            if web_dir.resolve() in f.parents and f.is_file():
                self._send(200, f.read_bytes(), mimetypes.guess_type(str(f))[0] or "text/html")
            else: self._send(404, "not found", "text/plain")
        def log_message(self, *a): pass
    return H

def make_server(db_path, web_dir, host="127.0.0.1", port=8000):
    return ThreadingHTTPServer((host, port), make_handler(db_path, web_dir))
def serve(db_path, web_dir, host="127.0.0.1", port=8000): make_server(db_path, web_dir, host, port).serve_forever()
