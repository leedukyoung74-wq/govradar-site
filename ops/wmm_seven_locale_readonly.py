#!/usr/bin/env python3
"""GET-only seven-locale public homepage availability/HTML source truth.

Small per-hour smoke for existing WMM hourly watcher. No POST, cookies, JS,
member account, browser login, API keys, payments or deployment. Does not
prove mobile responsiveness, accessibility or authenticated functionality.
"""
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

ORIGIN = "https://radar.wmm-hoa.com"
LANGS = ("ko", "en", "es", "fr", "ar", "vi", "id")
MAX_BYTES = 280_000

class DenyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def fetch(language, opener=None):
    if language not in LANGS:
        raise ValueError("locale not allowlisted")
    opener = opener or urllib.request.build_opener(DenyRedirect)
    url = ORIGIN + "/" + language + "/"
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname != "radar.wmm-hoa.com":
        raise ValueError("host not allowlisted")
    req = urllib.request.Request(
        url, method="GET", headers={
            "User-Agent":"WMM-GOVRADAR-7-language-readonly-smoke/1.0",
            "Accept":"text/html"})
    try:
        with opener.open(req, timeout=12) as res:
            code = int(res.status)
            raw = res.read(MAX_BYTES+1)
            body = raw.decode("utf-8", "replace")
            return {
                "status": "PASS" if (
                    code == 200 and len(raw) <= MAX_BYTES and
                    bool(re.search(r'<html\b[^>]*\blang=["\']'+language+r'["\']', body, re.I)) and
                    "GOV RADAR" in body and
                    "</html>" in body
                ) else "FAIL",
                "http_status": code,
                "html_lang_correct": bool(re.search(
                    r'<html\b[^>]*\blang=["\']'+language+r'["\']', body, re.I)),
                "body_size_within_limit": len(raw) <= MAX_BYTES,
                # This flag is a copy-review warning only; a landing page
                # containing "LIVE" elsewhere does not prove timed refresh.
                "snapshot_disclosure_present": (
                    "조사·제안 아이디어" in body if language == "ko"
                    else "Curated research ideas" in body if language == "en"
                    else None),
            }
    except urllib.error.HTTPError as exc:
        return {"status":"FAIL","http_status":int(exc.code)}
    except Exception as exc:
        return {"status":"FAIL","error_type":type(exc).__name__}

def check(opener=None):
    rows={code:fetch(code,opener) for code in LANGS}
    bad=[x for x,y in rows.items() if y["status"] != "PASS"]
    # A 200 HTML response is reachability, not proof that the reviewed
    # privacy/provenance copy is deployed. Treat missing audited copy as
    # PENDING rather than green, but never call a good site an outage.
    undeployed=[x for x in ("ko","en") if
                rows.get(x,{}).get("status") == "PASS" and
                rows[x].get("snapshot_disclosure_present") is False]
    result="FAIL" if bad else "PENDING_COPY_NOT_DEPLOYED" if undeployed else "PASS"
    return {
        "scope":"PUBLIC_SEVEN_LANGUAGE_GET_ONLY_SMOKE",
        "result":result,
        "locales":rows,
        "failed_locales":bad,
        "locales_missing_curated_research_copy":undeployed,
        "mobile_browser_verified":False,
        "registered_forms_verified":False,
        "identity_roles_verified":False,
        "payment_checkout_verified":False,
        "new_scheduled_jobs":0,
        "customer_posts":0,
        "public_site_changed":False,
    }

def main():
    result=check()
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    p=os.getenv("GITHUB_STEP_SUMMARY")
    if p:
        with Path(p).open("a",encoding="utf-8") as fp:
            fp.write("\n## Public seven-language homepages: "+result["result"]+"\n\n")
            fp.write("| Locale | Status | HTTP | Research copy present |\n|---|---|---|---|\n")
            for k,v in result["locales"].items():
                fp.write(f"| {k} | {v['status']} | {v.get('http_status','-')} | {v.get('snapshot_disclosure_present','not checked')} |\n")
            fp.write("\nGET-only HTML smoke. No mobile, account, form, payment, data freshness or source SLA proof.\n")
    return 1 if result["result"]=="FAIL" else 0

if __name__=="__main__":
    raise SystemExit(main())
