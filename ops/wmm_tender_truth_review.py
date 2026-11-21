#!/usr/bin/env python3
"""GOV RADAR procurement truth audit: never confuse search hits with confirmed open tenders.

Uses canonical src/tools/deadline.py (the same date/UTC-12 rule as site/feed).
Reads existing public live brief index + official feed + country summary.
No scraping, payments, personal data, secret material, alerts, or publishing.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

UTC=dt.timezone.utc
SOURCE_HOSTS={
    "World Bank":"projects.worldbank.org",
    "UK Find a Tender":"www.find-tender.service.gov.uk",
    "EU TED":"ted.europa.eu",
    "Prozorro (Ukraine)":"prozorro.gov.ua",
    "UK Contracts Finder":"www.contractsfinder.service.gov.uk",
}
GOOD_SOURCE_GRADES={"full","date"}
MAX_INPUT_BYTES=3_000_000
MAX_REVIEW_ITEMS=25
ISO_RX=re.compile(r"^[A-Z]{2}$")
DAY_RX=re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_json(path):
    p=Path(path)
    if p.stat().st_size>MAX_INPUT_BYTES:
        raise ValueError("input_too_large")
    v=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(v,dict):
        raise ValueError("expected_json_object")
    return v


def load_deadline_rules(path):
    # Caller supplies existing reviewed source file; does not fetch or execute remote code.
    p=Path(path)
    if p.name!="deadline.py" or p.stat().st_size>25_000:
        raise ValueError("expected_reviewed_deadline_module")
    spec=importlib.util.spec_from_file_location("wmm_reviewed_deadline",p)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if not callable(getattr(m,"state",None)) or not callable(getattr(m,"is_listed_open",None)):
        raise ValueError("missing_canonical_deadline_functions")
    return m


def parse_utc(s):
    if not isinstance(s,str):
        return None
    try:
        x=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
        if x.tzinfo is None: return None
        return x.astimezone(UTC)
    except (ValueError,TypeError,OverflowError):
        return None


def official_url_for_source(row):
    if not isinstance(row,dict):
        return False
    expected=SOURCE_HOSTS.get(row.get("source"))
    if not expected:
        return False
    try:
        p=urlsplit(row.get("url") or "")
        return (p.scheme=="https" and p.hostname==expected and
                p.username is None and p.password is None and
                p.fragment=="" and p.port is None)
    except (ValueError,TypeError):
        return False


def review_id(iso,kind,title,pos):
    return hashlib.sha256(
        (str(iso)+"|"+str(kind)+"|"+str(title)+"|"+str(pos)).encode("utf-8")
    ).hexdigest()[:20]


def audit(live, feed, country, deadline_rules, now=None):
    now=now or dt.datetime.now(UTC)
    if now.tzinfo is None: raise ValueError("now_must_have_timezone")
    now=now.astimezone(UTC)
    brief_rows=live.get("items")
    official_rows=feed.get("items")
    summary_time=parse_utc(country.get("updated"))
    if not isinstance(brief_rows,list) or not isinstance(official_rows,list):
        raise ValueError("missing_source_arrays")
    if len(brief_rows)<200 or len(official_rows)<100:
        raise ValueError("unexpectedly_small_source_dataset")
    if summary_time is None:
        raise ValueError("country_summary_missing_utc_timestamp")
    if type(country.get("t",{}).get("n")) is not int:
        raise ValueError("country_summary_missing_integer_counter")

    # Country analyses and individual procurement notices are completely separate sources.
    # No inferred match from title, country or description is ever a verified tender.
    briefs=[]
    brief_issues=Counter()
    for pos,x in enumerate(brief_rows,1):
        if not isinstance(x,dict): raise ValueError("bad_country_brief_row")
        if x.get("kind")!="tenders":
            continue
        title=x.get("ko") or x.get("en") or ""
        link=x.get("official_notice_url") or x.get("source_url") or x.get("url")
        if not link: brief_issues["MISSING_INDIVIDUAL_OFFICIAL_NOTICE_URL"]+=1
        if not x.get("deadline"): brief_issues["MISSING_DEADLINE"]+=1
        if x.get("may_send_business_alert") is not False: brief_issues["ALERT_PERMISSION_NOT_BLOCKED"]+=1
        if x.get("official_notice_verified") is not False: brief_issues["OFFICIAL_VERIFICATION_NOT_FALSE"]+=1
        if x.get("is_live_tender") is not False: brief_issues["UNVERIFIED_PROMOTED_TO_LIVE_TENDER"]+=1
        briefs.append({
            "review_id":review_id(x.get("iso"),"tenders",title,pos),
            "source_row":pos,"iso":x.get("iso"),"title_ko":x.get("ko"),
            "title_en":x.get("en"),"recorded_deadline":x.get("deadline") or None,
            "primary_notice_url":link if isinstance(link,str) and link.startswith("https://") else None,
            "review_status":"HUMAN_PRIMARY_SOURCE_REQUIRED",
            "customer_notification_allowed":False,
            "official_publication_approved":False,
        })
    if not briefs:
        raise ValueError("no_country_tender_candidates")

    grades,states=Counter(),Counter()
    urls_ok=True
    bad_urls,duplicates,seen=[],[],set()
    for pos,row in enumerate(official_rows,1):
        if not isinstance(row,dict):
            raise ValueError("bad_official_feed_row")
        k=(row.get("source"),row.get("sid") or row.get("url"))
        if k in seen: duplicates.append(pos)
        seen.add(k)
        grades[str(row.get("verify") or "missing")]+=1
        states[deadline_rules.state(row,now)]+=1
        if not official_url_for_source(row):
            urls_ok=False
            bad_urls.append(pos)
    listed_at_snapshot=sum(
        bool(x.get("iso")) and deadline_rules.is_listed_open(x,summary_time)
        for x in official_rows
    )
    listed_now=sum(
        bool(x.get("iso")) and deadline_rules.is_listed_open(x,now)
        for x in official_rows
    )
    stale_count=sum(x.get("stale") is True for x in official_rows)
    # A search result is NEVER an item-level reread of a publisher's status.
    individual_reread_grade=sum(x.get("verify") in GOOD_SOURCE_GRADES and
                                x.get("stale") is not True and
                                deadline_rules.is_listed_open(x,now)
                                for x in official_rows)
    summary_count=country["t"]["n"]
    future_summary=(summary_time-now).total_seconds()>5*60
    invariants={
        "existing_brief_index_declares_no_official_notices":
            live.get("index_kind")=="unverified_country_brief_candidates"
            and live.get("automated_customer_alerts_allowed") is False
            and type(live.get("verified_official_notice_count")) is int
            and live["verified_official_notice_count"]==0,
        "every_tender_brief_is_not_alertable":all(
            x.get("kind")!="tenders" or (
                x.get("official_notice_verified") is False and
                x.get("may_send_business_alert") is False and
                x.get("is_live_tender") is False
            ) for x in brief_rows),
        "actual_official_feed_count_is_consistent":
            type(feed.get("count")) is int and len(official_rows)==feed["count"],
        "no_unapproved_source_hosts":urls_ok,
        "no_duplicate_official_source_ids":not duplicates,
        "summary_count_matches_canonical_deadline_at_summary_time":
            summary_count==listed_at_snapshot,
        "summary_timestamp_not_future":not future_summary,
        "current_listed_not_greater_than_raw":0<=listed_now<=len(official_rows),
    }
    # Date-only deadlines get the conservative UTC-12 policy in canonical
    # site code. They are NOT proof the local-country submission is still accepted.
    ranked=sorted(briefs,key=lambda x:(
        0 if x["recorded_deadline"] else 1,
        x["recorded_deadline"] or "9999-12-31",
        x["iso"] or "",x["source_row"]
    ))
    result={
        "schema":"wmm.tender-truth-review.v1",
        "checked_at_utc":now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode":"READ_ONLY_NO_DEPLOY",
        "country_brief_index":{
            "all_rows":len(brief_rows),
            "tender_candidate_rows":len(briefs),
            "issues":dict(brief_issues),
            "unverified_tender_candidate_count":len(briefs),
            "real_official_tenders_promoted":0,
            "human_review_first_25":ranked[:MAX_REVIEW_ITEMS],
        },
        "official_procurement_feed":{
            "records":len(official_rows),
            "sources":dict(Counter(str(x.get("source") or "") for x in official_rows)),
            "verification_grades":dict(grades),
            "deadline_states_at_check_utc":dict(states),
            "stale_labeled_records":stale_count,
            "individual_record_reread_grade_current":individual_reread_grade,
            "listed_at_country_summary_time":listed_at_snapshot,
            "listed_at_check_time":listed_now,
            "country_summary_reported_count":summary_count,
            "country_summary_updated":country.get("updated"),
            "bad_source_url_row_numbers":bad_urls[:20],
            "duplicate_source_row_numbers":duplicates[:20],
            "date_only_warning_ko":
                "시간대 없이 마감 날짜만 있는 공고는 사이트의 UTC-12 보수 기준으로 잠시 열림 표시될 수 있습니다. 현지 실제 접수 가능 여부와 신청 시각은 공식 원문에서 재확인해야 합니다.",
            "search_grade_warning_ko":
                "verify=search는 원출처 검색 결과이며 개별 공고 상태·접수기한의 재검증 완료를 의미하지 않습니다.",
        },
        "invariants":invariants,
        "all_checks_pass":all(invariants.values()) and
           not any(brief_issues[k] for k in (
               "ALERT_PERMISSION_NOT_BLOCKED","OFFICIAL_VERIFICATION_NOT_FALSE",
               "UNVERIFIED_PROMOTED_TO_LIVE_TENDER")),
        "site_modified":False,"notifications_sent":0,"paid_api_calls":0,
        "customer_business_impact_confirmed":False,
        "country_brief_records_promoted_to_verified_feed":0,
    }
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--live-index",required=True)
    p.add_argument("--tenders",required=True)
    p.add_argument("--country-summary",required=True)
    p.add_argument("--canonical-deadline",required=True)
    p.add_argument("--as-of",help="Timezone-aware timestamp, defaults UTC now")
    p.add_argument("--out")
    a=p.parse_args()
    now=parse_utc(a.as_of) if a.as_of else dt.datetime.now(UTC)
    if now is None: p.error("--as-of must be ISO8601 with offset or Z")
    report=audit(load_json(a.live_index),load_json(a.tenders),
                 load_json(a.country_summary),load_deadline_rules(a.canonical_deadline),now)
    if a.out:
        out=Path(a.out)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    s=report["official_procurement_feed"]
    print(json.dumps({
        "country_brief_tender_candidates":report["country_brief_index"]["tender_candidate_rows"],
        "official_source_records":s["records"],
        "official_summary_reported":s["country_summary_reported_count"],
        "reproduced_canonical_count":s["listed_at_country_summary_time"],
        "verification_grades":s["verification_grades"],
        "deadline_states_now":s["deadline_states_at_check_utc"],
        "all_checks_pass":report["all_checks_pass"],
        "sent_alerts":report["notifications_sent"],"site_modified":False
    },ensure_ascii=False))
    return 0 if report["all_checks_pass"] else 2


if __name__=="__main__":
    raise SystemExit(main())
