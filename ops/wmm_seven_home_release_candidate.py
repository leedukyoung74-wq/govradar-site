#!/usr/bin/env python3
"""Offline 7-language GOV RADAR homepage release candidate (NEVER deploy).

Builds a review-only ZIP with seven generated Cloudflare-variant HTML pages.
Checks locale, RTL, copy, form and static resource drift against the existing
live branch without modifying live, data, DNS, billing, auth or CRM.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.parse
import zipfile

LANGS=("ko","en","es","fr","ar","vi","id")
COPY={
    "ko":"조사·제안 아이디어 · 실시간 입찰 아님",
    "en":"Curated research ideas · not live tenders",
    "es":"Ideas de estudio · no son licitaciones en vivo",
    "fr":"Pistes de recherche · pas des appels d'offres en direct",
    "ar":"أفكار بحثية · ليست مناقصات مباشرة",
    "vi":"Ý tưởng nghiên cứu · không phải gói thầu trực tiếp",
    "id":"Ide riset terkurasi · bukan tender langsung",
}
COUNTRY={
    "ko":"193개국 개요 제공 · 출처 검증 수준은 국가별로 다릅니다",
    "en":"193 country overviews · source verification varies",
    "es":"193 fichas nacionales · verificación variable",
    "fr":"193 fiches pays · vérification variable",
    "ar":"ملفات 193 دولة · يختلف التحقق من المصادر",
    "vi":"Hồ sơ 193 quốc gia · mức xác minh khác nhau",
    "id":"193 profil negara · verifikasi sumber bervariasi",
}
PERIODIC={
    "ko":"정기 갱신", "en":"PERIODIC", "es":"PERIÓDICO",
    "fr":"PÉRIODIQUE", "ar":"تحديث دوري", "vi":"ĐỊNH KỲ",
    "id":"BERKALA",
}


# The homepage candidate must match owner-approved VAT-inclusive KRW 20,000/month.
MONTHLY_LABEL = {
    "ko": "월 20,000원",
    "en": "₩20,000/mo",
    "es": "₩20.000/mes",
    "fr": "20 000 ₩/mois",
    "ar": "20,000 وون شهريًا",
    "vi": "₩20.000/tháng",
    "id": "₩20.000/bulan",
}
# A stale price anywhere in a candidate is a release blocker, not a typo to hide.
OBSOLETE_PRICE = re.compile(r"(?<![0-9])19[,.\u00a0\u202f ]800(?![0-9])")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def form_tags(page):
    tags=re.findall(r'<form\b[^>]*>',page,re.I)
    return [re.sub(r'\s+',' ',html.unescape(t)).strip() for t in tags]


def local_assets(page):
    out=set()
    for tag in re.findall(r'<(?:script|link|img)\b[^>]*>',page,re.I):
        matches=re.findall(r'\b(?:src|href)\s*=\s*["\']([^"\']+)["\']',tag,re.I)
        for raw in matches:
            parsed=urllib.parse.urlsplit(html.unescape(raw))
            if parsed.scheme or parsed.netloc:
                continue
            if parsed.path.startswith(("/assets/","/hazards/")) and ".." not in parsed.path:
                out.add(parsed.path.lstrip("/"))
    return sorted(out)


def assess(locale,source,existing,live_root):
    src=html.unescape(source)
    live=html.unescape(existing)
    tag=re.search(r'<html\b[^>]*>',src,re.I)
    matched=bool(tag and re.search(r'\blang=["\']'+locale+r'["\']',tag.group(),re.I))
    direction=bool(tag and re.search(r'\bdir=["\']'+("rtl" if locale=="ar" else "ltr")+r'["\']',tag.group(),re.I))
    required={
        "html_lang":matched,
        "html_direction":direction,
        "responsive_viewport":bool(re.search(r'<meta\b[^>]*name=["\']viewport["\']',src,re.I)),
        "research_disclosure":COPY[locale] in src,
        "country_source_scope":COUNTRY[locale] in src,
        "periodic_update_badge":PERIODIC[locale] in src,
        "existing_dynamic_tender_placeholder":'id="kp-t"' in src,
        "existing_dynamic_last_update":'id="kp-u"' in src,
        "canonical_monthly_krw_20000":MONTHLY_LABEL[locale] in src,
        "obsolete_monthly_krw_19800_absent":OBSOLETE_PRICE.search(src) is None,
    }
    assets=local_assets(src)
    missing=[path for path in assets if not (live_root/path).is_file()]
    differences={
        "candidate_sha256":sha(source.encode("utf-8")),
        "current_live_sha256":sha(existing.encode("utf-8")),
        "html_changed":source!=existing,
        "reviewed_research_copy_already_live":COPY[locale] in live,
        "existing_live_obsolete_19800_mentions":len(OBSOLETE_PRICE.findall(live)),
        "form_tag_count_before":len(form_tags(existing)),
        "form_tag_count_after":len(form_tags(source)),
        "form_tags_identical":form_tags(source)==form_tags(existing),
        "new_local_asset_refs_missing_in_live":missing,
        "check_results":required,
    }
    differences["blocking"] = (
        not all(required.values()) or
        not differences["form_tags_identical"] or
        bool(missing)
    )
    return differences


def build(source_dir,live_dir,out_dir):
    source_dir=Path(source_dir)
    live_dir=Path(live_dir)
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    checks={}
    package=[]
    for locale in LANGS:
        rel=Path(locale)/"index.html"
        source=(source_dir/rel).read_text(encoding="utf-8")
        existing=(live_dir/rel).read_text(encoding="utf-8")
        checks[locale]=assess(locale,source,existing,live_dir)
        package.append((str(rel).replace("\\","/"),source.encode("utf-8")))
    blocked=[code for code,entry in checks.items() if entry["blocking"]]
    report={
        "schema_version":1,
        "scope":"SEVEN_LANGUAGE_PUBLIC_HOMEPAGE_REVIEW_ONLY_NOT_DEPLOYED",
        "state":"BLOCKED_REVIEW" if blocked else "OWNER_RELEASE_REVIEW_REQUIRED",
        "generated_at_utc":dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "blocked_locales":blocked,
        "candidate_pages":len(package),
        "checks":checks,
        "safety":{
            "production_changed":False,
            "customer_records_read":False,
            "forms_submitted":False,
            "real_payments_executed":False,
            "new_cron":False,
            "deploy_action_present":False,
        },
    }
    (out_dir/"manifest.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    zip_path=out_dir/"wmm-seven-language-homepages-REVIEW-ONLY.zip"
    with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED) as out:
        for name,blob in package:
            out.writestr("public/"+name,blob)
        out.writestr("manifest.json",json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "candidate_zip":zip_path.name,
        "state":report["state"],
        "blocked_locales":blocked,
        "candidate_pages":len(package),
        "changed_locales":[name for name,c in checks.items() if c["html_changed"]],
        "live_research_copy_present":[name for name,c in checks.items() if c["reviewed_research_copy_already_live"]],
        "live_site_published":False,
        "new_paid_usage":False,
    },ensure_ascii=False,sort_keys=True))
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",required=True,type=Path)
    p.add_argument("--live",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    try:
        result=build(a.candidate,a.live,a.out)
    except (OSError,UnicodeError,ValueError,KeyError) as exc:
        print(json.dumps({"state":"FAIL_GENERATION",
                          "error_type":type(exc).__name__,
                          "live_site_published":False}))
        return 1
    # A candidate can be successfully generated even if it has review blockers;
    # NEVER promote a ZIP into production from this script or workflow.
    return 0


if __name__=="__main__":
    raise SystemExit(main())
