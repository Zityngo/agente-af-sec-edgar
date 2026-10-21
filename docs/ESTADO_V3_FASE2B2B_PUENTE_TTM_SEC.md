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
