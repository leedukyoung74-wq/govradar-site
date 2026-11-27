#!/usr/bin/env python3
"""Owner-approved, strictly READ-ONLY KONEPS/G2B API authorization probe.

Official data.go.kr dataset 15129394; 2026-11-10 max query window 7 days.
At most four GETs (supplies/services/works/foreign), one page * five rows
per category; no listing publication, customer data, email or billed API.
No raw exception, URL or API key may enter workflow logs or output.
"""
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService02/"
OPERATIONS = {
    "goods": "getBidPblancListInfoThngPPSSrch02",
    "services": "getBidPblancListInfoServcPPSSrch02",
    "works": "getBidPblancListInfoCnstwkPPSSrch02",
    "foreign": "getBidPblancListInfoFrgcptPPSSrch02",
}
FIELDS = ("bidNtceNo", "bidNtceOrd", "bidNtceNm", "bidNtceDt",
          "bidClseDt", "bidNtceDtlUrl", "ntceInsttNm", "dminsttNm")
KST = dt.timezone(dt.timedelta(hours=9))


class DoNotRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def make_url(category, key, today=None):
    if category not in OPERATIONS or not key:
        raise ValueError("unknown category or missing approved key")
    today = today or dt.datetime.now(KST).date()
    if not isinstance(today, dt.date):
        raise ValueError("invalid local date")
    start = today - dt.timedelta(days=2)
    params = {
        "serviceKey": key, "pageNo": 1, "numOfRows": 5,
        "inqryDiv": 1, "inqryBgnDt": start.strftime("%Y%m%d") + "0000",
        "inqryEndDt": today.strftime("%Y%m%d") + "2359",
        "type": "json",
    }
    # The data.go.kr portal may provide URL-encoded or plain service keys.
    return BASE + OPERATIONS[category] + "?" + urllib.parse.urlencode(params, safe="%") 


def parse_reply(body):
    """Return aggregate, no record content, no original response text."""
    try:
        d = json.loads(body)
        header = (d.get("response") or {}).get("header") or {}
        b = (d.get("response") or {}).get("body") or {}
        payload = b.get("items")
        if isinstance(payload, dict):
            payload = payload.get("item") or []
        if isinstance(payload, dict):
            payload = [payload]
        if payload is None:
            payload = []
        if not isinstance(payload, list):
            raise ValueError("invalid list")
        if not isinstance(b, dict) or not isinstance(header, dict):
            raise ValueError("invalid envelope")
        code = str(header.get("resultCode", ""))
        rows = [r for r in payload if isinstance(r, dict)]
        total = b.get("totalCount")
    except (ValueError, TypeError, AttributeError):
        # Some official G2B endpoints return an XML gateway error.
        try:
            root = ET.fromstring(body)
            code = root.findtext(".//resultCode") or root.findtext(".//returnReasonCode") or ""
            rows = [{c.tag.rsplit("}", 1)[-1]: (c.text or "")
                     for c in el} for el in root.findall(".//item")]
            total = root.findtext(".//totalCount")
        except (ValueError, ET.ParseError):
            return {"state": "UNRECOGNIZED_RESPONSE", "items": 0, "fields": []}
    safe_code = re.sub(r"[^A-Za-z0-9_-]", "", str(code))[:16]
    if safe_code not in ("00", "0", "NORMAL_SERVICE"):
        return {"state": "UPSTREAM_ERROR_OR_ACCESS_DENIED", "code": safe_code or "missing",
                "items": 0, "fields": []}
    try:
        n = max(0, int(total))
    except (ValueError, TypeError):
        n = None
    names = sorted(set().union(*(set(row) for row in rows)).intersection(FIELDS)) if rows else []
    return {"state": "OK_ROWS" if rows else "OK_EMPTY", "code": safe_code,
            "items": len(rows), "total": n, "fields": names}


# Official data.go.kr published authentication and gateway error names. Return
# ONLY an allowlisted classification; never echo a raw HTTP error document,
# redirected URL, submitted key, provider text, arbitrary result code or headers.
KNOWN_GATEWAY_ERRORS = (
    "SERVICE_ACCESS_DENIED_ERROR",
    "SERVICE_KEY_IS_NOT_REGISTERED_ERROR",
    "SERVICE_KEY_IS_NULL",
    "PERMISSION_DENIED",
    "DEADLINE_HAS_EXPIRED_ERROR",
    "BLACKLIST_IP_ACCESS_ERROR",
    "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR",
    "LIMITED_NUMBER_OF_SERVICE_REQUESTS_PER_SECOND_EXCEEDS_ERROR",
    "INVALID_REQUEST_PARAMETER_ERROR",
    "NO_OPENAPI_SERVICE_ERROR",
    "HTTP_ERROR",
    "SERVICETIMEOUT_ERROR",
    "APPLICATION_ERROR",
)


def classify_http_error(exc):
    result = {"state": "HTTP_DENIED_OR_ERROR", "http_status": int(exc.code),
              "provider_error": "UNSPECIFIED_HTTP_ERROR"}
    try:
        raw = exc.read(32769)
    except Exception:
        return result
    # A provider may echo an entire request URL in HTML. Never log it.
    if not isinstance(raw, bytes) or len(raw) > 32768:
        return result
    body = raw.decode("utf-8", "replace")
    for code in KNOWN_GATEWAY_ERRORS:
        if re.search(r"(?<![A-Z0-9_])" + re.escape(code) + r"(?![A-Z0-9_])",
                     body, flags=re.I):
            result["provider_error"] = code
            break
    return result


def probe(key, opener=None, today=None):
    if not key:
        return {"classification": "NO_APPROVED_KEY", "operations_attempted": 0,
                "ready_for_live_ingestion": False, "items_published": 0}
    opener = opener or urllib.request.build_opener(DoNotRedirect)
    results = {}
    for cat in OPERATIONS:  # hard four requests max, no retries
        url = make_url(cat, key, today)
        req = urllib.request.Request(url, method="GET",
                                     headers={"User-Agent": "WMM-KONEPS-readonly-authorization-check/1.0",
                                              "Accept": "application/json,application/xml"})
        try:
            with opener.open(req, timeout=14) as res:
                if getattr(res, "status", None) != 200:
                    results[cat] = {"state": "NON_200_RESPONSE"}
                else:
                    raw = res.read(450001)
                    results[cat] = (parse_reply(raw) if len(raw) <= 450000 else
                                    {"state": "RESPONSE_TOO_LARGE"})
        except urllib.error.HTTPError as exc:
            results[cat] = classify_http_error(exc)
        except Exception as exc:
            # Do not print the exception: HTTPError and URLError can include
            # a complete URL with the serviceKey query parameter.
            results[cat] = {"state": "NETWORK_ERROR", "error_type": type(exc).__name__}
    success = [k for k, v in results.items() if v.get("state") in ("OK_ROWS", "OK_EMPTY")]
    return {
        "classification": "OWNER_APPROVED_READ_ONLY_KONEPS_PROBE",
        "operations_attempted": len(results), "operations_succeeded": len(success),
        "results": results, "ready_for_live_ingestion": False,
        "schema_accepted_for_review": bool(success),
        "items_published": 0,
        "caution": "Provider account authorization and item-level notices require separate confirmation."
    }


def main():
    # Only a KONEPS-specific, explicitly approved secret may authorize a G2B
    # probe. A DAPA overseas procurement key is not interchangeable.
    # Missing KONEPS_KEY must result in zero network requests.
    key = (os.environ.get("KONEPS_KEY") or "").strip()
    result = probe(key)
    # A successful GitHub Actions job must NEVER mean "all four endpoints
    # returned HTTP 403". Gate the job status on all four upstream responses;
    # even a clean probe is only schema/transport evidence, not production
    # publishing permission or confirmed currently open notices.
    all_responded = (
        result.get("operations_attempted") == len(OPERATIONS)
        and result.get("operations_succeeded") == len(OPERATIONS)
        and result.get("schema_accepted_for_review") is True
    )
    result["authorization_probe_gate"] = (
        "SCHEMA_REVIEW_ONLY_NOT_LIVE" if all_responded else
        "BLOCKED_NO_KEY" if result.get("classification") == "NO_APPROVED_KEY" else
        "BLOCKED_UPSTREAM_RESPONSE"
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if all_responded else 2


if __name__ == "__main__":
    raise SystemExit(main())
