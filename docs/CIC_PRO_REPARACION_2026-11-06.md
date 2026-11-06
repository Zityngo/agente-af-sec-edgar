# CIC Pro — reparación de integración, 06/11/2026

**Alcance:** rama `repair/cic-pro-v04-e2e-20261106`, no `main`; sin base persistente, órdenes ni publicación del plugin privado.

## Causa raíz
El complemento privado V0.4 tiene motor `cic_engine.py` V0.2.0 y esquema V0.2.0, pero no había adaptador de ejecución ni generador HTML/PDF; la versión Amazon anterior recalculaba fórmulas fuera del motor. La plantilla aprobada fue suministrada posteriormente por el usuario.

## Código reparado
`integrations/cic_runtime_adapter.py`: entrada contrato `{document,tasks}`; carga ruta privada `CIC_ENGINE_PATH`; ejecuta funciones del motor (no copia ni modifica fórmulas); rechaza datos nulos, períodos, monedas, escalas y stocks de fechas incompatibles. Cada salida registra función, entrada, versión y hash de motor.

`tests/test_cic_runtime_adapter.py`: pruebas sintéticas de contrato, no certificación económica. El código y documentos privados NO se distribuyen en este repositorio.

## Evidencia en artefacto local entregado al titular
- CIC instalado: versión 0.4.0; motor original 0.2.0, SHA256 `2ea4a45c094659defc77e3d8d040da832987c97c9d43308155ed24996cf3b068`, fuente cotejada.
- En sesión local: 193 registros trazables, 43 cálculos invocados en motor original y 29 pruebas de regresión; datos SEC AMZN 2021-2025 y 2026 Q3.
- Plantilla **exacta** `CIC_Pro_PepsiCo_2_paginas_REPARADO.html` suministrada por usuario y adaptada con dos páginas ejecutivas + 4 anexos.
- HTML/PDF 6 páginas mismo modelo, Chromium glosario clic, teclado, toque, sensibilidad y 0 desbordamientos detectados en el render observado.
- Caso Amazon **NO CERTIFICADO**: puente leasing/deuda, ROIC/CIC, CapEx mantenimiento, valoración activos privados, FCFE, riesgo de valor terminal y algunos controles P0.
- Propuesta plugin **0.5.0-rc1 sin publicar**: motor 0.2.1 preserva fórmulas anteriores, añade excepción fiscal documentada 53 semanas, adaptador y plantilla.
- Arquitectura general aún requiere interfaz narrativa/generación genérica para otras empresas y ensayos adicionales.

**Advertencia:** los números de Amazon son simulaciones de valoración con hipótesis antiguas; no usar como precio objetivo certificado.
