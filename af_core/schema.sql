PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS schema_info(k TEXT PRIMARY KEY, v TEXT);
INSERT OR IGNORE INTO schema_info VALUES('schema_version','1');
CREATE TABLE IF NOT EXISTS companies(
  cik TEXT PRIMARY KEY, ticker TEXT NOT NULL, name TEXT, sector TEXT,
  is_financial INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS ix_companies_ticker ON companies(ticker);
CREATE TABLE IF NOT EXISTS ingest_runs(
  run_id TEXT PRIMARY KEY, started_utc TEXT, source TEXT, rows_in INTEGER, status TEXT);
CREATE TABLE IF NOT EXISTS periods(
  cik TEXT NOT NULL REFERENCES companies(cik),
  period_type TEXT NOT NULL CHECK(period_type IN('FY','Q1','Q2','Q3','Q4')),
  fiscal_year INTEGER NOT NULL, period_end TEXT NOT NULL,
  accession TEXT, filed TEXT, currency TEXT DEFAULT 'USD',
  derived INTEGER NOT NULL DEFAULT 0,
  revenue REAL, gross_profit REAL, operating_income REAL, net_income REAL, eps_diluted REAL,
  cfo REAL, capex REAL, assets REAL, equity REAL, cash REAL, debt_total REAL,
  da REAL, interest REAL, tax REAL, pretax REAL,
  operating_income_method TEXT, debt_method TEXT, da_method TEXT,
  sources_json TEXT, run_id TEXT,
  PRIMARY KEY(cik, period_type, fiscal_year));
CREATE TABLE IF NOT EXISTS periods_audit(
  audit_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, action TEXT,
  cik TEXT, period_type TEXT, fiscal_year INTEGER, old_row_json TEXT);
CREATE TABLE IF NOT EXISTS metrics(
  cik TEXT NOT NULL, scope TEXT NOT NULL, period_end TEXT NOT NULL, fiscal_year INTEGER,
  metric TEXT NOT NULL, value REAL, status TEXT NOT NULL,
  reason TEXT, definition TEXT, engine_version TEXT,
  PRIMARY KEY(cik, scope, period_end, metric));
CREATE TABLE IF NOT EXISTS checks(
  cik TEXT NOT NULL, check_id TEXT NOT NULL, severity TEXT NOT NULL CHECK(severity IN('BLOCK','WARN','INFO')),
  period_ref TEXT NOT NULL DEFAULT '', detail TEXT,
  PRIMARY KEY(cik, check_id, period_ref));
CREATE TABLE IF NOT EXISTS prices(
  ticker TEXT NOT NULL, price_date TEXT NOT NULL, close REAL NOT NULL, shares REAL,
  currency TEXT DEFAULT 'USD', source TEXT NOT NULL, license_note TEXT,
  PRIMARY KEY(ticker, price_date));
CREATE VIEW IF NOT EXISTS company_quality AS
  SELECT c.cik, c.ticker,
    COALESCE(SUM(k.severity='BLOCK'),0) AS blocks, COALESCE(SUM(k.severity='WARN'),0) AS warns
  FROM companies c LEFT JOIN checks k ON k.cik=c.cik GROUP BY c.cik;
