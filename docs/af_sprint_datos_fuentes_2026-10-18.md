# A.Fundamental A · Contrato de datos y sprint de integración
Fecha: 2026-10-18 · Estado: especificación, NO datos certificados

## Objetivo
Cubrir el universo S&P 500 con fundamentales y señales cualitativas, calculados de forma reproducible. Certificar primero una muestra de 10 emisores heterogéneos para validar el motor y escalar sin perder trazabilidad. Los 500 no se anunciarán como auditados.

## Jerarquía de fuentes
1. SEC EDGAR: 10-K, 10-Q, 8-K, DEF 14A, Form 3/4/5, 13D/G y 13F; Companyfacts y Submissions; accession obligatorio.
2. IR oficial: resultados, transcripciones publicadas, presentaciones, gestión, segmentos, CapEx y guidance. Guardar enlaces y metadatos, no redistribuir textos protegidos.
3. API comercial (EODHD/FMP solo tras validar términos): estimaciones, mercado, noticias, accionistas e insiders; usar como contraste del dato SEC.
4. Fuente no disponible => NULL + explicación y próxima revisión; nunca rellenar a cero.

## Entidades y esquemas mínimos
- company: CIK, ticker, exchange, sector, estado de cotización, periodos.
- filing: form, accession, filing_date, period_end, URL, SHA256, amended_by.
- fact: CIK, period_start/end, fiscal_year, fiscal_quarter, unit, tag, value, provenance, filing, fiscal_vs_calendar, availability.
- metric: nombre, fórmula/version, dependencias, calculado, estado (OK/PROXY/BLOCKED/NA_SECTOR/NULL), causa y fecha de actualización.
- governance: directivos, cargo, nombramiento y cese, tenencia accionarial, remuneración/SBC, objetivos, historial de ejecución con fuentes DEF14A y 8-K.
- insider_transaction: SEC Form 4, owner CIK, fecha transacción, code (P/S/A/M/F...), acciones, precio, propiedad directa/indirecta, 10b5-1 si consta, accession, flags; no equiparar grants/ejercicios/retenciones con compras a mercado.
- large_owner: 13D/13G y enmiendas, porcentaje declarado y fecha de corte; 13F posiciones trimestrales y demora: detectar variación entre snapshots, no afirmar fecha real de compraventa.
- event: results, guidance, filing material, buyback/dividend, cambios CEO/CFO, litigio, adquisición; fecha, importancia, documento, sin duplicados, con enlace.
- analysis: tesis/contra-tesis, MOAT (marca, licencias, red, costes, switching, posición), márgenes, ROIC/ROCE, flujos, balance, reinversión, recompra neta/dilución, valoración sectorial, riesgos, hipótesis y fuentes.

## Finanzas que se deben solucionar antes de promocionar datos
- EBIT: reported OperatingIncomeLoss; para bancos/aseguradoras/REIT fórmulas especializadas.
- CapEx: desembolso por PP&E y notas; evitar sumar adquisiciones de negocio o sumar D&A como mantenimiento.
- Beneficio neto atribuible a ordinarios: conciliar minoritarios y preferentes; no usar ProfitLoss consolidado como BPA.
- EPS trimestral: Q4 derivar desde FY y Q1–Q3 únicamente cuando acciones diluidas/periodos y ajustes permitan conciliación; splits y restatements.
- FCF: CFO-CapEx no es FCFF. EV/FCF con flujo apalancado requiere etiqueta metodológica explícita; para múltiplo consistente usar P/FCF o EV/FCFF.
- PER FY/TTM/FWD diferenciados y con cotización/capitalización fechada; estimaciones consensuales identificadas.
- Múltiplo sector: P/BV banca, P/FFO inmobiliarias, EV/EBITDA o múltiplos apropiados; comparar historia y comparables.
- Los hechos contables no sustituyen evaluación de MOAT ni calidad de dirección.

## Aceptación por etapas
1. Fuente: descargar datos SEC/IR/insiders y probar endpoints de proveedor con datos reales, sin credenciales en GitHub.
2. QA: 10 emisores representativos, al menos una financiera, una utility y casos ADP/AEP; matrices por CIK+accession+period_end.
3. Certificación: para cada métrica crítica comparar con línea específica de 10-K/10-Q/DEF14A, con tolerancia explicada; anomalías BLOCKED.
4. Seguridad: runner/servicios con acceso mínimo, PR y tests; no sobreescribir histórico, backups.
5. MVP: web consume exclusivamente motor af_core y muestra fecha, método, fuente y bloqueos sin disimularlos.
6. Expansión: validar lotes adicionales y solo comercializar datos para los que haya autorización de proveedor si aplica.

## Prueba de API comercial (un mes, si se contrata)
- Muestra: MSFT AAPL JPM ADP AEP EXR WYNN IBKR TSLA y un REIT.
- Comparar 30+ campos (FY, Q, TTM, owners, officers, Form4, news); exportar reporte de cobertura, exactitud vs SEC, lag, precios, términos.
- KPI aceptación: >=95% coincidencia para métricas contables críticas disponibles tras normalizar períodos (umbral objetivo, no hecho constatado); 100% trazabilidad o BLOCKED; capacidad de extraer >=450 tickers del índice para métricas esenciales; coste/margen sostenible con contrato comercial.
- Revisar condiciones de DISPLAY/REDISTRIBUTION por escrito antes de exponer datos de terceros a clientes.
- Evitar renovación sin medir resultados; no migrar fórmulas a proveedor, mantener af_core.

Referencias oficiales:
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- https://www.sec.gov/submit-filings/technical-specifications
- https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds
- https://eodhd.com/pricing
- https://site.financialmodelingprep.com/pricing-plans
