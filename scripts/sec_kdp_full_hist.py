"""SEC facts for KDP historical 2021/2022 + later FY (public)."""
import json,pathlib,os
from sec_backtest20_snapshot import sec,TAGS
cik=1418135;raw=sec(cik);out={"cik":cik,"entityName":raw.get("entityName"),"asof":"2026-10-25","us-gaap":{}}
for tag,item in raw.get("facts",{}).get("us-gaap",{}).items():
 if tag not in TAGS:continue
 units={}
 for unit,values in item.get("units",{}).items():
  good=[{k:v[k] for k in ("start","end","val","accn","fy","fp","form","filed","frame") if k in v} for v in values if "2019-01-01"<=v.get("end","")<="2026-10-25" and v.get("filed","")<="2026-10-26" and v.get("form") in ("10-K","10-Q","10-K/A","10-Q/A")]
  if good:units[unit]=good
 if units:out["us-gaap"][tag]={"units":units,"label":item.get("label")}
p=pathlib.Path("publico/af_backtest20");p.mkdir(parents=True,exist_ok=True)
(p/"kdp_sec_full_history_2026_10_25.json").write_text(json.dumps(out))
print("KDP extracted",len(out["us-gaap"]),"tags")
