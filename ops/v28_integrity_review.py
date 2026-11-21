#!/usr/bin/env python3
"""WMM GOV RADAR v28: read-only country/source and opportunity review queues.

Nothing in this script verifies an actual procurement notice, sends an alert,
updates site data, invokes a paid API, or changes a completed-country flag.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
import ipaddress

SOURCE_SLOTS = {"government": 3, "news": 3, "environment": 1, "weather": 1, "emergency": 1}
SOURCE_PER_COUNTRY = sum(SOURCE_SLOTS.values())
KNOWN_KINDS = {"biz", "oda", "tenders"}

def day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        parsed = date.fromisoformat(value)
        return parsed if parsed.isoformat() == value else None
    except ValueError:
        return None

def website_url(value):
    if not isinstance(value,str) or len(value)>2048 or any(ord(c)<32 for c in value):
        return False
    try:
        u=urlsplit(value)
        if u.scheme!="https" or not u.hostname or u.username or u.password or u.fragment or u.port not in (None,443):
            return False
        try:
            ipaddress.ip_address(u.hostname)
            return False
        except ValueError:
            return "." in u.hostname
    except ValueError:
        return False

def stable_ref(iso, kind, title, index):
    raw="|".join([str(iso or ""),str(kind or ""),str(title or ""),str(index)])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]

def safe_csv_cell(value):
    txt="" if value is None else str(value)
    # Avoid spreadsheet formula interpretation in downloaded review reports.
    return "'"+txt if txt.lstrip().startswith(("=","+","-","@")) else txt

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def inspect(root, as_of, candidates=None):
    root=Path(root)
    if isinstance(as_of,str):as_of=day(as_of)
    if not as_of: raise ValueError("as_of must be a valid YYYY-MM-DD")
    countries=read_json(root/"data/countries.json")
    opportunities=read_json(root/"data/opps.json")
    regions=read_json(root/"data/regions.json")
    if not isinstance(countries,list) or len(countries)!=193:raise ValueError("Expected 193 unique country records")
    codes=[row.get("iso") for row in countries]
    if len(set(codes))!=193 or any(not isinstance(x,str) or not re.fullmatch("[A-Z]{2}",x) for x in codes):
        raise ValueError("Invalid/duplicate country codes")
    if not isinstance(regions,list):raise ValueError("regions.json should be a list")
    region_codes={r.get("code") for r in regions}
    if not isinstance(opportunities,dict) or not isinstance(opportunities.get("items"),list):
        raise ValueError("opps.json missing items array")
    source_candidates=(candidates or {}).get("sources",[])
    if not isinstance(source_candidates,list):raise ValueError("Candidate sources must be an array")
    accepted=[]; candidate_flags=[]; seen=set()
    for source in source_candidates:
        if not isinstance(source,dict): candidate_flags.append("INVALID_ROW"); continue
        iso=source.get("iso"); role=source.get("category"); url=source.get("url")
        sid=source.get("id")
        if iso not in codes or role not in SOURCE_SLOTS or not website_url(url) or not sid or sid in seen:
            candidate_flags.append("BAD_COUNTRY_ROLE_URL_OR_DUPLICATE_ID");continue
        seen.add(sid)
        # Web research supports candidacy only. Human editorial approval is separate.
        if source.get("status")!="CANDIDATE":
            candidate_flags.append("STATUS_NOT_CANDIDATE");continue
        accepted.append(source)
    if candidate_flags:
        raise ValueError("Candidate registry invalid: "+",".join(candidate_flags))
    by_iso=defaultdict(lambda:Counter())
    for x in accepted:by_iso[x["iso"]][x["category"]]+=1
    profiles={p.stem for p in (root/"data/c").glob("??.json")}
    country_queue=[]; task_rows=[]
    for c in countries:
        code=c["iso"]; present=code in profiles; missing=not present
        candidate_count=sum(by_iso[code].values())
        country_queue.append({
            "iso":code,"country_ko":c.get("names",{}).get("ko"),"country_en":c.get("names",{}).get("en"),
            "profile_exists":present,"legacy_done":c.get("done") is True,
            "candidate_urls":candidate_count,
            "source_slots_required":SOURCE_PER_COUNTRY,
            "source_slots_editorially_verified":0,
            "country_ready_for_live":False,
            "next_step":"CREATE_PROFILE_REVIEW_ONLY" if missing else "VERIFY_EXISTING_PROFILE_PROVENANCE"
        })
        if missing:
            for category,quantity in SOURCE_SLOTS.items():
                for n in range(1,quantity+1):
                    task_rows.append({"iso":code,"country_ko":c.get("names",{}).get("ko"),
                        "category":category,"slot":n,"candidate_count_in_category":by_iso[code][category],
                        "verification_status":"UNVERIFIED","source_url":"","editor":"","reviewed_at":"",
                        "publication_status":"NOT_APPROVED"})
    opp_rows=[]; kind_counts=Counter(); status_counts=Counter(); missing_sources=0
    missing_deadlines=0; stale=0; snapshot=day(opportunities.get("updated"))
    source_dates=[]; bad_codes=[]; expired=0; future=0
    for pos,x in enumerate(opportunities["items"],1):
        if not isinstance(x,dict):raise ValueError(f"Opportunity row {pos} must be object")
        iso=x.get("iso");kind=x.get("kind")
        title=x.get("ko") or x.get("en") or ""
        url=x.get("source_url") or x.get("sourceUrl") or x.get("url") or None
        deadline=day(x.get("deadline"))
        if iso not in set(codes)|region_codes:bad_codes.append(iso)
        if kind not in KNOWN_KINDS:raise ValueError(f"Opportunity {pos} has unexpected kind")
        kind_counts[kind]+=1
        if not website_url(url):missing_sources+=1
        if not x.get("deadline"):missing_deadlines+=1
        if deadline and deadline<as_of:expired+=1
        if deadline and deadline>=as_of:future+=1
        # Deliberate conservative stage: URL alone is not authoritative proof.
        if not website_url(url): status="NEEDS_PRIMARY_SOURCE"
        else: status="SOURCE_LINK_REVIEW_REQUIRED"
        if deadline and deadline<as_of:status+="_PAST_DEADLINE"
        elif not deadline:status+="_DEADLINE_UNVERIFIED"
        status_counts[status]+=1
        source_dates.append(x.get("u"))
        opp_rows.append({
            "review_id":stable_ref(iso,kind,title,pos),"source_row":pos,"iso":iso,
            "kind":kind,"title_ko":x.get("ko",""),"title_en":x.get("en",""),
            "deadline":x.get("deadline",""),"recorded_update":x.get("u",""),
            "source_url":url or "","status":status,"editor_verified":False,
            "may_publish_as_official":False,"may_send_business_alert":False
        })
    return {
        "summary":{
            "as_of":as_of.isoformat(),"country_total":len(countries),
            "country_profiles_existing":sum(x["profile_exists"] for x in country_queue),
            "country_profiles_missing":sum(not x["profile_exists"] for x in country_queue),
            "missing_country_source_tasks":len(task_rows),
            "required_per_missing_country":SOURCE_SLOTS,
            "candidate_source_urls":len(accepted),"editorially_verified_new_sources":0,
            "opportunity_snapshot_updated":opportunities.get("updated"),
            "opportunity_snapshot_age_days":(as_of-snapshot).days if snapshot else None,
            "opportunity_total":len(opp_rows),"opportunity_kinds":dict(kind_counts),
            "opportunities_missing_primary_source":missing_sources,
            "opportunities_missing_deadline":missing_deadlines,
            "opportunities_expired_by_recorded_deadline":expired,
            "opportunities_with_future_or_current_deadline":future,
            "opportunity_status_counts":dict(status_counts),
            "opportunities_unknown_country_codes":sorted(set(bad_codes)),
            "operational_publication_authorized":False,
            "note":"A link or existing country profile is not independent validation. Unreviewed rows must not be advertised as real-time official procurement or trigger alerts."
        },
        "missing_countries":[x for x in country_queue if not x["profile_exists"]],
        "source_tasks":task_rows,
        "opportunity_review_rows":opp_rows,
        "source_candidates":accepted
    }

def write_csv(path,rows,columns):
    with open(path,"w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=columns,extrasaction="ignore")
        writer.writeheader()
        for x in rows:writer.writerow({k:safe_csv_cell(x.get(k)) for k in columns})

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root",type=Path,default=Path("."))
    parser.add_argument("--sources",type=Path,default=None)
    parser.add_argument("--as-of",default=date.today().isoformat())
    parser.add_argument("--out-dir",type=Path,default=Path("audit-results/v28"))
    args=parser.parse_args()
    root=args.repo_root.resolve()
    target=(root/args.out_dir).resolve()
    if not target.is_relative_to(root/"audit-results"):
        raise ValueError("Results can only be written below audit-results/")
    if target.is_symlink():raise ValueError("Symlink target forbidden")
    candidates=read_json(args.sources) if args.sources else {"sources":[]}
    report=inspect(root,args.as_of,candidates)
    target.mkdir(parents=True,exist_ok=True)
    (target/"summary.json").write_text(json.dumps(report["summary"],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    write_csv(target/"missing_countries.csv",report["missing_countries"],[
        "iso","country_ko","country_en","profile_exists","legacy_done","candidate_urls","source_slots_required","source_slots_editorially_verified","next_step"])
    write_csv(target/"source_tasks.csv",report["source_tasks"],[
        "iso","country_ko","category","slot","candidate_count_in_category","source_url","verification_status","editor","reviewed_at","publication_status"])
    write_csv(target/"opportunities_draft_review.csv",report["opportunity_review_rows"],[
        "review_id","source_row","iso","kind","title_ko","title_en","deadline","recorded_update","source_url","status","may_publish_as_official","may_send_business_alert"])
    print(json.dumps(report["summary"],ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
