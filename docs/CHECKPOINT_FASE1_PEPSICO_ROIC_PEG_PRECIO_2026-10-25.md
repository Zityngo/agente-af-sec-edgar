# A.FUNDAMENTAL · Fase 1 cerrada · ROIC/PEG/Precio medio de PepsiCo · 25/10/2026

Solicitud: analizar pantallazos ROIC 5 FY, PEG forward 2026-2030, precio medio anual y trimestral fiscal, mini tesis sin duplicaciones, diferenciar métricas, mantener competidores separados de Tesla y dividir trabajo con aprobación del usuario por fases.

## Entregables privados de conversación
En `AF_FASE1_PEPSICO_20261025/`: `PEPSICO_FASE1_PILOTO_VISUAL.html`, JSON auditoría, ROIC+precio FY CSV, precios trimestre fiscal CSV, PEG forward CSV, QA JSON, README y ZIP. Los extractos de Investing/IBKR no se publican en GitHub por condiciones de uso. Su fecha de extracción original para PEG es N/D.

## Validación
- Precio medio = media simple de cierres diarios IBKR STK NASDAQ dentro de trimestres/ejercicios fiscales; cinco años hasta 2026-10-23. NO VWAP, NO precio final, NO retorno total. 2021 FY medio N/D por historia parcial.
- FY2026 Q3 cierra 2026-09-05, anuncio resultados 2026-10-08. Promedio de cotización en el trimestre NO prueba efecto del anuncio posterior.
- ROIC del proveedor 2021–25 reproducible como NOPAT/capital invertido; variaciones en **puntos porcentuales**. Nunca mezclar con ROIC calculado con otra fórmula.
- 2025: **ROIC oficial PepsiCo 14,3%**, **core net ROIC oficial 19,1%** y **ROIC Investing 17,4%**. El oficial 10-K 2025 muestra numerador 9.670 MUSD, capital medio 67.777 MUSD, fórmula net income attributable + interest expense after tax sobre quarterly avg debt + equity; `https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm`.
- NOPAT capturado Investing 2025 12.136 MUSD no reconcilia con EBIT GAAP 11.498 MUSD; BLOQUEADO para derivar FCFF/ROIC homogéneo.
- PEG forward de proveedor 2029 negativo no es señal de infravaloración. 2026 crecimiento BPA 39,4% no equivale guía core EPS 2,5%-3,5% de PepsiCo 08/10/2026; NO convertir en conclusión de compra.
- El mensaje «Próxima prueba: comprobar siempre etiqueta temporal y unidad» es instrucción genérica de QA, no mini tesis útil. Reemplazarlo por consecuencia económica y dato que podría cambiar la decisión.
- Datos históricos reales, proveedores y estimaciones no se mezclan ni se imputan a NULL=0.
- Auditoría local JSON: **21/21 controles**. Chromium escritorio y móvil: **tres tablas (5, 7 y 5 filas)**, sin errores JS ni desbordamiento.

## Próximo paso solo con luz verde
**Fase 2:** incorporar precio medio fiscal (Tesla y PepsiCo por separado), métricas históricas con cambios interanuales y una sola mini tesis específica por sección en los informes PDF/HTML. Añadir comparables del sector propios (PEP KO/KDP, TSLA automoción y energía por separado), no PEPSICO vs TESLA. Para certificado ROIC / forward PEG, pedir al usuario exportación de nota metodológica e histórico de Investing Pro o TIKR si las definiciones no están publicadas. No alterar `main` ni Proyecto B; no publicar extractos licenciados en GitHub.
