#!/usr/bin/env python3
"""WMM pilot: Hong Kong Observatory RSS warnings + NZ GeoNet observed quakes.

Read-only public metadata, exactly two official allowlisted hosts, no secrets,
no customer profiling, no public release, and no cyberattack inference.
GeoNet quake list covers 365 days but WMM keeps only recent 48h events.
HKO summary dates may not prove a warning active: no automatic urgent alerts.
"""
import argparse
import datetime as dt
from email.utils import parsedate_to_datetime
import json
import math
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UTC = dt.timezone.utc
HKO_URL = "https://rss.weather.gov.hk/rss/WeatherWarningSummaryv2.xml"
GEONET_URL = "https://api.geonet.org.nz/quake?MMI=3"
MAX_BYTES = 8_000_000
MAX_ITEMS = 100
HKO_LINK_HOSTS = {"www.hko.gov.hk", "www.weather.gov.hk"}
SOURCE_DOCS = {
    "hko": "https://data.gov.hk/en-data/dataset/hk-hko-rss-weather-warning-summary",
    "geonet": "https://api.geonet.org.nz/",
}


def iso(value):
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_datetime(value):
    if not value or not isinstance(value, str):
        return None
    try:
        moment = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return moment.astimezone(UTC) if moment.tzinfo else None
    except (ValueError, OverflowError):
        return None


def allowed(url, provider):
    if not isinstance(url, str) or re.search(r"[\x00-\x20\\]", url):
        return False
    try:
        parts = urllib.parse.urlsplit(url)
        if (parts.scheme != "https" or parts.username or parts.password or parts.fragment
            or parts.port is not None):
            return False
        if provider == "hko":
            return (parts.hostname == "rss.weather.gov.hk"
                    and parts.path == "/rss/WeatherWarningSummaryv2.xml"
                    and not parts.query)
        if provider == "geonet":
            return (parts.hostname == "api.geonet.org.nz"
                    and parts.path == "/quake"
                    and parts.query == "MMI=3")
    except (ValueError, TypeError):
        return False
    return False


def hko_item_url(url):
    try:
        if not isinstance(url, str) or re.search(r"[\x00-\x20\\]", url):
            return HKO_URL
        v = urllib.parse.urlsplit(url)
        if (v.scheme == "https" and v.hostname in HKO_LINK_HOSTS
                and v.port is None and not v.username and not v.password
                and not v.fragment and v.path.startswith("/")):
            return url
    except (ValueError, TypeError):
        pass
    return HKO_URL


class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, provider):
        self.provider = provider
        super().__init__()
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl, self.provider):
            raise ValueError("redirect_not_allowlisted")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_source(provider):
    url = HKO_URL if provider == "hko" else GEONET_URL
    if not allowed(url, provider):
        raise ValueError("source_not_allowlisted")
    headers = {
        "User-Agent": "WMM-GOV-RADAR/1.0 (public agency data for internal quality checks)",
        "Accept": "application/rss+xml,application/xml,text/xml" if provider == "hko" else "application/vnd.geo+json;version=2",
    }
    opener = urllib.request.build_opener(StrictRedirect(provider))
    with opener.open(urllib.request.Request(url, headers=headers), timeout=25) as resp:
        if resp.status != 200 or not allowed(resp.geturl(), provider):
            raise ValueError("source_not_ok")
        raw = resp.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("source_too_large")
    return raw if provider == "hko" else json.loads(raw)


def parse_hko_rss(raw, now):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
        raise ValueError("hko_bad_payload")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("unsafe_xml")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        raise ValueError("invalid_rss_xml") from None
    channel = root.find("channel")
    if root.tag.lower() != "rss" or channel is None or not channel.findtext("title"):
        raise ValueError("invalid_rss_schema")
    raw_items = channel.findall("item")
    if len(raw_items) > 300:
        raise ValueError("too_many_rss_items")
    results, seen = [], set()
    empty_marker = False
    for entry in raw_items:
        title = (entry.findtext("title") or "").strip()
        desc = (entry.findtext("description") or "").strip()
        if not title:
            continue
        phrase = (title + " " + desc).casefold()
        if any(p in phrase for p in ("no weather warning", "no warning is in force",
                                      "no warning in force", "no warnings in force")):
            empty_marker = True
            continue
        pubdate = (entry.findtext("pubDate") or "").strip()
        timestamp = None
        if pubdate:
            try:
                candidate = parsedate_to_datetime(pubdate)
                timestamp = candidate.astimezone(UTC) if candidate.tzinfo else None
            except (ValueError, TypeError, OverflowError):
                pass
        seenkey = title.casefold()
        if seenkey in seen:
            continue
        seen.add(seenkey)
        recent = bool(timestamp and now - dt.timedelta(minutes=5) <= timestamp
                      + dt.timedelta(days=1) and timestamp <= now + dt.timedelta(minutes=5))
        results.append({
            "title": title[:220], "source_url": hko_item_url((entry.findtext("link") or "").strip()),
            "published_utc": iso(timestamp) if timestamp else None,
            "current_verified": False,  # RSS index alone never authorizes an urgent business alert
            "warning_summary_not_individual_cap": True,
            "observed_rss_item": True,
            "freshly_published": recent,
        })
    warning_state = (
        "NO_WARNINGS_IN_SUMMARY" if empty_marker and not results else
        "SUMMARY_AGE_UNVERIFIED" if results and not any(x["freshly_published"] for x in results) else
        "OFFICIAL_SUMMARY_REQUIRES_HUMAN_CHECK" if results else
        "EMPTY_SUMMARY_CHECK_SOURCE"
    )
    return {
        "schema": "wmm.regional-hk-nz.v1", "provider": "hko",
        "geo_scope": "CN-HK", "sovereign_parent": "CN",
        "source_name": "Hong Kong Observatory",
        "source_url": HKO_URL,
        "feed_type": "current_official_warning_summary",
        "warning_state": warning_state, "count": len(results),
        "items": results[:MAX_ITEMS], "source_is_official": True,
        "government_website_attack_confirmed": False,
        "confirmed_customer_impact": False,
        "notice": "Hong Kong SAR only, not all China. Do not issue automatic urgent warnings from RSS text alone.",
        "rights": "HKO open-data DATA.GOV.HK terms; source and government attribution required",
    }


def parse_geonet_quakes(raw, now):
    if (not isinstance(raw, dict) or raw.get("type") != "FeatureCollection"
        or not isinstance(raw.get("features"), list)):
        raise ValueError("invalid_geonet_schema")
    rawfeatures = raw["features"]
    if len(rawfeatures) > 150:
        raise ValueError("too_many_geonet_features")
    items, seen = [], set()
    for feature in rawfeatures:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("invalid_geonet_feature")
        p = feature.get("properties")
        if not isinstance(p, dict):
            raise ValueError("invalid_geonet_properties")
        public_id = str(p.get("publicID") or "")
        if not re.fullmatch(r"[0-9]{4}p[0-9]{6,10}", public_id):
            raise ValueError("invalid_geonet_identifier")
        if public_id in seen:
            raise ValueError("duplicate_geonet_identifier")
        seen.add(public_id)
        quality = p.get("quality")
        if quality == "deleted":
            continue
        if quality not in ("best", "preliminary", "automatic"):
            raise ValueError("unknown_geonet_quality")
        magnitude = p.get("magnitude")
        if (isinstance(magnitude, bool) or not isinstance(magnitude, (int,float)) or
                not math.isfinite(magnitude) or not 0 <= magnitude <= 10):
            raise ValueError("invalid_geonet_magnitude")
        occurred = parse_datetime(p.get("time"))
        if occurred is None or occurred > now + dt.timedelta(minutes=5):
            raise ValueError("invalid_geonet_time")
        if occurred < now - dt.timedelta(hours=48):
            continue
        mmi = p.get("mmi")
        if not isinstance(mmi, (float,int)) or not math.isfinite(mmi) or not -1 <= mmi <= 9:
            raise ValueError("invalid_geonet_mmi")
        items.append({
            "id": public_id, "occurred_utc": iso(occurred),
            "magnitude": round(float(magnitude),2), "mmi": mmi,
            "locality": str(p.get("locality") or "")[:160],
            "source_url": "https://www.geonet.org.nz/earthquake/" + public_id,
            "is_event_observation": True, "is_government_site_outage": False,
            "customer_impact_confirmed": False,
        })
    items.sort(key=lambda x:x["occurred_utc"],reverse=True)
    return {
        "schema": "wmm.regional-hk-nz.v1", "provider": "geonet",
        "geo_scope": "NZ", "source_name": "GeoNet (Earth Sciences New Zealand)",
        "source_url": GEONET_URL, "feed_type": "new_zealand_quake_observations_last_48h",
        "count": len(items), "items": items[:MAX_ITEMS],
        "source_is_official": True, "government_website_attack_confirmed": False,
        "scope_note": "Recent quake observations; not government attacks or emergency declarations.",
        "rights": "GeoNet data policy: attribution required; review before commercial redistributions.",
    }


def error_code(error):
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP_{error.code}"
    if isinstance(error, TimeoutError):
        return "TIMEOUT"
    if isinstance(error, json.JSONDecodeError):
        return "INVALID_JSON"
    if isinstance(error, ValueError) and str(error) in {
        "source_not_allowlisted", "redirect_not_allowlisted", "source_not_ok",
        "source_too_large", "invalid_rss_xml", "invalid_rss_schema",
        "invalid_geonet_schema", "invalid_geonet_feature", "invalid_geonet_properties",
        "invalid_geonet_magnitude", "invalid_geonet_time", "invalid_geonet_mmi",
        "unknown_geonet_quality", "duplicate_geonet_identifier", "unsafe_xml",
    }:
        return str(error)
    return "SOURCE_ERROR"


def collect(outpath, now, fetchers):
    outpath = Path(outpath).resolve()
    if {s.lower() for s in outpath.parts} & {"public", "dist", "live", "data_branch", "cf"}:
        raise ValueError("refuse_public_output")
    existing = {}
    if outpath.exists():
        existing = json.loads(outpath.read_text(encoding="utf-8"))
        if not isinstance(existing, dict) or not isinstance(existing.get("feeds"), dict):
            raise ValueError("invalid_previous_report")
    report = {
        "schema": "wmm.internal-official-hk-nz.v1", "checked_at": iso(now),
        "publication_allowed": False, "customer_data_processed": False,
        "government_website_attack_confirmed": False,
        "feeds": {}, "health": {},
    }
    for provider, parser in (("hko",parse_hko_rss),("geonet",parse_geonet_quakes)):
        previous = existing.get("feeds",{}).get(provider)
        previous_health = existing.get("health",{}).get(provider,{})
        try:
            current = parser(fetchers[provider](),now)
            report["feeds"][provider] = current
            report["health"][provider] = {"status":"OK","checked_at":iso(now),
                                           "last_success_at":iso(now),"stale":False,
                                           "last_error":None}
        except (OSError,ValueError,TypeError,json.JSONDecodeError,ET.ParseError) as e:
            report["feeds"][provider] = previous if isinstance(previous,dict) else {
                "provider":provider, "count":None,"items":[],
                "source_is_official":False,
            }
            report["health"][provider] = {
                "status": "STALE" if isinstance(previous,dict) else "ERROR",
                "checked_at":iso(now),
                "last_success_at":previous_health.get("last_success_at"),
                "stale":True,"last_error":error_code(e),
            }
    outpath.parent.mkdir(parents=True,exist_ok=True)
    fd,tmppath=tempfile.mkstemp(dir=outpath.parent,prefix=".wmm-",suffix=".tmp")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as file:
            json.dump(report,file,ensure_ascii=False,indent=2)
            file.write("\n")
        os.replace(tmppath,outpath)
    finally:
        if os.path.exists(tmppath):
            os.unlink(tmppath)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    now=dt.datetime.now(UTC)
    report=collect(args.out,now,{
        "hko":lambda:fetch_source("hko"),
        "geonet":lambda:fetch_source("geonet"),
    })
    print(json.dumps({
        "checked_at":report["checked_at"],
        "all_ok":all(v["status"]=="OK" for v in report["health"].values()),
        "sources":{k:{"state":report["health"][k]["status"],
                       "records":report["feeds"][k]["count"] if report["health"][k]["status"]=="OK" else None,
                       "last_success_at":report["health"][k]["last_success_at"],
                       "error":report["health"][k]["last_error"]}
                   for k in ("hko","geonet")},
        "commercial_release":False,"customer_alerts":False,
    },ensure_ascii=False))
    return 0 if all(v["status"]=="OK" for v in report["health"].values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
