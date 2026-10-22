"""Conciliación de 12 BPA con documentos originales del emisor (piloto).

Una comparación con referencias humanas fechadas NO convierte el motor en un
extractor automático general y NO verifica la recurrencia del beneficio.
"""
import json
from pathlib import Path


def load_benchmark(path):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    if obj.get("schema_version")!=1 or obj.get("scope")!="THREE_COMPANY_EPS_BENCHMARK_2026Q2":
        raise ValueError("Benchmark fuera del piloto")
    rows=obj.get("rows")
    if not isinstance(rows,list) or len(rows)<12:
        raise ValueError("Se exigen al menos doce referencias oficiales")
    keys=set()
    for r in rows:
        key=(r["ticker"],r["period_type"],r["period_end"])
        if key in keys or r["ticker"] not in ("AAPL","TSLA","AMZN"):
            raise ValueError("Benchmark duplicado o fuera del piloto")
        keys.add(key)
        if not isinstance(r["eps_diluted_gaap"],(int,float)) or not r["source_url"].startswith("https://"):
            raise ValueError("BPA o fuente no válido")
    return rows


def compare(audits, references):
    data={(r["ticker"],r["period_type"],r["period_end"]):r for r in references}
    result={}
    for ticker in ("AAPL","TSLA","AMZN"):
        audit=audits.get(ticker)
        if not audit or len(audit.get("quarters",[]))!=4:
            raise ValueError(f"{ticker}: faltan cuatro trimestres")
        items=[]
        for q in audit["quarters"]:
            key=(ticker,q["quarter"],q["period_end"])
            ref=data.get(key)
            if ref is None:raise ValueError(f"Sin benchmark {key}")
            value=q.get("eps")
            delta=abs(value-ref["eps_diluted_gaap"]) if value is not None else None
            status="MATCH" if delta is not None and delta<0.005 and q.get("provenance")=="TRACEABLE" else "BLOCKED"
            items.append({"quarter":q["quarter"],"end":q["period_end"],"eps_extracted":value,
                          "eps_official":ref["eps_diluted_gaap"],"delta":delta,"status":status,
                          "source_url":ref["source_url"]})
        result[ticker]={"status":"MATCH" if all(x["status"]=="MATCH" for x in items) else "BLOCKED",
                        "quarters":items}
    if any(x["status"]!="MATCH" for x in result.values()):
        raise ValueError("Discrepancia de BPA trimestral con documentos oficiales: revisar")
    return result
