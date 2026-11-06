"""CIC Pro P0 financial gates. No duplicated valuation formulas.
The caller supplies the installed CIC engine. No SEC/FMP credentials or datasets.
"""
from dataclasses import dataclass, asdict

@dataclass
class Gate:
    state: str
    reason: str
    evidence: dict
    def to_dict(self): return asdict(self)

def fcf_bridge(engine,cfo,capex,issuer_fcf,proceeds,tolerance=1e-4):
    if any(x is None for x in (cfo,capex,issuer_fcf,proceeds)):
        return Gate("BLOQUEADO","CFO/CapEx/FCF/adjustment missing",{})
    if capex<0:
        return Gate("BLOQUEADO","CapEx must be positive cash outflow",{})
    out=engine.fcf_gross(cfo,capex)
    if out.value is None:
        return Gate("BLOQUEADO","CIC engine rejected FCF",{"status":out.status})
    residual=out.value+proceeds-issuer_fcf
    if abs(residual)>tolerance:
        return Gate("DIFERENCIA PENDIENTE DE CONCILIACIÓN","Issuer FCF bridge failed",{"residual":residual})
    return Gate("CUMPLIDO","Gross and issuer FCF reconciled",{"gross_fcf":out.value,"residual":residual})

def debt_gate(engine,financial_debt,cash,finance_lease,operating_lease,provider_debt,
              provider_definition_verified=False,leases_in_debt_verified=False):
    if any(x is None for x in (financial_debt,cash,finance_lease,operating_lease,provider_debt)):
        return Gate("BLOQUEADO","Debt perimeter unavailable",{})
    n=engine.net_debt(financial_debt,cash)
    evidence={"strict_net_debt":n.value,"provider_debt":provider_debt,
              "finance_lease":finance_lease,"operating_lease":operating_lease}
    if not provider_definition_verified or not leases_in_debt_verified:
        return Gate("PARCIAL","Lease/provider debt reconciliation pending; expanded EV blocked",evidence)
    return Gate("LISTO PARA CÁLCULO","Debt/lease policy declared; confirm source matching",evidence)

def roic_gate(nopat,capital_open,capital_close,asset_exclusions_checked,
              leases_aligned,cash_excess_checked,adjustments_reviewed):
    if any(x is None for x in (nopat,capital_open,capital_close)):
        return Gate("BLOQUEADO","NOPAT/capital missing",{})
    if min(capital_open,capital_close)<=0:
        return Gate("BLOQUEADO","Capital nonpositive",{})
    checks=(asset_exclusions_checked,leases_aligned,cash_excess_checked,adjustments_reviewed)
    if not all(x is True for x in checks):
        return Gate("PARCIAL","Proxy ROIC only; operating return not homogeneous",{"checks":checks})
    return Gate("LISTO PARA CÁLCULO","Use installed CIC return_on_average_percent; financial interpretation still reviewable",{})

def dcf_gate(years,fcff,wacc,lease_bridge,other_assets,shares,terminal_reinvestment,source_per_year):
    checks={"five_consecutive_years":len(years)==5 and years==list(range(years[0],years[0]+5)),
            "five_fcff_known":len(fcff)==5 and all(isinstance(x,(float,int)) for x in fcff),
            "wacc_known":isinstance(wacc,(float,int)) and wacc>0,
            "lease_bridge":lease_bridge,"other_assets":other_assets,"shares":shares,
            "terminal_reinvestment":terminal_reinvestment,"source_per_year":source_per_year}
    if not all(checks.values()):
        return Gate("BLOQUEADO","Do not calculate intrinsic value / safety margin with missing economics",checks)
    return Gate("LISTO PARA CÁLCULO","Run CIC engine DCF; economic assumptions still require review",checks)


def reconcile_fmp_debt_components(provider_total,provider_long_debt,provider_lease,
                                  sec_operating_lease_noncurrent,sec_finance_lease_noncurrent,
                                  tolerance=1e-4):
    """Reconcile FMP totalDebt *field construction* with SEC, not its EV applicability."""
    values=(provider_total,provider_long_debt,provider_lease,
            sec_operating_lease_noncurrent,sec_finance_lease_noncurrent)
    if any(x is None for x in values):
        return Gate("BLOQUEADO","Debt / lease detail missing",{})
    a=provider_total-provider_long_debt-provider_lease
    b=provider_lease-sec_operating_lease_noncurrent-sec_finance_lease_noncurrent
    evidence={"provider_residual":a,"sec_residual":b,"provider_total":provider_total}
    if abs(a)>tolerance or abs(b)>tolerance:
        return Gate("DIFERENCIA PENDIENTE DE CONCILIACIÓN","FMP accounting normalization mismatch",evidence)
    return Gate("CUMPLIDO_DESGLOSE_NO_EV","Provider field explained; may omit current debt and mix lease classes. Cannot be used as strict CIC debt / EV.",evidence)
