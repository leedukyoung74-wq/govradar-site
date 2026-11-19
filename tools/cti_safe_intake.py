#!/usr/bin/env python3
"""WMM defensive CTI intake — CISA KEV ONLY, no darknet access or public publishing.

Outputs bounded, redacted, evidence-linked advisory metadata. This module does
not ingest stolen data, indicators of compromise, emails, passwords, or samples.
Manual internal artifact only: NEVER write to the site's public/data branches.
"""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

CISA_URL="https://raw.githubusercontent.com/cisagov/kev-data/refs/heads/develop/known_exploited_vulnerabilities.json"
OFFICIAL="https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
CVE=re.compile(r"^CVE-[0-9]{4}-[0-9]{4,19}$")
ALLOWED_RANSOM={"Known","Unknown"}
MAX_BYTES=5_000_000
MAX_ROWS=5000
MAX_TEXT=180

def fetch_cisa():
    req=Request(CISA_URL,headers={"User-Agent":"WMM-CTI-safe-intake/0.1 (manual QA)"})
    with urlopen(req,timeout=25) as response:
        if response.url!=CISA_URL: raise ValueError("Source redirect forbidden")
        raw=response.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES: raise ValueError("Feed too large")
    return raw

def clean_text(value):
    s=re.sub(r"[\\r\\n\\t]+"," ",str(value or ""))
    s=re.sub(r"[\\x00-\\x1f\\x7f]","",s)
    # Only keep non-sensitive vendor/product titles from the trusted official feed.
    return s.strip()[:MAX_TEXT]

def normalize(raw,now=None):
    if len(raw)>MAX_BYTES: raise ValueError("Feed too large")
    payload=json.loads(raw)
    if not isinstance(payload,dict) or not isinstance(payload.get("vulnerabilities"),list):
        raise ValueError("Invalid CISA KEV schema")
    records=payload["vulnerabilities"]
    if not 1<=len(records)<=MAX_ROWS: raise ValueError("Unexpected KEV record count")
    if payload.get("count")!=len(records): raise ValueError("Catalog count mismatch")
    names=set()
    today=(now or datetime.now(timezone.utc)).date()
    out=[]
    for v in records:
        if not isinstance(v,dict): raise ValueError("KEV row must be object")
        cve=v.get("cveID")
        if not isinstance(cve,str) or not CVE.fullmatch(cve) or cve in names:
            raise ValueError("Invalid/duplicate CVE")
        names.add(cve)
        try:
            added=date.fromisoformat(v["dateAdded"])
        except (KeyError,TypeError,ValueError):
            raise ValueError("Missing valid dateAdded")
        if added>today: raise ValueError("Future KEV catalog date")
        ransomware=v.get("knownRansomwareCampaignUse","Unknown")
        if ransomware not in ALLOWED_RANSOM: raise ValueError("Unknown ransomware flag")
        out.append({
            "id":cve,
            "vendor":clean_text(v.get("vendorProject")),
            "product":clean_text(v.get("product")),
            "date_added":added.isoformat(),
            "ransomware_reported":ransomware=="Known",
            "evidence_level":"OFFICIAL_CISA_KEV",
            "source_url":OFFICIAL,
            "public_redistribution_approval":"REVIEW_REQUIRED",
            "enterprise_impact":"NOT_ASSESSED",
            "victim_or_outage_confirmed":False,
            "tlp":"CLEAR",
        })
    out.sort(key=lambda v:(v["date_added"],v["id"]),reverse=True)
    return {
        "schema":"wmm-cti-safe-intake.v1",
        "checked_at_utc":(now or datetime.now(timezone.utc)).isoformat(),
        "source_catalog_version":clean_text(payload.get("catalogVersion")),
        "source_date_released":clean_text(payload.get("dateReleased")),
        "source":CISA_URL,
        "source_sha256":hashlib.sha256(raw).hexdigest(),
        "source_entries":len(out),
        "scope":"CISA official known exploited vulnerability metadata. NOT darkweb monitoring.",
        "deployable":False,
        "public_release_allowed":False,
        "cti_vendor_connected":False,
        "victim_identification":False,
        "records":out,
    }

def validate_safe_records(record):
    if record.get("public_release_allowed") is not False:
        raise ValueError("Release gate must default to false")
    if record.get("cti_vendor_connected") is not False:
        raise ValueError("Vendor connection must remain unclaimed")
    for item in record["records"]:
        if set(item)!={"id","vendor","product","date_added","ransomware_reported",
                       "evidence_level","source_url","public_redistribution_approval",
                       "enterprise_impact","victim_or_outage_confirmed","tlp"}:
            raise ValueError("Unsafe fields in record")
        if item["victim_or_outage_confirmed"] is not False:
            raise ValueError("KEV does not certify victim status")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--fixture",type=Path,help="Offline synthetic CISA-like fixture")
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    raw=args.fixture.read_bytes() if args.fixture else fetch_cisa()
    result=normalize(raw)
    validate_safe_records(result)
    output=args.out.resolve()
    if output.exists(): raise ValueError("Output exists: fail closed, never overwrite")
    if "/public/" in str(output).replace("\\\\","/") or "/data_branch/" in str(output).replace("\\\\","/"):
        raise ValueError("Refuse public-site or live-data output")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\\n",encoding="utf8")
    print(f"PASS: {result['source_entries']} KEV entries; internal report only, no public publish")
if __name__=="__main__": main()
