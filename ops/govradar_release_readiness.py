"""GOV RADAR release-readiness audit from local read-only branch snapshots.

This tool never contacts a paid service, edits source files or attempts login.
It distinguishes data-collection success from actual public-site deployment and
flags operations that require an owner-controlled authorized live test.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import hashlib

UTC=dt.timezone.utc


def read(path):
    try:
        return Path(path).read_bytes()
    except (OSError, ValueError):
        return None


def js_same(src, live):
    a,b=read(src),read(live)
    return bool(a is not None and b is not None and hashlib.sha256(a).digest()==hashlib.sha256(b).digest())


def parse_time(s):
    if not isinstance(s,str) or not s:return None
    try:
        d=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
        return d.astimezone(UTC) if d.tzinfo else None
    except (ValueError,OverflowError,TypeError):
        return None


def json_file(path):
    a=read(path)
    if a is None:return None
    try:return json.loads(a)
    except (UnicodeError,ValueError,TypeError):return None


def inspect(src,live,data,now=None):
    src,live,data=map(Path,(src,live,data))
    now=now or dt.datetime.now(UTC)
    if now.tzinfo is None:raise ValueError("now must be timezone-aware")
    records=[]
    def add(name,status,detail):
        records.append({"id":name,"status":status,"detail":detail})
    feed=json_file(data/"feeds"/"cty"/"_summary.json") or {}
    opening=(feed.get("t") or {}).get("n")
    updated=feed.get("updated")
    age=((now-parse_time(updated)).total_seconds()/3600
         if parse_time(updated) else None)
    fresh=isinstance(opening,int) and opening>=0 and age is not None and -0.1<=age<=30
    add("official_tenders", "pass" if fresh else "block",
        {"verified_open":opening,"updated":updated,"age_hours":round(age,2) if age is not None else None})
    raw=json_file(data/"feeds"/"sources_status.json") or {}
    for source,tag in (("UK Find a Tender","uk_fts"),("DAPA (Korea)","kr_dapa"),("SAM.gov (US)","us_sam")):
        item=raw.get(source,{})
        state=item.get("state")
        add(tag, "pass" if state=="SUCCESS" else "block",
            {"source_state":state or "MISSING","last_success":item.get("last_success"),
             "reason":"partial_upstream_or_missing_optional_key" if state in ("PARTIAL","SKIPPED") else "see_public_source_health"})
    homepage=read(live/"public"/"ko"/"index.html")
    html=homepage.decode("utf-8","replace") if homepage is not None else ""
    old=re.search(r'id="kp-t">([0-9][0-9,]*)<',html)
    published=int(old.group(1).replace(",","")) if old else None
    add("public_static_open_count","pass" if fresh and published==opening else "block",
        {"static_open":published,"verified_open":opening,
         "note":"Build-time HTML must match current public data; JS refresh alone is not sufficient."})
    for key,a,b in (("live_auth_js",src/"web"/"auth.js",live/"public"/"assets"/"auth.js"),
                    ("live_form_relay",src/"cf"/"functions"/"nfform.js",live/"functions"/"nfform.js"),
                    ("live_request_api",src/"cf"/"functions"/"api"/"req.js",live/"functions"/"api"/"req.js")):
        matches=js_same(a,b)
        add(key,"pass" if matches else "block",{"code_identical":matches})
    for key,filename,max_minutes in (("nws_source","nws_active.json",180),
                                      ("cisa_kev_source","cisa_kev.json",600)):
        doc=json_file(data/"hz"/filename) or {}
        h=doc.get("source_health") or {}
        stamp=parse_time(h.get("last_ok"))
        age_m=(now-stamp).total_seconds()/60 if stamp else None
        ok=h.get("ok") is True and h.get("stale") is False and age_m is not None and -5<=age_m<=max_minutes
        add(key,"pass" if ok else "block",
            {"source_health_ok":h.get("ok"),"stale":h.get("stale"),
             "age_minutes":round(age_m,1) if age_m is not None else None})
    directory=json_file(src/"src"/"government_business_sites.json")
    count=sum(len(x) for x in directory.get("countries",{}).values()) if isinstance(directory,dict) else 0
    markets=sum(len(x)>=3 for x in directory.get("countries",{}).values()) if isinstance(directory,dict) else 0
    add("national_government_portals","pass" if count>=579 and markets==193 else "block",
        {"official_site_records_in_src":count,"countries_with_3_or_more":markets,
         "minimum_required":579,"target_countries":193,
         "note":"Source-side catalog count only; each link needs separate official evidence."})
    # These require actual owner-controlled test identities, browser and D1/IdP
    # access. Local code or file equality NEVER proves production auth.
    for key,description in (
        ("member_login_authorized","Real Google login/OAuth redirect and server-side membership authorization"),
        ("member_revoke_authorized","Actual role downgrade/lockout and key rotation on safe test accounts"),
        ("buyer_intake_authorized","Synthetic buyer form -> D1 -> inbox/CRM end-to-end delivery"),
        ("mobile_browser_authorized","Cloudflare live URL / mobile 7-language browser tests after release"),
        ("scheduler_24h_evidence","Two or more actual scheduled collect/publish/public readbacks, GitHub cron best-effort"),
    ):
        add(key,"unverified",{"required_proof":description})
    blocks=[x["id"] for x in records if x["status"]=="block"]
    uncertain=[x["id"] for x in records if x["status"]=="unverified"]
    return {"checked_at_utc":now.isoformat(),"result":"NOT_READY" if blocks or uncertain else "READY",
            "blockers":blocks,"unverified":uncertain,"checks":records}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--src",required=True)
    p.add_argument("--live",required=True)
    p.add_argument("--data",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    report=inspect(a.src,a.live,a.data)
    out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"result":report["result"],"blockers":report["blockers"],
                      "unverified":report["unverified"]},ensure_ascii=False))
    # Operational readiness being blocked is a report, not a failed/audited code test.


if __name__=="__main__":
    main()
