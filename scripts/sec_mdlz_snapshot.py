"""Read official MDLZ companyfacts, as filed before 2026-10-26. Source dataset for independent peer comparison."""
import json,os,pathlib
from sec_backtest20_snapshot import sec,TAGS
tick,cik="MDLZ",1103982
raw=sec(cik)
d={"cik":cik,"entityName":raw.get("entityName"),"cutoff":"2026-10-25","us-gaap":{},"dei":{}}
for ns in ("us-gaap","dei"):
 for tag,item in raw.get("facts",{}).get(ns,{}).items():
  if tag not in TAGS and tag!="EntityCommonStockSharesOutstanding":continue
  units={}
  for unit,values in item.get("units",{}).items():
   xs=[{k:v[k] for k in ("start","end","val","accn","fy","fp","form","filed","frame") if k in v} for v in values if "2019-01-01"<=v.get("end","")<="2026-10-25" and v.get("filed","")<="2026-10-26" and v.get("form") in ("10-K","10-Q","10-K/A","10-Q/A")]
   if xs:units[unit]=xs
  if units:d[ns][tag]={"units":units,"label":item.get("label")}
p=pathlib.Path("publico/af_backtest20");p.mkdir(parents=True,exist_ok=True)
(p/"mdlz_sec_companyfacts_2026_10_25.json").write_text(json.dumps(d),encoding="utf-8")
print("MDLZ",cik,len(d["us-gaap"]),"TAGS; latest",max((v.get("filed","") for x in d["us-gaap"].values() for ys in x["units"].values() for v in ys),default="no date"))
