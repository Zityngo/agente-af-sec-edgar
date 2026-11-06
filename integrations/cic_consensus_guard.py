"""CIC Pro: 5-year annual source-consensus reconciliation, without forecasted cash invention.

The module *does not* calculate valuation or issue analyst recommendations.
Only the explicitly supplied observations are compared. A non-matching vendor
measure is quarantined. 2026-2030 is five fiscal columns maximum.
"""
from __future__ import annotations
from datetime import date
from typing import Any

SCHEMA_VERSION = "0.6-consensus-guard-rc1"

def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) < 1e16

def _sum_existing(values):
    return sum(values) if values and all(_num(x) for x in values) else None

def _round(v, p=3):
    return round(v, p) if _num(v) else None

def build_model(inputs: dict, *, engine) -> dict:
    """Validates source fields; never turns NULL into zero or invents DCF cash flows.

    Expected: `historical_quarters` SEC 2026 Q1-Q3, `guidance_q4` from IR,
    `forecasts` list per fiscal year, `provider_2026_ebit` optional,
    and source locators/dates. Money values must be in USD billions.
    """
    ticker=inputs.get('ticker')
    if not isinstance(ticker,str) or not 1 <= len(ticker) <= 12 or not ticker.replace('.','').replace('-','').isalnum():
        raise ValueError('Ticker inválido')
    if inputs.get('units') != 'USD billions':
        raise ValueError('Este adaptador exige unidad USD billions; cambiar de unidad requiere conversión verificable')
    if len(inputs.get('historical_quarters', [])) != 3:
        raise ValueError('Se requieren Q1, Q2 y Q3 2026 de SEC')
    quarters=sorted(inputs['historical_quarters'],key=lambda r:r['quarter'])
    anchor_year=inputs['guidance_q4'].get('fiscal_year')
    if not isinstance(anchor_year,int):raise ValueError('Ejercicio del guidance ausente')
    if [q['quarter'] for q in quarters] != ['Q1','Q2','Q3'] or any(q['year'] != anchor_year for q in quarters):
        raise ValueError('Trimestres 2026 incompletos o desordenados')
    for q in quarters:
        if not _num(q.get('revenue')) or not _num(q.get('operating_income')):
            raise ValueError('Valor SEC ausente, no sustituir por cero')
        if q['source_type']!='OFICIAL' or not q['source_url'] or not q.get('filed'):
            raise ValueError('Falta fecha de presentación o fuente SEC')
    g=inputs['guidance_q4']
    if g.get('basis')!='OFICIAL' or g.get('fiscal_year')!=anchor_year or not g.get('source_url'):
        raise ValueError('Guidance Q4 sin fuente oficial y fecha')
    for k in ('revenue_low','revenue_high','operating_income_low','operating_income_high'):
        if not _num(g.get(k)): raise ValueError('Guidance incompleto: '+k)
    if not (g['revenue_low']<=g['revenue_high'] and g['operating_income_low']<=g['operating_income_high']):
        raise ValueError('Rango de guidance invertido')
    obs_revenue = _sum_existing([x['revenue'] for x in quarters]); obs_ebit = _sum_existing([x['operating_income'] for x in quarters])
    fy_revenue_low=obs_revenue+g['revenue_low'];fy_revenue_high=obs_revenue+g['revenue_high']
    fy_ebit_low=obs_ebit+g['operating_income_low'];fy_ebit_high=obs_ebit+g['operating_income_high']
    fy2026 = {'fiscal_year':anchor_year, 'data_status':'CALCULO_OFICIAL', 'source':'SEC 9M + guidance Q4 oficial',
              'revenue_low':_round(fy_revenue_low),'revenue_high':_round(fy_revenue_high),
              'revenue_avg':_round((fy_revenue_low+fy_revenue_high)/2),
              'ebit_low':_round(fy_ebit_low),'ebit_high':_round(fy_ebit_high),
              'ebit_margin_low_pct':_round(engine.margin_percent(fy_ebit_low,fy_revenue_high).value,2),
              'ebit_margin_high_pct':_round(engine.margin_percent(fy_ebit_high,fy_revenue_low).value,2),
              'analysts_revenue':None,'operating_cash_flow':None,'capex':inputs.get('guidance_cash_capex_anchor_year',inputs.get('guidance_cash_capex_2026')),
              'fcff':None,'valuation_status':'BLOQUEADO', 'source_url':g['source_url']}
    estimates2026=inputs.get('provider_anchor_year',inputs.get('provider_2026',{}))
    discrepancies=[]
    cons_2026_rev=estimates2026.get('revenue_avg');cons_2026_ebit=estimates2026.get('ebit_avg')
    if _num(cons_2026_rev) and fy_revenue_low <= cons_2026_rev <= fy_revenue_high:
        revenue_2026_status='COMPATIBLE_CON_GUIDANCE'
    else:
        revenue_2026_status='REVISAR_CONSENSO'
        discrepancies.append({'metric':f'revenue_avg_{anchor_year}','provider_value':cons_2026_rev,'official_implicit_range':[fy_revenue_low,fy_revenue_high], 'status':'DIFERENCIA_PENDIENTE'})
    # No inferred GAAP/adjusted mapping. Explicit mismatch blocks the field globally.
    ebit_vendor_status='NO DISPONIBLE'
    if _num(cons_2026_ebit):
        ebit_vendor_status='NO_COMPARABLE_PENDIENTE_DEFINICION' if not fy_ebit_low<=cons_2026_ebit<=fy_ebit_high else 'COMPATIBLE_CON_GUIDANCE'
        if ebit_vendor_status != 'COMPATIBLE_CON_GUIDANCE':
            discrepancies.append({'metric':f'ebit_avg_{anchor_year}','provider_value':cons_2026_ebit,
             'official_implicit_range':[_round(fy_ebit_low),_round(fy_ebit_high)],
             'status':'NO_COMPARABLE_PENDIENTE_DEFINICION', 'action':'Bloquear proyección EBIT del mismo proveedor hasta conciliación'})
    futures=sorted(inputs['forecasts'],key=lambda x:x['year'])
    if [x.get('year') for x in futures]!=list(range(anchor_year+1,anchor_year+5)):
        raise ValueError('Se requieren máximo 5 columnas (ancla + 4 años), sin extrapolar ejercicios futuros')
    years=[fy2026]
    for x in futures:
        if x.get('source_type')!='PROVEEDOR' or not x.get('source') or not x.get('retrieved_at'):
            raise ValueError('Consenso sin proveedor/fecha')
        n=x.get('analyst_count_revenue')
        if not isinstance(n,int) or n<20: raise ValueError('Consenso insuficiente (<20 analistas)')
        for k in ('revenue_low','revenue_avg','revenue_high'):
            if not _num(x.get(k)) or x[k] <= 0:raise ValueError('Previsión sin datos: '+k)
        if not x['revenue_low']<=x['revenue_avg']<=x['revenue_high']:
            raise ValueError('Rango consenso de ingresos inválido')
        years.append({'fiscal_year':x['year'],'data_status':'PROVEEDOR_CONSENSO',
        'source':x['source'], 'revenue_low':_round(x['revenue_low']), 'revenue_avg':_round(x['revenue_avg']),
        'revenue_high':_round(x['revenue_high']), 'analysts_revenue':n,
        'confidence_label': 'COBERTURA_RELATIVAMENTE_BAJA' if n<30 else 'COBERTURA_AMPLIA',
        'ebit_low':None,'ebit_high':None,'ebit_margin_low_pct':None,'ebit_margin_high_pct':None,
        'operating_cash_flow':None,'capex':None,'fcff':None,'valuation_status':'BLOQUEADO',
        'source_url':x['source_url']})
    for i in range(1,len(years)):
        prev=years[i-1]['revenue_avg'];val=years[i]['revenue_avg']
        years[i]['revenue_growth_pct']=_round(engine.growth_percent(val,prev).value,2)
    years[0]['revenue_growth_pct']=None
    return {
      'schema_version':SCHEMA_VERSION, 'ticker':ticker,'asof_date':inputs['asof_date'],'anchor_fiscal_year':anchor_year,
      'fiscal_years':years, 'source_types':['OFICIAL','CALCULO_OFICIAL','PROVEEDOR_CONSENSO','NO DISPONIBLE'],
      'anchor_consensus_revenue_status':revenue_2026_status,'anchor_consensus_ebit_status':ebit_vendor_status,
      'discrepancies':discrepancies, 'guidance_cash_capex_anchor_year':inputs.get('guidance_cash_capex_anchor_year',inputs.get('guidance_cash_capex_2026')),
      'valuation':{'status':'NO CERTIFICABLE','value_usd_per_share':None,'risk':'CapEx 2027-2030, FCFF, ROIC incremental, WACC, caja/deuda y valor terminal no conciliados'},
      'remaining_data':['CFO y CapEx forward 2027-2030 sustentados','ROIC incremental y reinversión de servidores',
          'Ebit/GAAP de 2027-2030 conciliado con la guía oficial','WACC y coste deuda fechados y coherentes',
          'Bridge deuda/lease/activos no operativos y SBC/dilución'],
      'method':'CIC Pro: ingresos SEC+guidance / consenso por ejercicio; cálculo motor CIC; no FCF inventado',
      'engine_version':getattr(engine,'VERSION', 'UNKNOWN')}
