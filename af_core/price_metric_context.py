"""Price-context / ROIC / PEG methodology with no licensed provider data."""
from datetime import date
from math import isfinite

def price_mean_by_fiscal_window(bars, start, end):
    """Mean of daily closes; rows (YYYY-MM-DD,USD/share); distinct trading dates."""
    st=date.fromisoformat(start);en=date.fromisoformat(end)
    if en<st:raise ValueError("Reversed fiscal window")
    selected={}
    for d,close in bars:
        dt=date.fromisoformat(d)
        if not isinstance(close,(int,float)) or isinstance(close,bool) or not isfinite(close) or close<=0:
            raise ValueError("Invalid quote")
        if st<=dt<=en:
            if d in selected:raise ValueError("Duplicate trading date")
            selected[d]=float(close)
    if not selected:return {"status":"NOT_AVAILABLE","mean_close":None,"sessions":0}
    return {"status":"PROXY_DAILY_CLOSE_MEAN_NOT_VWAP","mean_close":sum(selected.values())/len(selected),
            "sessions":len(selected),"first_trade":min(selected),"last_trade":max(selected)}

def roic_components(numerator,invested_capital):
    if invested_capital is None or numerator is None:return None
    if invested_capital<=0:return None
    return numerator/invested_capital*100

def relative_difference(new, old, metric_type="amount"):
    if new is None or old is None:return None
    if metric_type=="ratio":return {"value":new-old,"unit":"pp"}
    if old<=0:return None
    return {"value":(new/old-1)*100,"unit":"%"}

def peg_screen(pe_forward, growth_eps_pct):
    if pe_forward is None or growth_eps_pct is None:
        return {"status":"NOT_AVAILABLE","value":None}
    if pe_forward<=0 or growth_eps_pct<=0:
        return {"status":"NOT_MEANINGFUL_NEGATIVE_OR_ZERO","value":None}
    return {"status":"PROXY_VERIFY_GAAP_CORE_AND_FORECAST_VINTAGE",
            "value":pe_forward/growth_eps_pct}

def valuation_allowed(official_roic,provider_roic,method_reconciled):
    """Do not substitute provider ROIC for issuer ROIC without a recorded bridge."""
    if official_roic is None or provider_roic is None:return False
    return bool(method_reconciled)
