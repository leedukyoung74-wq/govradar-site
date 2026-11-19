#!/usr/bin/env python3
"""Validate CTI-provider readiness. Fail closed; never requests provider APIs."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

EXPECTED={"cisa-kev","socradar","hibp","flare","urlhaus","threatfox","searchlight","recorded-future","hudson-rock"}
FIELDS={"id","provider","category","status","enabled_for_production","automated_collection_approved","permission","source","security_mode","allowed_data","client_redistribution"}
DENIED={"EVALUATION_NOT_CONNECTED","NOT_CONNECTED","ONE_SHOT_TESTED"}
def check(data):
    if not isinstance(data,dict) or data.get("schema")!="wmm-cti-provider-registry.v1":raise ValueError("Unknown registry schema")
    rows=data.get("providers")
    if not isinstance(rows,list) or len(rows)!=len(EXPECTED):raise ValueError("Unexpected provider count")
    ids=[p.get("id") for p in rows if isinstance(p,dict)]
    if set(ids)!=EXPECTED or len(set(ids))!=len(ids):raise ValueError("Missing/duplicate provider")
    for p in rows:
        if set(p)!=FIELDS:raise ValueError("Unknown provider fields or secret payload")
        if p["status"] not in DENIED:raise ValueError("Unreviewed production status")
        if p["enabled_for_production"] is not False or p["automated_collection_approved"] is not False or p["client_redistribution"] is not False:
            raise ValueError("Unapproved CTI live use or resale")
        if p["security_mode"]!="NO_CREDENTIALS":raise ValueError("Credentials must stay out of registry")
        if not (isinstance(p["permission"],str) and ("REQUIRED" in p["permission"] or p["permission"]=="REVIEW_REQUIRED")):
            raise ValueError("Contract or entitlement gate missing")
        u=urlsplit(p["source"])
        if u.scheme!="https" or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError("Unsafe provider source URL")
        if p["id"]!="cisa-kev" and not p["allowed_data"].startswith("NONE_"):
            raise ValueError("No provider payload can be imported before contract")
    return {"schema":"wmm-cti-provider-audit.v1","provider_count":len(rows),"production_enabled":0,
            "auto_collection_approved":0,"redistribution_approved":0,
            "connection":"NO_EXTERNAL_CTİ_VENDOR_CONNECTED".replace("İ","I"),
            "operator_action":"Review official terms, company account entitlement, authorized scope and CEO signoff; rerun audit before any activation."}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--registry",type=Path,default=Path(__file__).resolve().parents[1]/"ops/cti_provider_registry.json")
    args=parser.parse_args()
    d=json.loads(args.registry.read_text(encoding="utf-8"))
    report=check(d)
    print(json.dumps(report,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
