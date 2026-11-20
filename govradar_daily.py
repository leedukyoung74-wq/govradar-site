"""Collect public GOV RADAR feed metadata for private review."""

import concurrent.futures
import datetime as dt
import json
import pathlib
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


# Publisher ownership is curated. A distinct owner is not corroboration.
SOURCES = (
    ("government", "GOV.UK announcements", "uk-government", "https://www.gov.uk/search/news-and-communications.atom", "feed"),
    ("media", "BBC World", "bbc", "https://feeds.bbci.co.uk/news/world/rss.xml", "feed"),
    ("environment", "NOAA general news", "us-noaa", "https://www.noaa.gov/rss.xml", "feed"),
    ("weather", "US National Weather Service", "us-noaa", "https://api.weather.gov/alerts/active.atom", "feed"),
    ("emergency", "Global Disaster Alert and Coordination System", "gdacs", "https://www.gdacs.org/xml/rss.xml", "feed"),
    ("public_defence", "UK Ministry of Defence public information", "uk-government", "https://www.gov.uk/government/organisations/ministry-of-defence", "availability"),
)
KST = dt.timezone(dt.timedelta(hours=9))
MAX_BYTES = 8_000_000


def collect(source):
    category, publisher, owner, url, mode = source
    result = dict(category=category, publisher=publisher, owner=owner, url=url)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "WMM-GOV-RADAR/1.0 (internal feed review)"})
        with urllib.request.urlopen(request, timeout=15) as response:
            result.update(http_status=response.status, final_url=response.url)
            if mode == "availability":
                return dict(result, status="availability_only", items=[])
            payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("feed exceeds size limit")
        if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
            raise ValueError("feed includes unsupported XML declarations")
        root = ET.fromstring(payload)
        kind = root.tag.split("}")[-1]
        if kind not in {"rss", "feed"}:
            raise ValueError("unsupported feed format")
        entries = root.findall("./channel/item") if kind == "rss" else root.findall("{*}entry")
        items = {}
        for entry in entries:
            link = next((element.get("href") or element.text or ""
                         for element in entry.findall("{*}link")
                         if element.get("rel", "alternate") == "alternate"), "").strip()
            parsed = urllib.parse.urlsplit(link)
            if owner == "gdacs" and parsed.scheme == "http" and parsed.netloc.lower() == "www.gdacs.org":
                parsed = parsed._replace(scheme="https")
            if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                continue
            key = urllib.parse.urlunsplit(parsed._replace(fragment=""))
            items[key] = {
                "url": key,
                "title": (entry.findtext("{*}title") or "").strip()[:300],
                "published": (entry.findtext("{*}published") or entry.findtext("{*}pubDate")
                              or entry.findtext("{*}updated") or "").strip()[:100],
            }
        return dict(result, status="no_usable_links" if entries and not items else "ok",
                    items=list(items.values()), feed_entry_count=len(entries),
                    duplicate_or_rejected=len(entries) - len(items))
    except urllib.error.HTTPError as error:
        return dict(result, status="http_error", http_status=error.code,
                    retry_after=error.headers.get("Retry-After"), items=[])
    except (OSError, ValueError, ET.ParseError) as error:
        return dict(result, status="failed", error=str(error), items=[])


def main():
    now = dt.datetime.now(KST)
    directory = pathlib.Path(__file__).resolve().parent / "govradar-reports"
    directory.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        sources = list(pool.map(collect, SOURCES))
    owners = {}
    for source in sources:
        if source["status"] == "ok" and source["items"]:
            owners.setdefault(source["category"], set()).add(source["owner"])
    report = {
        "run_at_kst": now.isoformat(),
        "sources": sources,
        "owners_with_items_by_category": {category: sorted(group) for category, group in owners.items()},
        "independence": "Publisher ownership grouping only. Claim-level corroboration requires review.",
        "claude_qa": "pending",
        "scope": "Limited pilot. Public defence release page availability only. Internal review.",
    }
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as temp:
        json.dump(report, temp, ensure_ascii=False, indent=2)
    pathlib.Path(temp.name).replace(directory / (now.strftime("%Y-%m-%d_%H%M%S_%f") + ".json"))
    return int(any(source["status"] not in {"ok", "availability_only"} for source in sources))


if __name__ == "__main__":
    raise SystemExit(main())
