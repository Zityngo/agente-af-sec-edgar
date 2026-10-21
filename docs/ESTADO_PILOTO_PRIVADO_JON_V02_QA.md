# Checkpoint — Calidad del TTM y revisión privada de tres empresas

Fecha: 21 de octubre de 2026, rama `agent/chatgpt-a`.

Se ha construido el paquete piloto privado a partir de SQLite SEC:
- 5 FY + 12 trimestres por compañía.
- 18/18 líneas FY2025, 12/12 BPA trimestrales y 12/12 puentes EBIT/CFO/CapEx/FCF TTM.
- 3 precios Nasdaq cerrados al 20/10/2026 y número de acciones en 10-Q (julio), ambos enlazados y fechados.
- JSON común, HTML interactivo y PDF con escenarios de FCF bruto, NO valores justos certificados.
- Corrección: CFO trimestral por YTD/FY y CapEx por FY−9M deben conservar PROXY en indicadores TTM; bloquear CapEx con fuente sin aprobar.

**Aprobación de Jon:** no obtenida. No contactar sin autorización. Sin suscripción, contratos ni cambios en main, B o cartera.

El paquete es apto para revisión metodológica, no para recomendaciones de inversión. Faltan FCFE/FCFF reconciliados, flujos sostenibles, informes sectoriales/competidores, guidance, directiva y actualización automatizada de los precios.

Última revisión visual local de artefactos:
- PDF 4 páginas renderizadas sin clipping aparente (resolución 110 DPI).
- HTML probado en Chromium: 3 cambios de empresa, gráfica FCF, DCF Amazon negativo bloqueado, DCF editable, sin errores JS.
- Estas comprobaciones corresponden al artefacto del commit previo; deben revalidarse si se regenera con cambios en el motor.
