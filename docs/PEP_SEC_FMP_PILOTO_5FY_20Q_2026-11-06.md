# A.FUNDAMENTAL — Piloto SEC + FMP PepsiCo (5 FY, 20 trimestres)

**Fecha:** 2026-11-06. **Estado:** VALIDADO ESTRUCTURALMENTE, NO CERTIFICADO INTEGRALMENTE.
**Ámbito:** sólo piloto de lectura, no hay base persistente ni modificación de datos patrimoniales.
**Rama:** `agent/chatgpt-a` (nunca `main`).

## Evidencia ejecutada

- GitHub Actions (última ejecución correcta): https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/42231038694
- SEC XBRL: https://data.sec.gov/api/xbrl/companyfacts/CIK0000077476.json
- Reutiliza `scripts/normalize_sp500_v2.py`, agrega `scripts/pilot_pep_20q_sec.py`, `tests/test_pilot_pep_20q_sec.py`, `data/pep_q4_eps_official_2021_2025.json` y workflow `.github/workflows/af-pep-20q.yml`.
- 5 FY (2021–2025); 20 trimestres históricos Q1–Q4; 3 trimestres FY2026 adicionales.
- Cobertura 20/20: ingresos, beneficio bruto, beneficio operativo, beneficio neto, BPA diluido con respaldo en 8-K para Q4, CFO, CapEx, caja, deuda total normalizada, patrimonio, activos, D&A, intereses, impuestos, resultado antes de impuestos.
- 30/30 conciliaciones FY = Q1 + Q2 + Q3 + Q4 para seis flujos. **Importante:** Q4 se obtiene con FY−9M; son identidades internas, no 30 verificaciones independientes por filing.
- 20 ventanas móviles de BPA diluido TTM disponibles incluyendo 2026. El BPA TTM es PROXY (suma de BPA trimestrales), NO BPA TTM auditado del emisor.
- Secuencia fiscal excepcional confirmada: Q3 2022 (03/09/2022) → Q4 2022 (31/12/2022), 119 días, 17 semanas. Fuente: 10-K 2022 página 66, https://www.sec.gov/Archives/edgar/data/77476/000007747623000007/pep-20221231.htm.
- QA result: `STRUCTURAL_PASS`, `defects=[]`.

## Rescate de BPA Q4 oficial sin restar BPA anual

| FY | BPA GAAP diluido Q4 | 8-K oficial SEC | Fecha de publicación |
|---|---:|---|---|
| 2021 | 0.95 USD | https://www.sec.gov/Archives/edgar/data/77476/000007747622000011/q420218-kxexhibit991.htm | 2022-02-10 |
| 2022 | 0.37 USD | https://www.sec.gov/Archives/edgar/data/77476/000007747623000009/q420228-kxexhibit991.htm | 2023-02-09 |
| 2023 | 0.94 USD | https://www.sec.gov/Archives/edgar/data/77476/000007747624000010/q420238-kxexhibit991.htm | 2024-02-09 |
| 2024 | 1.11 USD | https://www.sec.gov/Archives/edgar/data/77476/000007747625000008/q420248-kxexhibit991.htm | 2025-02-04 |
| 2025 | 1.85 USD | https://www.sec.gov/Archives/edgar/data/77476/000007747626000009/q420258-kxexhibit991.htm | 2026-02-03 |

Estos cinco BPA están **verificados manualmente contra sus comunicados**. No está implementado un scraper automático general del 8-K. Fecha de disponibilidad del dato = fecha de publicación, no fin del ejercicio; evitar sesgo retrospectivo.

## Comparación FMP: PEP, TTM a Q3 2026

Cotización devuelta por FMP (consulta 2026-11-06): 142.71 USD; market cap 194,476,781,239 USD; precisión de cotización no garantizada fuera del instante de consulta.

| Métrica | SEC + referencia FMP de precio | FMP | Estado |
|---|---:|---:|---|
| BPA TTM proxy | 7.96 USD/acc. | — | CÁLCULO |
| FCF TTM = CFO − CapEx | 10,471 MUSD | — | CÁLCULO |
| PER diluido TTM = P / BPA | 17.928x | 17.928x | COINCIDE |
| P/FCF = Market cap / FCF | 18.573x | 18.573x | COINCIDE |
| FCF yield = FCF / Market cap | 5.384 % | 5.384 % | COINCIDE |
| ROIC TTM | 19.15 % **PROXY CIC** | 13.88 % | DEFINICIONES POR CONCILIAR |

No tratar los dos ROIC como comparables; investigar NOPAT, impuesto, caja neta, arrendamientos, capital invertido y ajustes. El ROIC del emisor es un tercer concepto.

## Alcance y bloqueos

- **Concluido:** disponibilidad de líneas contables para PEP, 5 FY, 20 Q, integridad trimestral/fiscal, FY vs 4Q, EPS Q4 oficial manual, aritmética de 3 múltiplos TTM y controles para datos ausentes.
- **Todavía NO certificado:** cada partida contable de los 20 trimestres comprobada en cada 10-Q; 53-semanas y cambios de perímetro en pares interanuales; EBIT/EBITDA y ROIC de cada sector; deuda estricta vs leasing; ROIC normalizado; FCF sostenible; BPA TTM oficial; dividendos, SBC, M&A; guidance y consenso; historia de precios/dividendos/splits y licencias; backtest libre de look-ahead.
- **FMP gratuito/conector actual:** devuelve 5 ejercicios anuales, 5 trimestres recientes, previsiones, ratios TTM y precios históricos de PEP. Ratios trimestrales históricos del endpoint bloqueados por plan, pero pueden calcularse localmente con SEC. Los 20 Q de FMP NO han sido consultados ni asumidos disponibles.
- **No creado:** base de datos propia, pagos, integración directa en habilidad CIC Pro, actualización automática de cartera, modificaciones de `main`.
- **Siguiente prioridad:** controles P0 de cobertura (dividendos, SBC, arrendamientos, acciones diluidas, guía, ratios forward) y prueba multicompañía sectorial antes de sustituir InvestingPro+ como única referencia.
