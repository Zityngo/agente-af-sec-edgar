# A.FUNDAMENTAL — QA dossier Tesla / PepsiCo V1.1

Fecha documental: 22/10/2026. Solo en rama `agent/chatgpt-a`.
El dossier revisado está guardado en los archivos generados de la conversación, no publicado en el repositorio porque la instantánea IBKR personal no se redistribuye.

## Validación de artefactos
- PDF: 8 páginas, renderizado y revisadas páginas 4 (inverso Tesla) y 5 (core PepsiCo).
- HTML: corrección de error de claves JSON `DATA[t]` (buscaba TSLA/PEP en lugar de Tesla/PepsiCo); prueba de Chromium `set_content` y cambio entre compañías sin JS errors.
- 18/18 pruebas locales verifican caja, capitalización, fechas, valoraciones indicativas, PDF y simuladores HTML.
- Datos de Tesla Q3 en la rama validados con CI del 22/10/2026: ejecución https://github.com/Zityngo/agente-af-sec-edgar/actions/runs/39777535932 ; 96/96 tests.
- PDF y HTML corregidos se hicieron fuera del repositorio; las 18 pruebas locales no forman parte todavía de CI.

## Correcciones
1. Tesla DCF inverso: el flujo calculado es `FCFE0` año base. `FCFE1 = FCFE0 × (1+g)`; no describir FCFE0 como primer año.
2. PepsiCo core: su comunicado Q3 (08/10/2026) informa +4 puntos porcentuales favorables en crecimiento de EBIT core por reembolsos arancelarios, incluso cuando el EBIT core total crece ~3 %. No inferir recurrencia. Fuente: https://www.sec.gov/Archives/edgar/data/77476/000007747626000050/q320268-kxexhibit991.htm .
3. HTML vuelve a navegar entre emisores y recalcular ambos ejercicios de valoración sin errores.

## Prioridad del siguiente bloque
Tesla: notas 10-Q Q3 para deuda corriente/larga, obligaciones financieras/operativas, efectivo restringido y net debt, separando facilidades sin disponer; N/D si falta.
PepsiCo: 10-Q Q3 corriente para leases, CFO y CapEx clasificados; discriminar dividendos, recompras, capital circulante, cash retornado y ajustes core.
No imputar CapEx mantenimiento/expansión como hecho salvo que la empresa lo declare. Probar escenarios explícitos antes de DCF final.
El estudio de proveedores o 500 compañías queda pausado por instrucción del usuario.

No se modifican main, Proyecto B, la cartera ni IBKR.
