#!/usr/bin/env python3
"""Owner-only OFFLINE classification of an existing KONEPS GitHub secret.

Never print the key, its length, prefix, suffix, digest, or decoded form.
Never call a data.go.kr or any other external API.
A plausible value shape DOES NOT prove provider approval.
"""
import json
import os
import re


def classify(value):
    if not value:
        return "NOT_CONFIGURED"
    if value.strip() != value or "\n" in value or "\r" in value:
        return "HAS_WHITESPACE_OR_MULTILINE"
    if value.startswith(("http://", "https://")) or re.search(
        r"(?i)(?:^|[?&])(?:servicekey|key|apikey)=", value
    ):
        return "URL_OR_PARAMETER_INSTEAD_OF_KEY"
    if value[:1] in ('"', "'") or value[-1:] in ('"', "'"):
        return "HAS_QUOTE_CHARACTERS"
    if "%" in value:
        if re.search(r"%(?![0-9a-fA-F]{2})", value):
            return "INVALID_PERCENT_ESCAPE"
        return "PERCENT_ENCODED_OR_PERCENT_CONTAINING"
    if any(ord(c) < 33 or ord(c) > 126 for c in value):
        return "NON_ASCII_OR_CONTROL_CHARACTER"
    return "PLAIN_OPAQUE_KEY_SHAPE"


def main():
    result = {
        "check": "KONEPS_SECRET_SHAPE_OFFLINE_ONLY",
        "secret_shape": classify(os.environ.get("KONEPS_KEY")),
        "provider_authorization_verified": False,
        "actual_koneps_access_verified": False,
        "api_requests": 0,
        "items_published": 0,
        "warning": "Plausible shape is not evidence of dataset 15129394 approval.",
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["secret_shape"] != "NOT_CONFIGURED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
