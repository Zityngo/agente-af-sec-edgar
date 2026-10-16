# A.FUNDAMENTAL — ESPACIO DE TRABAJO A

**Responsable:** ChatGPT
**Fecha de separación:** 2026-10-16
**Commit idéntico de partida:** `8645d11071eea18115d848ceee0ec071c8df9414`
**Rama:** `agent/chatgpt-a`
**Repositorio original:** `Zityngo/agente-af-sec-edgar` (público)
**Estado:** fase experimental, NO es producción y ninguna empresa está certificada.

## Reglas de aislamiento

1. Trabajar **exclusivamente** en `agent/chatgpt-a`. No modificar `main`, `feature/af-core-mvp`, ni la rama del otro agente.
2. Usar exclusivamente la **copia privada de Google Sheets de ChatGPT**. El archivo maestro preexistente es solo referencia histórica, no editable por estos experimentos.
3. Ninguna ejecución en esta rama escribirá resultados en la hoja original mediante `actualizar-sec.yml`. Sus pasos de escritura requieren `refs/heads/main` (modificación de seguridad de la rama).
4. Las credenciales de Actions son compartidas por repositorio. **No crear scripts de escritura con secretos a nivel repo; no leer ni registrar secretos; no probar la ruta de producción**. Para independencia de permisos completa, usar dos repositorios separados con secretos separados.
5. No subir a un repositorio público archivos internos de Drive, datos personales, credenciales, contratos, fuentes de pago ni PDFs con derechos reservados.
6. Métricas: `NULL != 0`; distinguir `OK / PROXY / BLOCKED / NA_SECTOR / NULL`; SEC XBRL + accession + fecha por cada cálculo; no promocionar datos bloqueados.
7. Trabajar con PR independiente y **no fusionar** sin comparar resultados A vs B contra un conjunto de casos de prueba congelado y autorización explícita.
8. El piloto real AAPL / MSFT / JPM / ADP / AEP procesó datos SEC, pero **no certificó** las cinco empresas. ADP, AEP y sector financiero siguen requiriendo conciliación.

## Protocolo de comparación

Entregar por cada iteración: commit SHA, lista de ficheros cambiados, test CI y número de pruebas, conjunto de empresas evaluadas, tabla de diferencias por `CIK+period_end+accession+metric`, motivos de bloqueos, fuente y fecha SEC, y cambios sugeridos con evidencia. Comparar sobre el mismo snapshot SEC; no comparar cotizaciones de fechas diferentes.

## Arquitectura estable

`SEC/EDGAR -> candidatos -> QA -> af_core SQLite -> informes`.
`main` conserva el pipeline actual y la web pública; ambas ramas son de investigación. El siguiente paso automático es reconciliar en staging, **no** escribir sobre las tablas financieras históricas.
