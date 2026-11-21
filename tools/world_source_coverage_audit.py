#!/usr/bin/env python3
"""WMM GOV RADAR evidence-only 193-country + 23-region official-source coverage.

No external network requests, no collection of article contents, no paid APIs,
no customer identifiers and NO claim that curated URLs are verified live feeds.
This reporter produces an internal research queue, NOT an operational alert.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT_TOOLS = Path(__file__).resolve().parent
if str(ROOT_TOOLS) not in sys.path:
    sys.path.insert(0, str(ROOT_TOOLS))
from government_business_sites import load_directory as load_government
from country_news_sources import load_directory as load_news
from environment_weather_emergency_sites import load_catalog as load_ewe, CATEGORIES

REGION_CATEGORIES = (
    "government_business", "news_media", "environment", "meteorology",
    "emergency", "defence_security", "public_health", "critical_infrastructure",
)
COUNTRY_CATEGORIES = (
    "government_business", "news_media", "environment", "weather",
    "emergency", "defence_security",
)


def _read(root, path):
    return json.loads((root / path).read_text(encoding="utf-8"))


def build_coverage(root):
    """Return a self-consistent, source-backed offline audit, with gaps explicit."""
    root = Path(root)
    meta = _read(root, "src/countries_meta.json")
    regions = _read(root, "src/regions.json")
    country_index = {x["iso"]: x for x in meta}
    region_index = {x["iso"]: x for x in regions}
    if len(meta) != 193 or len(country_index) != 193:
        raise ValueError("The sovereign country registry must contain 193 distinct codes")
    if len(regions) != 23 or len(region_index) != 23:
        raise ValueError("The separate special-region registry must contain 23 distinct codes")
    if set(region_index) & set(country_index):
        raise ValueError("Overlapping sovereign and special-region codes")
    if any(v["parent"] not in country_index for v in regions):
        raise ValueError("Special region has no sovereign parent")

    government, gov_report = load_government(root)
    news, news_report = load_news(root)
    _, ewe_report = load_ewe(root)
    defence_raw = _read(root, "src/country_defence_official_sources.json")["countries"]
    territory_raw = _read(root, "src/territory_official_sources.json")
    territories = territory_raw["territories"]
    ewe_counts = ewe_report["country_counts"]
    if set(defence_raw) != set(country_index) or set(territories) != set(region_index):
        raise ValueError("Country defence or territory coverage differs from official index")
    if set(territory_raw["categories"]) != set(REGION_CATEGORIES):
        raise ValueError("Territory categories must be explicitly separated")

    territory_out = {}
    territorial_government = territorial_news = 0
    territorial_news_missing = 0
    records = []
    countries = {}
    for iso in sorted(country_index):
        g = gov_report["country_counts"][iso]
        n = news_report["country_counts"][iso]
        e = ewe_counts[iso]
        defence = defence_raw[iso]["official_sites"]
        if any(s.get("access") != "not_live_tested" for s in defence):
            raise ValueError("Defence official-source links cannot claim live intelligence")
        countries[iso] = {
            "name_en": country_index[iso]["en"],
            "government_official_evidence": g["verified"],
            "government_unverified_candidates": g["candidate"],
            "government_gap_to_three": g["gap"],
            "news_publishers_recorded": n["publisher_links_recorded"],
            "news_gap_to_three": n["remaining_to_three"],
            "environment_weather_emergency_candidates": e["linked_candidates"],
            "environment_weather_emergency_missing": e["missing"],
            "defence_candidates": len(defence),
            "defence_structure": defence_raw[iso].get("defence_structure", "unknown"),
            "live_feed_verified": False,
        }
        counts = {
            "government_business": g["verified"], "news_media": n["publisher_links_recorded"],
            "environment": int(e["environment"]), "weather": int(e["weather"]),
            "emergency": int(e["emergency"]), "defence_security": len(defence),
        }
        for cat in COUNTRY_CATEGORIES:
            target = 3 if cat in ("government_business", "news_media", "defence_security") else 1
            records.append({
                "scope": "sovereign", "iso": iso, "parent_iso": "", "name": country_index[iso]["en"],
                "category": cat, "registered": counts[cat],
                "minimum_target": target, "remaining": max(0, target - counts[cat]),
                "status": "SOURCE_EVIDENCE_NOT_LIVE_VERIFIED",
            })

    for iso in sorted(region_index):
        t = territories[iso]
        if t.get("parent_iso") != region_index[iso]["parent"]:
            raise ValueError("Territory-parent registry mismatch: " + iso)
        region_counts = {}
        for cat in REGION_CATEGORIES:
            rows = t[cat]
            if any(s.get("access") != "not_live_tested" for s in rows):
                raise ValueError("Territory source is not a verified live alert feed: " + iso)
            region_counts[cat] = len(rows)
            target = 3 if cat in ("government_business", "news_media") else 1
            records.append({
                "scope": "special_region", "iso": iso, "parent_iso": t["parent_iso"],
                "name": t["name_en"], "category": cat, "registered": len(rows),
                "minimum_target": target, "remaining": max(0, target - len(rows)),
                "status": "CURATED_CANDIDATE_NOT_LIVE_TESTED",
            })
        territorial_government += region_counts["government_business"]
        territorial_news += region_counts["news_media"]
        territorial_news_missing += max(0, 3 - region_counts["news_media"])
        territory_out[iso] = {
            "name_en": t["name_en"], "parent_iso": t["parent_iso"],
            "category_counts": region_counts, "live_feed_verified": False,
        }

    gov_gaps = sorted(iso for iso, row in countries.items() if row["government_gap_to_three"] > 0)
    return {
        "schema": "wmm-world-source-coverage-offline.v1",
        "scope": {"sovereign_countries": len(country_index), "special_regions": len(region_index)},
        "policy": "Curated directory references and documented agency relationships do NOT verify a live fetch, active alert feed, redistribution rights or government cyber-incident confirmation.",
        "live_verified_url_count": 0,
        "production_feed_connected": False,
        "government": {
            "source_evidence_countries_with_3": gov_report["verified_countries"],
            "source_evidence_links": gov_report["verified_links"],
            "missing_minimum_slots": gov_report["remaining_required_link_slots"],
            "incomplete_countries": gov_gaps,
        },
        "news": {
            "publisher_links_recorded": news_report["registered_publisher_links"],
            "countries_with_3": news_report["countries_with_at_least_three_recorded"],
            "remaining_minimum_slots": news_report["remaining_minimum_link_slots"],
        },
        "environment_weather_emergency": {
            "complete_countries": ewe_report["linked_candidate_countries_all_three"],
            "candidate_links": ewe_report["linked_candidate_total"],
            "candidate_links_by_category": ewe_report["candidate_links_by_category"],
            "missing_national_category_links": ewe_report["missing_national_category_links"],
            "countries": {
                iso: {"candidate_total": data["linked_candidates"], "missing": data["missing"]}
                for iso, data in sorted(ewe_counts.items())
            },
        },
        "national_defence": {
            "countries_with_any_candidate": sum(bool(v["official_sites"]) for v in defence_raw.values()),
            "countries_with_3_candidates": sum(len(v["official_sites"]) >= 3 for v in defence_raw.values()),
            "candidate_links": sum(len(v["official_sites"]) for v in defence_raw.values()),
            "warning": "Civilian responsibilities and standing-army distinctions are not interchangeable.",
        },
        "territory_coverage": {
            "government_business_links": territorial_government,
            "news_media_links": territorial_news,
            "news_media_remaining_to_3": territorial_news_missing,
            "candidate_links_by_category": {
                k: sum(len(territories[iso][k]) for iso in region_index)
                for k in REGION_CATEGORIES
            },
        },
        "countries": countries,
        "territories": territory_out,
        "records": records,
    }


def export_coverage(audit, output_dir):
    """Write a fresh private review queue, never the public deployed data tree."""
    out = Path(output_dir).resolve()
    if {p.lower() for p in out.parts} & {"dist", "public", "live", "data_branch", "cf"}:
        raise ValueError("Refuse output inside public/deployment path")
    report = out / "world-source-coverage.json"
    queue = out / "world-source-gap-queue.csv"
    if report.exists() or queue.exists():
        raise FileExistsError("Refuse to overwrite an existing source-gap report")
    out.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with queue.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=(
            "scope", "iso", "parent_iso", "name", "category",
            "registered", "minimum_target", "remaining", "status"))
        writer.writeheader()
        for row in audit["records"]:
            writer.writerow(row)
    return {"json": str(report), "csv": str(queue)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True, help="New internal review directory (not dist/public)")
    args = parser.parse_args()
    report = build_coverage(args.root)
    paths = export_coverage(report, args.output)
    print(json.dumps({
        "193_countries": report["scope"]["sovereign_countries"],
        "23_special_regions": report["scope"]["special_regions"],
        "government_links": report["government"]["source_evidence_links"],
        "government_gaps": report["government"]["missing_minimum_slots"],
        "news_links": report["news"]["publisher_links_recorded"],
        "news_gaps": report["news"]["remaining_minimum_slots"],
        "ewe_candidates": report["environment_weather_emergency"]["candidate_links"],
        "ewe_gaps": report["environment_weather_emergency"]["missing_national_category_links"],
        "live_connections_verified": 0,
        "output": paths,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
