#!/usr/bin/env python3
"""Check BM3 v1.7's public GitHub raw feed endpoints. Read-only, no site publish."""
from urllib.request import urlopen, Request
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
import json, os, sys

BASE="https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/"
FEEDS={
    "tenders":"tenders.json",
    "awards":"awards.json",
    "countries":"cty/_summary.json",
    "sources":"sources_status.json"
}
def parse_date(t):
    if not isinstance(t,str):
        raise ValueError("missing updated ISO datetime")
    return datetime.fromisoformat(t.replace("Z","+00:00")).astimezone(timezone.utc)
def check(name,path):
    r={"feed":name,"status":"FAIL","http":None,"cors":"UNKNOWN","updated":None,"count":None,"age_hours":None,"error":None,"notes":[]}
    try:
        req=Request(BASE+path,headers={"Origin":"http://127.0.0.1:8765","User-Agent":"WMM-BM3-v17-readonly-acceptance/1.0"})
        with urlopen(req,timeout=25) as conn:
            r["http"]=conn.status
            r["cors"]=conn.headers.get("Access-Control-Allow-Origin","MISSING")
            raw=conn.read(3_500_001)
            if len(raw)>3_500_000: raise ValueError("oversized feed")
            o=json.loads(raw)
        if not isinstance(o,dict): raise ValueError("not JSON object")
        if name in ("tenders","awards"):
            stamp=parse_date(o.get("updated"))
            count=o.get("count")
            if not isinstance(count,int) or isinstance(count,bool) or count<0: raise ValueError("invalid count")
            rows=o.get("items")
            if not isinstance(rows,list): raise ValueError("invalid items list")
            if name=="tenders" and len(rows)!=count: raise ValueError("tender count does not match items")
            if name=="awards" and (len(rows)>count or (count>0 and len(rows)==0)): raise ValueError("award items exceed count or missing sample")
            if name=="awards" and len(rows)<count: r["notes"].append(f"AWARDS_LIST_CAPPED:{len(rows)}/{count}")
            r.update(updated=o["updated"],count=count,listed=len(rows))
        elif name=="countries":
            stamp=parse_date(o.get("updated"))
            r.update(updated=o["updated"],count=o.get("t",{}).get("n"))
        else:
            if not all(isinstance(x,dict) and "state" in x for x in o.values()):
                raise ValueError("source status record invalid")
            r["count"]=len(o)
            r["notes"]=[f"{k}:{v.get('state')}:{v.get('data_freshness','')}" for k,v in o.items() if v.get("state")!="SUCCESS" or v.get("data_freshness")=="HISTORICAL_SAMPLE"]
            stamp=None
        if stamp:
            age=(datetime.now(timezone.utc)-stamp).total_seconds()/3600
            r["age_hours"]=round(age,2)
            if age < -1: raise ValueError("future timestamp")
            if age > 30: r["notes"].append("DATA_STALE_OVER_30H")
        if r["cors"] not in ("*","http://127.0.0.1:8765"):
            raise ValueError("CORS does not permit BM3 local origin")
        r["status"]="PASS"
    except (ValueError,KeyError,TypeError,HTTPError,URLError,TimeoutError,OSError) as ex:
        r["error"]=f"{type(ex).__name__}: {str(ex)[:160]}"
    return r
def main():
    results=[check(k,p) for k,p in FEEDS.items()]
    print(json.dumps(results,ensure_ascii=False,indent=2))
    s=os.environ.get("GITHUB_STEP_SUMMARY")
    if s:
        with open(s,"a",encoding="utf-8") as f:
            f.write("## WMM BM3 v1.7 — public feed transport QA (read-only)\n\n")
            f.write("| Feed | HTTP | Browser CORS | Count | Updated (UTC) | Age hours | Validation |\n|---|---:|---|---:|---|---:|---|\n")
            for a in results:
                f.write(f"| {a['feed']} | {a['http']} | {a['cors']} | {a['count']} | {a['updated']} | {a['age_hours']} | {a['status']} |\n")
            for a in results:
                if a["notes"] or a["error"]:
                    f.write(f"\n**{a['feed']}**: "+", ".join(a["notes"]+[a["error"]] if a["error"] else a["notes"])+"\n")
            f.write("\nTransport/schema QA does NOT prove that individual tenders are official/open, that public radar.wmm-hoa.com renders them, or that WMM local v1.7 is installed. No credentials, membership data or live site changes.\n")
    if any(x["status"]!="PASS" for x in results): sys.exit(1)
if __name__=="__main__": main()
