#!/usr/bin/env python3
"""ONE official KONEPS GET with whitespace-only normalized private key.

Owner-authorized GitHub Actions secret; no key or URL echoed; no publishing.
This is a diagnostic, not a source collector or entitlement activation.
"""
import json
import os
import re
import urllib.error
import urllib.request

import wmm_koneps_bounded_probe as P


def clean_key(raw):
    if not raw:
        return None, "NO_KEY"
    # Whitespace is never a legitimate part of a data.go.kr service key.
    # Restrict repair to Unicode whitespace only, not arbitrary string edits.
    value = "".join(c for c in raw if not c.isspace())
    if not value:
        return None, "NO_KEY"
    if value.startswith(("http://", "https://")) or re.search(
        r"(?i)(?:^|[?&])(?:servicekey|key|apikey)=", value
    ):
        return None, "WRAPPED_URL_OR_PARAMETER"
    if any(ord(c) < 33 or ord(c) > 126 for c in value):
        return None, "UNSUPPORTED_CHARACTERS"
    if "%" in value and re.search(r"%(?![a-fA-F0-9]{2})", value):
        return None, "INVALID_PERCENT_ENCODING"
    return value, "WHITESPACE_NORMALIZED" if value != raw else "NO_WHITESPACE_REPAIR_NEEDED"


def one_get(raw, opener=None):
    key, state = clean_key(raw)
    out = {
        "check": "KONEPS_ONE_GET_WHITESPACE_NORMALIZED",
        "credential_format_state": state,
        "requests_made": 0,
        "items_published": 0,
        "live_ingestion_enabled": False,
        "provider_authorization_verified": False,
        "single_endpoint_schema_accepted": False,
    }
    if not key:
        out["outcome"] = "BLOCKED_KEY_FORMAT"
        return out
    opener = opener or urllib.request.build_opener(P.DoNotRedirect)
    # EXACTLY one GET to official goods search; no pagination, no source writes.
    req = urllib.request.Request(
        P.make_url("goods", key),
        method="GET",
        headers={"User-Agent": "WMM-KONEPS-key-whitespace-single-GET/1.0",
                 "Accept": "application/json,application/xml"},
    )
    out["requests_made"] = 1
    try:
        with opener.open(req, timeout=14) as res:
            if res.status != 200:
                out["outcome"] = "NON_200"
                return out
            response = res.read(450001)
            parsed = (P.parse_reply(response) if len(response) <= 450000
                      else {"state": "RESPONSE_TOO_LARGE"})
    except urllib.error.HTTPError as exc:
        parsed = P.classify_http_error(exc)
    except Exception as exc:
        parsed = {"state": "NETWORK_ERROR", "error_type": type(exc).__name__}
    out["response"] = parsed
    out["single_endpoint_schema_accepted"] = parsed.get("state") in ("OK_ROWS", "OK_EMPTY")
    out["outcome"] = ("TRANSPORT_SCHEMA_ONLY_NOT_LIVE" if out["single_endpoint_schema_accepted"]
                      else "BLOCKED_UPSTREAM")
    # Parsed result includes schema names/counts; never real tender content.
    return out


def main():
    result = one_get(os.environ.get("KONEPS_KEY"))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["single_endpoint_schema_accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
