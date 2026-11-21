#!/usr/bin/env python3
"""Read-only verify an exact live 879-opportunity provenance label patch.

The source index must not be called a set of confirmed government tenders.
Never send alerts, alter production, or infer URL reachability equals tender evidence.
"""
import argparse
import datetime as dt
import json
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

HOSTS=("https://radar.wmm-hoa.com", "https://wmm-radar.pages.dev")
INDEX_PATH="public/data/opps.json"
WIDGET_PATH="public/widget/index.html"
SAFE_ROW={
    "source_review_status":"individual_notice_unverified",
    "official_notice_verified":False,
    "may_send_business_alert":False,
    "is_live_tender":False,
}
SAFE_ROOT={
    "index_kind":"unverified_country_brief_candidates",
    "verified_official_notice_count":0,
    "automated_customer_alerts_allowed":False,
    "source_evidence_policy":"Not an official tender index. Each source URL, notice issuer, publication and deadline must be confirmed separately.",
}
SUPPORTED=("ko","en","es","fr","ar","vi","id")
MAX_HTTP_BYTES=1_000_000


def read_json(path):
    data=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict):
        raise ValueError("expected_top_level_dictionary")
    return data


def check_patch(baseline,candidate):
    base=Path(baseline)
    cand=Path(candidate)
    old=read_json(base/INDEX_PATH)
    new=read_json(cand/INDEX_PATH)
    before=old.get("items")
    after=new.get("items")
    if not isinstance(before,list) or not isinstance(after,list):
        raise ValueError("missing_array")
    details={
        "same_original_item_count":len(before)==len(after) and len(before)>0,
        "no_baseline_verification_assumptions":not set(SAFE_ROOT).intersection(old),
        "only_expected_root_fields":set(new)==(set(old)|set(SAFE_ROOT)),
        "old_root_fields_unchanged":all(new.get(k)==v for k,v in old.items() if k!="items"),
        "root_flags_fail_closed":all(k in new and new[k]==v for k,v in SAFE_ROOT.items()),
        "each_original_item_preserved":True,
        "each_item_qualified_unverified":True,
        "no_new_direct_sources_invented":True,
    }
    for before_row,after_row in zip(before,after):
        if not isinstance(before_row,dict) or not isinstance(after_row,dict):
            details["each_original_item_preserved"]=False
            details["each_item_qualified_unverified"]=False
            break
        if set(SAFE_ROW).intersection(before_row):
            details["no_baseline_verification_assumptions"]=False
        if {k:v for k,v in after_row.items() if k not in SAFE_ROW}!=before_row:
            details["each_original_item_preserved"]=False
        if set(after_row)!=(set(before_row)|set(SAFE_ROW)) or any(after_row.get(k)!=v for k,v in SAFE_ROW.items()):
            details["each_item_qualified_unverified"]=False
        if any(k in after_row and k not in before_row for k in ("url","source_url","official_notice_url")):
            details["no_new_direct_sources_invented"]=False
    oldw=(base/WIDGET_PATH).read_text(encoding="utf-8")
    neww=(cand/WIDGET_PATH).read_text(encoding="utf-8")
    details.update({
        "old_widget_preserved_header_and_links":('id="more"' in oldw and 'id="more"' in neww and '/data/opps.json' in neww),
        "all_seven_translations":all(lang+":" in neww for lang in SUPPORTED),
        "visible_source_warning":'id="source-disclaimer" role="note"' in neww,
        "strict_policy_guard":'o.index_kind!=="unverified_country_brief_candidates"' in neww
                              and 'o.verified_official_notice_count!==0' in neww
                              and 'o.automated_customer_alerts_allowed!==false' in neww
                              and 'o.items.some(x=>x.official_notice_verified!==false||x.may_send_business_alert!==false)' in neww,
        "unverified_deadlines_hidden":'x.official_notice_verified===true&&x.deadline?' in neww,
        "safe_title_rendering_retained":'li.querySelector(".t").textContent=' in neww,
        "widget_does_not_send":not any(x in neww for x in ("fetch('/api/email'","sendmail(","sendgrid","payment-intent")),
    })
    return {"record_count":len(before),"candidate_record_count":len(after),
            "checks":details,"pass":all(details.values()),
            "original_index_preserved":details["each_original_item_preserved"],
            "alert_eligible_count":sum(x.get("may_send_business_alert") is True for x in after if isinstance(x,dict))}


def get_public(url):
    # This is a bounded, fixed-host read-only check, not an availability guarantee.
    req=urllib.request.Request(url,headers={
        "User-Agent":"WMM-Opportunity-Source-Integrity-ReadOnly/1.0",
        "Cache-Control":"no-cache",
    },method="GET")
    with urllib.request.urlopen(req,timeout=12) as resp:
        if resp.status!=200 or resp.geturl()!=url:
            raise ValueError("wrong_host_redirect_or_status")
        data=resp.read(MAX_HTTP_BYTES+1)
        if len(data)>MAX_HTTP_BYTES:
            raise ValueError("response_too_large")
        return data.decode("utf-8","replace")


def public_one(host):
    out={"host":host,"kind":"public_readonly","status":"UNVERIFIED","http_check_failed":False}
    try:
        index=json.loads(get_public(host+"/data/opps.json"))
        widget=get_public(host+"/widget/")
        rows=index.get("items")
        if not isinstance(rows,list):
            raise ValueError("invalid_index")
        out["record_count"]=len(rows)
        out["all_items_flagged"]=all(isinstance(x,dict) and all(x.get(k)==v for k,v in SAFE_ROW.items()) for x in rows)
        out["root_policy_correct"]=all(index.get(k)==v for k,v in SAFE_ROOT.items())
        out["widget_warning_visible"]='id="source-disclaimer" role="note"' in widget
        out["status"]="PUBLIC_POLICY_VISIBLE" if all([
            out["all_items_flagged"],out["root_policy_correct"],out["widget_warning_visible"]
        ]) else "PUBLISH_NOT_APPLIED"
    except (OSError,ValueError,KeyError,json.JSONDecodeError,urllib.error.URLError,TimeoutError) as e:
        out["status"]="UNREACHABLE_OR_UNVERIFIABLE"
        out["error_type"]=type(e).__name__
        out["http_check_failed"]=True
    return out


def run(baseline,candidate,probe=False):
    patch=check_patch(baseline,candidate)
    public=[public_one(host) for host in HOSTS] if probe and patch["pass"] else []
    return {
        "schema":"wmm.live-unverified-opportunity-review.v1",
        "generated_at_utc":dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "release_patch":patch,
        "public":public,
        "public_policy_verified":bool(public) and all(x["status"]=="PUBLIC_POLICY_VISIBLE" for x in public),
        "site_modified":False,"customer_alerts_sent":False,"api_billing_started":False,
        "conclusion":"PATCH_TEST_FAILED" if not patch["pass"] else "PUBLIC_RELEASE_NOT_VERIFIED" if not (public and all(x["status"]=="PUBLIC_POLICY_VISIBLE" for x in public)) else "PUBLIC_POLICY_VISIBLE",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",required=True)
    p.add_argument("--candidate",required=True)
    p.add_argument("--probe",action="store_true")
    p.add_argument("--out")
    a=p.parse_args()
    report=run(a.baseline,a.candidate,a.probe)
    if a.out:
        dest=Path(a.out)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({
        "patch_safe":report["release_patch"]["pass"],
        "records_preserved":report["release_patch"]["record_count"],
        "alert_eligible":report["release_patch"]["alert_eligible_count"],
        "public_release":report["conclusion"],
        "modified_site":False,
    },ensure_ascii=False))
    return 0 if report["release_patch"]["pass"] else 2


if __name__=="__main__":
    raise SystemExit(main())
