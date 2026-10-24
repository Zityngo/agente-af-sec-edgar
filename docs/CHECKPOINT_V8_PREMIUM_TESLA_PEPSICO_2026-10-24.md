# Checkpoint V8 · Tesla y PepsiCo · 24/10/2026

## Entregables cerrados (en conversación, privados)
- Tesla `A_FUNDAMENTAL_TSLA_PREMIUM_V8_JON_20261023.pdf` **31 páginas** y HTML autónomo equivalente.
- PepsiCo `A_FUNDAMENTAL_PEP_PREMIUM_V8_JON_20261023.pdf` **31 páginas** y HTML autónomo equivalente.
- Paquete `A_FUNDAMENTAL_V8_TESLA_PEPSICO_FINAL_JON_20261024.zip`, SHA256 `516a98c6d6884c7ab44914ef28ff9b631d4c1f96f86b37fabe9800c52d595e8d`; contiene 12 entradas, 2 PDF, 2 HTML, JSON maestro, subconjunto SEC XBRL público, QA y README.
- Los documentos usan estilo y arquitectura de la plantilla de usuario `PepsiCo_V6_2_INFORME.pdf`.
- **No publicar** esos documentos con precios de IBKR en un repositorio público. Disponibles solo en el paquete descargable desde la conversación.

## Validaciones de esta sesión
- Auditoría numérica: **275/275**. Verificación independiente de TTM, deuda neta, EV, PER, FCF, yields, márgenes, DCF 10 años, terminal, valores por acción, potencial y accesiones SEC; ver `QA_financial_checks.json` dentro del paquete.
- Chromium: **34/34**. Dos emisores en escritorio/móvil, sin JS exceptions, tablas, gráficos, cambios de escenarios, precio manual, parámetros bloqueados, sin desbordamiento móvil; ver `QA_browser_checks.json`.
- Ambos PDF: **31 páginas** cada uno, texto legible por página y capturas de verificación visual.
- Tesla p. 17 y HTML: añadido **cambio de guidance CapEx FY2026 desde >25.000 MUSD (Q2) hasta >20.000 MUSD (Q3)**, contrastado con ambos 10-Q. La diferencia es umbral de guía, NO caja sostenible demostrada.
- Pág. 10 de ambos PDF y HTML: leasing Tesla **OFICIAL**; PepsiCo Q3 **NO DISPONIBLE**, corregidas etiquetas confusas.
- ZIP CRC y hashes SHA256 de cada archivo incluidos.

## Fuentes fundamentales
- Tesla Q3: https://www.sec.gov/Archives/edgar/data/1318605/000162828026066775/tsla-20260930.htm
- Tesla Q2: https://www.sec.gov/Archives/edgar/data/1318605/000162828026049270/tsla-20260630.htm
- PepsiCo Q3: https://www.sec.gov/Archives/edgar/data/77476/000007747626000048/pep-20260905.htm
- Guidance PepsiCo: https://www.sec.gov/Archives/edgar/data/77476/000007747626000050/q320268-kxexhibit991.htm
- Datos históricos SEC filtrados e incluidos en ZIP.

## Estado
- Valoraciones FCFE/Ke y FCFF/WACC a tres escenarios, DCF inverso, múltiplos y margen de seguridad **calculados como hipótesis y estimaciones**, no como valores intrínsecos certificados.
- **Pendiente para certificación**: consenso 2027–28 con derechos de uso/licencia, comparables sectoriales a fecha homogénea (pares cuantitativos), CapEx mantenimiento/expansión económicamente justificable, homogeneidad de impuestos/financiación/arrendamientos y ajuste completo beneficio recurrente.
- PEPSICO: la deuda leasing Q3 no está identificada con granularidad requerida, no rellenar con FY2025.
- TESLA: el tratamiento de intereses sobre inversiones líquidas y su posible doble cómputo en FCFF/EV requiere contraste sectorial antes de certificar el precio objetivo.
- Precios IBKR se capturaron 23/10/2026; no son feed streaming en HTML.
- Status para Jon: **evaluables con reservas explícitas**, no material certificado para operar.

## Integridad de rama
Solo se añade checkpoint técnico a `agent/chatgpt-a`; `main`, Proyecto B, carteras, proveedores, cuentas y órdenes intocados.

## Cierre
TESIS → EVIDENCIAS → RIESGOS → CATALIZADORES → VALORACIÓN → INVALIDACIÓN → ACCIÓN: dos informes evaluables para discusión con Jon; bloquear recomendaciones de compra basadas en escenarios no certificados.
