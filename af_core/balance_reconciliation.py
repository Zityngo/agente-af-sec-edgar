"""Quarterly balance reconciliation, strict definitions and no silent lease assumptions."""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Balance:
    cash: int
    investments: int
    debt_current: int
    debt_noncurrent: int
    finance_lease_current: int|None = None
    finance_lease_noncurrent: int|None = None
    operating_lease_current: int|None = None
    operating_lease_noncurrent: int|None = None
    # if debt figures already include finance leases, NEVER add again
    finance_lease_mode: str = "UNKNOWN"  # EXCLUDED, INCLUDED, UNKNOWN

def reconcile(b:Balance) -> dict:
    for name,v in asdict(b).items():
        if name=="finance_lease_mode":continue
        if v is not None and (isinstance(v,bool) or not isinstance(v,int) or v<0):
            raise ValueError(name+": invalid balance")
    if b.finance_lease_mode not in ("EXCLUDED","INCLUDED","UNKNOWN"):
        raise ValueError("Unknown finance lease accounting")
    debt=b.debt_current+b.debt_noncurrent
    strict=debt-b.cash
    liquid=b.cash+b.investments
    net_liquid=debt-liquid
    fc,fn=b.finance_lease_current,b.finance_lease_noncurrent
    oc,on=b.operating_lease_current,b.operating_lease_noncurrent
    fin_total=fc+fn if fc is not None and fn is not None else None
    op_total=oc+on if oc is not None and on is not None else None
    if b.finance_lease_mode=="EXCLUDED":
        fin_increment=fin_total
    elif b.finance_lease_mode=="INCLUDED":
        fin_increment=0  # already included, do not assert finance lease amount is zero
    else:
        fin_increment=None
    finance_adjusted=(net_liquid+fin_increment) if fin_increment is not None else None
    # Operating lease inclusive EV requires FULL amount; no fabricated 0.
    full=(finance_adjusted+op_total) if finance_adjusted is not None and op_total is not None else None
    return {"gross_financial_debt":debt,"liquidity_cash_only":b.cash,
       "liquidity_cash_plus_short_investments":liquid,
       "net_debt_strict":strict,"net_debt_liquid_assets":net_liquid,
       "finance_lease_obligation":fin_total,"operating_lease_obligation":op_total,
       "net_debt_including_finance_lease":finance_adjusted,
       "net_debt_all_leases":full,
       "lease_adjustment_status":"CALCULATED" if full is not None else "BLOCKED_INCOMPLETE_Q3_LEASES"}

def enterprise_value(equity_market_value_musd,net_debt_musd):
    if equity_market_value_musd is None or net_debt_musd is None:
        return None
    if equity_market_value_musd<=0:raise ValueError("Market cap invalid")
    return equity_market_value_musd+net_debt_musd
