"""Auditoría de los cuatro BPA trimestrales que forman el TTM del piloto.

No modifica bases de datos; comprueba periodos, origen y coherencia. TRACEABLE
solo implica procedencia comprobable, nunca certifica BPA recurrente ni PER.
"""
from __future__ import annotations
from datetime import date
import json
import re

SEC_ACC = re.compile(r"^\d{10}-\d{2}-\d{6}$")


def _days(start, end):
    try:
        return (date.fromisoformat(end)-date.fromisoformat(start)).days
    except (TypeError, ValueError):
        return None


def audit_company(con, cik):
    rows = [dict(x) for x in con.execute(
        "SELECT period_type, fiscal_year, period_end, accession, filed, eps_diluted, sources_json "
        "FROM periods WHERE cik=? AND period_type IN ('Q1','Q2','Q3','Q4') "
        "ORDER BY period_end DESC LIMIT 4", (cik,)).fetchall()][::-1]
    status, problems, result = "PROXY", [], []
    if len(rows) != 4:
        return {"status":"BLOCKED","reason":"No hay cuatro trimestres","quarters":[],"eps_sum":None}
    for idx, r in enumerate(rows):
        try:
            sources = json.loads(r.get("sources_json") or "{}")
        except (TypeError, ValueError):
            sources = {}
        proof = sources.get("eps_diluted")
        val = r["eps_diluted"]
        qtype = r["period_type"]
        pstatus, why = "TRACEABLE", ""
        source_url, source_acc = None, None
        if val is None:
            pstatus, why = "BLOCKED", "BPA ausente"
        elif not isinstance(proof, dict):
            pstatus, why = "BLOCKED", "BPA sin procedencia"
        elif qtype == "Q4":
            source_url = proof.get("issuer_url")
            start = proof.get("period_start")
            end = proof.get("period_end")
            if (proof.get("tag") != "IssuerReportedGAAPDilutedEPS" or
                proof.get("status") != "PILOT_SOURCED_NOT_AUTOMATED" or
                proof.get("derived_from") != "official_Q4_earnings_release" or
                not isinstance(source_url,str) or not source_url.startswith("https://") or
                end != r["period_end"] or
                _days(start,end) is None or not 70 <= _days(start,end) <= 112):
                pstatus, why = "BLOCKED", "BPA Q4 sin release oficial consistente"
        else:
            source_acc = proof.get("accession")
            if (proof.get("tag") != "EarningsPerShareDiluted" or
                proof.get("form") not in ("10-Q","10-Q/A") or
                proof.get("end") != r["period_end"] or
                _days(proof.get("start"),proof.get("end")) is None or
                not 70 <= _days(proof.get("start"),proof.get("end")) <= 112 or
                not SEC_ACC.fullmatch(str(source_acc or ""))):
                pstatus, why = "BLOCKED", "BPA Q1-Q3 sin XBRL SEC trimestral compatible"
            elif r["accession"] != source_acc:
                pstatus, why = "REVIEW", "Accession del BPA no coincide con filing del período; conciliar"
        if idx > 0 and not 70 <= _days(rows[idx-1]["period_end"],r["period_end"]) <= 112:
            pstatus, why = "BLOCKED", "Trimestres no consecutivos"
        if pstatus != "TRACEABLE":
            problems.append(f"{qtype} {r['period_end']}: {why}")
        result.append({"quarter":qtype,"period_end":r["period_end"],
                       "eps":val,"provenance":pstatus,"reason":why,
                       "source_accession":source_acc,"filing_accession":r["accession"],
                       "source_url":source_url})
    if any(r["provenance"] == "BLOCKED" for r in result): status = "BLOCKED"
    elif any(r["provenance"] == "REVIEW" for r in result): status = "REVIEW"
    eps_sum = round(sum(r["eps"] for r in result), 4) if all(r["eps"] is not None for r in result) else None
    if status == "BLOCKED": eps_sum = None
    return {"status":status,"reason":"; ".join(problems),
            "quarters":result,"eps_sum":eps_sum,
            "caveat":"La suma de BPA trimestrales está sujeta a redondeos y cambios de acciones diluidas; no equivale necesariamente a BPA TTM oficial."}
