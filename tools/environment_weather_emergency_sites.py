"""193 sovereign-country environment / weather / emergency source directory.

The primary entries are curated REVIEW CANDIDATES, not verified live feeds.
For missing national entries show clearly labelled UNEP/WMO/UNDRR directories;
those international directories NEVER count as national agency links.
"""
import json
from pathlib import Path
from urllib.parse import urlsplit

CATEGORIES = ("environment", "weather", "emergency")

def safe_https(url):
    if not isinstance(url, str) or any(c in url for c in ("\n", "\r", "\t")):
        return False
    try:
        x = urlsplit(url)
        return (x.scheme == "https" and bool(x.hostname)
                and x.username is None and x.password is None
                and x.port is None and x.fragment == "")
    except (ValueError, TypeError):
        return False

def load_catalog(root):
    root = Path(root)
    meta = json.loads((root / "src/countries_meta.json").read_text(encoding="utf-8"))
    sovereign = [x["iso"] for x in meta]
    if len(sovereign) != 193 or len(set(sovereign)) != 193:
        raise ValueError("invalid 193 country ISO list")
    data = json.loads((root / "src/environment_weather_emergency_sites.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported EWE catalog schema")
    items = data.get("countries")
    if not isinstance(items, dict) or set(items) != set(sovereign):
        raise ValueError("EWE catalog must explicitly account for all 193 sovereign countries")
    directory = data.get("directory_refs")
    if not isinstance(directory, dict) or set(directory) != set(CATEGORIES):
        raise ValueError("three fallback directory references required")
    if not all(safe_https(directory[k]) for k in CATEGORIES):
        raise ValueError("unsafe international directory URL")

    totals = {k: 0 for k in CATEGORIES}
    counts = {}
    completed = 0
    for iso in sovereign:
        entry = items[iso]
        if not isinstance(entry, dict) or set(entry) != set(CATEGORIES):
            raise ValueError("invalid national-category record for " + iso)
        n = 0
        for kind in CATEGORIES:
            row = entry[kind]
            if row is None:
                continue
            if (not isinstance(row, dict) or not safe_https(row.get("url"))
                or not isinstance(row.get("name"), str) or not row["name"].strip()
                or row.get("review") != "curated_candidate"
                or row.get("access") != "not_live_tested"):
                raise ValueError("source missing cautious provenance or unsafe URL: " + iso + " " + kind)
            totals[kind] += 1
            n += 1
        counts[iso] = {"linked_candidates": n, "missing": 3-n,
                       "environment": bool(entry["environment"]),
                       "weather": bool(entry["weather"]),
                       "emergency": bool(entry["emergency"]),
                       "live_verified": 0}
        if n == 3:
            completed += 1
    report = {
        "schema_version": 1,
        "target_countries": 193,
        "target_category_links": 579,
        "linked_candidate_countries_all_three": completed,
        "candidate_links_by_category": totals,
        "linked_candidate_total": sum(totals.values()),
        "missing_national_category_links": 579-sum(totals.values()),
        "live_verified_total": 0,
        "country_counts": counts,
        "warning": "Curated agency references, not independently live-verified; no 24h emergency response or alert-feed guarantee.",
        "international_directory_refs": directory
    }
    return items, report
