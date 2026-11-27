#!/usr/bin/env python3
"""Bounded READ ONLY GitHub Actions schedule-evidence audit, not an SLA claim.

Run from the EXISTING hourly operations watch. Two explicit workflow names,
max 8 GitHub API GETs, 24-hour audit window, no extra crons, source API calls,
site deployment or customer access. Reports observed scheduled runs separately
from published data freshness and automatic recovery.
"""
import datetime as dt
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

UTC=dt.timezone.utc
REPO="leedukyoung74-wq/govradar-site"
WORKFLOWS=(
 ("USGS_5MIN","wmm_fast_timer.yml",5),
 ("NWS_CISA_15MIN","wmm_nws_cisa_timer.yml",15),
)
MAX_PAGES=4
MAX_BODY=2_000_000
WINDOW_H=24


def parse_utc(s):
    if not isinstance(s,str):
        return None
    try:
        v=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
        return v.astimezone(UTC) if v.tzinfo else None
    except (ValueError,OverflowError,TypeError):
        return None


def api_get(workflow,page,opener=None,token=""):
    if workflow not in (name for _,name,_ in WORKFLOWS):
        raise ValueError("workflow not allowlisted")
    if type(page) is not int or not 1 <= page <= MAX_PAGES:
        raise ValueError("page out of bounds")
    opener=opener or urllib.request.build_opener()
    url=(f"https://api.github.com/repos/{REPO}/actions/workflows/"
         f"{workflow}/runs?event=schedule&per_page=100&page={page}")
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!="https" or parsed.hostname!="api.github.com":
        raise ValueError("host not allowlisted")
    headers={"User-Agent":"WMM-GOVRADAR-scheduled-run-readonly/1.0",
             "Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28"}
    if token:
        headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(url,headers=headers,method="GET")
    with opener.open(req,timeout=12) as response:
        if response.status!=200:
            raise ValueError("non-200 GitHub metadata response")
        if urllib.parse.urlsplit(response.geturl()).hostname!="api.github.com":
            raise ValueError("unexpected redirect")
        raw=response.read(MAX_BODY+1)
        if len(raw)>MAX_BODY:
            raise ValueError("response too large")
    data=json.loads(raw)
    runs=data.get("workflow_runs")
    if not isinstance(runs,list):
        raise ValueError("invalid workflow metadata")
    return runs


def summarize(name,interval,runs,now):
    start=now-dt.timedelta(hours=WINDOW_H)
    valid=[]
    for r in runs:
        if not isinstance(r,dict) or r.get("event")!="schedule":
            continue
        created=parse_utc(r.get("created_at"))
        if created and start<=created<=now+dt.timedelta(minutes=1):
            valid.append((created,r.get("conclusion"),r.get("status")))
    valid.sort(key=lambda x:x[0])
    timestamps=sorted({x[0] for x in valid})
    last=timestamps[-1] if timestamps else None
    max_gap=max(((b-a).total_seconds()/60 for a,b in
                 zip(timestamps,timestamps[1:])),default=None)
    target=WINDOW_H*60//interval
    observed=len(timestamps)
    known_completed=sum(1 for _,_,status in valid if status=="completed")
    unsuccessful=sum(1 for _,conc,status in valid
                     if status=="completed" and conc!="success")
    # This is observed GitHub schedule invocation coverage, NOT collection,
    # time-to-alert, provider update freshness, or guaranteed cron accuracy.
    ratio=round(observed/target,3) if target else None
    state=("SCHEDULE_GAP_OBSERVED" if not last or
           (now-last).total_seconds()/60 > interval*3 or
           observed < target*.5 or
           (max_gap is not None and max_gap > interval*3)
           else "SCHEDULE_EVENTS_OBSERVED")
    return {
        "name":name, "state":state, "interval_target_minutes":interval,
        "lookback_hours":WINDOW_H, "expected_ideal_invocations":target,
        "observed_distinct_schedule_invocations":observed,
        "observed_over_ideal_ratio":ratio,
        "last_scheduled_age_minutes":None if not last else round((now-last).total_seconds()/60,1),
        "max_inter_invocation_gap_minutes":None if max_gap is None else round(max_gap,1),
        "completed_invocations":known_completed,
        "unsuccessful_completed_invocations":unsuccessful,
        "source_freshness_verified":False,
        "published_feed_readback_verified":False,
        "hard_realtime_SLA_proven":False,
    }


def run(now=None,fetch=api_get):
    now=now or dt.datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("now must have timezone")
    token=os.environ.get("GH_TOKEN","")
    data={}
    for name,workflow,interval in WORKFLOWS:
        found=[]
        error=None
        for page in range(1,MAX_PAGES+1):
            try:
                subset=fetch(workflow,page,token=token)
            except (OSError,ValueError,TypeError,urllib.error.URLError) as exc:
                error=type(exc).__name__
                break
            found.extend(subset)
            if len(subset)<100:
                break
            oldest=parse_utc(subset[-1].get("created_at")) if isinstance(subset[-1],dict) else None
            if oldest and oldest<now-dt.timedelta(hours=WINDOW_H):
                break
        s=summarize(name,interval,found,now)
        if error:
            s["state"]="UNKNOWN_GITHUB_METADATA"
            s["metadata_error_type"]=error
        data[name]=s
    return {
        "scope":"GITHUB_BEST_EFFORT_SCHEDULE_EVENTS_NOT_SOURCE_FRESHNESS",
        "checked_at_utc":now.isoformat(),
        "result":"PENDING" if any(v["state"]!="SCHEDULE_EVENTS_OBSERVED" for v in data.values()) else "PASS_OBSERVED_EVENTS_ONLY",
        "workflows":data,
        "max_api_get_requests":len(WORKFLOWS)*MAX_PAGES,
        "new_schedule_created":False,
        "published_data_modified":False,
        "customer_access":False,
        "real_time_SLA_claimed":False,
    }


def main():
    result=run()
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    step=os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with Path(step).open("a",encoding="utf-8") as fp:
            fp.write("\n## GitHub schedule event evidence (not data freshness): "+result["result"]+"\n\n")
            fp.write("| Source job | Scheduled events in 24h | Ideal events | Latest age (m) | Max gap (m) | Status |\n|---|---:|---:|---:|---:|---|\n")
            for v in result["workflows"].values():
                fp.write("| {name} | {observed_distinct_schedule_invocations} | {expected_ideal_invocations} | {last_scheduled_age_minutes} | {max_inter_invocation_gap_minutes} | {state} |\n".format(**v))
            fp.write("\nGitHub does not guarantee scheduled events. Counts neither promise nor verify current live alerts or website publish latency.\n")
    # A scheduling gap is recorded as PENDING (not an official data FAIL);
    # actual provider/data freshness is separately fail-closed by existing watch.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
