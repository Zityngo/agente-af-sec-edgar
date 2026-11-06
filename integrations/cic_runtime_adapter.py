"""Puente genérico hacia el motor privado CIC Pro; no copia sus fórmulas.
Requiere CIC_ENGINE_PATH con ruta local autorizada del complemento instalado.
No persistencia, sin red, sin operaciones de trading.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

OPERATIONS = {
    "fcf_gross", "net_debt", "enterprise_value", "market_cap",
    "growth_percent", "cagr_percent", "margin_percent", "nopat",
    "return_on_average_percent", "interest_coverage", "leverage",
    "fcff", "fcfe", "fcfe_bridge", "ke", "wacc", "safety",
    "price_with_margin", "maintenance_capex", "ttm", "derive_q4",
}
FLOW_OPERATIONS = {"fcf_gross", "fcfe", "margin_percent", "ttm", "derive_q4"}
STOCK_OPERATIONS = {"net_debt", "enterprise_value"}

def load_engine(path):
    path = Path(path)
    if not path.is_file():
        raise RuntimeError("BLOQUEADO: CIC_ENGINE_PATH no apunta a motor instalado")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("private_cic_engine", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if module.VERSION not in ("0.2.0", "0.2.1"):
        raise RuntimeError("BLOQUEADO: versión no reconocida del motor")
    return module, digest

def execute(engine, payload):
    if set(payload) != {"document", "tasks"}:
        raise ValueError("Contrato requerido: document + tasks")
    doc = payload["document"]
    by_id = engine.validate_document(doc)
    results = []
    for task in payload["tasks"]:
        ids = task.get("input_ids")
        op = task.get("op")
        if op not in OPERATIONS or not isinstance(ids, list) or not ids:
            raise ValueError("Operación no permitida o sin entradas")
        if any(i not in by_id for i in ids):
            raise ValueError("ID de entrada inexistente")
        inputs = [by_id[i] for i in ids]
        kwargs = task.get("kwargs", {})
        if not isinstance(kwargs, dict):
            raise ValueError("kwargs debe ser objeto")
        reason = None
        if any(v["value"] is None or v["status"] in ("BLOQUEADO", "NO DISPONIBLE") for v in inputs):
            reason = "NULL/BLOQUEADO: nunca sustituir por cero"
        elif op in STOCK_OPERATIONS and (
            any(v["kind"] != "STOCK" or v["period"] != "INSTANT" for v in inputs)
            or any((v["end"], v["currency"], v["scale"]) !=
                   (inputs[0]["end"], inputs[0]["currency"], inputs[0]["scale"]) for v in inputs)
        ):
            reason = "Stock no homogéneo: fecha, moneda o escala"
        elif op == "market_cap" and (len(inputs) != 2 or
            inputs[0]["kind"] != "PER_SHARE" or inputs[1]["kind"] != "STOCK" or
            inputs[0]["currency"] != inputs[1]["currency"] or
            inputs[0]["end"] != inputs[1]["end"]):
            reason = "Capitalización: precio y acciones sin fecha/divisa común"
        elif op == "fcff" and len(inputs) == 5:
            monetary = [inputs[i] for i in (0, 2, 3, 4)]
            if any(m["kind"] != "FLOW" or
                   (m["currency"], m["scale"], m["basis"], m["period"], m["start"], m["end"]) !=
                   (monetary[0]["currency"], monetary[0]["scale"], monetary[0]["basis"],
                    monetary[0]["period"], monetary[0]["start"], monetary[0]["end"])
                   for m in monetary):
                reason = "FCFF: flujos monetarios heterogéneos"
        elif op == "fcf_gross" and (
            len(inputs) != 2 or inputs[0]["concept"] != "CFO"
            or inputs[1]["concept"] != "CAPEX_CASH_OUTFLOW"
            or inputs[0]["kind"] != "FLOW" or inputs[1]["kind"] != "FLOW"
        ):
            reason = "FCF exige CFO y CapEx monetarios"
        elif op in FLOW_OPERATIONS and (
            any((v["basis"], v["currency"], v["scale"]) !=
                (inputs[0]["basis"], inputs[0]["currency"], inputs[0]["scale"]) for v in inputs)
            or (op not in ("ttm", "derive_q4") and
                any((v["period"], v["start"], v["end"]) !=
                    (inputs[0]["period"], inputs[0]["start"], inputs[0]["end"]) for v in inputs))
        ):
            reason = "Bases contables, moneda, escala o períodos heterogéneos"
        if reason:
            result = engine.blocked(op, reason, ids)
        else:
            fn = getattr(engine, op)
            if op == "ttm":
                result = fn(inputs, **kwargs)
            elif op == "derive_q4":
                result = fn(inputs[0], inputs[1], **kwargs)
            else:
                result = fn(*(m["value"] for m in inputs), **kwargs)
        if hasattr(result, "to_dict"):
            result = result.to_dict()
        elif isinstance(result, dict):
            result = {k: v.to_dict() if hasattr(v, "to_dict") else v
                      for k, v in result.items()}
        status = result.get("status") if isinstance(result, dict) else None
        if not status and isinstance(result, dict) and isinstance(result.get("value"), dict):
            status = result["value"].get("status")
        results.append({"id": task.get("id"), "op": op, "input_ids": ids,
                        "status": status or "CÁLCULO", "result": result})
    return {"engine_version": engine.VERSION, "schema_version": doc["version"],
            "calculations": results}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, default=os.getenv("CIC_ENGINE_PATH"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.engine:
        raise SystemExit("BLOQUEADO: ruta del motor CIC Pro requerida")
    engine, digest = load_engine(args.engine)
    report = execute(engine, json.loads(args.input.read_text(encoding="utf-8")))
    report["engine_sha256"] = digest
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"version": engine.VERSION, "calculations": len(report["calculations"])}))

if __name__ == "__main__":
    main()
