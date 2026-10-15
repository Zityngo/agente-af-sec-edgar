# A.Fundamental · MVP core (rama de integración)

Núcleo SQLite + motor único de métricas + QA + API/web de solo lectura. **Reutiliza** `scripts/normalize_sp500_v2.py`
(no re-extrae XBRL) y **no toca** Google Sheets ni `main`.

> Este commit (1/2) añade solo `af_core/`, este README y el workflow de pruebas. Las pruebas, la web y la demo llegan en el commit 2/2; hasta entonces el workflow de pruebas no tiene tests que ejecutar.

## Estado honesto
- En el entorno de desarrollo pasaron 22 pruebas automáticas (casos sintéticos tipo ADP/AEP/ADM, NULL≠0, financieras, rollback, API de solo lectura).
- Datos reales verificados: **solo el CFO de Apple**. Ninguna otra métrica real está validada aún.
- El piloto de 5 empresas (AAPL, MSFT, JPM, ADP, AEP) **no se ha ejecutado**: requiere los datos SEC de tu pipeline.
- Los umbrales de conciliación (0,5 % / 2 %) son provisionales.

## Uso
```bash
python -m af_core build --db data/af.db --annual sp500_annual_5y.csv --quarterly sp500_quarterly_5y.csv --universe universo_sp500.csv
python -m af_core check --db data/af.db --ticker ADP
python -m af_core prices --db data/af.db --csv precios.csv --source "<proveedor>" --license-note "<licencia>"
python -m af_core rollback --db data/af.db --run-id <run_id>
python -m af_core serve --db data/af.db --port 8000
```
CSV de precios: `ticker,date,close,shares` (la SEC no publica cotizaciones; indica fuente y licencia).

## Reglas de diseño
1. Una sola fórmula por métrica: `af_core/metrics.py`. Web, API y Sheets solo leen.
2. NULL = no disponible, nunca 0. Estados: OK / PROXY / BLOCKED / NA_SECTOR / NULL. El screener excluye todo menos OK/PROXY.
3. EBIT solo si `operating_income_method == reported_OperatingIncomeLoss`; si no, EBIT/EBITDA/ROIC/múltiplos quedan BLOCKED.
4. La app abre SQLite con `mode=ro`.

## Riesgos conocidos
- `eps_ttm` es NULL si falta EPS trimestral (el normalizador no calcula el EPS de Q4): hay que añadir acciones diluidas medias al extractor.
- El normalizador carga solo etiquetas concretas de CapEx/EBIT; casos como AEP/ADP se detectan, no se corrigen solos.
- Cobertura del sector financiero basada en el texto del sector de `universo_sp500.csv` (columna no verificada).
- El .db no debe vivir solo como artefacto de Actions (90 días): definir copia de seguridad privada antes de usarlo como base canónica. Hasta conciliar, Google Sheets sigue siendo la base maestra operativa.
