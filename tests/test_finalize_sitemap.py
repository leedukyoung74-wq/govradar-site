import tempfile
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from finalize_sitemap import finalize, robots_update, LANGS, ORIGIN

def make_page(root: Path, lang: str, suffix: str = "", extra: str = "", canonical: str | None = None) -> Path:
    path = root / lang / suffix / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    link = canonical or f"{ORIGIN}/{lang}/" + (suffix + "/" if suffix else "")
    path.write_text(f'<!doctype html><html><head><link rel="canonical" href="{link}">{extra}</head><body>ok</body></html>', encoding="utf8")
    return path

class FinalizeSitemapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for l in LANGS:
            make_page(self.root, l)
            make_page(self.root, l, "ghana")
        (self.root / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /widget/\n", encoding="utf8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_no_writes_and_full_locale_coverage(self):
        result = finalize(self.root, min_urls=14)
        self.assertFalse(result["written"])
        self.assertEqual(result["public_urls"], 14)
        self.assertFalse((self.root / "sitemap.xml").exists())
        self.assertNotIn("Sitemap:", (self.root / "robots.txt").read_text())

    def test_write_valid_xml_and_robots_no_duplicates(self):
        result = finalize(self.root, min_urls=14, write=True)
        self.assertTrue(result["written"])
        xml = ET.fromstring((self.root / "sitemap.xml").read_text())
        self.assertEqual(len(xml.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")), 14)
        robots = (self.root / "robots.txt").read_text()
        self.assertIn("Disallow: /widget/", robots)
        self.assertEqual(robots.count("Sitemap:"), 1)
        finalize(self.root, min_urls=14, write=True)
        self.assertEqual((self.root / "robots.txt").read_text().count("Sitemap:"), 1)

    def test_noindex_and_canonical_mismatch_are_excluded(self):
        make_page(self.root, "ko", "thanks", '<meta name="robots" content="noindex,nofollow">')
        make_page(self.root, "en", "wrong", canonical=f"{ORIGIN}/en/")
        report = finalize(self.root, min_urls=14)
        self.assertEqual(report["public_urls"], 14)
        self.assertEqual(report["excluded"], 2)

    def test_review_and_private_routes_are_never_indexed(self):
        make_page(self.root, "ko", "resilience")
        make_page(self.root, "en", "account")
        make_page(self.root, "ko", "member")
        report = finalize(self.root, min_urls=14, write=True)
        self.assertEqual(report["public_urls"], 14)
        self.assertEqual(report["excluded"], 3)
        text = (self.root / "sitemap.xml").read_text(encoding="utf8")
        self.assertNotIn("/resilience/", text)
        self.assertNotIn("/account/", text)
        self.assertNotIn("/member/", text)

    def test_minimum_coverage_blocks_incomplete_write(self):
        with self.assertRaises(ValueError):
            finalize(self.root, min_urls=1000, write=True)
        self.assertFalse((self.root / "sitemap.xml").exists())

    def test_missing_language_blocks_publish(self):
        (self.root / "ko" / "index.html").unlink()
        with self.assertRaises(ValueError):
            finalize(self.root, min_urls=1)

    def test_robots_preserves_policy(self):
        s = robots_update("User-agent: *\nDisallow: /widget/\nSitemap: https://obsolete.example/\n")
        self.assertEqual(s.count("Sitemap:"), 1)
        self.assertIn("Disallow: /widget/", s)
        self.assertIn(f"Sitemap: {ORIGIN}/sitemap.xml", s)

if __name__ == "__main__":
    unittest.main()
