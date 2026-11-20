#!/usr/bin/env python3
"""Validate and finalize public Cloudflare sitemap after all site generators.

Default is read-only. --write modifies only <site_root>/sitemap.xml and robots.txt.
Never alters deployed files, GitHub branches, private data or customer accounts.
"""
from __future__ import annotations
import argparse
import html
import json
import os
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET

ORIGIN = "https://radar.wmm-hoa.com"
LANGS = ("ko", "en", "es", "fr", "ar", "vi", "id")
CANONICAL = re.compile(r"<link\b[^>]*>", re.I)
META = re.compile(r"<meta\b[^>]*>", re.I)
ATTR = re.compile(r"""([-\w]+)\s*=\s*(["'])(.*?)\2""", re.I | re.S)

def attributes(tag: str) -> dict[str, str]:
    return {k.lower(): html.unescape(v) for k, _, v in ATTR.findall(tag)}

def public_canonical_head(path: Path) -> tuple[str | None, str | None]:
    content = path.read_text(encoding="utf8")
    head = re.split(r"</head\s*>", content, maxsplit=1, flags=re.I)[0]
    for tag in META.findall(head):
        a = attributes(tag)
        if a.get("name", "").lower() in ("robots", "googlebot") and "noindex" in a.get("content", "").lower().split(","):
            return None, "NOINDEX"
        if a.get("name", "").lower() in ("robots", "googlebot") and re.search(r"\bnoindex\b", a.get("content", ""), re.I):
            return None, "NOINDEX"
    for tag in CANONICAL.findall(head):
        a = attributes(tag)
        if a.get("rel", "").lower() == "canonical":
            return a.get("href"), None
    return None, "MISSING_CANONICAL"

def collect(root: Path) -> tuple[list[tuple[str, dict[str, str]]], list[dict]]:
    if not root.is_dir():
        raise ValueError("Site root does not exist: " + str(root))
    groups: dict[str, dict[str, str]] = {}
    excluded = []
    for lang in LANGS:
        folder = root / lang
        if not (folder / "index.html").is_file():
            raise ValueError("Required language homepage missing: " + str(folder))
        for page in sorted(folder.rglob("index.html")):
            if page.is_symlink():
                excluded.append({"file": str(page.relative_to(root)), "reason": "SYMLINK"})
                continue
            rel = page.relative_to(folder).as_posix()
            suffix = "" if rel == "index.html" else rel.removesuffix("/index.html") + "/"
            expected = f"{ORIGIN}/{lang}/{suffix}"
            canonical, reason = public_canonical_head(page)
            if reason or canonical != expected:
                excluded.append({"file": str(page.relative_to(root)),
                                 "reason": reason or "CANONICAL_MISMATCH"})
                continue
            groups.setdefault(suffix, {})[lang] = expected
    return sorted(groups.items()), excluded

def render(groups: list[tuple[str, dict[str, str]]]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for _, links in groups:
        for lang in LANGS:
            if lang not in links:
                continue
            lines.extend(["  <url>", f'    <loc>{html.escape(links[lang], quote=True)}</loc>'])
            for alt in LANGS:
                if alt in links:
                    lines.append(f'    <xhtml:link rel="alternate" hreflang="{alt}" href="{html.escape(links[alt], quote=True)}"/>')
            if "en" in links:
                lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{html.escape(links["en"], quote=True)}"/>')
            lines.append("  </url>")
    lines.extend(["</urlset>", ""])
    return "\n".join(lines)

def robots_update(robots: str) -> str:
    lines = [line for line in robots.splitlines() if not line.strip().lower().startswith("sitemap:")]
    if not any(line.strip().lower().startswith("user-agent:") for line in lines):
        lines = ["User-agent: *", "Allow: /", "Disallow: /widget/"]
    return "\n".join(lines).rstrip() + f"\n\nSitemap: {ORIGIN}/sitemap.xml\n"

def atomic_write(path: Path, data: str) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".wmm-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf8") as out:
            out.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def finalize(root: Path, *, min_urls: int = 1000, write: bool = False) -> dict:
    groups, excluded = collect(root)
    count = sum(len(langs) for _, langs in groups)
    if count < min_urls:
        raise ValueError(f"Refusing incomplete sitemap: {count} URLs, minimum {min_urls}")
    payload = render(groups)
    xml_root = ET.fromstring(payload)
    if len(xml_root) != count or len({loc.text for loc in xml_root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}) != count:
        raise ValueError("Sitemap XML URL count/uniqueness check failed")
    report = {"kind": "SOURCE_VERIFIED", "public_urls": count, "groups": len(groups),
              "excluded": len(excluded), "excluded_examples": excluded[:10],
              "written": bool(write), "production_deployed": False}
    if write:
        sitemap = root / "sitemap.xml"
        robots = root / "robots.txt"
        new_robots = robots_update(robots.read_text(encoding="utf8") if robots.exists() else "")
        atomic_write(sitemap, payload)
        atomic_write(robots, new_robots)
    return report

def main() -> None:
    p = argparse.ArgumentParser(description="Guard sitemap before approved Cloudflare publish")
    p.add_argument("site_root", type=Path, nargs="?", default=Path("cf/public"))
    p.add_argument("--min-urls", type=int, default=1000)
    p.add_argument("--write", action="store_true", help="Modify generated public directory only")
    args = p.parse_args()
    print(json.dumps(finalize(args.site_root.resolve(), min_urls=args.min_urls, write=args.write), ensure_ascii=False))

if __name__ == "__main__":
    main()
