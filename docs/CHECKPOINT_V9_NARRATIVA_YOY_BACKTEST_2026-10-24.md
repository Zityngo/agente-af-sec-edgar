# A.FUNDAMENTAL Premium V9 · checkpoint privado (24/10/2026)

Petición del usuario: reescribir con narrativa comprensible, interpretación en mini tesis al final de apartados, distinguir trimestre/YTD/TTM, signos de Δ YoY en todas las tablas, visuales, DCF explicativo y backtest usando datos históricos a los que realmente se tenía acceso.

## Entregables (almacenados como archivos privados de esta conversación, no en repositorio)
- Tesla V9 PDF, 9 páginas; HTML autónomo con 19 apartados.
- PepsiCo V9 PDF, 9 páginas; HTML autónomo con 19 apartados.
- Datos JSON maestro de ambos, QA y README en ZIP `A_FUNDAMENTAL_PREMIUM_V9_TESLA_PEPSICO_NARRATIVO.zip`.
- QA local **483/483** verificaciones financieras, contrastes interanuales, puente DCF, fuente vintage SEC y pruebas de backtest.
- Chromium escritorio y móvil: navegación filtros, gráficos, input DCF, errores, bloqueos y 0 desbordamiento global móvil.

## Ampliación retrospectiva realizada
- Por empresa: 3 cortes 10-K FY2022, FY2023 y FY2024, y 3 cortes Q3 2023–2025.
- Cada corte utiliza XBRL del 10-K o 10-Q presentado, y en trimestre CFO−CapEx TTM = FY anterior + YTD actual − YTD comparación incluido en Q3 original.
- Cotización IBKR: cierre de barra semanal posterior a publicación comparado con cierre ~12 meses después. **Dividendo excluido**: el retorno PEP solo mide precio.
- La última cohorte trimestral TSLA Q3 2025 a octubre 2026 tiene menos de 52 semanas y se marca período parcial.
- Supuestos DCF fijados retrospectivamente hoy (2026), no fueron preregistrados en 2023–2025; este experimento mide límites económicos y no es prueba estadística de habilidad predictiva.
- La disciplina FCF pierde revalorizaciones de TSLA; deben incorporarse escenarios de opcionalidad respaldados por evidencia, evitando inventar resultados.
- **No publicar** precios históricos, instantáneas IBKR ni HTML/JSON adjuntos públicamente.

## Advertencias todavía abiertas
- Datos numéricos originales proceden de los 10-K/10-Q públicos y fuentes compartidas; V9 los organiza, **no sustituye** hipótesis por oficiales.
- FCF contable CFO−CapEx ≠ FCFE ni FCFF auditado. CapEx mantenimiento N/D por separado.
- El FCFF/WACC V8 emplea puente simplificado con intereses y no constituye valoración independiente robusta. La V9 lo advierte expresamente y muestra valores como escenarios.
- DCF valores exactos no certifican el valor intrínseco por acción. El modelo base requiere comprobar WACC/Ke, circulante, fiscalidad y opción de negocio.
- PEP leasing Q3, PEG forward y comparables homogéneos permanecen N/D.
- Próximo trabajo si se solicita: obtener peers a fecha común, tasas de descuento derivadas, cash impuestos y refinanciaciones, escalar backtest a universo mayor y rentabilidad total con datos licenciados.

Rama única `agent/chatgpt-a`; no cambiar `main`, Proyecto B, cartera, brokers ni publicar a Jon.
