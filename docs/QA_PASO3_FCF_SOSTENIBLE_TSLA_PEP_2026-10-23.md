# A.FUNDAMENTAL · Paso 3A · FCF sostenible y política de caja (23/10/2026)

## Qué se ha continuado
No repetir Paso 2, ni extrapolar cinco FY o convertir 36 semanas en un año.
Se retoma la revisión previa de 291 coincidencias SEC y 14 conciliaciones identificadas en el chat “Continuar paso 3”; **esa auditoría previa no se ha reejecutado aquí**.

- TSLA SEC 10-Q, cierre 30/09/2026, accession 0001628280-26-066775.
  - CFO 9M 14.897; PP&E cash paid **neto de ventas de activos**, excluyendo arrendamientos financieros 13.014; FCF de definición publicada 1.883.
  - 9M CFO 2025 10.934, capex 6.134, FCF 4.800. Cambio de CFO +3.963 del que administración atribuye aprox. +3.510 a comparación favorable del circulante; mejora restante aprox. 453.
  - Escenario no repetición de 50 % de mejora de WC: FCF 128; no repetición 100 %: FCF −1.627. **Son choques de sensibilidad, no flujos normalizados oficiales**.
  - CFO 9M incluye SBC 3.346. Adquisiciones de inmovilizado contabilizadas en pasivos y no pagadas 3.667, NOT cash CapEx actual. Compra equity SpaceX 2.002 fuera del cash CapEx industrial.
  - Deuda nueva neta 5.834−4.954=880, leasing financiero principal pagado 63. FCFE de financiación **PROXY PARCIAL**: 1.883+880−63=2.700, NO FCFE certificado.
  - FCF TTM 18.710−15.407=3.303, mantener estado de definición publicada / comparabilidad.

- PEP SEC 10-Q, cierre 05/09/2026, accession 0000077476-26-000048.
  - CFO 36 semanas 7.950, cash CapEx 2.182 -> FCF bruto 5.768. YTD comparable anterior CFO 5.468, CapEx 2.499 -> 2.969. Crece el FCF +2.799 (+2.482 CFO, −317 CapEx).
  - Dividendos 5.935 + recompras 739 = 6.674; déficit de distribución 906.
  - TTM 12.087+7.950−5.468=14.569 CFO; 4.415+2.182−2.499=4.098 CapEx; FCF = 10.471. No extrapolar YTD como año.
  - Comparación favorable de capital circulante no cuantificada por separado, NO imputar el ajuste como OFICIAL.
  - Último pago de obligación por transition tax 965 divulgado: la información disponible NO prueba el desglose temporal preciso como ajuste al CFO de 36 semanas. No se suma automáticamente.
  - FCFE/FCFF y margen de seguridad sin certificar hasta conciliar financiación, capex mantenimiento/expansión y coste de capital.

## Código y QA
- `af_core/fcf_sustainability.py` añade motor de cash bridge, estrés de circulante, escenarios de maintenance capex y control NULL!=0.
- `tests/test_fcf_sustainability.py` incorpora 8 tests nuevos de no doble cómputo, ventanas comparables, hipótesis y bloqueos.
- `data/fcf_sustainability_tsla_pep_q3_2026.json` almacena importes originales y URL SEC.
- Reporte local independiente del repo: `AF_PASO3_FCF_TESLA_PEPSICO_20261023.pdf` (3 páginas) y `AF_PASO3_FCF_INTERACTIVO.html` con navegación y sliders; ambos desde un solo JSON local. HTML validado en Chromium sin errores.

## Siguiente bloque
Paso 3B: revisar con los adjuntos de emisor el calendario de pagos de CapEx comprometido y conversiones de WC, desagregar cash tax/gains con evidencia y plantear bandas explícitas para FCF *sostenible*. Solo con financiación e intereses tras impuestos homogéneos decidir FCFE/Ke y FCFF/WACC. Ningún dato de mantenimiento/expansión divulgado se sustituirá silenciosamente por D&A.
No enviar nada a Jon ni tocar `main`, Proyecto B, Cartera David, broker o proveedores.
