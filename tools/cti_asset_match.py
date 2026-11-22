#!/usr/bin/env python3
"""Offline, authorization-gated, *candidate only* matching of KEV product names.

Never scans networks, sends data, confirms compromise, or handles PII.
The local inventory must have a signed authorization reference, but the script
does not verify the authenticity of a signature. Human review is mandatory.
"""
import argparse
import json
from pathlib import Path
import re
from cti_internal_review import load, approved_path, triage

ALLOW_FIELDS={"asset_tag","vendor","product","version"}
MAX_ASSETS=300
def limited(s):
    if not isinstance(s,str) or not 1<=len(s.strip())<=90:
        raise ValueError("Invalid inventory field length")
    if any(x in s.lower() for x in ("@", "http:", "https:", "password", "token", "\n", "\r")):
        raise ValueError("Potential private/inappropriate data in inventory")
    return s.strip()

def read_inventory(path):
    if path.stat().st_size>120_000: raise ValueError("Inventory too large")
    payload=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload,dict) or payload.get("schema")!="wmm-demo-asset-inventory.v1":
        raise ValueError("Unsupported inventory schema")
    if payload.get("authorization")!="EXPLICIT_OWNER_AUTHORIZATION" or not re.fullmatch(r"AUTH-[A-Z0-9-]{8,48}",str(payload.get("authorization_reference",""))):
        raise ValueError("Signed authorization reference required; cannot verify this reference automatically")
    assets=payload.get("assets")
    if not isinstance(assets,list) or not 1<=len(assets)<=MAX_ASSETS:
        raise ValueError("Invalid asset count")
    seen=set()
    for a in assets:
        if not isinstance(a,dict) or set(a)!=ALLOW_FIELDS:
            raise ValueError("Only product inventory without PII is supported")
        for k in ALLOW_FIELDS: limited(a[k])
        if a["asset_tag"] in seen: raise ValueError("Duplicate asset tag")
        seen.add(a["asset_tag"])
    return assets

def match(kev,assets):
    # Exact vendor+product names alone are not enough to verify the vulnerable
    # versions. Every candidate stays uncertain until human vendor advisory review.
    keys={}
    for r in kev["records"]:
        k=(r["vendor"].casefold().strip(),r["product"].casefold().strip())
        keys.setdefault(k,[]).append(r["id"])
    found=[]
    for a in assets:
        ids=keys.get((a["vendor"].casefold().strip(),a["product"].casefold().strip()),[])
        if ids:
            found.append({"asset_tag":a["asset_tag"],"candidate_cve_ids":sorted(ids),
                         "status":"UNVERIFIED_CANDIDATE",
                         "advisory_version_check":"REQUIRED",
                         "confirmed_vulnerable":False,
                         "confirmed_breached":False})
    return {"schema":"wmm-cti-internal-candidate-match.v1",
            "candidate_count":len(found),
            "matched_assets":found,
            "checked_assets":len(assets),
            "public_release_allowed":False,
            "signed_authorization_verified_by_tool":False,
            "manual_authorization_and_vendor_advisory_review":"REQUIRED",
            "disclaimer":"Exact product-name match is not version/patch validation and is not evidence of compromise."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--normalized",required=True,type=Path)
    p.add_argument("--inventory",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    kev=load(args.normalized)
    # Fail closed when official-feed data are stale.
    if triage(kev)["freshness"]!="REVIEW_REQUIRED":
        raise ValueError("Stale official feed")
    assets=read_inventory(args.inventory)
    output=match(kev,assets)
    path=approved_path(args.out)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PASS: candidate product matches={output['candidate_count']}, no confirmation and no public release")
if __name__=="__main__":main()
