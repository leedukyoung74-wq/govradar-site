"""National publisher-owned news site directory for all 193 GOV RADAR countries.

A stored publisher link is NOT evidence of article credibility, free reuse,
RSS/API permission, live health, independence from government or 24h updates.
A government press release must not be counted as a separate news publisher.
"""
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlsplit

VALID_TYPES=frozenset({
    "news_agency","state_news_agency","public_broadcaster",
    "broadcaster","newspaper","news_site","nonprofit_newsroom"
})

def safe_url(url):
    if not isinstance(url,str) or any(c in url for c in ("\n","\r","\t","\\"," ")):
        return False
    try:
        x=urlsplit(url)
        return (x.scheme=="https" and bool(x.hostname) and x.hostname.find(".")>0
                and x.username is None and x.password is None and x.port is None
                and not x.fragment and bool(x.path or x.hostname))
    except (ValueError,TypeError):
        return False

def host(url):
    return urlsplit(url).hostname.lower()

def load_directory(root):
    root=Path(root)
    countries=json.loads((root/"src/countries_meta.json").read_text(encoding="utf-8"))
    iso_codes=[c["iso"] for c in countries]
    if len(iso_codes)!=193 or len(set(iso_codes))!=193:
        raise ValueError("expected 193 unique sovereign country ISO codes")
    doc=json.loads((root/"src/country_news_sources.json").read_text(encoding="utf-8"))
    if doc.get("schema_version")!=1 or not isinstance(doc.get("countries"),dict):
        raise ValueError("invalid national news source catalog")
    if set(doc["countries"])-set(iso_codes):
        raise ValueError("unknown country in news catalog")
    index={iso:[] for iso in iso_codes}
    for iso,rows in doc["countries"].items():
        if not isinstance(rows,list):
            raise ValueError("news country must be an array")
        seen_urls=set()
        for row in rows:
            if not isinstance(row,dict):raise ValueError("not a publisher record")
            name=row.get("name_en")
            if (not isinstance(name,str) or not name.strip()
                or not isinstance(row.get("name_ko"),str)
                or not row["name_ko"].strip()
                or row.get("publisher_type") not in VALID_TYPES
                or row.get("verification")!="publisher_link_recorded"
                or not safe_url(row.get("url")) or not safe_url(row.get("evidence_url"))):
                raise ValueError("invalid publisher link/type in "+iso)
            try:
                checked=dt.date.fromisoformat(row.get("reviewed_on",""))
            except (ValueError,TypeError):
                raise ValueError("publisher review date invalid "+iso)
            if checked > dt.date.today()+dt.timedelta(days=1):
                raise ValueError("future publisher verification date "+iso)
            url=row["url"].rstrip("/").lower()
            if url in seen_urls:raise ValueError("duplicated publisher URL in "+iso)
            seen_urls.add(url)
            index[iso].append(dict(row))
    country_counts={iso:{"publisher_links_recorded":len(rows),
                         "remaining_to_three":max(0,3-len(rows))}
                    for iso,rows in sorted(index.items())}
    links=sum(x["publisher_links_recorded"] for x in country_counts.values())
    completed=sum(x["remaining_to_three"]==0 for x in country_counts.values())
    return index, {
        "source_kind":"original_publisher_news_sources",
        "not_government_site_count":True,
        "not_live_news_feed":True,
        "target_countries":193,
        "minimum_per_country":3,
        "target_links":579,
        "countries_with_at_least_three_recorded":completed,
        "registered_publisher_links":links,
        "remaining_minimum_link_slots":sum(x["remaining_to_three"] for x in country_counts.values()),
        "country_counts":country_counts,
        "uncatalogued_countries":[iso for iso,rows in sorted(index.items()) if len(rows)<3],
    }
