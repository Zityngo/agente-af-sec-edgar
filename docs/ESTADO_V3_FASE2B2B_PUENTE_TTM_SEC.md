# A.FUNDAMENTAL — Fase 1, bloque 2B.2b · Puente SEC de TTM

Fecha: 21/10/2026. Rama: `agent/chatgpt-a`.
Objetivo: contrastar las series TTM del motor contra una segunda construcción usando tres datos acumulativos oficiales SEC, no solamente sumar cuatro trimestres.

## Fórmula y alcance
Para Q1, Q2 o Q3 corriente:
`TTM = FY previo + YTD actual - YTD del mismo trimestre del ejercicio previo`.
Auditar EBIT reportado OperatingIncomeLoss, CFO y CapEx bruto en USD.
FCF bruto se calcula exclusivamente como CFO - CapEx (no FCFF ni FCF corporativo ajustado).

Fuentes desde los archivos `companyfacts_TICKER.json` recuperados por el piloto; chequeos de mismo tag SEC, fecha final, formulario 10-K/10-Q, accession exacto del período, divisa USD y duración de acumulados. Sin nuevo proveedor ni credenciales adicionales.

## Validaciones
- El resultado `MATCH` acredita **igualdad de valores bajo las definiciones XBRL utilizadas**, no una auditoría integral ni sostenibilidad.
- Si falta una pata, tag común o procedencia, marcar `PARTIAL_BLOCKED` (nunca 0).
- Si la fórmula discrepa contra el TTM del motor, `DIVERGENCE` y fallo del piloto CI.
- Estados y detalles se imprimen en consola y quedan en `auditoria_piloto_3.json` y `analisis_piloto_3.md`.
- Pruebas unitarias sintéticas para Q2, Q3, tag distinto, fecha incorrecta, bloqueos y divergencia.

## Sigue pendiente
- Intereses y arrendamientos comparables, efecto fiscal de extraordinarios, FCF sostenible/FCFF/FCFE, BPA normalizado, precios con derechos comerciales, valoraciones DCF, validación sectorial del piloto de 10 emisores.
- CI, 18/18 FY y 12/12 EPS deben verificarse después del commit en GitHub Actions.
- No tocar `main`, Proyecto B, Google Sheets ni cartera.

## Validación CI y cierre · 21/10/2026

- Commit de implementación: `d7a86f79348924604612f9a9303225caa4dbd82e`.
- GitHub Actions: https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/39673914878
- Conclusión: **SUCCESS**.
- Pruebas: **81/81** superadas (73 previas + 8 pruebas nuevas).
- SEC FY2025: 18/18 campos conciliados frente a referencias 10-K.
- EPS trimestral GAAP: 12/12 comparados con fuentes del emisor; EPS TTM continúa como PROXY.
- Puente SEC: Apple, Tesla y Amazon `MATCH` para `ebit_ttm`, `cfo_ttm`, `capex_ttm` y `fcf_ttm`, **12/12**.
- Ninguna descarga fallida; proveedor EODHD demo se mantiene solamente para contraste exploratorio, no para explotación comercial.
- HEAD `main` comprobado durante el cierre: `c3d536c95dd0003ef6c26774a2c7db41a4f06fcd` (sin cambios).
- No se ha revisado manualmente el artefacto ZIP completo; la conclusión se apoya en logs de CI y salidas impresas.

**ESTADO: bloque 2B.2b CERRADO**. No equivale a análisis empresarial íntegro certificado.

## Siguiente paso
Fase 1, bloque 2B.3: detectar eventuales ganancias no recurrentes y explicar su efecto por separado sobre EPS GAAP y EPS sostenible, evitando calcular un EPS ajustado sin impuestos/acciones diluidas. Después proceder al piloto sectorial de diez emisores.
