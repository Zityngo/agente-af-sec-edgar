# A.Fundamental · MVP core (rama de integración)

Núcleo SQLite + motor único de métricas + QA + API/web de solo lectura. **Reutiliza** `scripts/normalize_sp500_v2.py`
(no re-extrae XBRL) y **no toca** Google Sheets ni `main`.

## Estado honesto
- 22 pruebas automáticas pasan en el entorno de desarrollo (casos sintéticos tipo ADP/AEP/ADM, NULL≠0, financieras, rollback, API de solo lectura). Falta confirmarlo en GitHub Actions.
- Datos reales verificados: **solo el CFO de Apple** (ver `tests/aapl_real.py`). Ninguna otra métrica real está validada aún.
- El piloto de 5 empresas (AAPL, MSFT, JPM, ADP, AEP) está preparado en `scripts/pilot_5.py` y `.github/workflows/af-pilot-5.yml`, pero **no se ha ejecutado**: lanzarlo a mano con "Run workflow" (requiere el secreto `SEC_USER_AGENT`).
- Los umbrales de conciliación (0,5 % / 2 %) son provisionales. Tickers `SYN*` = sintéticos.

## Uso
```bash
python -m unittest discover -s tests
python scripts/build_demo_db.py
python -m af_core serve --db data/demo.db --port 8000
python -m af_core build --db data/af.db --annual sp500_annual_5y.csv --quarterly sp500_quarterly_5y.csv --universe universo_sp500.csv
python -m af_core check --db data/af.db --ticker ADP
python -m af_core prices --db data/af.db --csv precios.csv --source "<proveedor>" --license-note "<licencia>"
python -m af_core rollback --db data/af.db --run-id <run_id>
```
CSV de precios: `ticker,date,close,shares` (la SEC no publica cotizaciones; indica fuente y licencia).

## Reglas de diseño
1. Una sola fórmula por métrica: `af_core/metrics.py`. Web, API y Sheets solo leen.
2. NULL = no disponible, nunca 0. Estados: OK / PROXY / BLOCKED / NA_SECTOR / NULL. El screener excluye todo menos OK/PROXY.
3. EBIT solo si `operating_income_method == reported_OperatingIncomeLoss`; si no, EBIT/EBITDA/ROIC/múltiplos quedan BLOCKED.
4. La app abre SQLite con `mode=ro`.

## Riesgos conocidos
- `eps_ttm` es NULL si falta EPS trimestral (el normalizador no calcula el EPS de Q4): añadir acciones diluidas medias al extractor.
- El normalizador carga solo etiquetas concretas de CapEx/EBIT; casos como AEP/ADP se detectan, no se corrigen solos.
- Cobertura del sector financiero basada en el texto del sector de `universo_sp500.csv` (columna no verificada).
- El .db no debe vivir solo como artefacto de Actions (90 días): definir copia de seguridad privada. Hasta conciliar, Google Sheets sigue siendo la base maestra operativa.
