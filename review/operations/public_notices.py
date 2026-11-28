"""Read public defensive security advisories without inferring active attacks."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.error import HTTPError
from xml.etree import ElementTree

from pipeline.audit_feeds import KST, atomic_json


ROOT = Path(__file__).resolve().parent
MAX_BYTES = 700_000
SOURCES = {
    "KISA": ("KR", "https://www.boho.or.kr/kr/rss.do?bbsId=B0000133", {"www.boho.or.kr", "boho.or.kr", "www.krcert.or.kr", "krcert.or.kr"}),
    "CERT-EU": ("EU", "https://cert.europa.eu/publications/security-advisories-rss", {"cert.europa.eu", "www.cert.europa.eu"}),
    "ASD ACSC": ("AU", "https://www.cyber.gov.au/rss/advisories", {"www.cyber.gov.au", "cyber.gov.au"}),
}


def safe_url(value, hosts):
    try:
        parts = urlsplit(value.strip())
        if parts.scheme == "https" and parts.hostname in hosts and not parts.username and parts.port in (None, 443):
            return urlunsplit(parts._replace(fragment=""))
    except ValueError:
        pass
    return None


class OfficialRedirect(HTTPRedirectHandler):
    def __init__(self, hosts):
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not safe_url(newurl, self.hosts):
            raise ValueError("Unexpected redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def publication(value):
    text = (value or "").strip()
    if re.fullmatch(r"\d{4}-\d\d-\d\d", text):
        try:
            return {"date": datetime.strptime(text, "%Y-%m-%d").date().isoformat(), "precision": "day"}
        except ValueError:
            return {"precision": "unknown"}
    text = re.sub(r"\s+(CET|CEST)$", lambda match: " +0100" if match[1] == "CET" else " +0200", text)
    for parser in (datetime.fromisoformat, parsedate_to_datetime):
        try:
            v = parser(text)
            if v.tzinfo is not None:
                return {"kst": v.astimezone(KST).isoformat(), "precision": "time"}
        except (TypeError, ValueError, OverflowError):
            pass
    return {"precision": "unknown"}


def parse_feed(raw, hosts):
    if len(raw) > MAX_BYTES or re.search(br"<!\s*(?:DOCTYPE|ENTITY)\b", raw, re.I):
        raise ValueError("Unsupported XML")
    root = ElementTree.fromstring(raw)
    if root.tag == "rss":
        channel = root.find("channel")
        if channel is None:
            raise ValueError("Missing RSS channel")
        entries = channel.findall("item")
    elif root.tag == "{http://www.w3.org/2005/Atom}feed":
        entries = root.findall("{*}entry")
    else:
        raise ValueError("Feed format not recognized")
    result = {}
    for item in entries[:30]:
        link = next((e.get("href") or e.text or "" for e in item.findall("{*}link")
                     if e.get("rel", "alternate") == "alternate"), "")
        url = safe_url(link, hosts)
        title = " ".join((item.findtext("{*}title") or "").split())[:220]
        if url and title:
            date = (item.findtext("{*}pubDate") or item.findtext("{*}published")
                    or item.findtext("{*}updated"))
            result.setdefault(url, {"title": title, "url": url, "published": publication(date)})
    if entries and not result:
        raise ValueError("No official advisory link parsed")
    return list(result.values())[:12]


def fetch_source(name, previous, now):
    region, url, hosts = SOURCES[name]
    stamp = now.isoformat()
    report = {"region": region, "origin": url, "kind": "advisory", "checked_at_kst": stamp,
              "last_success_kst": previous.get("last_success_kst"), "items": previous.get("items", [])}
    headers = {"User-Agent": "WMM GOV RADAR Public Notice Review/1.0", "Accept": "application/rss+xml, application/xml, text/xml"}
    etag = previous.get("etag")
    if isinstance(etag, str) and 0 < len(etag) < 160 and "\r" not in etag and "\n" not in etag:
        headers["If-None-Match"] = etag
    try:
        opener = build_opener(OfficialRedirect(hosts))
        with opener.open(Request(url, headers=headers), timeout=9) as response:
            if not safe_url(response.url, hosts):
                raise ValueError("Unexpected source")
            items = parse_feed(response.read(MAX_BYTES + 1), hosts)
            report.update(status="ok", last_success_kst=stamp, items=items, etag=response.headers.get("ETag"))
    except HTTPError as exc:
        if exc.code == 304 and previous.get("last_success_kst"):
            report.update(status="unchanged", last_success_kst=stamp, etag=etag)
        else:
            report.update(status="cached" if report["last_success_kst"] else "unavailable", http_status=exc.code)
    except (OSError, ValueError, ElementTree.ParseError):
        report["status"] = "cached" if report["last_success_kst"] else "unavailable"
    return name, report


def main():
    output = ROOT / "state" / "cyber" / "latest.json"
    try:
        old = json.loads(output.read_text(encoding="utf-8")).get("sources", {})
    except (OSError, ValueError, AttributeError):
        old = {}
    now = datetime.now(KST)
    with ThreadPoolExecutor(max_workers=3) as pool:
        result = dict(pool.map(lambda name: fetch_source(name, old.get(name, {}), now), SOURCES))
    atomic_json(output, {"schema_version": 1, "kind": "public_security_advisories", "checked_at_kst": now.isoformat(),
                         "sources": result, "confirmed_incident_count": None})
    return int(not any(x["status"] in {"ok", "unchanged"} for x in result.values()))


if __name__ == "__main__":
    raise SystemExit(main())
