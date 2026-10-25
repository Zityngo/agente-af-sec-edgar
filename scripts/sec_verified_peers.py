"""Comparables GAAP public SEC facts, GM / F / KDP (one latest-window extract)."""
import os,json,time,pathlib
from sec_backtest20_snapshot import sec,TAGS
CO={"GM":1467858,"F":37996,"KDP":1418135}
data={"cutoff":"2026-10-25","companies":{},"errors":{}}
for tick,cik in CO.items():
 try:
  raw=sec(cik);result={"cik":cik,"name":raw.get("entityName"),"us-gaap":{},"dei":{}}
  for ns in ("us-gaap","dei"):
   for tag,x in raw.get("facts",{}).get(ns,{}).items():
    if tag not in TAGS and tag!="EntityCommonStockSharesOutstanding":continue
    units={}
    for unit,entries in x.get("units",{}).items():
     vals=[{k:v[k] for k in ("start","end","val","accn","fy","fp","form","filed","frame") if k in v} for v in entries if v.get("end","")>="2023-01-01" and v.get("end","")<="2026-10-25" and v.get("filed","")<="2026-10-25" and v.get("form") in ("10-K","10-Q","10-K/A","10-Q/A")]
     if vals:units[unit]=vals
    if units:result[ns][tag]={"units":units,"label":x.get("label")}
  data["companies"][tick]=result;print(tick,len(result["us-gaap"]),flush=True)
 except Exception as e:data["errors"][tick]=str(e);print(tick,"ERROR",e,flush=True)
 time.sleep(.25)
p=pathlib.Path("publico/af_backtest20");p.mkdir(parents=True,exist_ok=True)
(p/"peer_tesla_pepsi_public_sec.json").write_text(json.dumps(data))
if data["errors"]:raise RuntimeError(str(data["errors"]))
