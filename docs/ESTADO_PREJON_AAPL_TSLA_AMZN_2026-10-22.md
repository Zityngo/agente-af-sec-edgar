# A.FUNDAMENTAL — Checkpoint auditoría tres empresas (22/10/2026)

## Estado operativo
- GitHub rama `agent/chatgpt-a`; baseline código `9324d3d679896932f9e542db445b10765465b4d3`. No tocar main.
- Último GitHub Actions confirmado: https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/39777535932 ; 96/96 tests, 18/18 conciliaciones FY2025, 12/12 EPS, 12/12 puentes SEC TTM.
- Tesla Q3 2026 ingestado de SEC hasta 30/09/2026 y conciliado; 8-K publicado 21 octubre, SEC accession 0001628280-26-066775.
- AAPL último publicado Q3 fiscal cerrado 27 junio; Q4 presentado 2 nov próximo. AMZN último publicado Q2 calendario 30 junio; Q3 presentado 29 oct próximo.
- `af_core/market_data.py`: adaptador IBKR Client Portal local SOLO CONSULTA; gate de REALTIME/DELAYED/FROZEN, timestamps y validación CIK/DEI acciones. Suite sintética tests. Observación de cotizaciones IBKR desde conector personal no implica feed 24/7, gateway autenticado en servidor, ni licencia para redistribución.

## Informe profesional para Jon, generado fuera del repositorio (archivos de conversación)
- `A_FUNDAMENTAL_PREJON_PROFESIONAL_20261022.pdf` (14 páginas)
- `A_FUNDAMENTAL_PREJON_INTERACTIVO_20261022.html` (HTML autónomo, probado en Chromium)
- `af_datos_unificados_20261022.json` (unifica históricos, ratios, estado, escenarios y fuentes)
- `A_FUNDAMENTAL_PAQUETE_PREJON_20261022.zip` (los tres anteriores)
- El PDF fue renderizado e inspeccionado; el HTML pasó navegación AAPL/TSLA/AMZN y recalcular escenarios; AMZN FCF negativo bloquea DCF predeterminado. Archivos NO enviados ni expuestos públicamente.
- No subir licencias ni instantáneas personales IBKR a repositorio público.

## Datos cualificados
- PRECIOS: snapshots IBKR 22 octubre en respuesta del conector con top-status REALTIME y timestamp, no actualizados continuamente en HTML; snapshot solo.
- ACCIONES: cifra de acciones en circulación del 10-Q julio para las tres; Tesla septiembre Q3 pendiente extracción DEI de 10-Q antes de afirmar capitalización precisa; usar PROXY.
- TTM SEC: AAPL FY Q3 2026, TSLA Q3 2026, AMZN Q2 2026. CFO−CapEx bruto validado aritméticamente, NO flujo sostenible certificado.
- AAPL Q3 EPS favorable por aranceles de 0,11 USD por acción; aislar solo ese efecto (EPS TTM 8,72 -> 8,61) no da EPS completo ajustado.
- AMZN ganancias no operativas H1 other income 69.062 MUSD pretax, mayoritariamente inversiones. Solo sensibilidad fiscal con 10.889 millones acciones diluidas H1, NUNCA EPS normalizado oficial.
- Mantenimiento vs expansión CapEx separado solo en hipótesis 50/75/100%, no dado por emisor. Amazon empresa FCF ajustado ≠ CFO−CapEx bruto.
- Balance: net debt estricta y ampliada separadas. TSLA efectivo estricto pendiente al usar solo cash+short-term investments combinados. Amazon leasing y deuda de acuerdo 10-Q; AAPL leasing pendiente reconciliar.
- Benchmark independiente NYU Stern US Enero 2026 por sector (agregados, no media de 3 pares), no peers plenamente homogéneos Oct 2026.
- AMZN guía oficial Q3 (publicada julio): ventas 197–202 mil MUSD y EBIT 22,5–26,5 mil MUSD; actualización tras 29 octubre.

## Decisiones/impedimentos del objetivo final
- Valor intrínseco COMPRAR/MANTENER/VENDER: BLOQUEADO hasta normalizar caja (CapEx mantenimiento/expansión), deuda/lease e intereses, WACC/Ke, FCFF/FCFE y peers comparables.
- No licenciar ni vender una plataforma comercial con quotes de IBKR personal.
- Priorizar reunión con Jon sobre esta documentación y sus observaciones; no ampliar universo a 500 antes de validar 3.
- No se ha intervenido en cartera o brokers, no se ha contactado a Jon ni se ha contratado ningún proveedor.
