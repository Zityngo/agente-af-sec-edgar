# A.FUNDAMENTAL · Paso 2 finalizado: Tesla / PepsiCo · 23/10/2026

## Fuente y evidencia
- SEC Companyfacts extract, estrictamente accession y fecha de cada 10-Q:
  - TSLA, Q3 al 30/09/2026, accession `0001628280-26-066775`.
  - PEP, Q3 al 05/09/2026, accession `0000077476-26-000048`.
- Consulta auditada en GitHub Actions: https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/39924803101 ; 3/3 tests del extractor y tarea SEC **SUCCESS**.
- Reporte fuente de GitHub: artifact ID `12488059844`, `companyfacts_balance_lease_diagnostic.json`.
- Contabilidad reconciliada con dataset consolidado local: **13/13** componentes cuantitativos coinciden exactamente con etiquetas SEC.
- Motor y piloto preexistentes no deteriorados: https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/39925185501 con **108/108** tests, concluido SUCCESS.

## TSLA, oficial Q3, millones USD
- Cash: 17.853, inversiones corto plazo: 27.594, liquidez bruta: 45.447.
- Deuda financiera corriente: 1.311; larga: 7.956; total 9.267.
- Obligaciones de leasing financiero: 76 corriente + 180 largo = 256.
- Obligaciones leasing operativo: 1.075 corriente + 5.847 largo = 6.922.
- Comprobación de balance: 1.311+76 = 1.387 corriente y 7.956+180=8.136 largo.
- Deuda neta estricta financiera = 9.267−17.853 = **−8.586**.
- Deuda neta financiera con inversiones = 9.267−(17.853+27.594)= **−36.180**.
- Deuda neta con leasing financiero y operativo, caja+inversiones = 9.267+256+6.922−45.447 = **−29.002**.
- Obligaciones de pago de principal 9.284 vs carrying value 9.267, diferencia 17 (costes/descuentos). No sumar dos veces.
- Tesorería restringida: flujo de efectivo reporta cash+restricted 19.006; 19.006−17.853=1.153 **NO** equivale a caja libre.
- Línea bancaria disponible por 30.000 no se suma a deuda efectiva ni caja.

## PEP, oficial Q3, millones USD
- Cash 10.675, inversiones cortas 488, liquidez combinada 11.163.
- Obligaciones deuda corto 9.223, largo 42.658; total **51.881**.
- Papel comercial 4.800 forma parte de deuda corto: **NO SUMAR DOS VECES**.
- Deuda neta estricta = 51.881−10.675= **41.206**.
- Deuda neta con inversiones = 51.881−11.163 = **40.718**.
- Cash+restricted en cash flow 10.728, delta restringida=53 NO descontar como efectivo libre.
- **NO DISPONIBLE a Q3:** desagregación actualizada leasing operativo corriente/largo en SEC Companyfacts. Dato FY2025 oficial: 719+3127 = **3.846**.
- Hipótesis informativa no certificado: suponer leasing operativo constante al Q3 --> 40.718+3.846 = **44.564** sin resolver clasificación de finance leases. NO denominar cifra oficial Q3 ni EV consolidado definitivo.
- Identificación del tag `LongTermDebtAndCapitalLeaseObligations`: puede incorporar alguna obligación tipo capital lease; no añadir finance leases sin comprobar la nota.

## Archivos elaborados en esta conversación (fuera del repositorio)
- `A_FUNDAMENTAL_PASO2_BALANCE_TESLA_PEPSICO_20261023.pdf` (4 páginas renderizadas).
- `A_FUNDAMENTAL_PASO2_INTERACTIVO_20261023.html` autónomo, tests Chromium (cambio ticker, EV a precio manual, PEP bloquea).
- `AF_BALANCES_VERIFICADOS_Q3_2026.json` con descomposición, fuentes y fecha del último trade IBKR.
- `companyfacts_balance_lease_diagnostic.json` copia del artefacto oficial SEC.
- `QA_PASO2.json`: 15 pruebas locales + 13 contrastes directos contra SEC en copia del artefacto.

## Límites de la decisión
- EV a cotizaciones de IBKR del 23/10/2026 es **instantánea fechada**; no autorizar distribución comercial ni afirmar streaming continuado.
- No incorporar valores contables de leasing de FY2025 a Q3 como si fuesen actuales.
- EV puede requerir NCI/minoritarios y política homogénea de EBITDA IFRS/US GAAP y leases.
- Se mantiene bloqueada valoración intrínseca definitiva sin reconciliación de FCF sostenible, Ke/WACC, CapEx mantenimiento y escenarios.
- Sin cambios a main, Proyecto B, Cartera David, brokerage, suscripciones o proveedores.

**PASO 2:** CERRADO Tesla, **parcial verificable PepsiCo** (lesiones Q3 N/D). Siguiente paso autorizado solo bajo petición: FCF sostenible y capital allocation.
