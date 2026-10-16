"""Explicit, traceable XBRL tag exceptions. Never choose the largest number blindly.

Evidence: SEC companyfacts/submissions raw snapshots archived 10 Oct 2026.
This module contains *selection logic*, not valuation or financial metrics.
"""
from __future__ import annotations

REVENUE_TAG_BY_CIK={
    # Wynn uses the including-assessed-taxes tag as reported consolidated revenue.
    "0001174922": ("us-gaap", "RevenueFromContractWithCustomerIncludingAssessedTax"),
    # Extra Space's contract-customer revenues are partial; 'Revenues' is consolidated.
    "0001289490": ("us-gaap", "Revenues"),
    # Interactive Brokers earns net interest in addition to contract-service revenue.
    "0001381197": ("us-gaap", "RevenuesNetOfInterestExpense"),
}


def preferred_tags(cik,metric,tags):
    """Reorder candidate list for SEC-documented CIK without dropping fallback tags."""
    preferred=REVENUE_TAG_BY_CIK.get(str(cik).zfill(10)) if metric=="revenue" else None
    if not preferred: return list(tags)
    return [preferred]+[t for t in tags if t!=preferred]


def recover_amendment(submissions,facts,filing,cik,metric_fn):
    """Use an original 10-K only if a 10-K/A lacks financial statements.

    The fallback is ALWAYS flagged for manual amendment review. It never certifies
    numbers or substitutes a restated report silently.
    """
    if filing.get("form") not in ("10-K/A", "20-F/A"):
        return filing,None
    has_rev=metric_fn(facts,"revenue",filing,cik)[0] is not None
    has_ni=metric_fn(facts,"ni",filing,cik)[0] is not None
    if has_rev and has_ni:return filing,None
    rec=submissions.get("filings",{}).get("recent",{})
    keys=("form","reportDate","filingDate","accessionNumber","primaryDocument")
    if not rec or any(k not in rec for k in keys):return filing,None
    candidates=[]
    for i,form in enumerate(rec["form"]):
        if form not in ("10-K","20-F") or rec["reportDate"][i]!=filing["end"]:
            continue
        if rec["filingDate"][i]>filing["filed"]:continue
        orig={"form":form,"filed":rec["filingDate"][i],"end":rec["reportDate"][i],
              "acc":rec["accessionNumber"][i],"doc":rec["primaryDocument"][i],"kind":"FY"}
        rev=metric_fn(facts,"revenue",orig,cik)[0]
        ni=metric_fn(facts,"ni",orig,cik)[0]
        if rev is not None and ni is not None:candidates.append(orig)
    if not candidates:return filing,None
    chosen=max(candidates,key=lambda x:(x["filed"],x["acc"]))
    return chosen,{"amendment_accession":filing["acc"],
                   "amendment_filed":filing["filed"],"original_accession":chosen["acc"],
                   "reason":"Amendment has no matching annual revenue or income facts"}
