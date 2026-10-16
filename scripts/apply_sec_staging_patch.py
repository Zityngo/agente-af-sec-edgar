#!/usr/bin/env python3
"""One-time, fail-closed patch for existing scripts/sec_auto_staging.py.

Run from repo root BEFORE committing any GitHub changes. Abort on unexpected
source version; never silently rewrite different code.
"""
from pathlib import Path
p=Path('scripts/sec_auto_staging.py')
if not p.is_file():raise SystemExit('Run from the existing repo root; source not found')
s=p.read_text(encoding='utf-8')
patches=[
 ('from sec_quarterly_cashflow import isolate_ytd_flow\n',
  'from sec_quarterly_cashflow import isolate_ytd_flow\nfrom sec_tag_resolution import preferred_tags, recover_amendment\n'),
 ('"ni": [("us-gaap", "NetIncomeLoss"), ("ifrs-full", "ProfitLoss")],',
  '"ni": [("us-gaap", "NetIncomeLoss"), ("us-gaap", "ProfitLoss"), ("ifrs-full", "ProfitLoss")],'),
 ('def metric(facts, name, filing):\n    for taxonomy, tag in TAGS[name]:',
  'def metric(facts, name, filing, cik=None):\n    for taxonomy, tag in preferred_tags(cik, name, TAGS[name]):'),
 ('        for filing in recent_forms(subs):\n            values = {}',
  '        for filing in recent_forms(subs):\n            filing, amendment_backfill = recover_amendment(subs, cf["facts"], filing, cik, metric)\n            values = {}'),
 ('                values[name], source = metric(cf["facts"], name, filing)',
  '                values[name], source = metric(cf["facts"], name, filing, cik)'),
 ('            elif filing["kind"] == "Q" and fcf is None:\n                status = "QA_FCF_TRIMESTRAL_FALTANTE"',
  '            elif filing["kind"] == "Q" and fcf is None:\n                status = "QA_FCF_TRIMESTRAL_FALTANTE"\n'
  '            if amendment_backfill:\n                status = "QA_ENMIENDA_PENDIENTE"\n'
  '                evidence["amendment_backfill"] = amendment_backfill\n'
  '            if evidence.get("ni", {}).get("tag") == "ProfitLoss":\n'
  '                status = "QA_BENEFICIO_CONSOLIDADO_NO_ATRIBUIDO"'),
 ('                    "ver trazas_xbrl para los dos accn usados en la resta YTD.")',
  '                    "ver trazas_xbrl para los dos accn usados en la resta YTD.")\n'
  '            if amendment_backfill:\n'
  '                note += " ENMIENDA: datos recuperados del 10-K original; revisar 10-K/A antes de promover."\n'
  '            if cik == "0001381197":\n'
  '                note += " FINANCIERA: ProfitLoss consolidado no equivale al resultado atribuible al accionista común."'),
]
for before,after in patches:
    found=s.count(before)
    if found!=1:raise SystemExit(f'BLOCKED: incompatible upstream content for {before[:55]!r}: found {found}, no file written')
    s=s.replace(before,after,1)
# Test compilability without writing, then atomic replacement.
compile(s,str(p),'exec')
tmp=p.with_suffix('.py.afpatch.tmp')
tmp.write_text(s,encoding='utf-8')
tmp.replace(p)
print('Patched existing SEC staging. IMPORTANT: commit only after reviewing git diff and tests.')
