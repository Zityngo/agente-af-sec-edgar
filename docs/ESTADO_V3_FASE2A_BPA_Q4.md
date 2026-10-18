# A.Fundamental V3 · Fase 2A cerrada — BPA diluido Q4 2025

Fecha: 2026-10-18 UTC. Rama: `agent/chatgpt-a`. Ultimo commit de código validado: `afcba9548ca2901da09840203386eb7c82f2e0e1`.
Ejecución CI: https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/39145440992
**Estado: VALIDACIÓN DEL PILOTO (no certificación integral, no producción).**

## Objetivo / alcance
Incorporar el BPA diluido GAAP de Q4 2025, publicado expresamente, al piloto temporal AAPL / TSLA / AMZN, sin restar BPA FY menos BPA 9M, sin inferir EPS ausente ni modificar el normalizador general de las 500.

## Fuentes y datos oficiales para Q4 FY2025
| ticker | período Q4 | GAAP diluted EPS USD | fuente oficial |
|---|---|---:|---|
| AAPL | 2025-06-29 a 2025-09-27 | 1.85 | https://www.apple.com/newsroom/2025/10/apple-reports-fourth-quarter-results/ |
| TSLA | 2025-10-01 a 2025-12-31 | 0.24 | https://ir.tesla.com/_flysystem/s3/sec/000162828026003837/tsla-20260128-gen.pdf |
| AMZN | 2025-10-01 a 2025-12-31 | 1.95 | https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Fourth-Quarter-Results/default.aspx |

Los tres valores se introdujeron como **registro oficial revisado, TEMPORAL PARA EL PILOTO** en `data/q4_eps_official_pilot_2025.json`. El registro NO representa la extracción automatizada. Módulo `scripts/official_eps_pilot.py` verifica: ticker, CIK, FY, Q4, duración, fuente oficial y discrepancia con cualquier XBRL previo; en caso de diferencia mayor de 0.011 USD falla, no sustituye el dato.

## Resultado reproducible
Workflow CI `39145440992`: **55 pruebas OK** (49 previas, 6 del módulo); 3/3 Q4 incorporados (ninguno venía reportado en el XBRL SEC seleccionado), sin errores de descarga; 18/18 controles 10-K FY2025 previos coincidentes (6 por empresa).

| ticker | EPS Q4 2025 | Último EPS TTM sumando cuatro trimestres | fin TTM | estado |
|---|---:|---:|---|---|
| AAPL | 1.85 | 8.72 | 2026-06-27 | PROXY |
| TSLA | 0.24 | 1.08 | 2026-06-30 | PROXY |
| AMZN | 1.95 | 12.43 | 2026-06-30 | PROXY |

**IMPORTANTE**: EPS TTM procede de suma de EPS publicados por trimestre. Es `PROXY` por redondeos, cambios en acciones ponderadas, splits y falta de una conciliación independiente. La compañía Amazon informa **12,44 USD** TTM en el comunicado del 2T 2026 (diferencia de 0,01 por redondeo); fuente https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Second-Quarter-Results/default.aspx . La empresa informó de beneficio extraordinario relacionado con inversión en Anthropic en 2026; los 12,43/12,44 USD TTM no deben extrapolarse como BPA recurrente. No se ha calculado PER sin cotización fechada. No hay valores de mercado inventados.

## Archivos del cambio
- `data/q4_eps_official_pilot_2025.json` — fuente auditada del piloto (3 empresas).
- `scripts/official_eps_pilot.py` — regla de incorporación y conflictos.
- `scripts/pilot_5.py` — opción `official_q4_path` solo en el piloto invocado explícitamente.
- `scripts/pilot_3_sec_eodhd.py` — activa opción; registra fuente y TTM en reporte y CI.
- `tests/test_official_eps_pilot.py` — seis pruebas de regresión.

## Aislamiento
Sin escrituras en Google Sheets ni modificaciones a `main` o rama ajena. `main` seguía en `c3d536c95dd0003ef6c26774a2c7db41a4f06fcd` tras la prueba.

## Fase 2B siguiente (sin ejecutar)
1. Validar los cuatro EPS individuales TTM frente a publicaciones trimestrales oficiales en cada emisor; conciliar Amazon 12,43 vs 12,44.
2. Sustituir el puente registrado manualmente por un extractor de 8-K/exhibits y fuentes IR con parser trazable, preferiblemente secuencia de archivos estructurados y sin dependencia de páginas comerciales.
3. Añadir estado de calidad EPS por cada trimestre y bloquear `PER TTM` si cualquiera difiere o carece de procedencia verificable.
4. Escalar 3 → 10 empresas heterogéneas antes de aplicar a 500; sin anunciar certificación completa.

## Regla de reanudación
Leer este documento y el CI más reciente antes de modificar nada. Confirmar rama, commit, resultados y fuentes. Mantener workflow de bloques breves y confirmar resultado antes de seguir.
