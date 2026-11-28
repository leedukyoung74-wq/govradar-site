#!/usr/bin/env python3
"""Surgical 7-locale GOV RADAR copy-only release candidate; does NOT deploy.

Transplants just four reviewed, noninteractive UI sections from the generated
src preview into *existing* live HTML:
  1) hero research scope sentence, 2) periodical source ticker,
  3) country-KPI label, 4) research disclaimer under business-KPI label.
All forms, scripts, numeric counts, existing links and backend endpoints are
byte-identical to the published live branch. No writes to branches or sites.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import zipfile

LANGS=("ko","en","es","fr","ar","vi","id")
HERO=re.compile(r'<p class="eb"><i class="live"></i>.*?</p>',re.S)
TICK=re.compile(r'<section class="tick"[^>]*>.*?</section>',re.S)
KPI=re.compile(r'<div class="kpis">(?P<inner>(?:<div>.*?</div>){4})</div>',re.S)
KID=re.compile(r'<div>.*?</div>',re.S)
SPAN=re.compile(r'<span>[^<]*</span>',re.S)
SMALL=re.compile(r'<small>[^<]*</small>',re.S)
SCRIPT=re.compile(r'<script\b[^>]*>.*?</script>',re.S)
FORM=re.compile(r'<form\b[^>]*>',re.S)


def unique(pattern,text,name):
    matches=list(pattern.finditer(text))
    if len(matches)!=1:
        raise ValueError("unsafe page structure for "+name)
    return matches[0].group(0)


def replace_once(text,old,new,label):
    if not old or text.count(old)!=1:
        raise ValueError("replacement anchor not unique: "+label)
    return text.replace(old,new,1)


def kpi_parts(page):
    kpi=unique(KPI,page,"kpi")
    bits=KID.findall(kpi)
    if len(bits)!=4:
        raise ValueError("unexpected KPI count")
    return kpi,bits


def patch(locale,src,live):
    if locale not in LANGS:
        raise ValueError("locale not allowlisted")
    src_hero=unique(HERO,src,"source hero")
    live_hero=unique(HERO,live,"live hero")
    src_tick=unique(TICK,src,"source ticker")
    live_tick=unique(TICK,live,"live ticker")
    # The only difference allowed in transplanted ticker is textual content
    # and aria labels; markup element hierarchy must not change.
    if re.findall(r'</?[\w:-]+',src_tick)!=re.findall(r'</?[\w:-]+',live_tick):
        raise ValueError("ticker DOM shape changed")
    src_kpi, src_bits=kpi_parts(src)
    live_kpi, live_bits=kpi_parts(live)
    if not all(("id=\"kp-t\"" in src_bits[1],"id=\"kp-t\"" in live_bits[1],
                "id=\"kp-u\"" in src_bits[3],"id=\"kp-u\"" in live_bits[3])):
        raise ValueError("dynamic KPI hooks changed")
    country_new=unique(SPAN,src_bits[0],"new country label")
    country_old=unique(SPAN,live_bits[0],"old country label")
    business_disclaimer=unique(SMALL,src_bits[2],"business disclaimer")
    if SMALL.search(live_bits[2]):
        raise ValueError("live business KPI already has unreviewed small label")
    first=replace_once(live_bits[0],country_old,country_new,"country label")
    third=replace_once(live_bits[2],"</span></div>",
                       "</span>"+business_disclaimer+"</div>","biz label")
    new_kpi=live_kpi.replace(live_bits[0],first,1).replace(live_bits[2],third,1)
    out=replace_once(live,live_hero,src_hero,"hero scope")
    out=replace_once(out,live_tick,src_tick,"ticker")
    out=replace_once(out,live_kpi,new_kpi,"kpi badges")

    if FORM.findall(out)!=FORM.findall(live):
        raise ValueError("form tags altered")
    if SCRIPT.findall(out)!=SCRIPT.findall(live):
        raise ValueError("script contents altered")
    if re.findall(r'<(?:link|img)\b[^>]*>',out)!=re.findall(r'<(?:link|img)\b[^>]*>',live):
        raise ValueError("static resource tags altered")
    # No changes to form bodies, handlers, inline scripts or JS references.
    if business_disclaimer not in out or src_hero not in out or src_tick not in out:
        raise ValueError("reviewed copy not fully applied")
    if out==live:
        raise ValueError("unexpected no-op; already released or wrong source")
    return out,{
        "source_scope_replaced":True,
        "source_refresh_claim_replaced":True,
        "country_kpi_label_replaced":True,
        "research_disclaimer_added":True,
        "forms_byte_identical":True,
        "source_generated_form_changes_intentionally_excluded":FORM.findall(src)!=FORM.findall(live),
        "scripts_byte_identical":True,
        "static_resources_byte_identical":True,
        "original_numeric_kpis_preserved":(
            re.findall(r'<b[^>]*>[^<\d]*\d+[^<]*',live_kpi) ==
            re.findall(r'<b[^>]*>[^<\d]*\d+[^<]*',new_kpi)
        ),
        "before_sha256":hashlib.sha256(live.encode()).hexdigest(),
        "candidate_sha256":hashlib.sha256(out.encode()).hexdigest(),
    }


def generate(src_dir,live_dir,out_dir):
    src_dir=Path(src_dir);live_dir=Path(live_dir);out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    entries=[];details={}
    for lang in LANGS:
        rel=Path(lang)/"index.html"
        src=(src_dir/rel).read_text(encoding="utf-8")
        live=(live_dir/rel).read_text(encoding="utf-8")
        out,check=patch(lang,src,live)
        if not check["original_numeric_kpis_preserved"]:
            raise ValueError("numeric KPI altered")
        entries.append((str(rel).replace("\\","/"),out))
        details[lang]=check
    manifest={
        "schema_version":1,
        "scope":"SEVEN_LANGUAGE_SURGICAL_COPY_ONLY_RELEASE_REVIEW",
        "result":"OWNER_REVIEW_REQUIRED_NOT_DEPLOYED",
        "checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "patched_locales":len(entries),
        "checks":details,
        "new_charges":False,
        "live_site_modified":False,
        "customer_forms_submitted":False,
        "login_or_checkout_executed":False,
        "new_automation_created":False,
    }
    out_file=out_dir/"wmm-seven-homepages-COPY-ONLY-REVIEW.zip"
    with zipfile.ZipFile(out_file,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for name,page in entries:
            z.writestr("public/"+name,page.encode("utf-8"))
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    (out_dir/"manifest.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"result":manifest["result"],
                      "locales":manifest["patched_locales"],
                      "form_changes":0,"script_changes":0,
                      "live_site_modified":False,
                      "review_zip":out_file.name},ensure_ascii=False))
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--live",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    generate(args.source,args.live,args.out)
