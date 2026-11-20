"""Build a country-by-country directory without fabricating official status.

The legacy national source registry is a candidate ledger, not a list of
government-verified pages. Its HTTP 200 statuses cannot count towards the
owner's target of >=3 independently verified sites per sovereign state.
"""
import json
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA_VERSION = 1
REQUIRED_CATEGORIES = frozenset(("procurement", "support", "investment"))


def safe_https(url):
    try:
        x = urlsplit(url)
        return (x.scheme == "https" and bool(x.hostname) and not x.username
                and not x.password and not x.port and not any(v in url for v in ("\n", "\r", "\t")))
    except (ValueError, TypeError):
        return False


def key(url):
    x = urlsplit(url)
    return (x.hostname or "").lower() + x.path.rstrip("/").lower()


def load_directory(root):
    root = Path(root)
    meta = json.loads((root / "src/countries_meta.json").read_text(encoding="utf-8"))
    isos = {x["iso"] for x in meta}
    if len(isos) != 193:
        raise ValueError("expected 193 unique sovereign-state ISO identifiers")
    direct = json.loads((root / "src/government_business_sites.json").read_text(encoding="utf-8"))
    if direct.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("government site catalog schema version is not supported")
    verified_rows = direct.get("countries")
    if not isinstance(verified_rows, dict) or set(verified_rows) - isos:
        raise ValueError("verified government site list contains invalid country codes")
    sites = {iso: [] for iso in isos}
    already = {iso: set() for iso in isos}
    for iso, rows in verified_rows.items():
        if not isinstance(rows, list):
            raise ValueError("government catalog country entry must be a list")
        for row in rows:
            url = row.get("url", "")
            if (not safe_https(url) or not safe_https(row.get("evidence_url", ""))
                or row.get("category") not in REQUIRED_CATEGORIES
                or row.get("verification") != "official_primary"
                or not row.get("name_ko") or not row.get("name_en")
                or not row.get("verified_on")):
                raise ValueError("invalid verified official government site for " + iso)
            if key(url) in already[iso]:
                raise ValueError("duplicate verified official government site for " + iso)
            already[iso].add(key(url))
            sites[iso].append(dict(row))

    reg = json.loads((root / "tools/sources/registry.json").read_text(encoding="utf-8"))
    entries = reg if isinstance(reg, list) else list(reg.values())
    for row in entries:
        iso, url = row.get("iso", ""), row.get("url", "")
        if (row.get("kind") != "national-portal" or iso not in isos
            or row.get("url_status") != "200" or not safe_https(url)
            or key(url) in already[iso]):
            continue
        already[iso].add(key(url))
        sites[iso].append({"name_ko": row.get("name") or iso,
                           "name_en": row.get("name") or iso,
                           "url": url, "category": "procurement",
                           "verification": "registry_candidate",
                           "verified_on": "",
                           "evidence_url": "",
                           "note": "Historical registry HTTP response; official agency status unconfirmed"})

    report = {
        "target_countries": len(isos),
        "minimum_verified_per_country": 3,
        "target_verified_links": len(isos) * 3,
        "verified_countries": 0,
        "verified_links": 0,
        "countries_below_target": [],
        "candidate_only_countries": [],
        "country_counts": {},
    }
    for iso in sorted(isos):
        n = sum(x["verification"] == "official_primary" for x in sites[iso])
        report["country_counts"][iso] = {"verified": n,
                                          "candidate": len(sites[iso]) - n,
                                          "gap": max(0, 3 - n)}
        report["verified_links"] += n
        if n >= 3:
            report["verified_countries"] += 1
        else:
            report["countries_below_target"].append(iso)
            if n == 0:
                report["candidate_only_countries"].append(iso)
    report["remaining_required_link_slots"] = sum(x["gap"] for x in report["country_counts"].values())
    return sites, report
