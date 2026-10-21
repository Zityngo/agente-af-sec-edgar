# Fase 1 — Piloto de tres emisores para revisión de Jon · MVP privado V0.1

Fecha snapshot mercado: 2026-10-20. A partir de SEC EDGAR + Yahoo Finance consultado manualmente y contrastado; no se automatiza Yahoo ni se declara permiso para redistribuir datos de mercado.

Objetivo validable: AAPL, TSLA y AMZN con cinco FY, últimos 12 trimestres disponibles, métricas TTM auditadas, BPA GAAP con eventos no recurrentes, precio fechado, acciones reportadas 10-Q, capitalización proxy, PER GAAP TTM proxy y escenarios educativos de flujo de caja.

## Componentes
- `data/pilot_price_reference_2026-10-20.json`: cotización de cierre manual + acciones oficiales del 10-Q, URLs y fechas.
- `scripts/build_jons_review.py`: único transformador SQLite/JSON a paquete auditable JSON, HTML, PDF.
- `app/jon_review_template.html`: HTML autónomo adaptable, 3 emisores, gráficos históricos propios, FY/Q, TTM, fuentes y DCF interactivo.
- `tests/test_review_pack.py`: límites y regresiones.
- `.github/workflows/af-pilot3-sec-eodhd.yml`: test + SEC + EODHD demo + paquete de revisión y validación básica PDF.

## Metodología y bloqueos esenciales
- FCF bruto = CFO − CapEx bruto, no FCFE ni FCFF.
- DCF pedagógico usa CFO-CapEx como proxy y deuda neta futura 0 como HIPÓTESIS. **No** se autoriza mostrarlo como valor intrínseco de compra/venta.
- Amazon: ganancias no operativas Anthropic inflan BPA GAAP, FCF TTM negativo => DCF ilustrativo bloqueado con baseline SEC.
- Apple: impacto arancelario 0,11 USD/BPA; tasas escenario no constituyen previsión.
- Tesla: inversiones/opciones en robotaxis/IA no se modelan sin caja sostenible verificada.
- Capitalización PROXY por precio 20/10/26 vs número de acciones de julio (10-Q), distinta fecha.
- No P/FCF sostenible ni FCFE/FCFF ni precio justo auditado. Deuda/caja/leasing y FCF de mantenimiento pendientes de reconciliar.
- PDF/HTML consumen un mismo dataset JSON y fórmulas idénticas en Python para valores precalculados; HTML recalcula interactivamente en JavaScript con la misma fórmula.
- Empaquetado en GitHub Actions solo para piloto privado y descarga manual; NO lanzar app a clientes ni publicar las cotizaciones.

## Verificación pendiente en CI
1. Suite unitaria completa verde.
2. Piloto SEC real y 18/18 FY, 12/12 EPS, 12/12 puentes TTM conservados.
3. Generación de HTML autónomo + PDF extraíble + JSON con 3 compañías y mínimo 5 FY cada una.
4. Revisar visualmente PDF/HTML en dispositivo y examinar todo el paquete antes de enviarlo a Jon.
5. Evaluación personal de Jon: criterios y modificaciones metodológicas, no delegar decisión a calificaciones sintéticas.

Este trabajo no cambia main ni Proyecto B ni Cartera David. No envía mensajes ni contrata proveedor.
