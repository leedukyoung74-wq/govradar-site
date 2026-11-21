"""Check published GOV RADAR snapshots without collecting or writing production feeds."""

import argparse
import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import urllib.request


UTC = dt.timezone.utc
KST = dt.timezone(dt.timedelta(hours=9))
BASE = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/"
RAPID_PATHS = ("hz/official.json", "hz/nws_active.json")
DAILY_PATHS = RAPID_PATHS + (
    "hz/cisa_kev.json", "feeds/tenders.json", "feeds/cty/_summary.json",
    "feeds/today.json", "feeds/active.json", "feeds/awards.json", "feeds/pipeline.json",
    "feeds/econ.json", "feeds/sanctions.json", "feeds/sources_status.json",
)
OWNERS = {
    "cneos": "us-nasa", "eonet": "us-nasa", "gdacs": "un-eu-gdacs",
    "nws": "us-noaa", "swpc": "us-noaa", "usgs": "us-usgs", "who": "who",
    "cisa": "us-cisa",
}
TENDER_PUBLISHERS = {
    "eu ted": "EU TED", "world bank": "World Bank", "uk find a tender": "UK Find a Tender",
    "uk fts": "UK Find a Tender", "uk contracts finder": "UK Contracts Finder",
    "sam.gov": "SAM.gov", "us sam.gov": "SAM.gov", "kr dapa": "DAPA", "dapa": "DAPA",
    "oecd": "OECD",
}
LIMIT = 12_000_000


def mapping(value):
    return value if isinstance(value, dict) else {}


def series(value):
    return value if isinstance(value, list) else []


def age_minutes(value, now, fallback_tz):
    if not isinstance(value, str) or not (10 < len(value) < 55):
        return None
    try:
        stamp = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if not stamp.tzinfo:
        stamp = stamp.replace(tzinfo=fallback_tz)
    return round((now - stamp).total_seconds() / 60, 1)


def audit(payloads, mode, now):
    findings, checks, owners = [], [], {}

    def check(key, document, stamp, max_age, *, count=None, owner=None, scope=None,
              healthy=True, required=False, zone=UTC):
        age = age_minutes(stamp, now, zone)
        code, severity = None, None
        if not document:
            code, severity = "unavailable", "BLOCKED" if required else "REVIEW"
        elif age is not None and age < -5:
            code, severity = "future-timestamp", "BLOCKED"
        elif not healthy:
            code, severity = ("upstream-failed-cached" if count else "upstream-failed"), "REVIEW"
        elif age is None:
            code, severity = "missing-timestamp", "REVIEW"
        elif age > max_age:
            code, severity = "stale", "REVIEW"
        checks.append({"id": key, "age_minutes": age, "max_minutes": max_age,
                       "count": count, "scope": scope, "state": severity or "PASS"})
        if code:
            findings.append({"id": key, "code": code, "severity": severity})
        if not code and owner:
            owners.setdefault(owner, set()).add(key)

    official = mapping(payloads.get(RAPID_PATHS[0]))
    agency = mapping(official.get("sources"))
    items = mapping(official.get("items"))
    usgs = mapping(agency.get("usgs"))
    check("usgs-fast", official, official.get("usgs_fast_checked"), 20,
          count=len(series(items.get("usgs"))), healthy=usgs.get("ok") is True, required=True, zone=KST)

    def official_agency(key, max_age):
        meta = mapping(agency.get(key))
        count = len(series(items.get(key)))
        check(key, meta, meta.get("last_ok"), max_age, count=count,
              owner=OWNERS[key], healthy=meta.get("ok") is True, zone=KST)

    official_agency("usgs", 35)
    official_agency("gdacs", 36 * 60)

    def distinct_feed(key, path, limit, scope):
        doc = mapping(payloads.get(path))
        health = mapping(doc.get("source_health"))
        check(key, doc, health.get("last_ok"), limit, count=len(series(doc.get("items"))),
              owner=OWNERS[key], scope=scope,
              healthy=health.get("ok") is True and health.get("stale") is False)

    distinct_feed("nws", RAPID_PATHS[1], 55, "us-only")
    if mode == "daily":
        distinct_feed("cisa", DAILY_PATHS[2], 24 * 60, "public-verified-vulnerabilities")
        for key in ("eonet", "who", "cneos", "swpc"):
            official_agency(key, 36 * 60)
        for key, path in zip(
            ("tenders", "country-tenders", "today", "active", "awards", "pipeline", "economy", "sanctions"),
            DAILY_PATHS[3:-1],
        ):
            doc = mapping(payloads.get(path))
            check(key, doc, doc.get("updated"), 36 * 60, count=len(series(doc.get("items"))) if "items" in doc else None,
                  required=key in {"tenders", "today"}, zone=KST)
        sources = mapping(payloads.get(DAILY_PATHS[-1]))
        for key, value in sorted(sources.items()):
            label = TENDER_PUBLISHERS.get(key.strip().lower())
            if not label:
                if not any(f["id"] == "tender-sources" and f["code"] == "unclassified-source" for f in findings):
                    findings.append({"id": "tender-sources", "code": "unclassified-source", "severity": "REVIEW"})
                continue
            state = mapping(value).get("state")
            if state != "SUCCESS":
                code = {"SKIPPED": "source-skipped", "PARTIAL": "source-partial"}.get(state, "source-failed")
                findings.append({"id": label, "code": code, "severity": "REVIEW"})

    severity = {finding["severity"] for finding in findings}
    status = "BLOCKED" if "BLOCKED" in severity else "REVIEW" if severity else "PASS"
    return {"schema_version": 1, "mode": mode, "checked_at_kst": now.astimezone(KST).isoformat(),
            "status": status, "can_stage_review": status != "BLOCKED", "checks": checks,
            "findings": findings, "independence": {
                "available_official_owner_groups": {k: sorted(v) for k, v in sorted(owners.items())},
                "claim_corroborated": False,
            }}


def load(path, snapshot):
    try:
        if snapshot is not None:
            with (snapshot / path).open("rb") as stream:
                payload = stream.read(LIMIT + 1)
        else:
            request = urllib.request.Request(BASE + path, headers={
                "User-Agent": "WMM-GOV-RADAR-health/1.0", "Cache-Control": "no-cache",
            })
            with urllib.request.urlopen(request, timeout=14) as response:
                if response.url != BASE + path:
                    return None
                payload = response.read(LIMIT + 1)
        return json.loads(payload) if len(payload) <= LIMIT else None
    except (OSError, UnicodeError, ValueError):
        return None


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(stream.name, path)


def inspect(mode, snapshot=None, now=None):
    paths = DAILY_PATHS if mode == "daily" else RAPID_PATHS
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        values = pool.map(lambda path: load(path, snapshot), paths)
        payloads = dict(zip(paths, values))
    return audit(payloads, mode, now or dt.datetime.now(UTC))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("daily", "rapid"), required=True)
    provider = parser.add_mutually_exclusive_group(required=True)
    provider.add_argument("--snapshot", type=Path)
    provider.add_argument("--published", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = inspect(args.mode, args.snapshot)
    atomic_json(args.output, report)
    return {"PASS": 0, "REVIEW": 2, "BLOCKED": 1}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
