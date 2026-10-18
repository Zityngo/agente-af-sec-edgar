"""SEC Form 4 public XML reader. Supplemental observations, not investment signals.

Never count options exercises, tax withholding or grants as open-market buys.
No full XML or names are committed to public GitHub; use source filing URLs.
"""
from __future__ import annotations
import urllib.request
import xml.etree.ElementTree as ET
import re
from urllib.parse import urlsplit,urlunsplit

EVENTS={"P":"Compra (código P)","S":"Venta (código S)",
        "A":"Concesión/adjudicación","M":"Ejercicio o conversión","F":"Retención fiscal"}
def _text(el,path):
    q=el.find(path) if el is not None else None
    return q.text.strip() if q is not None and q.text else None

def parse_form4_xml(data,source_url="",accession=""):
    root=ET.fromstring(data)
    if root.tag.split("}")[-1]!="ownershipDocument":
        raise ValueError("Not an SEC Form 4 ownershipDocument")
    issuer=_text(root,"./issuer/issuerTradingSymbol")
    owners=[_text(a,"./reportingOwnerId/rptOwnerName") for a in root.findall("./reportingOwner")]
    owners=[x for x in owners if x]
    transactions=[]
    for table,kind in (("nonDerivativeTable","SHARE"),("derivativeTable","DERIVATIVE")):
        for node in root.findall("./"+table+"/*"):
            if node.tag.split("}")[-1] not in ("nonDerivativeTransaction","derivativeTransaction"):continue
            c=_text(node,"./transactionCoding/transactionCode")
            def number(s):
                try:return float(s) if s not in (None,"") else None
                except (ValueError,TypeError):return None
            entry={"kind":kind,"code":c,"label":EVENTS.get(c,"Código a revisar"),
                "date":_text(node,"./transactionDate/value"),
                "shares":number(_text(node,"./transactionAmounts/transactionShares/value")),
                "price":number(_text(node,"./transactionAmounts/transactionPricePerShare/value")),
                "acq_disposal":_text(node,"./transactionAmounts/transactionAcquiredDisposedCode/value"),
                "direct_indirect":_text(node,"./ownershipNature/directOrIndirectOwnership/value"),
                "security":_text(node,"./securityTitle/value"),
                "open_market":kind=="SHARE" and c in ("P","S"),
                "plan_10b5_1_confirmed":None}
            # XML-only source lacks all optional footnote narrative and plan context.
            transactions.append(entry)
    return {"issuer":issuer,"owners":owners,"transactions":transactions,
            "source_url":source_url,"accession":accession,"status":"PARSED_NOT_CERTIFIED"}

def raw_form4_url(url):
    """The SEC submissions primaryDocument can include an XSL transform subfolder.
    Strip only the official xslF345XNN directory to request the real XML source."""
    p=urlsplit(url)
    if p.scheme!="https" or p.hostname!="www.sec.gov" or "/Archives/edgar/data/" not in p.path:
        raise ValueError("Untrusted SEC Form 4 URL")
    path=re.sub(r"/xslF345X[0-9]+/","/",p.path,flags=re.IGNORECASE)
    if not path.lower().endswith(".xml"):raise ValueError("Form 4 filing must be XML")
    return urlunsplit((p.scheme,p.netloc,path,"",""))

def fetch_recent_form4(filings,ticker,limit=5,fetch=None,user_agent=None):
    """Select the newest SEC filings; record any fetch/parse errors, never guess."""
    def _http(url):
        req=urllib.request.Request(url,headers={"User-Agent":user_agent or "AFundamental-Research-Agent/1.0",
                 "Accept":"application/xml","Accept-Encoding":"identity"})
        with urllib.request.urlopen(req,timeout=40) as r:return r.read()
    fetch=fetch or _http
    out=[]
    for entry in [x for x in filings if x.get("form") in ("4","4/A")][:limit]:
        try:
            raw_url=raw_form4_url(entry["url"])
            parsed=parse_form4_xml(fetch(raw_url),raw_url,entry["accession"])
            if parsed["issuer"] and parsed["issuer"].upper()!=ticker:
                parsed["status"]="BLOCKED_TICKER_MISMATCH"
            out.append(parsed)
        except Exception as e:
            out.append({"source_url":entry["url"],"accession":entry["accession"],
                        "status":"UNAVAILABLE","reason":type(e).__name__+":"+str(e)[:120],
                        "transactions":[]})
    return out
