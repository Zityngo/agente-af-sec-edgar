"""Puente temporal a BPA diluido GAAP Q4 de publicaciones oficiales.

Solo se activa si un piloto proporciona explícitamente un JSON revisado.
No hace scraping, no calcula FY EPS menos 9M EPS y no modifica el extractor SEC general.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import json


def _valid(row):
    required = ("ticker", "cik", "fiscal_year", "period_type", "period_start",
                "period_end", "metric", "value", "currency", "source_type",
                "source_url", "reviewed_on")
    if any(k not in row for k in required):
        raise ValueError("Registro Q4 incompleto")
    if row["period_type"] != "Q4" or row["metric"] != "eps_diluted_gaap":
        raise ValueError("Solo se admite BPA GAAP diluido Q4 expresamente reportado")
    if row["currency"] != "USD/share" or type(row["value"]) not in (int, float):
        raise ValueError("Unidad o BPA no válidos")
    if not -100.0 < row["value"] < 100.0:
        raise ValueError("BPA fuera del rango del registro piloto")
    if row["source_type"] not in ("ISSUER_RELEASE", "SEC_8K_EXHIBIT"):
        raise ValueError("Tipo de fuente no oficial")
    if not row["source_url"].startswith("https://"):
        raise ValueError("Fuente Q4 sin URL HTTPS")
    start, end = date.fromisoformat(row["period_start"]), date.fromisoformat(row["period_end"])
    if not 70 <= (end-start).days <= 112:
        raise ValueError("El período Q4 no tiene duración trimestral")
    if int(row["fiscal_year"]) != end.year:
        raise ValueError("Ejercicio y fin del Q4 no coinciden")
    if len(str(row["cik"])) != 10 or not str(row["cik"]).isdigit():
        raise ValueError("CIK incorrecto")
    return (str(row["cik"]), int(row["fiscal_year"]), row["period_end"])


def load_registry(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if obj.get("schema_version") != 1 or not str(obj.get("scope", "")).endswith("_PILOT_ONLY"):
        raise ValueError("Registro fuera de ámbito del piloto")
    recs = obj.get("observations")
    if not isinstance(recs, list) or not recs:
        raise ValueError("Registro sin observaciones")
    out = {}
    for r in recs:
        key = _valid(r)
        if key in out:
            raise ValueError("Registro Q4 duplicado")
        out[key] = r
    return out


def apply(qrows, registry):
    """Anotar Q4 ausente, nunca sobreescribir un EPS SEC divergente.

    Mutación únicamente en filas efímeras del piloto antes de escribir CSV/SQLite.
    """
    matched = set()
    added, corroborated = 0, 0
    for r in qrows:
        if r.get("period_type") != "Q4":
            continue
        key = (str(r["cik"]).zfill(10), int(r["fiscal_year"]), r["period_end"])
        proof = registry.get(key)
        if proof is None:
            continue
        if proof["ticker"] != r["ticker"]:
            raise ValueError("Ticker/CIK Q4 incompatibles")
        if key in matched:
            raise ValueError("Dos filas Q4 coinciden con una observación")
        matched.add(key)
        reported = float(proof["value"])
        existing = r.get("eps_diluted")
        if existing is not None and abs(float(existing)-reported) > 0.011:
            raise ValueError("BPA Q4 SEC y emisor discrepantes: " + r["ticker"])
        evidence = {
            "tag": "IssuerReportedGAAPDilutedEPS",
            "derived_from": "official_Q4_earnings_release",
            "source_type": proof["source_type"],
            "issuer_url": proof["source_url"],
            "period_start": proof["period_start"],
            "period_end": proof["period_end"],
            "reviewed_on": proof["reviewed_on"],
            "status": "PILOT_SOURCED_NOT_AUTOMATED",
        }
        if proof.get("sec_accession"):
            evidence["sec_accession"] = proof["sec_accession"]
        src = r.setdefault("sources", {})
        if existing is None:
            r["eps_diluted"] = reported
            src["eps_diluted"] = evidence
            added += 1
        else:
            src["eps_official_confirmation"] = evidence
            corroborated += 1
    missing = sorted(set(registry) - matched)
    if missing:
        raise ValueError("Sin Q4 normalizado para " + ", ".join(str(k) for k in missing))
    return {"sources_matched":len(matched),"eps_added":added,"eps_corroborated":corroborated}
