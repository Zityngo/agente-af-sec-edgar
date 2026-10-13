#!/usr/bin/env python3
"""MSFT public-source official SEC document collector (no licensed vendor data).

Preserve a manifest of successes/failures. Public archives can throttle cloud hosts;
failed original document downloads remain linked rather than fabricated.
"""
import csv, gzip, hashlib, io, json, os, re, sys, time, urllib.error, urllib.request, zipfile
from pathlib import Path
from datetime import datetime, timezone

CIK="0000789019"
UA=os.environ.get("SEC_USER_AGENT","").strip()
OUT=Path(os.environ.get("MSFT_ARCHIVE_DIR","/tmp/msft_sec_documents"))
TODAY="2026-10-13"
SUB=f"https://data.sec.gov/submissions/CIK{CIK}.json"
FACT=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"
MAX_BYTE=16_000_000
MAX_DOCS=45
def get(url,ua,limit=MAX_BYTE):
 req=urllib.request.Request(url,headers={"User-Agent":ua,"Accept":"text/html,application/json,*/*","Accept-Encoding":"identity"})
 with urllib.request.urlopen(req,timeout=55) as resp:
  kind=resp.headers.get("Content-Type","")
  b=resp.read(limit+1)
  if len(b)>limit:raise ValueError("content exceeds maximum archival size")
  if not b:raise ValueError("empty document")
  return b,kind

def main():
 if "@" not in UA:raise SystemExit("SEC_USER_AGENT secret missing")
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/"SEC").mkdir(exist_ok=True)
 manifest=[]
 subs_raw,typ=get(SUB,UA,8_000_000)
 companyfacts_raw,typ=get(FACT,UA,16_000_000)
 subs=json.loads(subs_raw)
 cf=json.loads(companyfacts_raw)
 if str(subs.get("cik")).zfill(10)!=CIK or str(cf.get("cik")).zfill(10)!=CIK:
  raise ValueError("SEC CIK identity mismatch")
 for key,raw in (("submissions",subs_raw),("companyfacts",companyfacts_raw)):
  (OUT/f"{key}_2026-10-13.json.gz").write_bytes(gzip.compress(raw,9,mtime=0))
  print("SEC_API_ARCHIVED",key,"bytes",len(raw))
 filings=subs["filings"]["recent"]
 rows=[]
 for i,form in enumerate(filings["form"]):
  filed=filings["filingDate"][i]
  if not ("2021-07-01" <= filed <= TODAY):continue
  if form not in ("10-K","10-Q","8-K"):continue
  accession=filings["accessionNumber"][i]
  primary=filings["primaryDocument"][i]
  report_date=filings["reportDate"][i]
  item=filings.get("items",[""]*len(filings["form"]))[i]
  url=f"https://www.sec.gov/Archives/edgar/data/789019/{accession.replace('-','')}/{primary}"
  rows.append({"form":form,"accession":accession,"filing_date":filed,"report_date":report_date,
               "items":item or "","primary_document":primary,"url":url})
 rows.sort(key=lambda x:x["filing_date"],reverse=True)
 fiveks=[r for r in rows if r["form"]=="10-K" and r["report_date"].startswith(tuple(f"{y}-" for y in range(2022,2027)))]
 qs=[r for r in rows if r["form"]=="10-Q" and "2021-07-01" <= r["report_date"] <= "2026-06-30"]  # FY2022 Q1/Q2 close in 2021
 eightks=[r for r in rows if r["form"]=="8-K" and ("2.02" in r["items"] or r["filing_date"]>="2026-06-01")]
 # prioritization: 5 annual K + all 15 interim Q + 2026 K results and selected material 8K
 selected={(r["accession"]):r for r in fiveks+qs+eightks}
 selected=list(selected.values())[:MAX_DOCS]
 print("SEC_DOCUMENT_CANDIDATES",len(selected),"5Y_10K",len(fiveks),"5Y_10Q",len(qs),"8K",len(eightks))
 for i,r in enumerate(selected):
  dest=f"SEC/{r['accession']}_{r['form']}.html"
  entry={**r,"archive_path":dest,"status":"NOT_FETCHED","size_bytes":"","sha256":"","reason":""}
  try:
   blob,mimetype=get(r["url"],UA)
   if b"<html" not in blob[:1000].lower() and b"<!doctype" not in blob[:1000].lower():
    raise ValueError("not an HTML EDGAR primary filing")
   (OUT/dest).write_bytes(blob)
   entry.update(status="ARCHIVED_OFFICIAL_HTML",size_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
  except Exception as exc:
   # SEC sometimes responds with 403 from cloud runners. Keep links and reason,
   # and never mark the inaccessible document as archived.
   entry.update(status="SOURCE_URL_ONLY",reason=(type(exc).__name__ + " " + str(exc))[:150])
  manifest.append(entry)
  if i%10==0:print("DOC_PROGRESS",i+1,"of",len(selected),"archived",sum(x["status"].startswith("ARCHIVED_OFFICIAL") for x in manifest))
  time.sleep(0.35)
 # latest official IR content; do not claim source fetched on failures
 official=[
  ("FY2026_Q4_PRESS","https://www.microsoft.com/en-us/investor/earnings/fy-2026-q4/press-release-webcast"),
  ("FY2026_Q4_CALL_TRANSCRIPT","https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4"),
 ]
 for label,url in official:
  dest=f"OFFICIAL_IR/{label}.html"
  entry={"form":"IR","accession":"","filing_date":"2026-07-29","report_date":"2026-06-30",
         "items":label,"primary_document":"","url":url,"archive_path":dest,"status":"SOURCE_URL_ONLY","size_bytes":"","sha256":"","reason":""}
  try:
   blob,ctype=get(url,"Mozilla/5.0 (compatible; AgenteAFundamental/1.0; official source archival)",8_000_000)
   if b"<html" not in blob[:1500].lower() and b"<!doctype" not in blob[:1500].lower():raise ValueError("unexpected non-HTML")
   (OUT/"OFFICIAL_IR").mkdir(exist_ok=True)
   (OUT/dest).write_bytes(blob)
   entry.update(status="ARCHIVED_OFFICIAL_HTML",size_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
  except Exception as exc:entry["reason"]=(type(exc).__name__+" "+str(exc))[:150]
  manifest.append(entry)
 # Official downloadable earnings pack: slide deck, outlook and financial workbook.
 # Stored privately as GitHub artifact, not committed as public repo content.
 official_assets=[
  ("FY26Q4_Slides.pptx","https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/SlidesFY26Q4.pptx"),
  ("FY26Q4_FinancialStatements.xlsx","https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/FinancialStatementFY26Q4.xlsx"),
  ("FY27Q1_Outlook.pptx","https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/OutlookFY27Q1.pptx"),
  ("FY26Q4_OfficialAssetPackage.zip","https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/FY26Q4-zip"),
 ]
 for filename,url in official_assets:
  dest=f"OFFICIAL_IR_ASSETS/{filename}"
  entry={"form":"IR_ASSET","accession":"","filing_date":"2026-07-29","report_date":"2026-06-30",
         "items":filename,"primary_document":"","url":url,"archive_path":dest,
         "status":"SOURCE_URL_ONLY","size_bytes":"","sha256":"","reason":""}
  try:
   blob,ctype=get(url,"Mozilla/5.0 (compatible; AgenteAFundamental/1.0)",34_000_000)
   if not zipfile.is_zipfile(io.BytesIO(blob)):
    raise ValueError("File not a valid ZIP/OOXML archive")
   (OUT/"OFFICIAL_IR_ASSETS").mkdir(exist_ok=True)
   (OUT/dest).write_bytes(blob)
   entry.update(status="ARCHIVED_OFFICIAL_BINARY",size_bytes=len(blob),
                sha256=hashlib.sha256(blob).hexdigest())
  except Exception as exc:
   entry["reason"]=(type(exc).__name__+" "+str(exc))[:150]
  manifest.append(entry)
 # Full public filing inventory even when heavy original documents not downloaded
 with (OUT/"MSFT_FILINGS_ALL_SEC.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 with (OUT/"MSFT_DOCUMENT_DOWNLOAD_QA.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=manifest[0].keys());w.writeheader();w.writerows(manifest)
 report={"ticker":"MSFT","cik":CIK,"asof":TODAY,"sec_api_snapshot":"live","public_forms_in_inventory":len(rows),
         "five_year_10k":len(fiveks),"five_year_10q":len(qs),"archive_attempts":len(manifest),
         "download_success":sum(x["status"]=="ARCHIVED_OFFICIAL_HTML" for x in manifest),
         "download_failures":sum(not x["status"].startswith("ARCHIVED_OFFICIAL") for x in manifest),
         "by_type":{t:sum(x["status"]=="ARCHIVED_OFFICIAL_HTML" and x["form"]==t for x in manifest) for t in ("10-K","10-Q","8-K","IR")},
         "rules":["never claim failed HTML was archived","raw SEC XBRL downloaded from SEC API",
                  "not used for trading until latest 10-K and investor data reconciled"]}
 (OUT/"ARCHIVE_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
 archive=OUT.parent/"msft_official_source_archive.zip"
 with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for p in sorted(OUT.rglob("*")):
   if p.is_file():z.write(p,p.relative_to(OUT))
 print("OFFICIAL_MSFT_RESULT",json.dumps(report,ensure_ascii=False))
 print("OFFICIAL_MSFT_ARCHIVE",archive,archive.stat().st_size)

if __name__=="__main__":
 main()
