#!/usr/bin/env python3
"""Review-only audit of separate *data* branch feeds; read-only, never sends alerts."""
import argparse
from collections import Counter
from datetime import datetime,date,timezone,timedelta
import json
from pathlib import Path
from urllib.parse import urlsplit

KST=timezone(timedelta(hours=9))
def parse_timestamp(raw, assume_utc=True):
    if not raw or not isinstance(raw,str):return None
    try:
        x=datetime.fromisoformat(raw.replace("Z","+00:00"))
        if x.tzinfo is None:x=x.replace(tzinfo=timezone.utc if assume_utc else KST)
        return x.astimezone(timezone.utc)
    except ValueError:return None

def age_minutes(raw,now,assume_utc=True):
    d=parse_timestamp(raw,assume_utc)
    return round((now-d).total_seconds()/60,1) if d else None

def date_yyyy_mm_dd(s):
    try:return date.fromisoformat(s) if isinstance(s,str) and len(s)==10 else None
    except ValueError:return None

def good_url(raw):
    try:
        p=urlsplit(raw or "")
        return p.scheme=="https" and bool(p.hostname) and not p.username and not p.password
    except (ValueError,TypeError):return False

def read(root,name):
    return json.loads((Path(root)/name).read_text(encoding="utf-8"))
def analyze(data_root,now):
    if isinstance(now,str):now=parse_timestamp(now)
    if now is None:raise ValueError("UTC as-of required")
    tend=read(data_root,"feeds/tenders.json")
    awards=read(data_root,"feeds/awards.json")
    country=read(data_root,"feeds/cty/_summary.json")
    official=read(data_root,"hz/official.json")
    nws=read(data_root,"hz/nws_active.json")
    cisa=read(data_root,"hz/cisa_kev.json")
    arr=tend.get("items",[])
    if not isinstance(arr,list):raise ValueError("tenders items is not a list")
    kinds=Counter(x.get("verify") or "(none)" for x in arr)
    expired=sum(bool(date_yyyy_mm_dd(x.get("deadline")) and date_yyyy_mm_dd(x.get("deadline"))<now.date()) for x in arr)
    links=sum(good_url(x.get("url")) for x in arr)
    missing_links=len(arr)-links
    valid_notice_ids=len({x.get("sid") for x in arr if x.get("sid")})
    fast_age=age_minutes(official.get("usgs_fast_checked"),now,assume_utc=False)
    nws_health=nws.get("source_health",{})
    cisa_health=cisa.get("source_health",{})
    nws_age=age_minutes(nws_health.get("last_ok"),now)
    cisa_age=age_minutes(cisa_health.get("last_ok"),now)
    n_fresh=nws_age is not None and -5<=nws_age<=180 and nws_health.get("ok") is True
    c_fresh=cisa_age is not None and -5<=cisa_age<=600 and cisa_health.get("ok") is True
    f_fresh=fast_age is not None and -5<=fast_age<=120
    report={
      "checked_at_utc":now.isoformat(),
      "tender_feed":{
        "snapshot_updated":tend.get("updated"),
        "snapshot_age_minutes":age_minutes(tend.get("updated"),now),
        "reported_records":tend.get("count"),"displayed_records":len(arr),
        "source_urls_present":links,"source_urls_missing":missing_links,
        "verification_method_counts":dict(kinds),
        "records_with_deadline_before_as_of":expired,
        "unique_source_ids":valid_notice_ids,
        "may_auto_certify_currently_open":False,
        "interpretation":"verify=search or partial is a collector method label, not confirmation that each tender is currently open."
      },
      "country_open_summary":{"updated":country.get("updated"),"reported_open":country.get("t",{}).get("n"),
        "scope_note":"Country summary and tender feed have distinct filters, so counts need not match."},
      "awards":{"updated":awards.get("updated"),"reported_total":awards.get("count"),
        "displayed_items":len(awards.get("items",[])),
        "truncated_for_display":isinstance(awards.get("count"),int) and awards["count"]>len(awards.get("items",[]))},
      "hazards":{"official_checked":official.get("checked"),"usgs_fast_checked":official.get("usgs_fast_checked"),
        "usgs_fast_age_minutes":fast_age,"usgs_fast_fresh_at_check":f_fresh},
      "nws":{"health_flag_in_file":nws_health.get("stale"),"last_success_age_minutes":nws_age,
        "fresh_at_check":n_fresh,"items_displayed":len(nws.get("items",[]))},
      "cisa_kev":{"health_flag_in_file":cisa_health.get("stale"),"last_success_age_minutes":cisa_age,
        "fresh_at_check":c_fresh,"items_displayed":len(cisa.get("items",[])),
        "not_realtime_attack_feed":cisa.get("not_realtime_attack_feed")},
      "alerting_operational_ready":False,
      "caveat":"Separate static opps.json and dynamic data-branch tenders.json. Never label URL presence or verify=search as government-issued open tender validation."
    }
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--as-of",required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    out=a.output.resolve()
    if "audit-results" not in out.parts:raise ValueError("Output must be in audit-results")
    r=analyze(a.data_root,a.as_of)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"tenders":r["tender_feed"],"hazard_fast_fresh":r["hazards"]["usgs_fast_fresh_at_check"],"nws_fresh":r["nws"]["fresh_at_check"]},ensure_ascii=False))
if __name__=="__main__":main()
