# A.FUNDAMENTAL · PepsiCo Premium V10 INTEGRAL · 25/10/2026

## Entrega cerrada en conversación
Se corrigió el error de presentar un informe de competidores como si fuera el informe integral de PepsiCo. Ahora hay UNA entrega completa:
- `A_FUNDAMENTAL_PEPSICO_PREMIUM_V10_INFORME_COMPLETO.pdf` — 20 páginas, 20 capítulos, 20 mini tesis narrativas.
- `A_FUNDAMENTAL_PEPSICO_PREMIUM_V10_COMPLETO_INTERACTIVO.html` — 20 capítulos, 22 tablas, 6 gráficos, navegación móvil/escritorio, filtros de series y pares y DCF editable.
- `A_FUNDAMENTAL_PEP_DATOS_MAESTROS_V10.json` — JSON común a PDF/HTML.
- cuatro CSVs (históricos anuales YoY, trimestres YoY, 5 ejercicios SEC de KO/KDP/MDLZ, precio medio trimestral).
- `QA_V10_FINANCIERO.json`, `QA_V10.json`, README y manifest.
- ZIP privado `A_FUNDAMENTAL_PEPSICO_PREMIUM_V10_INTEGRAL_20261025.zip`; SHA256 `07463568c334fa3508a7dd27d15d3673e0b902e1c01bbe9ed2f6e6376a1e1473`; test CRC OK, once elementos.

## Alcance
- PepsiCo FY2021-2025, 8 trimestres Q4 FY2024-Q3 FY2026, YTD FY2026 y TTM separados, crecimiento y márgenes, flujo, deuda, ROIC/ROE/ROA/ROCE, insider/gobernanza, guía, revisiones y proyecciones, escenarios de DCF con sensibilidad, margen de seguridad y DCF inverso, y backtest exploratorio.
- Benchmark SOLO PEPSICO vs KO, KDP, MDLZ, propios cinco FY para los cuatro emisores, sin comparar con Tesla.
- Precios históricos medios por FY y trimestre, definidos como media aritmética de cierres diarios; precio ref PEP US 135,77 cierre 23/10/2026 (NO streaming).
- Apuntes del curso CIC, PepsiCo V6.2 y retroalimentación de V8/V9 integradas: mini tesis no duplicadas, signos YoY, conceptos temporales separados, narrativa accesible.

## Cifras y advertencias materiales
- Ventas TTM PEP USD 98.241m, FCF contable TTM USD 10.471m; FY2025 CFO 12.087m-CapEx 4.415m=7.672m, FCF del emisor 8.200m por producto de ventas de activos +528m.
- FY2026 Q3 EBIT GAAP 4.260m +19% YoY versus core EBIT 4.277m +3% YoY, con impacto de reembolsos arancelarios ~4pp en core.
- ROIC 2025 empresa 14,3%; core net 19,1%; InvestingPro 17,4%; son tres series metodológicamente distintas.
- FCFF/WACC escenario central hipotético USD 129,67/acción; FCFE/Ke USD 114,87/acción; cotización 135,77. **Valores NO certificados y modelos NO reconciliados (residuo ~707m USD)**, no promediar.
- 36 semanas YTD 2026 CFO−CapEx 5.768m, dividendos 5.935m, recompras 739m, diferencia −906m.
- Faltan CapEx mantenimiento oficial, tasas Ke/WACC totalmente trazadas, leasing Q3, normalizaciones core y comparables 2026 a misma fecha, cohortes de backtest fuera de muestra. No declarar BUY/SELL definitiva ni calidad decision-grade.

## Control de calidad
- `QA_V10_FINANCIERO.json` 237/237 controles aritméticos/campos y fuentes; no valida la economía de hipótesis.
- `QA_V10.json`: PDF veinte páginas con texto, selección de capturas inspeccionadas; HTML Chromium a 1360 y 390 px, cero excepciones JS, cero overflow, DCF central y favorable, edición precio, inputs inválidos bloqueados.
- No publicar precios/bases IBKR/InvestingPro ni PDF/HTML/JSON/ZIP bajo GitHub público. Este checkpoint es solo de metodología/estado, no de datos licenciados.
- main, Proyecto B, carteras y brokers intocados.

## Fuentes oficiales
PepsiCo 10-K 2025 https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm
PepsiCo Q3 2026 https://www.sec.gov/Archives/edgar/data/77476/000007747626000048/pep-20260905.htm
PepsiCo Q3 2026 comunicado https://www.sec.gov/Archives/edgar/data/77476/000007747626000050/q320268-kxexhibit991.htm

Estado: INFORME INTEGRAL FINALIZADO Y AUDITADO TECNICAMENTE; VALORACION CERTIFICADA BLOQUEADA HASTA CONCILIACION ECONOMICA.
