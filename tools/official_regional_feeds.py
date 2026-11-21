#!/usr/bin/env python3
"""UK Environment Agency flood and JMA official XML index: internal-only pilot.

Only metadata from two provider-documented free public information endpoints.
No login, dark-web source, user data, government website scanning, or website
deployment. A JMA Atom entry is a *recent bulletin*, NOT a current alert.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UTC = dt.timezone.utc
EA_URL = "https://environment.data.gov.uk/flood-monitoring/id/floods"
JMA_URL = "https://www.data.jma.go.jp/developer/xml/feed/extra.xml"
CAP = 8_000_000
ATOM = "{http://www.w3.org/2005/Atom}"
VALID_EA_SEVERITY = frozenset(("Flood Alert", "Flood Warning", "Severe Flood Warning"))
MAX_STORED = 100
DOCS = {
    "ea": "https://environment.data.gov.uk/flood-monitoring/doc/reference",
    "jma": "https://xml.kishou.go.jp/xmlpull.html",
}


def iso(now):
    return now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def time_of(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        moment = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if moment.tzinfo is None:
            return None
        return moment.astimezone(UTC)
    except (ValueError, OverflowError):
        return None


def is_allowed_url(value, provider):
    if not isinstance(value, str) or re.search(r"[\x00-\x20\\]", value):
        return False
    try:
        u = urllib.parse.urlsplit(value)
        if (u.scheme != "https" or not u.hostname or u.username
            or u.password or u.port is not None or u.fragment):
            return False
        if provider == "ea":
            return u.hostname == "environment.data.gov.uk" and (
                u.path == "/flood-monitoring/id/floods"
                or u.path.startswith("/flood-monitoring/id/floods/")
            )
        if provider == "jma":
            return u.hostname == "www.data.jma.go.jp" and (
                u.path == "/developer/xml/feed/extra.xml"
                or u.path.startswith("/developer/xml/data/")
            )
        return False
    except (ValueError, TypeError):
        return False


class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_allowed_url(newurl, self.provider):
            raise ValueError("redirect_not_allowlisted")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_official(url, provider):
    if not is_allowed_url(url, provider):
        raise ValueError("source_not_allowlisted")
    opener = urllib.request.build_opener(StrictRedirect(provider))
    req = urllib.request.Request(url, headers={
        "User-Agent": "WMM-GOV-RADAR/1.0 (official public source metadata, https://radar.wmm-hoa.com/)",
        "Accept": "application/json" if provider == "ea" else "application/atom+xml,application/xml",
    })
    with opener.open(req, timeout=25) as response:
        if response.status != 200 or not is_allowed_url(response.geturl(), provider):
            raise ValueError("source_not_ok")
        content = response.read(CAP + 1)
    if len(content) > CAP:
        raise ValueError("source_too_large")
    return content


def parse_england_floods(raw, now):
    """EA warnings apply to England, not all of United Kingdom."""
    if not isinstance(raw, dict) or not isinstance(raw.get("items"), list):
        raise ValueError("ea_bad_schema")
    rows = raw["items"]
    if len(rows) > 20000:
        raise ValueError("ea_too_many")
    result, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("ea_invalid_row")
        severity = row.get("severity")
        if severity == "Warning no Longer in Force":
            continue
        if severity not in VALID_EA_SEVERITY:
            raise ValueError("ea_unknown_severity")
        key = str(row.get("floodAreaID") or row.get("@id") or "")
        if not key or key in seen:
            raise ValueError("ea_duplicate_or_missing_id")
        seen.add(key)
        official = row.get("@id", "")
        if not is_allowed_url(official, "ea"):
            official = EA_URL
        area = row.get("floodArea")
        if not isinstance(area, dict):
            area = {}
        result.append({
            "source_id": key[:160],
            "title": str(row.get("description") or severity)[:200],
            "area": str(area.get("label") or row.get("floodAreaID") or "")[:180],
            "severity": severity,
            "source_url": official,
            "issued_at": str(row.get("timeRaised") or "")[:48],
            "changed_at": str(row.get("timeMessageChanged") or "")[:48],
            "source": "UK Environment Agency",
            "confirmed_active": True,
            "not_a_cyberattack_report": True,
        })
    rank = {"Severe Flood Warning": 0, "Flood Warning": 1, "Flood Alert": 2}
    result.sort(key=lambda x: (rank.get(x["severity"], 9), x["source_id"]))
    return {
        "schema": "wmm.official_regional.1", "provider": "ea",
        "geo_scope": "GB-ENG", "source_is_official": True,
        "source_name": "Environment Agency",
        "official_url": EA_URL, "feed_type": "active_flood_warnings_england",
        "count": len(result), "display_count": min(len(result), MAX_STORED),
        "items": result[:MAX_STORED],
        "government_website_cyberattack_confirmed": False,
        "attribution": "This uses Environment Agency flood and river level data from the real-time data API (Beta).",
        "license": "UK Open Government Licence v3.0",
        "scope_note": "England only. A flood warning is not proof of an attack or certain business loss."
    }


def parse_jma_feed(raw, now):
    if not isinstance(raw, bytes) or not raw or len(raw) > CAP:
        raise ValueError("jma_invalid_payload")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("jma_dtd_rejected")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        raise ValueError("jma_bad_xml") from None
    if root.tag != ATOM + "feed":
        raise ValueError("jma_not_atom")
    result, seen = [], set()
    entries = root.findall(ATOM + "entry")
    if len(entries) > 5000:
        raise ValueError("jma_too_many")
    for ent in entries:
        title = (ent.findtext(ATOM + "title") or "").strip()
        moment = time_of(ent.findtext(ATOM + "updated") or ent.findtext(ATOM + "published"))
        if not title or moment is None or moment > now + dt.timedelta(minutes=5):
            continue
        if now - moment > dt.timedelta(hours=48):
            continue
        official = ""
        for link in ent.findall(ATOM + "link"):
            candidate = link.attrib.get("href") or ""
            if is_allowed_url(candidate, "jma") and candidate != JMA_URL:
                official = candidate
                break
        if not official or official in seen:
            continue
        seen.add(official)
        result.append({
            "source_id": (ent.findtext(ATOM + "id") or official)[:200],
            "title": title[:200],
            "issued_at": iso(moment),
            "source_url": official,
            "source": "Japan Meteorological Agency",
            "confirmed_active": False,
            "bulletin_only": True,
            "not_a_cyberattack_report": True,
        })
    result.sort(key=lambda x: x["issued_at"], reverse=True)
    return {
        "schema": "wmm.official_regional.1", "provider": "jma",
        "geo_scope": "JP", "source_is_official": True,
        "source_name": "Japan Meteorological Agency",
        "official_url": JMA_URL, "feed_type": "recent_jma_xml_bulletin_index",
        "count": len(result), "display_count": min(len(result), MAX_STORED),
        "items": result[:MAX_STORED],
        "government_website_cyberattack_confirmed": False,
        "attribution": "Japan Meteorological Agency (JMA)",
        "license": "Government of Japan Standard Terms of Use; verify reuse for each downstream use",
        "scope_note": "Bulletins published recently; NOT proof warnings remain in effect. Read full bulletin before action."
    }


def save_private(path, value):
    path = Path(path).resolve()
    banned = {"dist", "public", "live", "data_branch"}
    if any(part.lower() in banned for part in path.parts):
        raise ValueError("refuse_public_output_directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".wmm-source-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def error_code(e):
    if isinstance(e, TimeoutError):
        return "timeout"
    if isinstance(e, json.JSONDecodeError):
        return "invalid_json"
    if isinstance(e, urllib.error.HTTPError):
        return "HTTP_" + str(e.code)
    if isinstance(e, ValueError):
        label = str(e)
        return label if label in {
            "source_not_allowlisted", "redirect_not_allowlisted", "source_not_ok",
            "source_too_large", "ea_bad_schema", "ea_invalid_row",
            "ea_unknown_severity", "ea_duplicate_or_missing_id", "ea_too_many",
            "jma_invalid_payload", "jma_dtd_rejected", "jma_bad_xml", "jma_not_atom",
            "jma_too_many"
        } else "source_invalid"
    return "source_unavailable"


def run_collector(output, now, fetchers):
    path = Path(output).resolve()
    if set(p.lower() for p in path.parts) & {"dist", "public", "live", "data_branch"}:
        raise ValueError("refuse_public_output_directory")
    old = {}
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(old, dict) or not isinstance(old.get("feeds"), dict)
            or not isinstance(old.get("feed_health"), dict)):
            raise ValueError("invalid_previous_report")
    result = {
        "schema": "wmm.official_regional.internal.1",
        "checked_at": iso(now), "public_publish_allowed": False,
        "customer_data_processed": False, "cyberattack_confirmed": False,
        "customer_impact_confirmed": False,
        "feeds": {}, "feed_health": {},
    }
    for provider, fn, parse in (
        ("ea", fetchers["ea"], parse_england_floods),
        ("jma", fetchers["jma"], parse_jma_feed)
    ):
        previous = old.get("feed_health", {}).get(provider, {})
        try:
            fresh = fn()
            if provider == "ea" and isinstance(fresh, bytes):
                fresh = json.loads(fresh)
            feed = parse(fresh, now)
            result["feeds"][provider] = feed
            result["feed_health"][provider] = {
                "status": "OK", "last_success_at": iso(now), "last_checked_at": iso(now),
                "stale": False, "last_error": None,
                "original_source": EA_URL if provider == "ea" else JMA_URL,
                "rights_reference": DOCS[provider]
            }
        except (OSError, ValueError, ET.ParseError, TypeError, json.JSONDecodeError) as exc:
            prev_feed = old.get("feeds", {}).get(provider)
            result["feeds"][provider] = prev_feed if isinstance(prev_feed, dict) else {
                "provider": provider, "items": [], "source_is_official": False,
                "geo_scope": "GB-ENG" if provider == "ea" else "JP",
                "feed_type": "unknown_due_to_fetch_failure",
                "count": None,
                "government_website_cyberattack_confirmed": False
            }
            result["feed_health"][provider] = {
                "status": "STALE" if isinstance(prev_feed, dict) else "ERROR",
                "last_success_at": previous.get("last_success_at"),
                "last_checked_at": iso(now), "stale": True, "last_error": error_code(exc),
                "original_source": EA_URL if provider == "ea" else JMA_URL,
                "rights_reference": DOCS[provider]
            }
    save_private(path, result)
    return result


def main():
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--out", required=True, type=Path)
    args = arg.parse_args()
    now = dt.datetime.now(UTC)
    r = run_collector(args.out, now, {
        "ea": lambda: fetch_official(EA_URL, "ea"),
        "jma": lambda: fetch_official(JMA_URL, "jma"),
    })
    print(json.dumps({
        "checked_at": r["checked_at"], "all_ok": all(
            v["status"] == "OK" for v in r["feed_health"].values()),
        "feeds": {k: {"status": r["feed_health"][k]["status"],
                       "last_success_at": r["feed_health"][k]["last_success_at"],
                       "error_category": r["feed_health"][k]["last_error"],
                       "record_count": (r["feeds"][k].get("count") if r["feed_health"][k]["status"] == "OK" else None)}
                  for k in ("ea", "jma")},
        "external_customer_data": False,
        "published_to_site": False
    }, ensure_ascii=False))
    return 0 if all(v["status"] == "OK" for v in r["feed_health"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
