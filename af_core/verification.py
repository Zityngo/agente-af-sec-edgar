"""Conservative audit rules for SEC-derived amounts.

Do not convert unavailable fields to zero. Synthetic unit fixtures lack SEC accession
and are exempt from provenance enforcement, not from semantic-tag checks.
"""
from __future__ import annotations
import json
import re

SEC_ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")
CAPEX_ALLOWED = {"PaymentsToAcquirePropertyPlantAndEquipment",
                 "PaymentsToAcquireProductiveAssets"}
NET_INCOME_COMMON = {"NetIncomeLossAvailableToCommonStockholdersBasic",
                     "NetIncomeLoss"}
CONSOLIDATED = {"ProfitLoss"}

def sec_filing(period):
    return bool(SEC_ACCESSION.fullmatch(str(period.get("accession") or "")))

def source(period, name):
    try:
        raw = json.loads(period.get("sources_json") or "{}")
    except (ValueError, TypeError):
        return None
    return raw.get(name) if isinstance(raw, dict) else None

def tags_from_evidence(entry):
    if not isinstance(entry,dict): return []
    if isinstance(entry.get("tag"),str): return [entry["tag"]]
    out = []
    for field in ("source","annual_source","nine_month_source"):
        e=entry.get(field)
        if isinstance(e,dict): out += tags_from_evidence(e)
    return out

def capex_quality(period):
    """Return (status, explanation); derived YTD and Q4 need provenance for BOTH legs."""
    val=period.get("capex")
    if val is None:return "NULL","capex no disponible"
    if val<0:return "BLOCKED","CapEx negativo: revisar signo"
    e=source(period,"capex")
    tags=tags_from_evidence(e)
    if not tags:
        return ("BLOCKED","capex SEC sin etiqueta/origen verificable") if sec_filing(period) else ("OK","dato sintetico de pruebas")
    rejected=[t for t in tags if t not in CAPEX_ALLOWED]
    if rejected:return "BLOCKED","CapEx tag no validado: "+", ".join(rejected)
    if isinstance(e,dict) and e.get("derived_from") in ("ytd_delta","ytd_Q1") and not isinstance(e.get("source"),dict):
        return "BLOCKED","Delta de CapEx no tiene fuente YTD"
    if isinstance(e,dict) and e.get("derived_from")=="FY_minus_9M":
        if not isinstance(e.get("annual_source"),dict) or not isinstance(e.get("nine_month_source"),dict):
            return "BLOCKED","CapEx Q4 requiere fuentes FY y 9M"
    return "OK","CapEx PP&E fuente SEC compatible; comparabilidad economica por verificar"

def attributable_quality(period):
    """A parent-level tag is not necessarily income available to common shareholders."""
    if period.get("net_income") is None:return "NULL","sin net_income"
    tags=tags_from_evidence(source(period,"net_income"))
    if not tags:
        return ("BLOCKED","net income SEC sin fuente atribuible") if sec_filing(period) else ("OK","sintetico")
    if any(t in CONSOLIDATED for t in tags):
        return "BLOCKED","ProfitLoss consolidado no equivale a resultado atribuible"
    if all(t in NET_INCOME_COMMON for t in tags):
        return ("OK","net income atribuido a ordinarios") if "NetIncomeLossAvailableToCommonStockholdersBasic" in tags else ("PROXY","NetIncomeLoss de matriz; comprobar preferentes")
    return "BLOCKED","tag de beneficio no conciliado: "+", ".join(tags)

def ebit_quality(period):
    val=period.get("operating_income")
    if val is None:return "NULL","sin operating_income"
    method=period.get("operating_income_method")
    e=source(period,"operating_income")
    tags=tags_from_evidence(e)
    if method=="derived_Q4_FY_minus_9M":
        good=isinstance(e,dict) and e.get("derived_from")=="FY_minus_9M" and all(
            isinstance(e.get(k),dict) and e[k].get("tag")=="OperatingIncomeLoss" and e[k].get("accession")
            for k in ("annual_source","nine_month_source"))
        if good:return "PROXY","EBIT Q4=10-K FY menos 10-Q 9M (trazable, no reportado)"
        return "BLOCKED","EBIT Q4 sin fuentes SEC FY/9M concordantes"
    if method!="reported_OperatingIncomeLoss":
        return "BLOCKED","EBIT derivado sin linea OperatingIncomeLoss"
    if sec_filing(period) and tags != ["OperatingIncomeLoss"]:
        return "BLOCKED","EBIT SEC sin etiqueta OperatingIncomeLoss"
    return "OK","EBIT reportado"
