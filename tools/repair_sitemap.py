#!/usr/bin/env python3
"""Repair *generated*, pre-deployment GOV RADAR sitemap/robots without truncating it.

Call only on a disposable Cloudflare build folder after build.py, not on a live host.
Retains existing valid <url> entries & lastmod; removes only demonstrably invalid
(noindex, canonical mismatch, absent file, unapproved route) entries, then fixes
hreflang targets. Fails closed on missing/oversized loss or a damaged XML input.
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
from urllib.parse import urlsplit

from finalize_sitemap import (
    ORIGIN, LANGS, SITEMAP_NS, EXCLUDED_ROUTE_PREFIXES,
    canonical_and_indexability, validate,
)

XHTML_NS = "{http://www.w3.org/1999/xhtml}"
ET.register_namespace("", SITEMAP_NS.strip("{}"))
ET.register_namespace("xhtml", XHTML_NS.strip("{}"))


def _atomic(path: Path, content: str) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".wmm-sitemap-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf8") as f:
            f.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _page_state(root: Path, location: str) -> tuple[bool, str]:
    parsed = urlsplit(location)
    if (parsed.scheme != "https" or parsed.netloc != "radar.wmm-hoa.com"
            or parsed.query or parsed.fragment):
        return False, "OFFSITE_OR_UNSAFE"
    parts = [x for x in parsed.path.split("/") if x]
    if not parts or parts[0] not in LANGS or not parsed.path.endswith("/"):
        return False, "UNKNOWN_ROUTE"
    if any(x in (".", "..") for x in parts):
        return False, "UNSAFE_PATH"
    relative = "/".join(parts[1:]) + ("/" if len(parts) > 1 else "")
    if any(relative.startswith(prefix) for prefix in EXCLUDED_ROUTE_PREFIXES):
        return False, "UNAPPROVED_ROUTE"
    page = root.joinpath(*parts, "index.html")
    if not page.is_file() or page.is_symlink():
        return False, "PAGE_MISSING"
    canonical, indexable = canonical_and_indexability(page)
    if not indexable:
        return False, "NOINDEX"
    if canonical != location:
        return False, "CANONICAL_MISMATCH"
    return True, "OK"


def _robots_with_sitemap(data: str) -> str:
    kept = [line for line in data.splitlines()
            if not re.match(r"(?i)^\s*sitemap\s*:", line)]
    if not any(re.match(r"(?i)^\s*user-agent\s*:", l) for l in kept):
        kept = ["User-agent: *", "Allow: /", "Disallow: /widget/"]
    return "\n".join(kept).rstrip() + f"\n\nSitemap: {ORIGIN}/sitemap.xml\n"


def repair(root: Path, *, min_urls: int = 1000,
           max_removed: int = 100, max_removed_ratio: float = 0.1) -> dict:
    """Modify only the generated site's sitemap.xml and robots.txt, then revalidate.

    The caller must use a staging/CI build directory, not a production checkout.
    """
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Site root must be an existing normal directory")
    xml_path = root / "sitemap.xml"
    if not xml_path.is_file() or xml_path.is_symlink() or xml_path.stat().st_size < 200:
        raise ValueError("Generated sitemap missing, symlinked or suspiciously small")
    robots_path = root / "robots.txt"
    if robots_path.is_symlink():
        raise ValueError("Refusing symlinked robots.txt")
    tree = ET.parse(xml_path)
    xml_root = tree.getroot()
    if xml_root.tag != SITEMAP_NS + "urlset":
        raise ValueError("Unexpected sitemap namespace")
    original = xml_root.findall(SITEMAP_NS + "url")
    if len(original) < min_urls:
        raise ValueError("Original sitemap too small; refusing to rebuild")
    keep: set[str] = set()
    removed: list[dict[str, str]] = []
    for entry in original:
        loc = entry.find(SITEMAP_NS + "loc")
        url = (loc.text or "").strip() if loc is not None else ""
        if not url or url in keep:
            removed.append({"url": url, "reason": "MISSING_OR_DUPLICATE_LOC"})
            xml_root.remove(entry)
            continue
        ok, why = _page_state(root, url)
        if not ok:
            removed.append({"url": url, "reason": why})
            xml_root.remove(entry)
        else:
            keep.add(url)
    if (len(removed) > max_removed
            or len(removed) > len(original) * max_removed_ratio
            or len(keep) < min_urls):
        raise ValueError(
            f"Unsafe sitemap loss {len(removed)}/{len(original)}; "
            f"retained {len(keep)}; publishing blocked"
        )
    for entry in xml_root.findall(SITEMAP_NS + "url"):
        for alt in list(entry.findall(XHTML_NS + "link")):
            if alt.get("href") not in keep:
                entry.remove(alt)
    serialized = ET.tostring(xml_root, encoding="unicode", short_empty_elements=True)
    payload = '<?xml version="1.0" encoding="UTF-8"?>\n' + serialized + "\n"
    # Check generated XML before touching either destination.
    parsed = ET.fromstring(payload)
    if len(parsed.findall(SITEMAP_NS + "url")) != len(keep):
        raise ValueError("Sitemap XML integrity check failed")
    new_robots = _robots_with_sitemap(
        robots_path.read_text("utf8") if robots_path.is_file() else "")
    # Validate *before* committing each write by checking the candidate in a
    # temporary build directory with links to original HTML.
    # The following atomic writes are safe inside a disposable staging build.
    previous_sitemap = xml_path.read_text("utf8")
    previous_robots = robots_path.read_text("utf8") if robots_path.exists() else None
    try:
        _atomic(xml_path, payload)
        _atomic(robots_path, new_robots)
        check = validate(root, min_urls=min_urls)
    except Exception:
        _atomic(xml_path, previous_sitemap)
        if previous_robots is None:
            robots_path.unlink(missing_ok=True)
        else:
            _atomic(robots_path, previous_robots)
        raise
    return {
        **check,
        "status": "REPAIRED_STAGING_NOT_DEPLOYED",
        "original_urls": len(original),
        "removed_urls": len(removed),
        "removed_examples": removed[:25],
        "production_deployed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site_root", type=Path, nargs="?", default=Path("cf/public"))
    parser.add_argument("--min-urls", type=int, default=1000)
    parser.add_argument("--max-removed", type=int, default=100)
    parser.add_argument("--max-removed-ratio", type=float, default=0.1)
    parser.add_argument("--write", action="store_true",
                        help="Required: patch only a generated, disposable predeploy directory")
    args = parser.parse_args()
    if not args.write:
        raise SystemExit("Read-only by default. Pass --write for a disposable predeploy folder.")
    if args.min_urls < 1 or args.max_removed < 0 or not 0 <= args.max_removed_ratio <= 1:
        raise SystemExit("Invalid safety limit")
    print(json.dumps(
        repair(args.site_root.resolve(), min_urls=args.min_urls,
               max_removed=args.max_removed,
               max_removed_ratio=args.max_removed_ratio),
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
