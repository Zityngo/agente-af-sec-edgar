"""Data semantics for A.FUNDAMENTAL V9, independent of private IBKR prices."""
from __future__ import annotations
from datetime import date
from math import isfinite

def period_change(current, previous, *, ratio=False):
    """Return (value, unit) YoY; ratios in pp, ordinary flows as percent.
    Null and nonpositive percent denominators are not manufactured into zeros.
    Signs describe movement, not quality, especially for CapEx and SBC.
    """
    if current is None or previous is None:
        return None
    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and isfinite(x) for x in (current,previous)):
        return None
    if ratio:return (current-previous,"pp")
    if previous<=0:return None
    return ((current-previous)/abs(previous)*100,"%")

def is_valid_point_in_time(filed, entry_week, exit_week, *, preceding_report_filed=None):
    try:
        current=date.fromisoformat(filed)
        entry=date.fromisoformat(entry_week)
        exit_=date.fromisoformat(exit_week)
        prior=date.fromisoformat(preceding_report_filed) if preceding_report_filed else None
    except (TypeError, ValueError):
        return False
    return (prior is None or prior<=current) and current<entry<exit_

def fixed_discount_cashflow(cash_base, growth, discount, terminal_growth, *, years=10):
    """10-year FCFE-style perpetuity sensitivity, not certified valuation."""
    for x in (cash_base,growth,discount,terminal_growth):
        if not isinstance(x,(float,int)) or isinstance(x,bool) or not isfinite(x):
            return None
    if cash_base<0 or years<1 or discount<=terminal_growth or discount<=0 or growth<=-1 or terminal_growth<=-1:
        return None
    forecast=sum(cash_base*(1+growth)**t/(1+discount)**t for t in range(1,years+1))
    terminal=cash_base*(1+growth)**years*(1+terminal_growth)/(discount-terminal_growth)/(1+discount)**years
    total=forecast+terminal
    return {"pv_forecast":forecast,"pv_terminal":terminal,"value":total,
            "terminal_pct":100*terminal/total if total>0 else None}

def price_return(entry_price, exit_price):
    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and isfinite(x) and x>0 for x in (entry_price,exit_price)):
        return None
    return (exit_price/entry_price-1)*100
