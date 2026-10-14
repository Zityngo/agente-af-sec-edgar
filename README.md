# Archivo financiero SEC EDGAR — piloto gratuito

**Objetivo:** probar acceso a la API oficial SEC EDGAR desde GitHub Actions con Nike (NKE, CIK 0000320187) y Nu Holdings (NU, CIK 0001691493), sin depender del ordenador del usuario.

Este repositorio es **público** y sólo debe contener datos empresariales que la SEC publique abiertamente. **No incluyas cartera personal, credenciales, posiciones de broker ni documentos privados.**

## Estado

- Descarga SEC y seguimiento diario **operativos**: el 14/10/2026 el workflow descargó 40/40 empresas sin errores de integridad.
- Programación diaria de GitHub Actions **activa**, por lotes de unas 40 empresas (13 lotes para todo el universo).
- Nuevo control **SEC_AUTO_STAGING**: ejecución real 14/10/2026 generó 80 candidatos (40 empresas x máximo FY y último Q) y aprobó cuatro pruebas automáticas; resultados conservados como artefacto SEC.
- Escritura automática en el Google Sheets maestro **DESACTIVADA hasta conceder los permisos seguros a la cuenta de servicio de Google** y habilitar la variable SEC_SHEETS_ENABLE_WRITE. No actualiza aún los fundamentales verificados.
- Manual de activación: [docs/SEC_SHEETS_PILOT.md](docs/SEC_SHEETS_PILOT.md).

## Paso 1 — configurar contacto SEC (secreto)

GitHub: **Settings → Secrets and variables → Actions → New repository secret**.

Nombre: \`SEC_USER_AGENT\`.

Valor: \`AgenteAF-ArchivoFinanciero correo-real-de-contacto@dominio.com\`.

La SEC requiere identificar peticiones automatizadas. El valor permanece como secreto de GitHub, nunca debe escribirse en ficheros públicos. No es una contraseña, y no se sube un token de broker.

## Paso 2 — ejecutar piloto una vez

**Actions → SEC EDGAR - prueba inicial → Run workflow**. Espera al resultado:
- ✅ **ÉXITO**: registros NKE y NU, datos XBRL y un artefacto \`sec-edgar-piloto\` con los JSON comprimidos.
- ❌ **403**: servidores GitHub también bloqueados por SEC; no hay conexión válida todavía.
- ❌ **SEC_USER_AGENT**: secreto ausente o mal configurado.

## Paso 3 — sólo si tiene éxito

Una vez verificada la descarga, activar la revisión diaria y archivar los datos en Google Drive utilizando el índice ya creado. El script está configurado para verificar ambos documentos por compañía: \`submissions\` y \`companyfacts\` completos expuestos por la SEC. La fuente no incluye todos los documentos narrativos, etiquetas personalizadas ni consenso de analistas.

El programa usa sólo Python estándar y no necesita suscripciones ni claves API.


## Módulo FMP Basic (gratuito y opcional)

- Fuente primaria: **SEC EDGAR**. FMP es **un contraste privado** de incidencias, no sustituto de cifras SEC.
- Script de comparación: [scripts/fmp_free_crosscheck.py](scripts/fmp_free_crosscheck.py).
- Pruebas offline: [scripts/test_fmp_free_crosscheck.py](scripts/test_fmp_free_crosscheck.py).
- Documentación 80/20, límites y pasos: [docs/FMP_BASIC_80_20.md](docs/FMP_BASIC_80_20.md).
- Comprobación manual: **Actions → FMP Basic - prueba segura**; exige crear el secreto \`FMP_API_KEY\` en GitHub Actions para hacer peticiones reales.
- La modalidad gratuita publica **250 llamadas/día**, pero **no garantiza acceso a estados históricos ni a todas las empresas**; los endpoints se validan antes de escalar. Sin clave o sin permisos, el agente SEC sigue funcionando.
- No se publican respuestas de FMP ni claves API. No ejecutar scraping o redistribuir datos FMP para la futura web sin licencia.
