# Piloto SEC EDGAR a Google Sheets maestro

## Alcance y garantías

La descarga SEC existente (actualizar-sec.yml) se complementa con scripts/sec_auto_staging.py.
Solo escribe candidatos en la pestaña SEC_AUTO_STAGING del archivo maestro, nunca en las hojas
SEC_FY_5Y, SEC_Q_5Y, SEC_TTM_500, AF_RATIO_500 o AF_VALORACION_500.

Cada fila se identifica por CIK, periodo, fecha de cierre y accession de SEC. Conserva
el URL oficial, taxonomía/tag, inicio y fin contable, sha256 y estado QA.
No se inventan importes ausentes ni se interpreta un CFO/CapEx semestral como trimestral.
El job diario procesa un lote de aproximadamente 40 empresas, no las 500 al mismo tiempo.

## Activación

**Por defecto NO se escribe en Google Sheets.** La rama puede ser probada sin credenciales.

Para activar la escritura tras revisar la primera previsualización:

1. Crear cuenta de servicio específica en Google Cloud Console y activar Google Sheets API.
2. Compartir UNICAMENTE el Google Sheets maestro con el email client_email de esa cuenta
   de servicio, asignando permisos Editor. No compartir cartera personal ni otros documentos.
3. En GitHub -> Settings -> Secrets and variables -> Actions -> Repository secrets,
   crear GOOGLE_SERVICE_ACCOUNT_JSON con el JSON completo de la cuenta de servicio,
   y GOOGLE_SHEET_ID con el identificador del documento maestro.
4. Crear una Repository variable SEC_SHEETS_ENABLE_WRITE con el valor true.
5. En Actions -> SEC EDGAR - seguimiento diario -> Run workflow, revisar tests, validación
   CIK/SHA256 y resumen STAGING_UPDATED. Comprobar filas en SEC_AUTO_STAGING.
6. Ante incidencias, desactivar SEC_SHEETS_ENABLE_WRITE poniendo false. No tocar el histórico.

Nunca pegar la clave JSON en el chat ni subirla al repositorio. El repositorio es público.

## Pruebas y criterios de cierre

Tests sin red: python -m unittest discover -s scripts -p test_sec_auto_staging.py -v

Etapa 1: datos descargados, CIK y hash comprobados, sin escribir.
Etapa 2: staging en Sheets poblado sin duplicados, con procedencia verificable.
Etapa 3: **pendiente de implementar** promoción de candidatos reconciliados al histórico
y recálculo TTM/ratios de manera transaccional, con versionado y QA por sector.

La existencia de una fila en staging NO certifica una empresa ni actualiza valoraciones.
