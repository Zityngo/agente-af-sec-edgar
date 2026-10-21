# A.FUNDAMENTAL · Fase 1, bloque 2B.2a — calidad TTM y alertas de recurrencia

Fecha de incorporación: 2026-10-21.
Rama exclusiva: `agent/chatgpt-a`. Punto de partida: `11108239b141135d1294ce0f1c26980e61bdc649`.

## Alcance
- Reparar la propagación del estado de calidad de FCF a su margen y FCF yield.
- Propagar estados PROXY/BLOCKED en EV, EV/EBITDA, EBITDA TTM y deuda/EBITDA TTM; no convertir proxies en OK por un cálculo posterior.
- Añadir catálogo **manual, no exhaustivo** de tres impactos singulares de fuentes oficiales:
  - AMZN Q1 2026: ganancias preimpuestos de inversiones Anthropic 16.800 MUSD (SEC exhibit 99.1).
  - AMZN Q2 2026: otros ingresos no operativos preimpuestos 53.400 MUSD, **principalmente** inversiones Anthropic (SEC exhibit 99.1). No atribuir el importe total a Anthropic.
  - AAPL Q3 FY2026: impacto favorable de devoluciones arancelarias de 0,11 USD/acción (Apple IR).
- Incorporar avisos a auditoría JSON y al informe markdown del piloto de tres empresas, sin cambiar BPA GAAP ni crear cifras normalizadas.
- Nuevas pruebas sintéticas de regresión para propagación de calidad y validación del catálogo.

## Fuera del alcance
- No certificar ingresos extraordinarios restantes de todos los emisores.
- No recalcular impuestos, BPA ajustado, CF empresarial ni DCF sin fuente reconciliada.
- No crear ni modificar ninguna hoja de cartera, ni tocar main/Proyecto B.
- No consultar API comercial ni trasladar datos sujetos a licencia.

## Criterios de aceptación
1. `python -m unittest discover -s tests -v` sin fallos.
2. Piloto CI SEC + EODHD demo (solo lectura) completo y reporte que incluya `earnings_events`.
3. Conciliaciones EPS 12/12 y FY2025 18/18 conservadas.
4. Ningún ratio derivado de PROXY puede publicarse como OK.
5. Estado final se verifica con nueva ejecución GitHub Actions. Hasta entonces: **PENDIENTE VALIDACIÓN CI**.

Siguiente subbloque propuesto: cotejar CFO, CapEx y EBIT TTM por emisor contra ventanas YTD/FY y estudiar otras partidas materiales y su impacto fiscal, sin alterar GAAP.
