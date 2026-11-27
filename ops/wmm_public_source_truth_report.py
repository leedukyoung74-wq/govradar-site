#!/usr/bin/env python3
"""Read-only source truth evidence for existing hourly GOV RADAR operations watch.

Prevents treating manual country ideas, recorded agency URLs, search-level
tenders, or a four-page public smoke as proof of live verified operations.
No credentials, no writes to the public data branch, no POST or deployment.
"""
import datetime as dt
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RAW = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/"
ALLOWED = {"tenders.json", "sources_status.json", "site_check.json"}
UTC = dt.timezone.utc


def get_public(name):
    if name not in ALLOWED:
        raise ValueError("unapproved read-only feed")
    url = RAW + name
    if urllib.parse.urlsplit(url).hostname != "raw.githubusercontent.com":
        raise ValueError("unapproved source")
    req = urllib.request.Request(
        url, headers={"User-Agent": "WMM-GOVRADAR-public-provenance-audit/1.0"})
    with urllib.request.urlopen(req, timeout=14) as response:
        raw = response.read(2_500_001)
        if len(raw) > 2_500_000:
            raise ValueError("feed size over review cap")
        return json.loads(raw.decode("utf-8"))


def timestamp(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(UTC) if parsed.tzinfo else None
    except (ValueError, OverflowError, TypeError):
        return None


def build(opps, countries, regions, tenders, source_status, site_check, now=None):
    now = now or dt.datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    if not isinstance(opps, dict) or not isinstance(opps.get("items"), list):
        raise ValueError("unreadable manually curated opportunities")
    if not isinstance(countries, list) or not isinstance(regions, list):
        raise ValueError("unreadable legacy country/region indexes")
    if not isinstance(tenders, dict) or not isinstance(tenders.get("items"), list):
        raise ValueError("unreadable published tender feed")
    if not isinstance(source_status, dict) or not isinstance(site_check, dict):
        raise ValueError("unreadable published source/site evidence")

    notices = tenders["items"]
    opportunities = opps["items"]
    grades = {"search": 0, "partial": 0, "full": 0, "unknown": 0}
    for item in notices:
        if not isinstance(item, dict):
            grades["unknown"] += 1
            continue
        state = item.get("verify")
        grades[state if state in ("search", "partial", "full") else "unknown"] += 1
    when = timestamp(tenders.get("updated"))
    elapsed_h = round((now - when).total_seconds() / 3600, 2) if when else None
    tender_status = ("UNKNOWN" if elapsed_h is None or elapsed_h < -0.1
                     else "STALE" if elapsed_h > 30
                     else "WITHIN_30_HOUR_WINDOW")
    partial_sources = sum(
        1 for x in source_status.values() if isinstance(x, dict)
        and (x.get("state") == "PARTIAL" or x.get("coverage_partial") is True))
    failed_sources = sum(
        1 for x in source_status.values() if isinstance(x, dict)
        and x.get("state") in ("FAIL", "ERROR", "BLOCKED"))
    dapa = source_status.get("DAPA (Korea)") or {}
    kones = source_status.get("KONEPS (Korea)")
    pages = site_check.get("pages") or []
    sample_coverage = [p.get("page") for p in pages if isinstance(p, dict)]
    source_urls_present = sum(
        1 for x in opportunities if isinstance(x, dict)
        and bool(x.get("url") or x.get("source_url") or x.get("link")))

    result = {
        "schema_version": 1,
        "scope": "PUBLIC_READ_ONLY_PROVENANCE_AND_UPDATE_CADENCE",
        "checked_at_utc": now.astimezone(UTC).isoformat(),
        "static_opportunity_snapshot": {
            "classification": "CURATED_RESEARCH_SNAPSHOT_NOT_LIVE_TENDER",
            "updated": opps.get("updated"),
            "items": len(opportunities),
            "with_evidence_url": source_urls_present,
            "with_deadline": sum(1 for x in opportunities
                                 if isinstance(x, dict) and bool(x.get("deadline"))),
            "public_live_status_not_proven": True,
        },
        "legacy_index": {
            "countries_indexed": len(countries),
            "countries_marked_done": sum(1 for x in countries if isinstance(x, dict)
                                          and x.get("done") is True),
            "regions_indexed": len(regions),
            "regions_marked_done": sum(1 for x in regions if isinstance(x, dict)
                                        and x.get("done") is True),
            "different_from_live_page_content": True,
        },
        "official_tenders": {
            "published_updated": tenders.get("updated"),
            "elapsed_hours": elapsed_h,
            "freshness": tender_status,
            "total": len(notices),
            "verification_grades": grades,
            "all_items_individually_verified": grades["search"] == 0 and grades["partial"] == 0 and grades["unknown"] == 0,
        },
        "collector_coverage": {
            "partial_sources": partial_sources,
            "failed_sources": failed_sources,
            "koneps_published_source_in_status": bool(kones),
            "dapa_current_verified_notices": dapa.get("kept", None),
            "all_193_countries_collected_realtime": False,
        },
        "site_smoke_evidence": {
            "result": site_check.get("result"),
            "listed_pages_tested": len(sample_coverage),
            "seven_locale_browser_qa_verified": False,
            "login_payment_forms_verified": False,
        },
        "customer_records_accessed": False,
        "real_payments_executed": False,
        "production_site_changed": False,
        "new_schedule_created": False,
    }
    warnings = []
    if source_urls_present != len(opportunities):
        warnings.append("MANUAL_OPPORTUNITIES_LACK_PROVENANCE")
    if grades["search"] or grades["partial"] or grades["unknown"]:
        warnings.append("TENDER_SEARCH_OR_PARTIAL_VERIFICATION")
    if partial_sources or failed_sources:
        warnings.append("SOME_OFFICIAL_COLLECTORS_PARTIAL_OR_FAILED")
    if len(countries) != 193 or len(regions) != 23:
        warnings.append("INDEX_SCOPE_INCOMPLETE")
    if len(sample_coverage) < 7:
        warnings.append("SITE_SMOKE_NOT_SEVEN_LOCALES")
    if tender_status in ("STALE", "UNKNOWN"):
        warnings.append("PUBLISHED_TENDER_FRESHNESS_UNVERIFIED")
    result["warnings"] = warnings
    result["result"] = ("FAIL" if tender_status in ("STALE", "UNKNOWN") else
                        "PENDING" if warnings else "PASS")
    return result


def main():
    try:
        local = {name: json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
                 for name in ("opps.json", "countries.json", "regions.json")}
        published = {name: get_public(name) for name in sorted(ALLOWED)}
        report = build(local["opps.json"], local["countries.json"], local["regions.json"],
                       published["tenders.json"], published["sources_status.json"],
                       published["site_check.json"])
    except (OSError, UnicodeError, ValueError, TypeError,
            urllib.error.URLError) as exc:
        print(json.dumps({"result": "FAIL", "error_type": type(exc).__name__,
                          "reason": "SOURCE_TRUTH_READ_FAILED", "customer_records_accessed": False}))
        return 1
    # Only public aggregate statistics; do not emit raw documents or response URLs.
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as out:
            out.write("\n## GOV RADAR provenance / snapshot audit: " + report["result"] + "\n\n")
            o = report["static_opportunity_snapshot"]
            t = report["official_tenders"]
            c = report["collector_coverage"]
            out.write(f"- Manual research ideas: {o['items']} (source URLs {o['with_evidence_url']}, snapshot {o['updated']}) — NOT current live tenders\n")
            out.write(f"- Public tenders: {t['total']} (search-level {t['verification_grades']['search']}, full {t['verification_grades']['full']}, source timestamp {t['published_updated']})\n")
            out.write(f"- Collector coverage: PARTIAL {c['partial_sources']}, FAIL {c['failed_sources']}; KONEPS publication unverified\n")
            out.write(f"- Public site smoke: {report['site_smoke_evidence']['listed_pages_tested']} pages only; no verified sign-in, forms or payments\n")
            out.write("- GitHub schedule is best effort, not a five-minute realtime SLA. This audit does not deploy to the public website.\n")
    return 1 if report["result"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
