"""Curated issuer-disclosed unusual earnings effects: warnings, not normalized EPS.

Manual pilot evidence from dated issuer releases. Never infer 'no exceptional
items' from absence in this partial catalogue and never subtract pretax amounts
from after-tax EPS without a separately reconciled calculation.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import json

SCOPE = "THREE_COMPANY_NONRECURRING_EARNINGS_PILOT_2026Q2"
BASES = {"PRETAX_INVESTMENT_GAINS_USD_MILLIONS",
         "PRETAX_OTHER_INCOME_USD_MILLIONS",
         "EPS_FAVORABLE_IMPACT_USD_PER_SHARE"}


def load_events(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if obj.get("schema_version") != 1 or obj.get("scope") != SCOPE:
        raise ValueError("Catálogo de eventos fuera del piloto")
    events = obj.get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("Catálogo de eventos vacío")
    keys = set()
    for e in events:
        required = ("ticker", "period_type", "period_end", "basis", "amount", "source_url", "description")
        if any(k not in e for k in required):
            raise ValueError("Evento sin metadatos suficientes")
        key = (e["ticker"], e["period_type"], e["period_end"], e["basis"])
        if key in keys or e["ticker"] not in ("AAPL", "TSLA", "AMZN"):
            raise ValueError("Evento duplicado o emisor fuera del piloto")
        keys.add(key)
        if e["basis"] not in BASES or e["period_type"] not in ("Q1", "Q2", "Q3", "Q4"):
            raise ValueError("Unidad o trimestre no admitido")
        try:
            date.fromisoformat(e["period_end"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Fecha inválida") from exc
        if (not isinstance(e["amount"], (int, float)) or isinstance(e["amount"], bool)
            or e["amount"] <= 0 or not str(e["source_url"]).startswith("https://")
            or not str(e["description"]).strip()):
            raise ValueError("Importe, fuente o descripción inválidos")
    return events


def audit_window(ticker, quarter_ends, events):
    """Flag dated events inside a four-quarter window, without changing GAAP EPS."""
    ends = list(quarter_ends)
    if len(ends) != 4 or len(set(ends)) != 4:
        return {"status": "INSUFFICIENT_QUARTERS", "events": [],
                "reason": "Cuatro trimestres distintos requeridos"}
    found = [dict(e) for e in events if e["ticker"] == ticker and e["period_end"] in ends]
    return {"status": "REVIEW_NONRECURRING" if found else "NOT_FULLY_SCREENED",
            "events": found,
            "reason": ("Efectos singulares divulgados; no extrapolar BPA GAAP como recurrente"
                       if found else "Sin alertas en catálogo parcial; NO acredita ausencia de extraordinarios"),
            "adjusted_eps": None,
            "adjusted_eps_status": "BLOCKED_NO_TAX_SHARE_RECONCILIATION"}
