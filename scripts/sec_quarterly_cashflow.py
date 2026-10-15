"""CFO/CapEx quarter isolation from SEC YTD 10-Q facts, conservative and traceable.

For Q2/Q3 SEC cash flow is commonly 6M/9M YTD. Require the same
taxonomy, accounting concept, unit USD and fiscal start for both YTD
observations. Older observation must have been publicly filed no later
than the target report. Never guess Q4 or mix unrelated definitions.
"""
from datetime import date
from math import isfinite

Q_FORMS = {"10-Q", "10-Q/A"}

def _days(a, b):
    try:
        return (date.fromisoformat(b) - date.fromisoformat(a)).days
    except (TypeError, ValueError):
        return -1

def isolate_ytd_flow(facts, preferred_tags, filing, flow_name):
    if filing.get("kind") != "Q" or flow_name not in ("cfo", "capex"):
        return None, None
    end = filing.get("end")
    filed = filing.get("filed", "")
    acc = filing.get("acc")
    for taxonomy, tag in preferred_tags:
        unit_values = facts.get(taxonomy, {}).get(tag, {}).get("units", {}).get("USD", [])
        current = [
            v for v in unit_values
            if v.get("accn") == acc and v.get("form") == filing.get("form")
            and v.get("end") == end and v.get("start")
            and v.get("val") is not None and
            140 <= _days(v["start"], end) <= 320
        ]
        if not current:
            continue
        starts = {v["start"] for v in current}
        if len(starts) != 1 or len({v["val"] for v in current}) != 1:
            # Contradictory source concepts from the same filing: fail closed.
            return None, None
        cur = current[0]
        cur_d = _days(cur["start"], end)
        if 140 <= cur_d <= 220:
            low, high, label = 65, 115, "Q2"
        elif 225 <= cur_d <= 320:
            low, high, label = 140, 220, "Q3"
        else:
            return None, None
        prior = [
            v for v in unit_values
            if v.get("val") is not None and v.get("start") == cur["start"]
            and v.get("form") in Q_FORMS and v.get("end") and
            low <= _days(v["start"], v["end"]) <= high
            and 65 <= _days(v["end"], end) <= 115
            and v.get("filed") and v["filed"] <= filed
            and v.get("accn")
        ]
        if not prior:
            continue
        nearest_end = max(v["end"] for v in prior)
        latest = max(v["filed"] for v in prior if v["end"] == nearest_end)
        selected = [v for v in prior if v["end"] == nearest_end and v["filed"] == latest]
        if len({v["val"] for v in selected}) != 1:
            return None, None
        prev = selected[0]
        result = cur["val"] - prev["val"]
        if not isinstance(result, (int,float)) or not isfinite(result):
            return None, None
        if flow_name == "capex" and result < 0:
            return None, None
        source = {
            "derived_from": "SAME_TAG_YTD_MINUS_PREVIOUS_YTD",
            "fiscal_quarter": label,
            "taxonomy": taxonomy,
            "tag": tag,
            "start": cur["start"],
            "end": end,
            "current": {"accn": acc, "end": end, "filed": filed, "val": cur["val"]},
            "previous": {
                "accn": prev["accn"], "end": prev["end"],
                "filed": prev["filed"], "val": prev["val"]
            }
        }
        return result, source
    return None, None
