#!/usr/bin/env python3
"""Read-only public GOV RADAR API diagnostics. NEVER send a customer submission.

Only anonymous GET and anonymous OPTIONS. No accounts, cookies, keys, body,
POST, PATCH, D1 queries or provider credentials. Avoid guessing based on HTML.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

HOST = "https://radar.wmm-hoa.com"
PATHS = ("/api/req", "/nfform")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def anonymous_get(path, timeout=12, opener=None):
    if path not in PATHS:
        raise ValueError("Only read-only approved endpoint paths may be checked")
    opener = opener or urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(HOST + path,
                                 headers={"User-Agent": "WMM-readonly-api-health/1.0",
                                          "Accept": "application/json,text/plain"},
                                 method="GET")
    try:
        with opener.open(req, timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as error:
        return int(error.code)


def interpret(req_status, form_status):
    if req_status == 401:
        d1 = "PROBABLE_BOUND_AUTH_GUARD_PRESENT"
        # An unauthenticated GET 401 is strong evidence the handler reached its
        # auth gate, but NOT proof a D1 read/write or identity flow works.
    elif req_status == 503:
        d1 = "UNAVAILABLE_OR_D1_UNBOUND"
    elif req_status == 404:
        d1 = "ROUTE_NOT_FOUND"
    elif req_status == 200:
        d1 = "SECURITY_ALERT_ANONYMOUS_GET_SUCCEEDED"
    else:
        d1 = "INCONCLUSIVE_HTTP_" + str(req_status)
    if form_status == 405:
        form = "GET_REJECTED_POST_ONLY"
    elif form_status in (200, 301, 302, 303, 404):
        form = "INCONCLUSIVE_NO_POST_SENT"
    else:
        form = "INCONCLUSIVE_HTTP_" + str(form_status)
    return {"classification": "ANONYMOUS_READ_ONLY_API_PROBE",
            "d1_binding_evidence": d1,
            "form_get_evidence": form,
            "submission_tested": False,
            "netlify_inbox_verified": False,
            "google_login_verified": False,
            "d1_write_verified": False,
            "payment_actions": False}


def main():
    codes = {}
    for path in PATHS:
        try:
            codes[path] = anonymous_get(path)
        except (OSError, ValueError, TimeoutError) as err:
            print(json.dumps({"classification": "ANONYMOUS_READ_ONLY_API_PROBE",
                              "status": "INCONCLUSIVE_NETWORK_ERROR",
                              "path": path,
                              "error_type": type(err).__name__,
                              "submitted": False}, ensure_ascii=False))
            return 2
    report = interpret(codes["/api/req"], codes["/nfform"])
    report["http_codes"] = codes
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if codes["/api/req"] == 200 else 0


if __name__ == "__main__":
    sys.exit(main())
