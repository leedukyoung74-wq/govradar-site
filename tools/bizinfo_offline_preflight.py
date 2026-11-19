#!/usr/bin/env python3
"""Offline Bizinfo government-grant XML normalization; no API key, no submission.

Official specification: https://www.bizinfo.go.kr/apiDetail.do?id=bizinfoApi
Endpoint (NOT CALLED): https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do
The agency's XML/RSS fields are retained as evidence-linked candidates.
It does NOT infer eligibility, co-funding, notice amendments or eligibility.
"""
import argparse
from datetime import datetime, timezone, date
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

MAX_BYTES=4_000_000
ITEM_LIMIT=500
SPEC="https://www.bizinfo.go.kr/apiDetail.do?id=bizinfoApi"
PROVIDER="https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
ID=re.compile(r"^PBLN_[0-9]{8,20}$")
ALLOWED_HOSTS={"www.bizinfo.go.kr","bizinfo.go.kr"}
FORM_EXT={"pdf","hwp","hwpx","doc","docx","zip","other","NONE"}
def plain(t,limit=400):
    s=" ".join((t or "").split())
    if any(c in s for c in ("\u0000","\u001b")): raise ValueError("Control character")
    return s[:limit]
def official_url(raw):
    s=plain(raw,700)
    u=urlparse(s)
    if u.scheme!="https" or u.hostname not in ALLOWED_HOSTS or u.username or u.password or u.fragment:
        raise ValueError("Notice URL must be official HTTPS")
    return s
def elem(it,name):
    return "".join(it.find(name).itertext()) if it.find(name) is not None else ""
def parse(xml_bytes,checked=None):
    checked=checked or datetime.now(timezone.utc)
    if len(xml_bytes)>MAX_BYTES: raise ValueError("Response too large")
    if b"<!DOCTYPE" in xml_bytes.upper() or b"<!ENTITY" in xml_bytes.upper():
        raise ValueError("XML DTD and entities forbidden")
    root=ET.fromstring(xml_bytes)
    if root.tag!="rss": raise ValueError("Not a Bizinfo RSS root")
    channel=root.find("channel")
    if channel is None: raise ValueError("Missing RSS channel")
    src=plain(elem(channel,"copyright"),70)
    if src.lower()!="bizinfo":raise ValueError("Unexpected source attribution")
    items=channel.findall("item")
    if not 1<=len(items)<=ITEM_LIMIT:raise ValueError("Empty or unexpectedly large response")
    seen=set(); output=[]
    for it in items:
        rid=plain(elem(it,"seq") or elem(it,"pblancId"),90)
        if not ID.fullmatch(rid) or rid in seen:raise ValueError("Bad or duplicate notice ID")
        seen.add(rid)
        link=official_url(elem(it,"link") or elem(it,"pblancUrl"))
        title=plain(elem(it,"title") or elem(it,"pblancNm"),180)
        if not title:raise ValueError("Missing notice title")
        filename=plain(elem(it,"fileNm"),180)
        ext=filename.rsplit(".",1)[-1].lower() if "." in filename else "NONE"
        ext=ext if ext in FORM_EXT else "other"
        req=plain(elem(it,"reqstDt") or elem(it,"reqstBeginEndDe"),150)
        output.append({
            "source_provider":"BIZINFO_OFFICIAL",
            "official_id":rid,
            "original_url":link,
            "title":title,
            "issuer":plain(elem(it,"author") or elem(it,"jrsdInsttNm"),150),
            "executor":plain(elem(it,"excInsttNm"),150),
            "published_at_raw":plain(elem(it,"pubDate") or elem(it,"creatPnttm"),70),
            "application_period_raw":req,
            "target_raw":plain(elem(it,"trgetNm"),180),
            "category_raw":plain(elem(it,"lcategory") or elem(it,"pldirSportRealmLclasCodeNm"),100),
            "official_attachment_name":filename,
            "official_attachment_type_unverified":ext,
            "issuer_eligibility_verified":False,
            "deadline_verified":False,
            "amendments_verified":False,
            "self_contribution_verified":False,
            "exact_official_form_reviewed":False,
            "official_submission_executed":False,
            "human_review_status":"REQUIRES_ORIGINAL_NOTICE_AND_FILE",
        })
    output.sort(key=lambda r:r["official_id"])
    return {"schema":"wmm-bizinfo-offline-preflight.v1",
        "checked_at_utc":checked.isoformat(),
        "official_api_spec":SPEC,
        "api_live_called":False,
        "api_key_used":False,
        "public_release_allowed":False,
        "official_funding_eligibility_determined":False,
        "source_sha256":hashlib.sha256(xml_bytes).hexdigest(),
        "notice_candidates":len(output),
        "records":output}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",type=Path,required=True,help="Offline RSS sample only; no API request")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    data=parse(args.fixture.read_bytes())
    out=args.out.resolve()
    if out.exists():raise ValueError("Refuse overwrite")
    if {"public","data_branch","functions"}&set(out.parts):raise ValueError("Not allowed to write production data")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PASS: {data['notice_candidates']} official-format offline candidates; no eligibility, API key or publication")
if __name__=="__main__": main()
