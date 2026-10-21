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

## Cierre CI, datos reales y prueba funcional

- Commit fuente validado: `296890bb5313513cbb8d7f6a6c1fdf0498f62744`.
- GitHub Actions: https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/39677993631
- Estado: **SUCCESS**, pruebas unitarias, SEC+EODHD demo, generación PDF/HTML/JSON y artefacto ejecutados.
- 89/89 pruebas (verificar cantidad en logs), 18/18 comparaciones FY, 12/12 BPA, 12/12 puentes TTM; todos sin divergencias registradas en stdout.
- Último artefacto ID 12381988146, `af-a-pilot3-sec-eodhd` de GitHub Actions. Archivos: `revision_jon/jon_review.html`, `revision_jon/jon_review.pdf`, `revision_jon/jon_review.json`, auditoría, informe y SQLite.
- Datos mercado congelados: AAPL 339,50 USD / 14.594.180.000 acciones; TSLA 373,71 USD / 3.949.547.394; AMZN 262,63 USD / 10.786.313.572; precio 20/10/26, acciones al julio 2026 en 10-Q. Capitalización PROXY.
- Estado TTM: CFO, CapEx y FCF `PROXY` en las 3 debido a reconstrucción por YTD/FY, pese a puente aritmético `MATCH`.
- PDF: 4 páginas renderizadas, inspección visual realizada.
- HTML: prueba en Chromium de Apple/Tesla/Amazon, selección de serie de FCF y cálculo DCF local; sin excepciones JS. Amazon FCF TTM negativo bloquea DCF por defecto; con un FCF positivo manual se muestra hipotético.
- `main` verificado sin cambios: `c3d536c95dd0003ef6c26774a2c7db41a4f06fcd`.
- No se ha modificado Proyecto B, cartera, Google Sheets o subscripciones.
- Un ZIP limpio para Jon contiene HTML/PDF/JSON y texto; sin SQLite ni dump EODHD.

**Alcance aprobado solo como PILOTO PRIVADO METODOLÓGICO.** No certificar todavía los cinco objetivos en su interpretación comercial: FCF sostenible, FCFE y FCFF, coste de capital, guidance/segmentos, pares sectoriales, deuda/arrendamientos, accionistas/insiders y precio actualizado automáticamente requieren trabajo y revisión documental.

**Próximo checkpoint mínimo de 3 compañías:** confrontación SEC/IR y notas de deuda/caja, CapEx, SBC, buybacks y eventos; validación de FCF sostenible y escenarios sectoriales, después enviar el pack actualizado a Jon previa autorización.
