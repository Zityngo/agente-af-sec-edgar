"""Apple (CIK 0000320193): flujo de caja operativo (CFO) REAL, en millones de USD.

PROCEDENCIA Y VERIFICACIÓN
Fuente: API oficial https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/NetCashProvidedByUsedInOperatingActivities.json
Verificación: el 15/10/2026 se contrastó cada cifra, su accession y su fecha de presentación con la respuesta
COMPLETA de esa API; coinciden las 7. Aviso de historial: una primera consulta devolvió el contenido truncado y estas
cifras se habían escrito antes de poder verlas; la segunda consulta, completa, las confirmó sin cambios.
ALCANCE: solo CFO. No valida ninguna otra métrica de Apple. Reconfirmar con el companyfacts descargado por el pipeline.
"""
M = 1_000_000
def fact(start, end, val, accn, fy, fp, form, filed):
    return dict(start=start, end=end, val=val * M, accn=accn, fy=fy, fp=fp, form=form, filed=filed)

RECORDS = [  # (start, end, val_M, accn, fy, fp, form, filed)
 ("2024-09-29","2024-12-28", 29935,"0000320193-25-000008",2025,"Q1","10-Q","2025-01-31"),
 ("2024-09-29","2025-03-29", 53887,"0000320193-25-000057",2025,"Q2","10-Q","2025-05-02"),
 ("2024-09-29","2025-06-28", 81754,"0000320193-25-000073",2025,"Q3","10-Q","2025-08-01"),
 ("2024-09-29","2025-09-27",111482,"0000320193-25-000079",2025,"FY","10-K","2025-10-31"),
 ("2025-09-28","2025-12-27", 53925,"0000320193-26-000006",2026,"Q1","10-Q","2026-01-30"),
 ("2025-09-28","2026-03-28", 82627,"0000320193-26-000013",2026,"Q2","10-Q","2026-05-01"),
 ("2025-09-28","2026-06-27",116996,"0000320193-26-000020",2026,"Q3","10-Q","2026-07-31"),
]
FACTS = {"us-gaap": {"NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [fact(*r) for r in RECORDS]}}}}
TAGS = [("us-gaap", "NetCashProvidedByUsedInOperatingActivities")]

def quarterly_rows():
    """Trimestres discretos de CFO: Q1 directo; Q2/Q3 = YTD - YTD previo; Q4 FY25 = FY - 9M (derivado)."""
    a = lambda i: RECORDS[i][2]
    return [("2025","Q1","2024-12-28",a(0),RECORDS[0][3]), ("2025","Q2","2025-03-29",a(1)-a(0),RECORDS[1][3]),
            ("2025","Q3","2025-06-28",a(2)-a(1),RECORDS[2][3]), ("2025","Q4","2025-09-27",a(3)-a(2),RECORDS[3][3]),
            ("2026","Q1","2025-12-27",a(4),RECORDS[4][3]), ("2026","Q2","2026-03-28",a(5)-a(4),RECORDS[5][3]),
            ("2026","Q3","2026-06-27",a(6)-a(5),RECORDS[6][3])]
