#!/usr/bin/env python3
"""Source-only customer route / localisation inventory. No network, no PII."""
import argparse
import json
import pathlib
import re
import sys

LANGS=("ko","en","es","fr","ar","vi","id")
ROUTES=(
    "index.html","pricing/index.html","request/index.html","how/index.html",
    "membership/index.html","legal/terms/index.html","legal/privacy/index.html",
    "legal/refund/index.html","legal/disclaimer/index.html","thanks/index.html",
    "consortium/thanks/index.html","gcsme/index.html","partners/index.html",
    "consortium/index.html","member/index.html","account/index.html",
    "solutions/index.html","experts/index.html","contracts/index.html",
    "unlock/index.html"
)
FALLBACK={f"{lang}/{route}" for lang in ("es","fr","vi","id")
          for route in ("pricing/index.html","request/index.html")}
SAFE_EMAIL="73036396@naver.com"

def audit(root):
    root=pathlib.Path(root)
    problems=[]
    fallback=[]
    full=0
    for lang in LANGS:
        for route in ROUTES:
            rel=f"{lang}/{route}"
            path=root/rel
            if not path.is_file():
                problems.append({"route":rel,"error":"missing_html"})
                continue
            try:html=path.read_text("utf-8")
            except UnicodeError:
                problems.append({"route":rel,"error":"invalid_utf8"})
                continue
            if rel in FALLBACK:
                target="/en/"+route.removesuffix("index.html")
                checks={
                  "meta":f'http-equiv="refresh" content="0;url={target}"' in html,
                  "script":f'location.replace("{target}"+location.search+location.hash)' in html,
                  "link":f'href="{target}"' in html,
                  "noindex":'name="robots" content="noindex"' in html
                }
                if not all(checks.values()):
                    problems.append({"route":rel,"error":"unverified_language_fallback","checks":checks})
                else:fallback.append(rel)
                continue
            if not re.search(r'<html\b[^>]*\blang=["\x27]'+lang+r'["\x27]',html,re.I):
                problems.append({"route":rel,"error":"wrong_html_language"})
                continue
            if route in ("thanks/index.html","consortium/thanks/index.html"):
                main=html.split("<main>",1)[-1].split("</main>",1)[0]
                if 'role="status"' not in main or SAFE_EMAIL not in main:
                    problems.append({"route":rel,"error":"unverified_receipt_notice_missing"})
                    continue
                # Checking a URL directly does not prove provider-side intake.
                claim=re.search(r"<h1>\s*(?:신청을 받았습니다|Thank you — (?:application received|we've got your request))",main,re.I)
                if claim:
                    problems.append({"route":rel,"error":"unverified_received_claim"})
                    continue
            full+=1
    support=root/"support/index.html"
    if not support.is_file():problems.append({"route":"support/index.html","error":"missing_support_hub"})
    else:
        content=support.read_text("utf-8")
        if 'id="faqs"' not in content or '<form' in content:
            problems.append({"route":"support/index.html","error":"support_not_local_readonly"})
    return {
       "scope":"STATIC_RELEASE_REVIEW_NOT_REAL_BROWSER_NOT_SUBMISSION",
       "locales":len(LANGS),"routes_per_locale":len(ROUTES),
       "expected_routes":len(LANGS)*len(ROUTES),
       "standalone_pages_with_language_and_receipt_gates":full,
       "declared_en_fallbacks":sorted(fallback),
       "known_untranslated_route_count":len(fallback),
       "problems":problems,
       "customer_provider_records_verified":False,
       "release_state":"BLOCKED" if problems else "SOURCE_PASS_NEEDS_OWNER_RELEASE_VERIFICATION"
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="public")
    a=p.parse_args()
    report=audit(a.root)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 1 if report["problems"] else 0
if __name__=="__main__":
    sys.exit(main())
