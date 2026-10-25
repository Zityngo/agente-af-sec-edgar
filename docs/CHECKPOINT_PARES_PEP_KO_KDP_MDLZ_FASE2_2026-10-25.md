# A.FUNDAMENTAL · Fase 2 · PepsiCo frente a KO, KDP y MDLZ · 25/10/2026

## Contexto y alcance
El usuario entregó `COMPETIDORES_A_FUNDAMENTAL_FASE1_VERIFICACION.md` y `PEP_COMPARABLES_2026 (1).csv` y autorizó avanzar en los informes si existían datos. El CSV del proveedor trae 32 líneas (21 con valor y 11 NULL). La fase 1 quedó detenida por acceso parcial a InvestingPro. No afirmar que los archivos del usuario aportan los estados completos.

## Fuentes oficiales independientes
Se reconstruyó por SEC EDGAR, con accesión/fuente en CSV, cinco ejercicios FY2021–FY2025 para cuatro empresas: PEP, KO, KDP y MDLZ. Conjunto 20 empresa-año. Campos con fuente XBRL:
- Ingresos GAAP, beneficio bruto, EBIT GAAP, beneficio neto, CFO, pagos CapEx, BPA diluido, dividendos, etc. donde se informa.
- FCF contable = CFO − cash CapEx; **NO** FCFF normalizado ni FCFE.
- YoY, márgenes y variaciones de pp formulados por dato y período.
- FY2025 SEC: PEP revenue 93.925 BUSD/EBIT 11.498 BUSD/FCF CFO−CapEx 7.672 BUSD; KO 47.941/13.762/5.296; KDP 16.603/3.575/1.505; MDLZ 38.537/3.548/3.235.

## Hallazgos materiales
- KO: FY2025 FCF CFO−CapEx 5.296 BUSD; pago extraordinario fairlife 6.069 BUSD y FCF ajustado por emisor 11.365 BUSD. FY2024 depósito fiscal relacionado IRS, afecta comparabilidad.
- KDP: JDE Peet's adquirida el 1/4/2026, TTM 2026 incluye adquisición; requiere estados pro forma e intereses/deuda post-M&A para valoración homogénea.
- MDLZ: FY2025 EBIT cae marcadamente, presión costes cacao/volumen-mix, GAAP distinto de core.
- PEP: snacks + bebidas, modelo de negocio distinto de embotellador/concentrados KO y chocolate MDLZ.
- Earnings Q3 2026 aún no publicadas a 25/10/2026: KO 27/10, MDLZ 29/10, KDP 03/11; no insertar información futura en 25/10.

## Paquete entregado solo en conversación privada
- `AF_FASE2_PEPSICO_PARES_5FY_AUDITADO_20261025.zip`: PDF de 3 páginas, HTML autónomo, CSV contable FY2021–FY2025 con source accession, CSV user InvestingPro preservado, cotización media anual IBKR y YoY, JSON y QA.
- `AF_FASE2_PEP_COMPARABLES_OFICIALES_20261025.pdf` y `PEP_COMPARABLES_FASE2_INTERACTIVO.html`.
- **No copiar archivos con datos de usuario/IBKR/proveedor a repositorio público.**
- QA local: **104/104 pruebas** aritméticas y trazabilidad básicas, zip CRC, PDF renderizado, HTML Chromium escritorio/móvil probado con selector de métrica, 0 page errors y sin overflow global.
- Precio medio: **media aritmética de cierre diario** en ventana de FY, no VWAP ni rentabilidad total, FY2021 no histórico completo. Fuente IBKR, privada. No confundir el precio del ejercicio con la fecha de publicación del 10-K.

## Límites
No constituye DCF certificado ni BUY/SELL signal. Quedan pendientes ROIC GAAP homogéneo sectorial, ajustes a EBIT/FCF recurrentes, CapEx mantenimiento vs expansión, datos deuda/leasing/pro forma KDP, EV homogéneo y FCFF desde NOPAT + D&A − CapEx − dNWC, FCFE/Ke, WACC documentado y valoración inversa/sensibilidad.

## Siguiente fase, con aprobación del usuario
Normalizar EBIT/FCF y ROIC; estimar flujo sostenible por escenarios, valorar PepsiCo FCFF/WACC y FCFE/Ke independientemente; contrastar KO/KDP/MDLZ con múltiplos de misma fecha y sentido económico, sin promediar a ciegas; decidir por margen de seguridad e invalidación. Esperar/publicar nuevas revisiones tras las fechas Q3 oficiales.

## Integridad
GitHub solo `agent/chatgpt-a`; no `main` o Proyecto B. Cero broker trades/carteras.
