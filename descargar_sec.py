"""Archivo histórico público de SEC EDGAR. Piloto: NKE y NU.

Sólo descarga información financiera oficial, nunca datos privados de cartera.
El User-Agent identificable se configura como secreto SEC_USER_AGENT de GitHub.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "publico" / "sec"
COMPANIES = {"NKE": "0000320187", "NU": "0001691493"}
AGENT = os.environ.get("SEC_USER_AGENT", "").strip()
if "@" not in AGENT or len(AGENT) < 12:
    raise SystemExit("Falta SEC_USER_AGENT. Añade el secreto GitHub con nombre del agente y un email real de contacto.")


def retrieve(url: str, ticker: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": AGENT, "Accept": "application/json",
                      "Accept-Encoding": "identity"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                if response.status != 200:
                    raise RuntimeError(f"{ticker}: HTTP {response.status} en {url}")
                raw = response.read()
                decoded = json.loads(raw)
                if not isinstance(decoded, dict):
                    raise ValueError(f"{ticker}: contenido SEC inesperado")
                time.sleep(0.8)
                return raw
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                raise RuntimeError(
                    f"{ticker}: SEC HTTP {exc.code}. Acceso no validado desde GitHub; "
                    "no eludir restricciones ni rellenar con datos no oficiales."
                ) from exc
            if exc.code not in (500, 502, 503, 504) or attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{ticker}: no fue posible consultar SEC")


def save_gzip(path: Path, raw: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    if path.exists() and path.read_bytes() == packed:
        return False
    path.write_bytes(packed)
    return True


def main() -> None:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {"schema": "SEC_EDGAR_ARCHIVE_V1",
                "generated_at_utc": timestamp, "companies": {}}
    for ticker, cik in COMPANIES.items():
        base = OUT / f"CIK{cik}"
        url_sub = f"https://data.sec.gov/submissions/CIK{cik}.json"
        url_facts = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        print(f"SEC: solicitando {ticker}, CIK {cik}", flush=True)
        sub = retrieve(url_sub, ticker)
        facts = retrieve(url_facts, ticker)
        sub_obj, facts_obj = json.loads(sub), json.loads(facts)
        if not sub_obj.get("filings") or not facts_obj.get("facts"):
            raise ValueError(f"{ticker}: respuesta no contiene filings/facts esperados")
        changed_sub = save_gzip(base / "submissions.json.gz", sub)
        changed_facts = save_gzip(base / "companyfacts.json.gz", facts)
        manifest["companies"][ticker] = {
            "cik": cik,
            "source_submissions": url_sub,
            "source_companyfacts": url_facts,
            "sha256_submissions": hashlib.sha256(sub).hexdigest(),
            "sha256_companyfacts": hashlib.sha256(facts).hexdigest(),
            "changed": bool(changed_sub or changed_facts),
            "reported_taxonomies": sorted(facts_obj.get("facts", {}).keys()),
        }
        print(
            f"{ticker} OK: submissions {len(sub)} bytes, "
            f"companyfacts {len(facts)} bytes", flush=True
        )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"ÉXITO: dos compañías descargadas de SEC {timestamp}", flush=True)


if __name__ == "__main__":
    main()
