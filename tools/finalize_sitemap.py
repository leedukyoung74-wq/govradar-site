#!/usr/bin/env python3
"""Read-only verification of existing Cloudflare sitemap.xml before publishing.

The upstream build.py already writes a large production sitemap. NEVER rewrite it
from a smaller inventory; validate it and stop publishing if it is damaged.
"""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ORIGIN = "https://radar.wmm-hoa.com"
LANGS = ("ko", "en", "es", "fr", "ar", "vi", "id")
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
EXCLUDED_ROUTE_PREFIXES = ("resilience/", "account/", "member/", "feeds/", "embed/")
ATTR = re.compile(r"""([-\w]+)\s*=\s*(["'])(.*?)\2""", re.I | re.S)
LINK = re.compile(r"<link\b[^>]*>", re.I)
META = re.compile(r"<meta\b[^>]*>", re.I)

def attrs(tag: str) -> dict[str, str]:
    return {k.lower(): html.unescape(v) for k, _, v in ATTR.findall(tag)}

def canonical_and_indexability(page: Path) -> tuple[str | None, bool]:
    head = re.split(r"</head\s*>", page.read_text(encoding="utf8"), maxsplit=1, flags=re.I)[0]
    noindex = any(
        a.get("name", "").lower() in ("robots", "googlebot")
        and bool(re.search(r"\bnoindex\b", a.get("content", ""), re.I))
        for tag in META.findall(head) for a in [attrs(tag)]
    )
    for tag in LINK.findall(head):
        a = attrs(tag)
        if a.get("rel", "").lower() == "canonical":
            return a.get("href"), not noindex
    return None, not noindex

def validate(root: Path, min_urls: int = 1000) -> dict:
    if not root.is_dir():
        raise ValueError("Cloudflare public directory missing")
    for lang in LANGS:
        if not (root / lang / "index.html").is_file():
            raise ValueError(f"Missing {lang} public homepage")
    xml_file = root / "sitemap.xml"
    if not xml_file.is_file() or xml_file.stat().st_size < 200:
        raise ValueError("Sitemap missing or suspiciously small — refusing live publish")
    tree = ET.parse(xml_file)
    if tree.getroot().tag != SITEMAP_NS + "urlset":
        raise ValueError("Invalid sitemap namespace")
    urls = []
    for entry in tree.getroot().findall(SITEMAP_NS + "url"):
        location = entry.find(SITEMAP_NS + "loc")
        if location is None or not location.text:
            raise ValueError("Missing sitemap loc")
        urls.append(location.text.strip())
    if len(urls) < min_urls or len(urls) != len(set(urls)):
        raise ValueError(f"Incomplete or duplicate sitemap: {len(urls)} total / {len(set(urls))} unique, minimum {min_urls}")
    per_locale = {lang: 0 for lang in LANGS}
    for url in urls:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "radar.wmm-hoa.com" or parsed.query or parsed.fragment:
            raise ValueError("Invalid/offsite sitemap URL: " + url)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 1 or parts[0] not in LANGS or any(p in (".","..") for p in parts):
            raise ValueError("Unexpected sitemap path: " + url)
        lang = parts[0]
        suffix = "/".join(parts[1:]) + ("/" if len(parts) > 1 else "")
        if any(suffix.startswith(prefix) for prefix in EXCLUDED_ROUTE_PREFIXES):
            raise ValueError("Unapproved review/private route indexed: " + url)
        page = root.joinpath(*parts, "index.html")
        if not page.is_file() or page.is_symlink():
            raise ValueError("Sitemap location missing static page: " + url)
        canonical, indexable = canonical_and_indexability(page)
        if not indexable or canonical != url:
            raise ValueError("Non-canonical or noindex page in sitemap: " + url)
        per_locale[lang] += 1
    if not all(per_locale.values()):
        raise ValueError("One or more site languages missing from sitemap")
    # hreflang must never direct crawlers to missing, noindex, or wrong-language URLs.
    # Some older feeds carry no alternate metadata; validate all present alternates.
    valid_urls = set(urls)
    xhtml_ns = "{http://www.w3.org/1999/xhtml}"
    for entry in tree.getroot().findall(SITEMAP_NS + "url"):
        loc = entry.find(SITEMAP_NS + "loc").text.strip()
        loc_path = urlsplit(loc).path
        loc_suffix = "/".join([p for p in loc_path.split("/") if p][1:])
        seen_langs = set()
        for alt in entry.findall(xhtml_ns + "link"):
            if alt.get("rel") != "alternate":
                raise ValueError("Invalid alternate relation for: " + loc)
            lang, href = alt.get("hreflang", ""), alt.get("href", "")
            if lang not in LANGS and lang != "x-default":
                raise ValueError("Unknown alternate language for: " + loc)
            if lang in seen_langs:
                raise ValueError("Duplicate alternate language for: " + loc)
            seen_langs.add(lang)
            if href not in valid_urls:
                raise ValueError("Orphan hreflang URL for: " + loc + " => " + href)
            target_parts = [p for p in urlsplit(href).path.split("/") if p]
            if lang in LANGS and target_parts[0] != lang:
                raise ValueError("Wrong-language hreflang URL for: " + loc)
            target_suffix = "/".join(target_parts[1:])
            if target_suffix != loc_suffix:
                raise ValueError("Mismatched hreflang route for: " + loc)

    robots_file = root / "robots.txt"
    if not robots_file.is_file():
        raise ValueError("robots.txt missing")
    robots = robots_file.read_text(encoding="utf8")
    if not re.search(r"(?im)^\s*sitemap:\s*https://radar\.wmm-hoa\.com/sitemap\.xml\s*$", robots):
        raise ValueError("robots.txt does not identify official sitemap")
    return {
        "status": "VALIDATED_NO_WRITE", "urls": len(urls),
        "by_locale": per_locale, "sitemap_bytes": xml_file.stat().st_size,
        "production_deployed": False
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site_root", type=Path, nargs="?", default=Path("cf/public"))
    parser.add_argument("--min-urls", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(validate(args.site_root.resolve(), args.min_urls), ensure_ascii=False))

if __name__ == "__main__":
    main()
