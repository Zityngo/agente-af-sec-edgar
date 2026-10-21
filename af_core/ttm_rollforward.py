"""Independent TTM roll-forward QA using SEC primary XBRL cumulative facts.

For a latest fiscal Q1/Q2/Q3, compare the motor's four quarterly values with
FY(previous year) + current YTD - prior-year same-quarter YTD.
This is an arithmetic consistency gate, NOT confirmation of economic
sustainability, revised segments, cash-flow classification, or earnings quality.
All three anchors must use identical SEC us-gaap tags and original filing
accessions, date spans, currency, and expected forms.
"""
from __future__ import annotations

from datetime import date
import math

FLOW_TAGS = {
    "operating_income": ("OperatingIncomeLoss",),
    "cfo": ("NetCashProvidedByUsedInOperatingActivities",),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment",
              "PaymentsToAcquireProductiveAssets"),
}
RANGES = {"FY": (320, 390), "Q1": (60, 115),
          "Q2": (135, 225), "Q3": (215, 325)}
METRICS = {"operating_income": "ebit_ttm", "cfo": "cfo_ttm",
           "capex": "capex_ttm"}


def _span(row):
    try:
        return (date.fromisoformat(row["end"]) -
                date.fromisoformat(row["start"])).days
    except (KeyError, TypeError, ValueError):
        return -1


def _proof(facts, tag, point, form):
    end = point.get("period_end")
    accession = point.get("accession")
    unit = "USD"
    span = RANGES.get(form)
    accepted_forms = {"10-K", "10-K/A"} if form == "FY" else {"10-Q", "10-Q/A"}
    observations = (facts.get("facts", {}).get("us-gaap", {})
                    .get(tag, {}).get("units", {}).get(unit, []))
    candidates = [x for x in observations
                  if x.get("end") == end
                  and x.get("accn") == accession
                  and x.get("form") in accepted_forms
                  and span is not None and span[0] <= _span(x) <= span[1]
                  and isinstance(x.get("val"), (int, float))
                  and not isinstance(x.get("val"), bool)
                  and math.isfinite(x["val"])]
    if not candidates:
        return None
    # Filing identity is exact; prefer its most recently filed duplicate fact,
    # and retain the exact original start/end for audit.
    x = sorted(candidates, key=lambda x: (x.get("filed") or "", x["start"]))[-1]
    return {"value": x["val"], "tag": tag, "unit": unit,
            "start": x["start"], "end": x["end"],
            "form": x["form"], "accession": x["accn"],
            "filed": x.get("filed")}


def audit_ttm(con, cik, companyfacts):
    quarters = [dict(r) for r in con.execute(
        "SELECT * FROM periods WHERE cik=? AND period_type IN ('Q1','Q2','Q3','Q4') "
        "ORDER BY period_end DESC LIMIT 4", (cik,)).fetchall()][::-1]
    result = {"status": "BLOCKED", "period_end": quarters[-1]["period_end"] if quarters else None,
              "method": "FY anterior + YTD actual - YTD previo",
              "metrics": {}, "limitations": "Conciliación aritmética SEC, no certificación de calidad económica"}
    if len(quarters) != 4:
        result["reason"] = "Faltan cuatro trimestres"
        return result
    recent = quarters[-1]
    qtype = recent["period_type"]
    fy = recent["fiscal_year"]
    if qtype not in ("Q1", "Q2", "Q3"):
        result["reason"] = "Sin período acumulado intermedio para cierre Q4"
        return result
    # Calendar correctness: not just four arbitrarily adjacent period ends.
    types = [q["period_type"] for q in quarters]
    expected_types = {"Q1":["Q2","Q3","Q4","Q1"],
                      "Q2":["Q3","Q4","Q1","Q2"],
                      "Q3":["Q4","Q1","Q2","Q3"]}[qtype]
    if types != expected_types or any(
        not 70 <= (date.fromisoformat(b["period_end"]) -
                   date.fromisoformat(a["period_end"])).days <= 112
        for a,b in zip(quarters, quarters[1:])):
        result["reason"] = "Cuatro trimestres no consecutivos o fuera de orden fiscal"
        return result
    prior_ytd = next((x for x in con.execute(
        "SELECT * FROM periods WHERE cik=? AND fiscal_year=? AND period_type=?",
        (cik, fy - 1, qtype)).fetchall()), None)
    prior_fy = con.execute(
        "SELECT * FROM periods WHERE cik=? AND fiscal_year=? AND period_type='FY'",
        (cik,fy-1)).fetchone()
    if prior_fy is None or prior_ytd is None:
        result["reason"] = "Falta FY anterior o YTD comparable anterior"
        return result
    anchors = {"fy": dict(prior_fy), "current_ytd": recent,
               "prior_ytd": dict(prior_ytd)}
    if (anchors["fy"]["currency"] != "USD"
        or anchors["current_ytd"]["currency"] != "USD"
        or anchors["prior_ytd"]["currency"] != "USD"):
        result["reason"] = "Unidades o monedas no homogéneas"
        return result

    for field, name in METRICS.items():
        found = None
        for tag in FLOW_TAGS[field]:
            sources = {role: _proof(companyfacts, tag, p,
                                    "FY" if role == "fy" else qtype)
                       for role,p in anchors.items()}
            if all(sources.values()):
                found = sources
                break
        db = con.execute(
            "SELECT value,status,reason FROM metrics WHERE cik=? AND scope='TTM' "
            "AND metric=? AND period_end=?", (cik,name,recent["period_end"])).fetchone()
        metric = {"engine_value": db["value"] if db else None,
                  "engine_status": db["status"] if db else "NULL",
                  "engine_reason": db["reason"] if db else "Sin métrica TTM"}
        if found is None:
            metric.update(status="BLOCKED", reason="No hay tres anclajes XBRL con mismo tag, "
                          "USD, duración, formularios y accessions originales", reference=None)
        elif db is None or db["value"] is None or db["status"] not in ("OK","PROXY"):
            metric.update(status="BLOCKED", reason="Métrica del motor bloqueada o ausente",
                          reference=None, sources=found)
        else:
            ref = (found["fy"]["value"] + found["current_ytd"]["value"]
                   - found["prior_ytd"]["value"])
            delta = db["value"] - ref
            # 1 USD absolute tolerance; SEC facts are USD, not financial report millions.
            ok = abs(delta) <= max(1.0, abs(ref) * 1e-10)
            metric.update(status="MATCH" if ok else "DIVERGENCE", reference=ref,
                          difference=delta, sources=found,
                          reason=("Igualdad aritmética, sin certificar recurrencia"
                                  if ok else "TTM no reconcilia con FY+YTD-YTD SEC"))
        result["metrics"][name] = metric

    c, x = result["metrics"]["cfo_ttm"], result["metrics"]["capex_ttm"]
    fcf = con.execute(
        "SELECT value,status,reason FROM metrics WHERE cik=? AND scope='TTM' "
        "AND metric='fcf_ttm' AND period_end=?", (cik,recent["period_end"])).fetchone()
    f = {"engine_value": fcf["value"] if fcf else None,
         "engine_status": fcf["status"] if fcf else "NULL"}
    if (c["status"] == "MATCH" and x["status"] == "MATCH"
        and fcf and fcf["value"] is not None
        and fcf["status"] in ("OK","PROXY")):
        ref = c["reference"] - x["reference"]
        delta = fcf["value"] - ref
        match = abs(delta) <= max(1.0, abs(ref) * 1e-10)
        f.update(status="MATCH" if match else "DIVERGENCE",
                 reference=ref, difference=delta,
                 reason="CFO bruto menos CapEx bruto; no es FCFF")
    else:
        f.update(status="BLOCKED", reason="No se puede conciliar FCF sin CFO y CapEx comparables",
                 reference=None)
    result["metrics"]["fcf_ttm"] = f
    statuses = [v["status"] for v in result["metrics"].values()]
    result["status"] = ("DIVERGENCE" if "DIVERGENCE" in statuses
                        else "MATCH" if all(s=="MATCH" for s in statuses)
                        else "PARTIAL_BLOCKED")
    result["reason"] = ("Cuatro métricas coinciden en el puente FY+YTD-YTD"
                        if result["status"] == "MATCH"
                        else "Revisar causas de los bloqueos o discrepancias, sin rellenar NULL")
    return result
