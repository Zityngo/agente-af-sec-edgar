# A.Fundamental 2.0 — Microsoft (MSFT) | edición 13/10/2026

Este directorio contiene un panel estático, didáctico e interactivo para acompañar un PDF ejecutivo. Es válido en GitHub Pages o sin servidor si se descargan todos los ficheros.

- `index.html`: panel, navegación y preguntas.
- `styles.css`: estilos adaptables y alternancia de tema.
- `data.js`: magnitudes SEC 2022–2026, hipótesis DCF y métricas de mercado fechadas. **Es un corte fijo, no una API de mercado en directo**.
- `app.js`: gráficas, herramienta DCF, glosario y preguntas sin backend ni claves privadas.

La pregunta personalizada solo copia un texto para pegarlo en ChatGPT; **no existe chat de IA embebido ni envío de datos**. No se reproducen datos brutos de InvestingPro o FMP.

## Metodología

La estructura procede del material del curso FUNDAMENTAL 1–9 y DEUDA Y CAJA del proyecto. Datos primarios de SEC XBRL FY2022–FY2026 y formularios 10-K; aclaraciones de management desde Microsoft Investor Relations. Datos de cotización y consenso, de proveedores externos citados y con fecha. El DCF descuenta FCF = CFO - CAPEX de caja como aproximación al flujo disponible al accionista; por tanto emplea una tasa de coste del equity y **no aplica un ajuste adicional automático de deuda/caja**. Esta aproximación no reemplaza un FCFE totalmente reconciliado ni un FCFF descontado al WACC.

## Material de referencia

- https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm
- https://www.microsoft.com/en-us/investor/earnings/fy-2026-q4/press-release-webcast
- https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json
- https://www.marketbeat.com/stocks/NASDAQ/MSFT/
- https://www.marketbeat.com/stocks/NASDAQ/MSFT/forecast/
- https://stockanalysis.com/stocks/msft/statistics/

El material didáctico no representa recomendación individualizada ni promesa de rentabilidad. Copyright del proyecto: contenido analítico propio; no se publica la documentación privada del curso ni se redistribuyen archivos privados de proveedores.


## Actualización 2.1 — Selección múltiple y pares SEC (13/10/2026)

La primera gráfica admite selección simultánea de **Ingresos, EBIT, beneficio neto y CFO**, además de accesos «Mostrar todas» y «Solo ingresos». Debajo se incorpora el comparador de **Microsoft, Oracle, Salesforce, Alphabet y Amazon** con ocho métricas y dos escalas: miles de millones USD (márgenes en %) o evolución relativa **FY2022 = 100**. Se seleccionan varias compañías a la vez y se consultan cierres fiscales individuales en cada punto.

Datos de origen **S&P 500 SEC EDGAR v6.9 (snapshot 2026-10-13)**, no de InvestingPro, FMP de pago ni estimaciones. FY2026 aún no disponible para Alphabet y Amazon en esta fotografía; no se imputan valores faltantes. Los cierres fiscales varían por emisor y la comparación es **anual, orientativa, no de periodos calendarios idénticos**. Algunas cifras normalizadas están marcadas como PROVISIONAL; cotejar un dato importante con el 10-K original antes de invertir.

El índice base FY2022 se omite para compañías con métrica inicial negativa o nula, porque produciría porcentajes engañosos (p.ej., FCF Amazon). Los márgenes se comparan directamente en puntos porcentuales y no se indexan. Los competidores son comparables parciales por línea de negocio: Oracle/Salesforce software, Alphabet/Amazon grandes plataformas cloud diversificadas.

La **web es una fotografía estática fechada**; publicar la actualización no activa datos de bolsa en tiempo real ni recalcula automáticamente todas las empresas. Un futuro actualizador deberá regenerar las series y verificar nuevas presentaciones oficiales.