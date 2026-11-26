#!/usr/bin/env python3
"""Read-only, bounded HTTP GET readiness of 7 GOV RADAR public locales.
No login, cookies, form submissions, paid APIs, browser simulation, or mutations.
"""
import json
import sys
import urllib.error
import urllib.request

BASE="https://radar.wmm-hoa.com"
LANGS=("ko","en","es","fr","ar","vi","id")
REQUEST_LANGS=("ko","en","ar")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

def routes():
    return tuple(f"/{lang}/" for lang in LANGS)+tuple(f"/{lang}/request/" for lang in REQUEST_LANGS)

def fetch_status(path,opener=None):
    if path not in routes():
        raise ValueError("Not an approved read-only public route")
    opener=opener or urllib.request.build_opener(NoRedirect)
    request=urllib.request.Request(BASE+path,method="GET",headers={
        "User-Agent":"WMM-GOV-RADAR-read-only-route-check/1.0",
        "Accept":"text/html"})
    try:
        with opener.open(request,timeout=12) as response:
            # Need only status and content-type, never collect customer data.
            return {"path":path,"status":response.status,
                    "content_type":response.headers.get("content-type","").split(";")[0].lower()}
    except urllib.error.HTTPError as exc:
        return {"path":path,"status":exc.code,"content_type":""}

def interpret(rows):
    good=all(r["status"]==200 and r["content_type"]=="text/html" for r in rows)
    return {"classification":"PUBLIC_HTML_GET_ONLY","checked_routes":len(rows),
            "all_public_html_200":good,"result":"PASS" if good else "DEGRADED",
            "responses":rows,"mobile_rendering_verified":False,
            "login_verified":False,"form_submission_verified":False,
            "staff_inbox_verified":False}

def main():
    rows=[]
    for p in routes():
        try: rows.append(fetch_status(p))
        except (OSError,TimeoutError,ValueError) as exc:
            rows.append({"path":p,"status":None,"content_type":"",
                         "error_type":type(exc).__name__})
    print(json.dumps(interpret(rows),ensure_ascii=False,indent=2))
    # Degraded availability is recorded as evidence; not a reason to disable
    # existing scheduled workflow or prevent report artifact retention.
    return 0

if __name__=="__main__":
    sys.exit(main())
