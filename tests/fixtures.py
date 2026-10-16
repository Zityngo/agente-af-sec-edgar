"""Generadores de CSV en el formato de scripts/normalize_sp500_v2.py.
Los tickers SYN* son SINTÉTICOS (ni empresas ni cifras reales)."""
import csv, json
COLS = ["cik","ticker","entity","period_type","fiscal_year","period_end","filing_accession","filing_date","currency",
        "revenue","gross_profit","operating_income","net_income","eps_diluted","cfo","capex","assets","equity","cash",
        "debt_total","da","interest","tax","pretax","operating_income_method","debt_method","da_method","source_tags_json"]

def row(cik, tk, ptype, fy, end, **kw):
    r = {c: "" for c in COLS}
    r.update(cik=cik, ticker=tk, entity=kw.pop("entity", "SINTETICO " + tk), period_type=ptype, fiscal_year=fy, period_end=end,
             filing_accession=kw.pop("accn", f"SYN-{fy}-{ptype}"), filing_date=kw.pop("filed", end), currency="USD",
             operating_income_method=kw.pop("oim", "reported_OperatingIncomeLoss"), debt_method="current+noncurrent+short_if_distinct",
             da_method="reported_combined_D&A:X", source_tags_json=json.dumps(kw.pop("src", {})))
    r.update({k: ("" if v is None else v) for k, v in kw.items()})
    return r

def write_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=COLS); w.writeheader(); w.writerows(rows)

QEND = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}

def company_rows(cik, tk, fys=(2023, 2024, 2025), qyears=(2024, 2025), q_scale=0.25, fy_over=None, q_over=None,
                 oim="reported_OperatingIncomeLoss", capex_tag=None, eps_q=True, base=1000.0):
    ann, qr = [], []
    for i, y in enumerate(fys):
        f = base * (1 + 0.1 * i)
        d = dict(revenue=f, gross_profit=f*0.4, operating_income=f*0.2, net_income=f*0.15, eps_diluted=round(f*0.15/100, 4),
                 cfo=f*0.22, capex=f*0.05, assets=f*2, equity=f*1.0, cash=f*0.3, debt_total=f*0.5, da=f*0.04,
                 interest=f*0.01, tax=f*0.05, pretax=f*0.2)
        d.update((fy_over or {}).get(y, {}))
        src = {"capex": {"tag": capex_tag}} if capex_tag else {}
        ann.append(row(cik, tk, "FY", y, f"{y}-12-31", oim=oim, src=src, **d))
    for y in qyears:
        f = base * (1 + 0.1 * list(fys).index(y))
        for q in (1, 2, 3, 4):
            d = dict(revenue=f*q_scale, gross_profit=f*0.4*q_scale, operating_income=f*0.2*q_scale, net_income=f*0.15*q_scale,
                     eps_diluted=(round(f*0.15/100*q_scale, 4) if (eps_q and q < 4) else None), cfo=f*0.22*q_scale,
                     capex=f*0.05*q_scale, assets=f*2, equity=f, cash=f*0.3, debt_total=f*0.5, da=f*0.04*q_scale, interest=f*0.01*q_scale,
                     tax=None, pretax=None)
            d.update((q_over or {}).get((y, q), {}))
            qr.append(row(cik, tk, f"Q{q}", y, f"{y}-{QEND[q]}", oim=oim, **d))
    return ann, qr
