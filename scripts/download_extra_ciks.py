#!/usr/bin/env python3
import gzip,json,os,time,urllib.request
from pathlib import Path
C={"XOM_CORRECT":"0000034088","CTVA_PREDECESSOR":"0001755672"}
ua=os.environ.get("SEC_USER_AGENT","").strip()
if "@" not in ua: raise SystemExit("SEC_USER_AGENT missing")
out=Path("publico/sec_extra")
for name,cik in C.items():
    base=out/f"CIK{cik}"; base.mkdir(parents=True,exist_ok=True)
    for kind,url in [
      ("submissions",f"https://data.sec.gov/submissions/CIK{cik}.json"),
      ("companyfacts",f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")]:
        req=urllib.request.Request(url,headers={"User-Agent":ua,"Accept":"application/json","Accept-Encoding":"identity"})
        with urllib.request.urlopen(req,timeout=45) as r: raw=r.read()
        obj=json.loads(raw)
        expected="filings" if kind=="submissions" else "facts"
        if not obj.get(expected): raise RuntimeError(f"{name} {kind} missing {expected}")
        (base/f"{kind}.json.gz").write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
        print(name,kind,len(raw))
        time.sleep(0.8)
