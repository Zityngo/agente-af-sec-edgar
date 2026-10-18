# A.Fundamental V3 — Fase 2B.1: auditoría BPA TTM con documentos oficiales
**Fecha:** 2026-10-18 · **Estado:** cerrada satisfactoriamente en rama `agent/chatgpt-a` · Sin certificados de análisis integral.

## Punto de recuperación
- Último commit de código verificado: `1f2e61cc17cbbd2801d51046fc96221914a1eba5`.
- Ejecución reproducible: https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/39146565390
- **65/65 pruebas OK**; ejecución SEC + EODHD demo completa; 18/18 campos FY2025 frente a 10-K y sin errores de descarga.
- **12/12** BPA GAAP diluidos trimestrales contrastados automáticamente con cifras de comunicados oficiales de Apple, Tesla y Amazon (4 por empresa, 0 discrepancias).
- QA SEC XBRL comprobó accession, período, etiqueta, formulario trimestral, y Q4 fuente de emisor.

## BPA publicados y suma TTM (fin junio 2026)
| ticker | Q anterior al Q4 FY2025 | Q4 FY2025 | Q1 FY2026 | Q2 FY2026 o Q3 Apple | suma | estado |
|---|---:|---:|---:|---:|---:|---|
| AAPL | — | 1,85 | 2,84 | 2,01 + Q3 2,02 | 8,72 | PROXY |
| TSLA | Q3 0,39 | Q4 0,24 | Q1 0,13 | Q2 0,32 | 1,08 | PROXY |
| AMZN | Q3 1,95 | Q4 1,95 | Q1 2,78 | Q2 5,75 | 12,43 | PROXY |

Apple cuenta FY2025 Q4 + FY2026 Q1, Q2 y Q3. Tesla/Amazon cuentan FY2025 Q3, Q4 + FY2026 Q1 y Q2.
Los 12 valores y las URL exactas están en `data/eps_benchmarks_pilot_2026q2.json`. La auditoría reconstruible está en `af_core/eps_audit.py` y la conciliación en `af_core/eps_benchmark.py`; pruebas específicas `tests/test_eps_quarter_audit.py` y `tests/test_eps_benchmark.py`.
El informe completo, incluyendo los accession por trimestre, se guarda en el artefacto Actions de la ejecución.

## Advertencias importantes
- BPA **TTM = PROXY**; suma de trimestres puede diferir del BPA TTM corporativo por redondeos y acciones diluidas. Amazon publica **12,44 USD** TTM al 2026-06-30; el motor suma **12,43**, diferencia de 0,01, NO error demostrado.
- **Amazon**: el informe Q1 2026 atribuye 16,8 miles de millones USD de ganancias no operativas antes de impuestos a Anthropic; Q2 2026 incorpora 53,4 miles de millones USD de ingresos no operativos antes de impuestos, principalmente relacionados con Anthropic. Por tanto los BPA trimestrales y TTM no son equivalentes a BPA recurrente o sostenible; el PER GAAP simple puede resultar engañoso.
- **Apple**: Q3 FY2026 BPA 2,02 USD incluye efecto favorable por devoluciones arancelarias de 0,11 USD por acción. Evaluar recurrencia al normalizar.
- **Tesla**: distinguir beneficios GAAP atribuibles a ordinarios y ajustes non-GAAP. El documento IR Q2 2026 muestra consecutivamente 0,39 / 0,24 / 0,13 / 0,32 USD GAAP.
- Ninguna de las tres valoraciones ha sido certificada; faltan precios fechados, acciones en circulación al mismo período, márgenes/FCF/deuda TTM auditados y escenarios de valoración. NO inventar un precio justo.

## URLs de fuente pública verificadas
- Apple Q1 FY2026 https://www.apple.com/newsroom/2026/01/apple-reports-first-quarter-results/
- Apple Q2 FY2026 https://www.apple.com/newsroom/2026/04/apple-reports-second-quarter-results/
- Apple Q3 FY2026 https://www.apple.com/newsroom/2026/07/apple-reports-third-quarter-results/
- Tesla Q2 FY2026 https://ir.tesla.com/_flysystem/s3/sec/000162828026049213/tsla-20260722-gen.pdf
- Amazon Q1 2026 https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-First-Quarter-Results/default.aspx
- Amazon Q2 2026 https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Second-Quarter-Results/default.aspx

## Aislamiento y próximos bloques
- Todo el código solo en `agent/chatgpt-a`, `main` sin cambios (verificar de nuevo antes del próximo trabajo), rama Proyecto B intocada, no se ha escrito a Google Sheets ni se han efectuado operaciones.
- **Siguiente prioridad 2B.2:** detectar ganancias no recurrentes por empresa, construir resultados operativos/FCF TTM contrastados. No extrapolar ganancias Anthropic al EPS sostenible.
- **Después:** integrar fuente gratuita viable de precios/acciones fechados y valorar con múltiplos sectoriales, FCF/escenarios. Elaborar tres fichas de análisis de prueba usando sólo datos trazables.
- Estimación a este punto para tres fichas de calidad: aproximadamente 2–5 horas adicionales de trabajo efectivo, suponiendo acceso continuado a SEC y precios públicos verificables. Estimación, no garantía ni trabajo programado en segundo plano.

**Regla:** fases cortas, commit, CI y checkpoint. No continuar tras error CI sin aislar la causa. 
