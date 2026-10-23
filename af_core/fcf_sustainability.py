"""FCF bridge / sustainability stress. USD millions, no certified FCFE/FCFF."""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class CashPeriod:
    cfo:float
    capex_cash:float
    dividend_cash:float|None=None
    repurchases_cash:float|None=None
    debt_issuance:float|None=None
    debt_repayments:float|None=None
    finance_lease_principal:float|None=None

def _nonnegative(v,label):
    if v is not None and (not isinstance(v,(float,int)) or isinstance(v,bool) or not isfinite(v) or v<0):
        raise ValueError(label+": nonnegative finite value required")

def cash_bridge(x:CashPeriod):
    for k,v in vars(x).items():_nonnegative(v,k)
    fcf=x.cfo-x.capex_cash
    out={"fcf_gross":fcf,
         "fcf_definition":"CFO minus cash-capex line as filed; TSLA net asset sales/ex finance leases; PEP paid capital spending. NOT comparable strict gross FCF or FCFF",
         "distributions":None,"surplus_after_distributions":None,
         "new_borrowings_net":None,"fcfe_financing_proxy":None,
         "financing_proxy_status":"BLOCKED_INCOMPLETE_CASH_FLOWS"}
    if x.dividend_cash is not None and x.repurchases_cash is not None:
        d=x.dividend_cash+x.repurchases_cash
        out.update(distributions=d,surplus_after_distributions=fcf-d,
                   distributions_coverage=fcf/d if d>0 else None)
    if x.debt_issuance is not None and x.debt_repayments is not None:
        out["new_borrowings_net"]=x.debt_issuance-x.debt_repayments
        if x.finance_lease_principal is not None:
            out.update(fcfe_financing_proxy=fcf+out["new_borrowings_net"]-x.finance_lease_principal,
                       financing_proxy_status="PROXY_NOT_FCFE_CERTIFIED")
    return out

def fcf_stress(x:CashPeriod,*,cashflow_headwind:float=0,maintenance_share:float|None=None):
    _nonnegative(cashflow_headwind,"cashflow_headwind")
    if maintenance_share is not None and (not isinstance(maintenance_share,(int,float)) or
        isinstance(maintenance_share,bool) or not isfinite(maintenance_share)
        or not 0<=maintenance_share<=1):
        raise ValueError("maintenance_share must be 0..1 or None")
    reported=cash_bridge(x)["fcf_gross"]
    out={"reported_fcf_gross":reported,
         "stressed_fcf_after_all_capex":reported-cashflow_headwind,
         "headwind_status":"HYPOTHESIS_NOT_REPORTED",
         "maintenance_capex":None,"growth_capex":None,
         "cash_capacity_before_growth_capex":None,
         "maintenance_status":"BLOCKED_NO_ISSUER_SPLIT"}
    if maintenance_share is not None:
        m=x.capex_cash*maintenance_share
        out.update(maintenance_capex=m,growth_capex=x.capex_cash-m,
                   cash_capacity_before_growth_capex=x.cfo-cashflow_headwind-m,
                   maintenance_status="HYPOTHESIS_NOT_DISTRIBUTABLE_FCFE")
    return out

def ttm_rollforward(fy,current_ytd,old_ytd):
    if not all(isinstance(x,CashPeriod) for x in (fy,current_ytd,old_ytd)):
        raise ValueError("Three comparable CashPeriod inputs required")
    return CashPeriod(fy.cfo+current_ytd.cfo-old_ytd.cfo,
                      fy.capex_cash+current_ytd.capex_cash-old_ytd.capex_cash)

def wc_improvement_stress(x:CashPeriod,yoy_wc_contribution:float,fraction:float):
    if (not isinstance(fraction,(int,float)) or not isfinite(fraction)
        or not 0<=fraction<=1 or not isinstance(yoy_wc_contribution,(int,float))
        or not isfinite(yoy_wc_contribution)):
        raise ValueError("Invalid working-capital stress")
    return fcf_stress(x,cashflow_headwind=max(0,yoy_wc_contribution)*fraction)
