#!/usr/bin/env python3
"""Read-only GitHub Actions schedule triage. Does not retry, dispatch or publish."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path

POLICIES={
 "WMM GOV RADAR fast official data publishing":(150,"Fast USGS official feed"),
 "WMM Official NWS + CISA KEV public updates":(180,"US NWS/CISA KEV feed"),
 "WMM GOV RADAR hourly public operations watch":(180,"Public health observer"),
 "Scheduled feeds":(2160,"Daily external feeds")
}

def utc_date(value):
    if not value:return None
    try:
        t=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if t.tzinfo is None:return None
        return t.astimezone(timezone.utc)
    except (ValueError,TypeError):return None

def analyze_runs(runs,at):
    if isinstance(at,str):at=utc_date(at)
    if not isinstance(at,datetime) or at.tzinfo is None:raise ValueError("Need timezone-aware as_of")
    if not isinstance(runs,list):raise ValueError("GitHub runs must be array")
    result=[]
    for name,(tolerance_minutes,description) in POLICIES.items():
        events=sorted((r for r in runs if r.get("name")==name and r.get("event")=="schedule"),
            key=lambda r:r.get("created_at") or "",reverse=True)
        latest=events[0] if events else None
        successes=[r for r in events if r.get("status")=="completed" and r.get("conclusion")=="success"]
        newest_ok=successes[0] if successes else None
        last_age=(at-utc_date(latest.get("created_at"))).total_seconds()/60 if latest and utc_date(latest.get("created_at")) else None
        success_age=(at-utc_date(newest_ok.get("created_at"))).total_seconds()/60 if newest_ok and utc_date(newest_ok.get("created_at")) else None
        if latest is None:state="NO_SCHEDULE_RUN"
        elif last_age is None or last_age< -10:state="INVALID_RUN_TIMESTAMP"
        elif latest.get("status")=="completed" and latest.get("conclusion")=="failure":state="LATEST_RUN_FAILED"
        elif success_age is None or success_age>tolerance_minutes:state="NO_RECENT_SUCCESS"
        elif last_age>tolerance_minutes:state="SCHEDULE_OVERDUE"
        elif latest.get("status")!="completed":state="RUN_PENDING"
        else:state="RUN_SUCCESS_RECENT"
        result.append({"name":name,"description":description,
            "allowed_age_minutes":tolerance_minutes,
            "latest_run_id":latest.get("id") if latest else None,
            "latest_run_status":latest.get("status") if latest else None,
            "latest_conclusion":latest.get("conclusion") if latest else None,
            "last_schedule_age_minutes":round(last_age,1) if last_age is not None else None,
            "last_success_age_minutes":round(success_age,1) if success_age is not None else None,
            "state":state,"healthy_run_schedule":state=="RUN_SUCCESS_RECENT",
            "public_data_freshness_verified":False})
    return {"checked_at":at.isoformat(),"monitors":result,
        "all_schedule_checks_healthy":all(x["healthy_run_schedule"] for x in result),
        "important":"Schedule-run success is not proof that the site or published data is fresh. Query source_health and live endpoints separately. No automated recovery or deployment is performed."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True,help="GitHub Actions API response saved locally")
    p.add_argument("--as-of",required=True,help="UTC offset-aware timestamp")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    d=json.loads(args.input.read_text(encoding="utf-8"))
    runs=d.get("workflow_runs") if isinstance(d,dict) else d
    report=analyze_runs(runs,args.as_of)
    if "audit-results" not in args.out.resolve().parts:raise ValueError("Reports must be stored in audit-results")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"states":{x["name"]:x["state"] for x in report["monitors"]},
        "all_schedule_checks_healthy":report["all_schedule_checks_healthy"]},ensure_ascii=False))
if __name__=="__main__":main()
