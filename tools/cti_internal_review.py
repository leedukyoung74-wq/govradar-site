#!/usr/bin/env python3
"""Offline, internal-only WMM defensive CTI triage from approved KEV normalization.

Never queries or scans a customer system. No vendor/darkweb feed and no
production publication. Produces a review-required evidence brief only.
"""
import argparse
from datetime import datetime, timezone, timedelta, date
import json
from pathlib import Path
import re
import sys

SCHEMA="wmm-cti-safe-intake.v1"
CVE=re.compile(r"^CVE-\d{4}-\d{4,19}$")
MAX_IN=12_000_000
MAX_AGE=48
ALLOWED={"OFFICIAL_CISA_KEV"}
RECOMMENDATIONS=[
  "Confirm affected vendor/product/version against the official vendor advisory",
  "Inventory authorized systems; prioritize patch or supported mitigation",
  "Verify tested backup/restore, access controls and MFA",
  "Document the owner, next review time and any exceptions",
]
def load(path):
    if path.stat().st_size>MAX_IN: raise ValueError("Input too large")
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict) or obj.get("schema")!=SCHEMA:
        raise ValueError("Unexpected normalized schema")
    if obj.get("deployable") is not False or obj.get("public_release_allowed") is not False or obj.get("cti_vendor_connected") is not False:
        raise ValueError("Illegal publication/provider state")
    records=obj.get("records")
    if not isinstance(records,list) or not 1<=len(records)<=5000 or obj.get("source_entries")!=len(records):
        raise ValueError("Invalid record count")
    for x in records:
        if not isinstance(x,dict) or not CVE.fullmatch(x.get("id","")):
            raise ValueError("Invalid CVE")
        if x.get("evidence_level") not in ALLOWED or x.get("victim_or_outage_confirmed") is not False:
            raise ValueError("Invalid provenance or victim assertion")
        if x.get("public_redistribution_approval")!="REVIEW_REQUIRED":
            raise ValueError("Unexpected release status")
        if x.get("enterprise_impact")!="NOT_ASSESSED" or x.get("tlp")!="CLEAR":
            raise ValueError("Unsafe claim or TLP")
    if len({x["id"] for x in records})!=len(records):
        raise ValueError("Duplicate CVE")
    return obj

def parse_utc(value):
    if not isinstance(value,str): raise ValueError("Missing checked_at_utc")
    result=datetime.fromisoformat(value.replace("Z","+00:00"))
    if result.tzinfo is None: raise ValueError("Naive collection timestamp")
    return result.astimezone(timezone.utc)

def triage(obj,now=None,limit=20):
    if limit<1 or limit>100: raise ValueError("Limit must be 1..100")
    now=now or datetime.now(timezone.utc)
    checked=parse_utc(obj.get("checked_at_utc"))
    age=(now-checked).total_seconds()/3600
    if age< -0.1: raise ValueError("Collection clock is in the future")
    state="STALE_BLOCKED" if age>MAX_AGE else "REVIEW_REQUIRED"
    rows=sorted(obj["records"],key=lambda x:(x["date_added"],x["id"]),reverse=True)
    new=[x for x in rows if 0 <= (now.date()-date.fromisoformat(x["date_added"])).days <=30]
    return {
      "schema":"wmm-cti-internal-review.v1",
      "checked_at_utc":checked.isoformat(),
      "reviewed_at_utc":now.isoformat(),
      "freshness":state,
      "age_hours":round(age,2),
      "age_threshold_hours":MAX_AGE,
      "source_sha256":obj.get("source_sha256"),
      "source":obj.get("source"),
      "source_entries":len(rows),
      "recent_30d_entries":len(new),
      "recent_ransomware_association":sum(x["ransomware_reported"] for x in new),
      "sample_recent_cves":[{"cve":x["id"],"date_added":x["date_added"],"vendor":x["vendor"],"product":x["product"],"ransomware_association":x["ransomware_reported"]} for x in new[:limit]],
      "actions":RECOMMENDATIONS,
      "customer_asset_matching":"DISABLED_UNTIL_SIGNED_AUTHORIZATION",
      "confirmed_customer_breaches":0,
      "public_release_allowed":False,
      "provider_darkweb_connected":False,
      "status":"HUMAN_REVIEW_REQUIRED",
      "next_step":"Approve internal collection policy, then verify exact vendor/product versions with asset owner's written authorization",
    }
def approved_path(path):
    target=path.resolve()
    names={x.lower() for x in target.parts}
    if any(x in names for x in ("public","data_branch","functions","cf","dist")):
        raise ValueError("Never write internal CTI to public/deployment directory")
    if target.exists(): raise ValueError("Output exists, refusing overwrite")
    return target

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--limit",type=int,default=20)
    a=p.parse_args()
    obj=load(a.input)
    report=triage(obj,limit=a.limit)
    if report["freshness"]=="STALE_BLOCKED":
        print("STALE: refusing to produce actionable current-risk report",file=sys.stderr)
        raise SystemExit(2)
    target=approved_path(a.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PASS: internal-only CTI brief: total={report['source_entries']}, recent30d={report['recent_30d_entries']}, no public release")
if __name__=="__main__": main()
