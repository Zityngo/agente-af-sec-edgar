# Agente A.Fundamental — Integración FMP Basic (gratis) bajo principio 80/20

**Estado a 13/10/2026:** integración desarrollada y 11 pruebas offline superadas. **No hay credencial FMP enlazada** a esta sesión, por lo que **no está acreditado que tu cuenta Basic permita consultar los tres endpoints financieros**. La ejecución en modo de simulación sí ha sido validada. **No se ha reemplazado ningún dato de SEC ni actualizado el archivo maestro.**

## Jerarquía y objetivo

1. **SEC EDGAR companyfacts**: cifras contables principales y rastro de formulario + accession; fuente maestra.
2. **Motor propio**: ROIC proxy, solvencia, ratios, estados por calidad, tests regresivos. Mantiene dato desconocido como NULL.
3. **FMP Basic opcional**: contraste automatizado de 2–3 empresas problemáticas por ejecución, y recuperación de **candidatos** para investigar lagunas. Nunca reemplaza valores SEC silenciosamente.
4. **InvestingPro**: referencia humana puntual, **no** exportación manual de cientos de compañías.

## Suscripción y límites constatables

- FMP publica el plan **Basic a 0 USD** con **250 consultas al día**, datos EOD y perfiles de referencia.
- Su página de precios distingue los fundamentales anuales y cinco años históricos como prestaciones de Starter. Por tanto **NO GARANTIZAMOS** acceso desde Basic a Income Statement, Balance Sheet o Cash Flow: cada endpoint debe probarse con la API key individual.
- **Ninguna suscripción debe comprarse** para iniciar esta prueba. Si las tres rutas están restringidas, se aborta la idea de usarlas en Basic: SEC permanece como solución principal.
- El plan Basic indica uso individual/personal; para una web monetizada se requiere evaluar licencia comercial/redistribución aparte.

Documentación del proveedor:
- https://site.financialmodelingprep.com/pricing-plans
- https://site.financialmodelingprep.com/developer/docs/quickstart
- https://site.financialmodelingprep.com/developer/docs/stable/income-statement
- https://site.financialmodelingprep.com/developer/docs/stable/balance-sheet-statement
- https://site.financialmodelingprep.com/developer/docs/stable/cashflow-statement

## Alta (una sola vez, sin gasto)

1. Crear cuenta gratuita en https://site.financialmodelingprep.com/ y localizar **Dashboard → API Keys**.
2. En GitHub, repositorio `Zityngo/agente-af-sec-edgar`, ir a **Settings → Secrets and variables → Actions → New repository secret**.
3. Nombre exacto del secreto: `FMP_API_KEY`; valor: clave privada FMP obtenida en el panel. **No pegar la clave en este chat ni en el código**.
4. Ir a **Actions → FMP Basic - prueba segura → Run workflow**; la primera prueba usa **solo AAPL y un máximo de tres peticiones** (Income / Balance / Cash Flow).
5. Observar el resultado: si un endpoint está restringido, quedará como `API_UNAVAILABLE`; no se fuerza un pago ni se vuelve a intentar sistemáticamente.

## Ejecución con CSV SEC local

Ejemplo desde la carpeta que contiene el repositorio y la base de SEC:

```bash
python scripts/fmp_free_crosscheck.py \
  --sec-csv /ruta/SEC/sp500_annual_5y.csv \
  --qa-queue /ruta/SEC/qa_review_queue_latest.csv \
  --max-companies 3 --max-calls 9 --dry-run

# Cuando el entorno ya tenga FMP_API_KEY configurada, eliminar --dry-run:
python scripts/fmp_free_crosscheck.py \
  --sec-csv /ruta/SEC/sp500_annual_5y.csv \
  --qa-queue /ruta/SEC/qa_review_queue_latest.csv \
  --max-companies 3 --max-calls 9 --out-dir /ruta/privada/qa_fmp
```

Los archivos de comparación del último comando **son privados**, no se suben a un repositorio público. No se guardan respuestas JSON completas de FMP. La clave nunca se imprime ni se conserva en los informes.

## Criterios de conciliación

- Comparación **FY contra FY**, mismo **CIK** si se proporciona, moneda idéntica y cierre fiscal con desfase <= 7 días; TTM/periodos trimestrales no se comparan con FY.
- **CAPEX** SEC como desembolso positivo; FMP a menudo negativo: se compara el valor absoluto. **FCF = CFO - CAPEX**, salvo advertencia de definición.
- Umbral inicial **1,5 % relativo** para mostrar `REVIEW_DIFFERENCE`, que **no certifica** automáticamente error; anomalías de importe alto merecen priorización.
- **ROIC**: no forzamos igualdad con el proveedor porque NOPAT y capital invertido tienen distintas definiciones.
- **Total Debt y Net Debt** de FMP no se comparan directamente con `financial_debt_ex_leases_v2` ni `net_debt_ex_leases_v2` porque el tratamiento de arrendamientos y efectivo varía. Deuda y caja se reconcilian por componentes y notas contables SEC.
- Si un dato falta, es **NULL**, nunca 0 estimado.
- El script solo emite reporte privado, no escribe ni sobrescribe `sp500_annual_5y.csv`.

## Regla Pareto para el siguiente ciclo

A. Mantener cálculos con alta cobertura y relevancia: ventas, EBIT, márgenes, FCF, EPS, crecimiento, caja verificable.

B. Mostrar ROIC/ROE/deuda neta **solo cuando pase controles**. Si no, mostrar "No calculable con fiabilidad" y el motivo; evita revisar miles de registros manualmente.

C. Auditoría selectiva: empezar con **AAPL, CSCO y MCK** para cubrir arrendamientos, liquidez e indicadores distorsionados por patrimonio negativo. Aplicar correcciones **de fórmula** masivamente desde SEC; FMP se consulta solamente si está permitido y aporta diferencia comprobable.

D. En cuanto se valide la clave y los endpoints disponibles, conectar este módulo al flujo de actualización del motor. **Hasta entonces, no se declara integración operativa remota ni una actualización automática de FMP.**