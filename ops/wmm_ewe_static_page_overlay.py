#!/usr/bin/env python3
"""Surgical, review-only patch of existing GOV RADAR national agency card HTML.

Never regenerates whole country pages, changes routing, login, memberships,
payments, SEO, hidden details, or sends notifications. No source feed I/O.
A redirect-only locale must remain byte-for-byte untouched. The caller controls
which Git branch, if any, gets committed; this script never deploys or pushes.
"""
import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

LANGS=("ko","en","es","fr","ar","vi","id")
KINDS=("environment","weather","emergency")
COUNTRIES=("DZ","AO","BJ","BW","BF","BI","CV","CM",
           "ET","MV","JO","GE","LU","MD","SK","FJ")
GOOD={
"ko":"국가기관 링크 후보 · 접속/실시간 경보 미검증",
"en":"National agency candidate · live/alert status unverified",
"es":"Organismo nacional candidato · no verificado en vivo",
"fr":"Organisme national candidat · non vérifié en direct",
"ar":"رابط جهة وطنية مرشح · غير متحقق منه مباشرة",
"vi":"Liên kết cơ quan quốc gia đề xuất · chưa xác thực trực tiếp",
"id":"Calon tautan lembaga nasional · belum diverifikasi langsung",
}
SECTION=re.compile(r'<section class="sec" id="environment-weather-emergency">.*?</section>',re.S)
CARD=re.compile(
    r'<a class="card" href="[^"]+" target="_blank" '
    r'rel="noopener noreferrer nofollow" '
    r'style="display:block;text-decoration:none">'
    r'<b>([^<]*)</b><p>.*?</p><p class="note">.*?</p></a>',re.S)
MAX_PAGE_BYTES=1_000_000


def safe_source(item):
    if not isinstance(item,dict) or not isinstance(item.get("url"),str):
        return False
    if (item.get("review")!="curated_candidate"
        or item.get("access")!="not_live_tested"
        or not isinstance(item.get("name"),str)
        or not item["name"].strip()):
        return False
    url=item["url"]
    if len(url)>2048 or any(ord(c)<32 for c in url):
        return False
    try:
        parsed=urlsplit(url)
        return (parsed.scheme=="https" and bool(parsed.hostname) and
                parsed.port is None and parsed.fragment=="" and
                parsed.username is None and parsed.password is None)
    except ValueError:
        return False


def plan_changes(site_root,catalog,countries,target_countries=COUNTRIES):
    """Read everything and validate all target pages BEFORE touching any file."""
    root=Path(site_root)
    if not isinstance(catalog,dict) or not isinstance(catalog.get("countries"),dict):
        raise ValueError("expected_canonical_source_catalog")
    source=catalog["countries"]
    if not isinstance(countries,list) or len(countries)<193:
        raise ValueError("expected_193_country_site_index")
    slugs={r["iso"]:r["slug"] for r in countries if isinstance(r,dict)
           and isinstance(r.get("iso"),str) and isinstance(r.get("slug"),str)}
    if len(set(target_countries))!=len(target_countries):
        raise ValueError("duplicate_target_countries")
    changes=[]
    redirects=[]
    already=[]
    seen_files=set()
    for iso in target_countries:
        if iso not in source or iso not in slugs:
            raise ValueError("missing_country_source_or_slug_"+iso)
        if not re.fullmatch(r"[a-z0-9-]{2,100}",slugs[iso]):
            raise ValueError("unsafe_country_slug_"+iso)
        rows=source[iso]
        if set(rows)!=set(KINDS) or not all(safe_source(rows[x]) for x in KINDS):
            raise ValueError("country_not_fully_curated_"+iso)
        for lang in LANGS:
            relative=Path("public")/lang/slugs[iso]/"index.html"
            if relative in seen_files:
                raise ValueError("duplicate_country_path")
            seen_files.add(relative)
            path=root/relative
            if not path.is_file() or path.stat().st_size>MAX_PAGE_BYTES:
                raise ValueError("missing_or_large_country_page_"+relative.as_posix())
            before=path.read_text(encoding="utf-8")
            matches=list(SECTION.finditer(before))
            if not matches:
                # Preserve existing 7-language routing; a redirect is not a
                # real page and should never be replaced by fake localized UI.
                if (len(before)<3000 and 'http-equiv="refresh"' in before
                    and 'name="robots" content="noindex"' in before
                    and "location.replace" in before):
                    redirects.append(relative.as_posix())
                    continue
                raise ValueError("missing_ewe_section_not_safe_to_patch_"+relative.as_posix())
            if len(matches)!=1:
                raise ValueError("duplicate_ewe_section_"+relative.as_posix())
            old_sec=matches[0].group(0)
            card_matches=list(CARD.finditer(old_sec))
            if len(card_matches)!=3:
                raise ValueError("expected_exactly_three_cards_"+relative.as_posix())
            def rebuild(m):
                i=next_index[0];next_index[0]+=1
                item=rows[KINDS[i]]
                label=m.group(1)  # Existing escaped localized category label.
                if not label or any(c in label for c in "<>"):
                    raise ValueError("unsafe_localized_category_label")
                return (f'<a class="card" href="{html.escape(item["url"],quote=True)}" '
                    'target="_blank" rel="noopener noreferrer nofollow" '
                    'style="display:block;text-decoration:none">'
                    f'<b>{label}</b><p>{html.escape(item["name"],quote=True)}</p>'
                    f'<p class="note">{html.escape(GOOD[lang],quote=True)}</p></a>')
            next_index=[0]
            new_sec=CARD.sub(rebuild,old_sec)
            if next_index[0]!=3 or new_sec.count('class="card"')!=3:
                raise ValueError("invalid_new_card_count_"+relative.as_posix())
            after=before[:matches[0].start()]+new_sec+before[matches[0].end():]
            # Whole-document exact reversible replacement: auth, SEO, CSS,
            # other sections, translations and JavaScript stay byte-identical.
            if after[:matches[0].start()]!=before[:matches[0].start()]:
                raise ValueError("page_prefix_modified")
            if after[matches[0].start()+len(new_sec):]!=before[matches[0].end():]:
                raise ValueError("page_suffix_modified")
            if after==before:
                already.append(relative.as_posix())
            else:
                changes.append((relative.as_posix(),path,after))
    return {"expected_pages":len(target_countries)*len(LANGS),
            "total_country_count":len(target_countries),
            "changes":changes,"redirects_preserved":redirects,
            "already_current":already}


def run(site_root,catalog_path,countries_path,dry_run=True,out_path=None):
    catalog=json.loads(Path(catalog_path).read_text(encoding="utf8"))
    countries=json.loads(Path(countries_path).read_text(encoding="utf8"))
    plan=plan_changes(site_root,catalog,countries,COUNTRIES)
    assert len(plan["changes"])+len(plan["redirects_preserved"])+len(plan["already_current"])==plan["expected_pages"]
    if not dry_run:
        for _,p,content in plan["changes"]:
            p.write_text(content,encoding="utf8")
    report={
        "schema":"wmm.ewe-16-country-static-card-only-review.v1",
        "status":"DRY_RUN" if dry_run else "LOCAL_FILES_CHANGED_REVIEW_ONLY",
        "target_countries":list(COUNTRIES),
        "languages":list(LANGS),
        "expected_pages":plan["expected_pages"],
        "updated_country_page_count":len(plan["changes"]),
        "redirect_pages_preserved":plan["redirects_preserved"],
        "already_current_pages":plan["already_current"],
        "changed_paths":[row[0] for row in plan["changes"]],
        "scope":"EWE card anchors only; no other page markup",
        "site_published":False,"customer_messages_sent":False,
        "customer_data_read":False,"paid_api_used":False,
        "live_source_feeds_verified":0,
    }
    if out_path:
        p=Path(out_path);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in report.items()
                      if k not in ("changed_paths","redirect_pages_preserved","already_current_pages")},
                     ensure_ascii=False))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--site",required=True,type=Path)
    p.add_argument("--catalog",required=True,type=Path)
    p.add_argument("--countries",required=True,type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--apply-local",action="store_true",help="Write review working tree only; never push/deploy")
    v=p.parse_args()
    run(v.site,v.catalog,v.countries,not v.apply_local,v.out)
