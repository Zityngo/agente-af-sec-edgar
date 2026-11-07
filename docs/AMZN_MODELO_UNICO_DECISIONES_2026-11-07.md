# A.FUNDAMENTAL — ÚNICA línea de trabajo y decisiones aprobadas (07/11/2026)

**Objetivo único hasta aceptación del usuario:** generar y perfeccionar el informe integral **Amazon (AMZN)** como plantilla-modelo reproducible. No abrir nuevas empresas, bases de datos, backtests, conectores ni funcionalidades secundarias. No fusionar `main` y no operar en cartera.

**Versión vigente:** complemento privado `analista-fundamental-cic-pro` V0.6.0 (motor 0.2.2-rc1 / esquema 0.2.1), metodología CIC V0.4 + enmiendas, proyecto A.FUNDAMENTAL V7.1 y contrato/checklist V12 como fuentes originales. Revisar siempre cuál es la versión realmente instalada; nuevas versiones solo tras pruebas y registro de cambio. La rama de reparaciones no es una release instalada.

## Precedencia de datos y previsiones

1. Para cifras históricas y contables: SEC 10-K / 10-Q y documentos del emisor, con período, fecha y base GAAP.
2. Para previsiones de cada período y métrica: **guidance oficial vigente primero**. Si se publica rango, éste prevalece. No interpolar artificialmente un guidance para años sin publicación.
3. **Consenso (FMP u otro proveedor autorizado) solo como apoyo**, contraste o proxy en métricas/años sin guidance; siempre etiquetar PROVEEDOR, con fecha, N analistas y definición contable. Desacuerdos materiales (EBIT 2026 AMZN) se bloquean hasta conciliar.
4. Orientación cualitativa oficial, como crecimiento de CapEx para 2027, es una **restricción económica**; no significa cifra publicada de CapEx 2027.
5. FCF/FCFF futuros: históricos no bastan; modelar explícitamente reinversión, circulante, D&A, impuestos, coste de capital y arrendamientos. Una entrada proyectada no publicada debe etiquetarse HIPÓTESIS justificada + sensibilidad, no OFICIAL.

### Caso de prueba ancla
SEC/IR a 29/10/2026: 9M ventas 584.069 BUSD y EBIT operativo 79.389 BUSD; guidance Q4 ventas 240–247 BUSD y EBIT 28.5–33.5 BUSD. FY2026 implícito 824.069–831.069 BUSD y EBIT operativo 107.889–112.889 BUSD. Para 2027–2030 no existe guía financiera anual integral equivalente; usar consenso **como apoyo, no como guía**.

Fuente: https://www.sec.gov/Archives/edgar/data/1018724/000101872426000040/amzn-20260930.htm
Guía: https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Third-Quarter-Results/default.aspx

## Adaptación sectorial
Usar el método más adecuado al negocio y al propósito, no imponer métricas industriales a bancos ni usar Graham/Gordon cuando no apliquen. AMZN: DCF FCFF/WACC por etapas con ROIC/reinversión terminal y contraste de múltiplos por segmentos; fuente/margen de seguridad y riesgos explícitos. El valor numérico no se certifica hasta conciliar deuda/leasing, activos no operativos, CapEx sostenible, NOPAT, tasas y dilución.

## Aceptación — no ampliar producto hasta conseguirlo
- 5 FY + 20 Q y período 2026 actualizado; GAAP/ajustado/estimación sin mezclas; ratios CIC con motor único y trazabilidad.
- Balance, capital invertido y ROIC definidos coherentemente; FCFF/WACC y, cuando proceda, FCFE/Ke sin doble conteo.
- Proyección máx. 5 ejercicios: fuente de cada variable y análisis de sensibilidad. DCF solo con hipótesis económicamente defendibles; de lo contrario NO CERTIFICADO.
- Informe HTML/PDF de un único modelo, 2 páginas ejecutivas + anexos, plantilla aprobada, barras anuales/trimestrales, múltiples, sectores, riesgos, glosario, QA P01–P40.
- Pruebas unitarias, financieras, visuales, de interacción y regresión con evidencia. Publicar release estable solo al superar controles relevantes, sin maquillarlos.

## Código de política de previsiones
`integrations/cic_consensus_guard.py`: resolución `guidance oficial por ejercicio/métrica > consenso`, bloquea look-ahead, discrepancias y caja prospectiva ausente. `tests/test_cic_v06_guidance_priority.py` y `tests/test_amzn_official_guidance_2026.py` son pruebas de regresión.

**Estado:** rama `repair/cic-v06-consensus-responsive-20261106`, PR #6 en borrador; la V0.6.0 instalada y `main` no cambian en este commit. No considerar tests sintéticos como aceptación financiera.
