# Checkpoint · PepsiCo Premium V10 integral · 25/10/2026

## Petición y alcance
Usuario indicó que la fase previa era solo comparador y que quería **informe integral de PepsiCo**, con todos sus contenidos, y competidores KO, KDP, MDLZ como un capítulo, nunca Tesla. Requisitos de narrativa contextual, visualización, 5 FY, YoY, 8 trimestres, YTD 36 semanas, TTM, ROIC, deuda, múltiplos, forward, precio medio histórico, mini tesis específicas, DCF FCFF/FCFE, backtest y HTML autónomo interactivo.

## Entregables privados de conversación
- PDF **12 páginas**, 19 capítulos, `A_FUNDAMENTAL_PEPSICO_V10_ENTREGA_COMPLETO.pdf`.
- HTML autónomo **19 capítulos**, menú lateral, filtro de métricas / años FY y minigráfico con ajuste estadístico NO previsión, DCF interactivo con precio editable `A_FUNDAMENTAL_PEPSICO_V10_ENTREGA_INTERACTIVO.html`.
- JSON maestro, CSV anual con cambios YoY, CSV trimestral con variaciones YoY, CSV con FY2021–25 de PEP/KO/KDP/MDLZ, QA y README.
- ZIP `A_FUNDAMENTAL_PEPSICO_PREMIUM_V10_INTEGRAL_Y_COMPARABLES_20261025.zip` solo en el archivo privado de esta conversación. IBKR y InvestingPro NO subidos a GitHub.

## Evidencia y QA
- PDF renderizado y página por página inspeccionada (12 páginas; ninguna vacía).
- QA aritmético **237/237**: histórico, CFO−cash CapEx, YoY, TTM=FY+YTD−YTD comparativo, deuda neta, accesiones SEC por par, dos modelos DCF, caja, sensibilidad, fuentes y contenido.
- Chromium HTML en escritorio 1440 y móvil 390: cero errores JS, cero desbordamiento global; 19 capítulos, filtros históricos reaccionan, simulador DCF recalcula y bloquea tasas inválidas.
- ZIP 10 ficheros con SHA256 de cada uno, CRC íntegro.

## Fuentes pivote
- FY2025 PEP: https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm
- Q3 PEP: https://www.sec.gov/Archives/edgar/data/77476/000007747626000048/pep-20260905.htm
- Guidance Q3: https://www.sec.gov/Archives/edgar/data/77476/000007747626000050/q320268-kxexhibit991.htm
- Historias de pares recuperadas SEC con accession por celda y archivadas en ficheros privados.

## Estado de valoración
- Precio captura 23/10/2026 PEP 135,77 USD (no streaming), 2026 Q3 cierra 5/9/2026.
- FY2025 FCF CFO−CapEx 7.672 MUSD; FCF no-GAAP publicado incluye venta PP&E 528 MUSD => 8.200 MUSD. NUNCA mezclarlos.
- ROIC FY2025 PepsiCo oficial no-GAAP 14,3 %; core net 19,1 %; InvestingPro 17,4 % (proveedor independiente).
- FCFF/WACC escenario central ~129,67 USD, FCFE/Ke central ~114,87 USD. Dos vías no promediadas, ambas **hipótesis**, no objetivos certificados. Residuo de puente FCFF/FCFE 707 MUSD. CapEx mantenimiento/crecimiento oficial desconocido; costes de capital no calibrados de forma independiente.
- Seis backtests de PEP: datos de archivo fechados pero parámetros retrospectivos y rentabilidad de precio sin dividendos; no prueba predictiva.
- Comparables: 5 FY homogéneos GAAP SEC y ratios de InvestingPro parciales / TTM no plenamente homogeneizados; KDP JDE Peet's pro forma, KO fairlife, MDLZ cacao deben ajustarse. NO media sectorial artificial.

## Siguiente paso
Auditar ROIC homogéneo peer, intereses/cash tax, deuda leasing, CapEx mantenimiento normalizado y fuentes de WACC/Ke; actualizar guía y resultados sectoriales Q3 tras publicación; nuevo checkpoint antes de elevar a decision-grade. Las conclusiones de V10 son condicionales.

Integridad: solo `agent/chatgpt-a`. No editar `main`, Proyecto B, carteras ni realizar operaciones financieras.
