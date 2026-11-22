#!/usr/bin/env python3
"""Single-pass HTTPS agency URL reachability evidence, NOT a data-feed collector.

Nine government/agency directory candidates in Jordan, Georgia and Luxembourg.
No scraping, credentials, user data, alerts, site publishing, or recurring jobs.
An HTTP 200 for an institution homepage proves NEITHER an API/RSS data feed NOR
live national warning coverage NOR commercial republication permission.
"""
import argparse
import datetime as dt
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CATEGORIES = ("environment", "weather", "emergency")
EXPECTED_HOSTS = {
    "JO": ("moenv.gov.jo", "jmd.gov.jo", "ncscm.gov.jo"),
    "GE": ("mepa.gov.ge", "nea.gov.ge", "es.gov.ge"),
    "LU": ("environnement.public.lu", "meteolux.lu", "lu-alert.lu"),
}
MAX_REDIRECTS = 2


def validate_url(url, expected_host):
    """Do not follow a changed catalog URL to any non-approved host."""
    if not isinstance(url, str):
        raise ValueError("non_string_url")
    parts = urllib.parse.urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname or parts.username
            or parts.password or parts.fragment or parts.port is not None):
        raise ValueError("not_plain_https_url")
    host = parts.hostname.lower()
    canonical = host[4:] if host.startswith("www.") else host
    if canonical != expected_host:
        raise ValueError("different_host_or_redirect")
    return url


class RestrictedRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, expected_host):
        super().__init__()
        self.expected_host = expected_host
        self.seen = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl, self.expected_host)
        self.seen += 1
        if self.seen > MAX_REDIRECTS:
            raise ValueError("too_many_redirects")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def candidates(catalog):
    """Require all nine still marked unverified and hosted on known agencies."""
    country_data = catalog["countries"]
    result = []
    for iso, hosts in EXPECTED_HOSTS.items():
        for category, host in zip(CATEGORIES, hosts):
            row = country_data[iso][category]
            if row.get("access") != "not_live_tested" or row.get("review") != "curated_candidate":
                raise ValueError("pilot_must_not_be_prelabelled_live")
            url = validate_url(row["url"], host)
            result.append({"iso": iso, "category": category, "host": host, "url": url})
    if len(result) != 9:
        raise ValueError("unexpected_pilot_size")
    return result


def probe_one(item, opener_factory=urllib.request.build_opener):
    """One HEAD request per site. No content download, no follow-up GET."""
    result = {
        "iso": item["iso"], "category": item["category"],
        "host": item["host"], "http_status": None,
        "reachable_http_200": False, "evidence_kind": "homepage_head_only",
        "feed_confirmed": False, "license_confirmed": False,
    }
    validate_url(item["url"], item["host"])
    headers = {"User-Agent": "WMM-GOV-RADAR-Agency-Reachability-QA/1.0",
               "Accept": "*/*"}
    request = urllib.request.Request(item["url"], method="HEAD", headers=headers)
    opener = opener_factory(RestrictedRedirects(item["host"]))
    try:
        with opener.open(request, timeout=10) as response:
            validate_url(response.geturl(), item["host"])
            result["http_status"] = int(response.status)
            result["reachable_http_200"] = response.status == 200
            result["outcome"] = "reachable_homepage_only" if response.status == 200 else "unconfirmed"
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
        result["outcome"] = "http_error_or_head_unsupported"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, OverflowError):
        result["outcome"] = "unavailable_or_restricted"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default="src/environment_weather_emergency_sites.json")
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    data = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    items = candidates(data)
    checks = [{**{"iso": x["iso"], "category": x["category"], "host": x["host"]},
               "outcome": "offline_registry_validated", "feed_confirmed": False}
              for x in items] if args.no_network else [probe_one(x) for x in items]
    print(json.dumps({
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "test_scope": "jo_ge_lu_nine_agency_homepages_not_193_national_live_feeds",
        "mode": "offline" if args.no_network else "one_https_head_per_site",
        "commercial_reuse_verified": False,
        "customer_notification": False,
        "site_published": False,
        "results": checks,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
