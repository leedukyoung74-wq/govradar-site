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



def official_https(url):
    """Structural URL screen; this does NOT prove a government's ownership."""
    if not isinstance(url,str) or any(c in url for c in ("\n","\r","\t")):
        return False
    try:
        from urllib.parse import urlsplit
        p=urlsplit(url)
        return (p.scheme=="https" and bool(p.hostname) and p.hostname!="localhost"
                and p.port is None and not p.username and not p.password
                and not p.fragment and " " not in url)
    except (TypeError,ValueError):
        return False


def check_government_catalog(src,now):
    """Verify metadata integrity; never invent external institutional proof."""
    meta=json_file(src/"src"/"countries_meta.json")
    directory=json_file(src/"src"/"government_business_sites.json")
    result={"official_site_records_in_src":0,"countries_with_3_or_more":0,
            "structurally_complete":False,"invalid_records":0,"missing_country_count":193}
    if not isinstance(meta,list) or not isinstance(directory,dict) or directory.get("schema_version")!=1:
        return result
    try:
        isos=[r["iso"] for r in meta]
        if len(isos)!=193 or len(set(isos))!=193 or not all(isinstance(i,str) and len(i)==2 for i in isos):
            return result
    except (TypeError,KeyError):
        return result
    rows_by_iso=directory.get("countries")
    if not isinstance(rows_by_iso,dict) or set(rows_by_iso)-set(isos):
        return result
    valid=0
    covered=0
    invalid=0
    for iso in isos:
        entries=rows_by_iso.get(iso,[])
        if not isinstance(entries,list):
            invalid+=1
            continue
        seen=set()
        for r in entries:
            if not isinstance(r,dict):
                invalid+=1
                continue
            url,ev=r.get("url"),r.get("evidence_url")
            try:
                check_date=dt.date.fromisoformat(r.get("verified_on",""))
            except (ValueError,TypeError):
                check_date=None
            from urllib.parse import urlsplit
            canonical=(urlsplit(url).hostname or "").lower()+urlsplit(url).path.rstrip("/").lower() if official_https(url) else ""
            ok=(bool(canonical) and canonical not in seen and official_https(ev)
                and r.get("verification")=="official_primary"
                and r.get("category") in ("procurement","support","investment")
                and isinstance(r.get("name_ko"),str) and bool(r["name_ko"].strip())
                and isinstance(r.get("name_en"),str) and bool(r["name_en"].strip())
                and check_date is not None and check_date<=now.date())
            if not ok:
                invalid+=1
                continue
            seen.add(canonical)
            valid+=1
        if len(seen)>=3:
            covered+=1
    result.update(official_site_records_in_src=valid,countries_with_3_or_more=covered,
                  invalid_records=invalid,missing_country_count=193-covered,
                  structurally_complete=(valid>=579 and covered==193 and invalid==0))
    return result

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
    gov_sites=check_government_catalog(src,now)
    add("national_government_portals",
        # A structurally complete file never proves an external authority is real.
        "unverified" if gov_sites["structurally_complete"] else "block",
        {**gov_sites,"minimum_required":579,"target_countries":193,
         "note":"Only official_primary entries with dated evidence count. Even a complete catalog needs independent authority/redirect review before release."})
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
