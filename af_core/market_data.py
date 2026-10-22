"""Market data quality gate and SEC outstanding-share selector.

Read-only adapter compatible with authenticated IBKR Client Portal Gateway.
No login or orders. Does not redistribute IBKR data and refuses stale,
delayed and frozen ticks when REALTIME is explicitly required.
"""
from __future__ import annotations
import math
import re
import json
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from pathlib import Path

CONTRACTS={"AAPL":265598,"TSLA":76792991,"AMZN":3691937}
FIELDS="31,55,6509"
SEC_SHARE_TAG="EntityCommonStockSharesOutstanding"

def clean_price(s):
    if isinstance(s,(int,float)) and not isinstance(s,bool):
        v=float(s)
    elif isinstance(s,str) and not s.startswith(("C","H")):
        v=float(s.replace(",",""))
    else:raise ValueError("No last trade, price is frozen or halted")
    if not math.isfinite(v) or v<=0:raise ValueError("Invalid price")
    return v

def quote_from_ibkr_snapshot(snapshot, ticker, *, asof=None, require_realtime=True,
                              max_age_seconds=900):
    """Parse IBKR Client Portal's official field 31/6509/_updated."""
    if not isinstance(snapshot,dict):raise ValueError("Snapshot must be an object")
    t=ticker.upper()
    if t not in CONTRACTS or int(snapshot.get("conid",-1))!=CONTRACTS[t]:
        raise ValueError("Unknown/mismatched IBKR contract")
    avail=str(snapshot.get("6509") or "")
    market_status={"R":"REALTIME","D":"DELAYED","Z":"FROZEN",
                   "Y":"FROZEN_DELAYED","N":"NOT_SUBSCRIBED"}.get(avail[:1],"UNKNOWN")
    if require_realtime and market_status!="REALTIME":
        raise ValueError("Not realtime: "+market_status)
    ts=snapshot.get("_updated")
    if not isinstance(ts,(int,float)) or isinstance(ts,bool):
        raise ValueError("Quote timestamp missing")
    now=asof or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("asof timezone required")
    quote_date=datetime.fromtimestamp(ts/1000,timezone.utc)
    age=(now-quote_date).total_seconds()
    if age < -120 or age>max_age_seconds:
        raise ValueError("Stale or future market data")
    return {"ticker":t,"price_usd":clean_price(snapshot.get("31")),
            "market_status":market_status,"last_trade_utc":quote_date.isoformat(),
            "quote_observed_utc":now.astimezone(timezone.utc).isoformat(),
            "source":"IBKR_CLIENT_PORTAL_GATEWAY","license":"PRIVATE_ACCOUNT_VIEW_ONLY",
            "exchange":"SMART","conid":CONTRACTS[t]}

def from_ibkr_gateway(*,gateway="https://localhost:5000/v1/api",
                      fetch=None,now=None, max_age_seconds=900):
    """Query authenticated local IBKR gateway only, no external password.

    The user must authenticate independently. Fail closed if the local gateway
    is not secured/available. A callable fetch is injectable for tests.
    """
    if not gateway.startswith("https://localhost:5000/"):
        raise ValueError("Only local authenticated IBKR gateway accepted")
    conids=",".join(str(CONTRACTS[t]) for t in CONTRACTS)
    url=gateway+"/iserver/marketdata/snapshot?"+urlencode({"conids":conids,"fields":FIELDS})
    if fetch is None:
        import ssl
        # IBKR localhost gateway uses unsigned cert; do not disable TLS
        # certificate verification in a cloud process. Install trusted cert.
        def fetch(address):
            with urlopen(Request(address,headers={"Accept":"application/json"}),timeout=10) as r:
                return json.loads(r.read())
    snapshots=fetch(url)
    if not isinstance(snapshots,list):raise ValueError("Invalid IBKR response")
    by={s.get("conid"):s for s in snapshots if isinstance(s,dict)}
    return {t:quote_from_ibkr_snapshot(by.get(conid),t,asof=now,max_age_seconds=max_age_seconds)
            for t,conid in CONTRACTS.items()}

def sec_latest_shares(companyfacts, *, cutoff_date, earliest_filing=None):
    """Find latest DEI cover shares by reported date and filing date.

    Shares outstanding are NOT weighted-average diluted shares for EPS.
    """
    facts=(companyfacts.get("facts",{}).get("dei",{})
           .get(SEC_SHARE_TAG,{}).get("units",{}).get("shares",[]))
    valid=[]
    cutoff=str(cutoff_date)
    for r in facts:
        if not isinstance(r,dict):continue
        val=r.get("val"); filed=r.get("filed"); end=r.get("end")
        if (not isinstance(val,(int,float)) or isinstance(val,bool) or val<=0
            or not filed or not end or filed>cutoff or end>cutoff
            or (earliest_filing and filed<str(earliest_filing))
            or r.get("form") not in ("10-Q","10-K","10-Q/A","10-K/A")):continue
        valid.append(r)
    if not valid:
        return {"value":None,"status":"BLOCKED","reason":"No DEI shares matching cutoff"}
    p=max(valid,key=lambda r:(r["end"],r["filed"]))
    days=(datetime.fromisoformat(cutoff).date()-datetime.fromisoformat(p["end"]).date()).days
    return {"value":int(p["val"]),"status":"OFFICIAL" if days<=120 else "PROXY_STALE_SHARES",
            "period_end":p["end"],"filed":p["filed"],"accession":p.get("accn"),
            "age_days":days,"tag":SEC_SHARE_TAG,"source":"SEC companyfacts dei"}

def validate_quote_and_shares(quote, shares, *, max_share_age_days=120):
    if shares.get("value") is None or shares.get("age_days",999)>max_share_age_days:
        return {"market_cap_usd":None,"status":"BLOCKED","reason":"Shares stale or absent"}
    return {"market_cap_usd":quote["price_usd"]*shares["value"],
            "status":"CALC_FROM_OFFICIAL_SHARES_REALTIME_QUOTE",
            "price_utc":quote["last_trade_utc"],"shares_period":shares["period_end"],
            "share_count":shares["value"],"reason":"Price and shares do not share exact timestamp"}
