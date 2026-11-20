import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from finalize_sitemap import validate, LANGS, ORIGIN

def make_page(root: Path, lang: str, suffix: str = "", extra: str = "", canonical: str | None = None):
    page = root / lang / suffix / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    link = canonical or f"{ORIGIN}/{lang}/" + (suffix + "/" if suffix else "")
    page.write_text(
        '<!doctype html><html><head><link rel="canonical" href="' + link +
        '">' + extra + '</head><body>ok</body></html>', encoding="utf8"
    )
    return page

class SitemapGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for lang in LANGS:
            make_page(self.root, lang)
            make_page(self.root, lang, "ghana")
        self.urls = [f"{ORIGIN}/{lang}/{suffix}" for lang in LANGS for suffix in ("","ghana/")]
        self.write_sitemap()
        self.set_robots(True)

    def tearDown(self):
        self.tmp.cleanup()

    def write_sitemap(self):
        xml = ('<?xml version="1.0" encoding="UTF-8"?>'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
               "".join(f"<url><loc>{url}</loc></url>" for url in self.urls) +
               "</urlset>")
        (self.root / "sitemap.xml").write_text(xml, encoding="utf8")

    def set_robots(self, has_sitemap):
        text = "User-agent: *\nAllow: /\nDisallow: /widget/\n"
        if has_sitemap: text += f"\nSitemap: {ORIGIN}/sitemap.xml\n"
        (self.root / "robots.txt").write_text(text, encoding="utf8")

    def test_valid_existing_full_sitemap_remains_byte_identical(self):
        before = (self.root / "sitemap.xml").read_bytes()
        report = validate(self.root, min_urls=14)
        self.assertEqual(report["status"], "VALIDATED_NO_WRITE")
        self.assertEqual(report["urls"], 14)
        self.assertTrue(all(report["by_locale"][lang] == 2 for lang in LANGS))
        self.assertEqual((self.root / "sitemap.xml").read_bytes(), before)

    def test_low_url_count_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            validate(self.root, min_urls=1000)

    def test_missing_homepage_fails(self):
        (self.root / "en/index.html").unlink()
        with self.assertRaisesRegex(ValueError, "homepage"):
            validate(self.root, min_urls=14)

    def test_noindex_page_in_sitemap_fails(self):
        make_page(self.root, "ko", "ghana", '<meta name="robots" content="noindex,nofollow">')
        with self.assertRaisesRegex(ValueError, "noindex"):
            validate(self.root, min_urls=14)

    def test_mismatched_canonical_fails(self):
        make_page(self.root, "en", "ghana", canonical=f"{ORIGIN}/en/")
        with self.assertRaisesRegex(ValueError, "Non-canonical"):
            validate(self.root, min_urls=14)

    def test_unapproved_resilience_page_fails(self):
        make_page(self.root, "ko", "resilience")
        self.urls.append(f"{ORIGIN}/ko/resilience/")
        self.write_sitemap()
        with self.assertRaisesRegex(ValueError, "Unapproved"):
            validate(self.root, min_urls=14)

    def test_duplicate_url_fails(self):
        self.urls.append(self.urls[0])
        self.write_sitemap()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate(self.root, min_urls=14)

    def test_orphan_hreflang_fails(self):
        xml = (self.root / "sitemap.xml").read_text(encoding="utf8")
        xml = xml.replace(
            '<url><loc>' + self.urls[0] + '</loc></url>',
            '<url><loc>' + self.urls[0] + '</loc>'
            '<xhtml:link rel="alternate" hreflang="es" href="' + ORIGIN + '/es/not-a-page/"/></url>',
        ).replace(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        )
        (self.root / "sitemap.xml").write_text(xml, encoding="utf8")
        with self.assertRaisesRegex(ValueError, "Orphan hreflang"):
            validate(self.root, min_urls=14)

    def test_wrong_locale_hreflang_fails(self):
        xml = (self.root / "sitemap.xml").read_text(encoding="utf8")
        xml = xml.replace(
            '<url><loc>' + self.urls[0] + '</loc></url>',
            '<url><loc>' + self.urls[0] + '</loc>'
            '<xhtml:link rel="alternate" hreflang="es" href="' + ORIGIN + '/en/"/></url>',
        ).replace(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        )
        (self.root / "sitemap.xml").write_text(xml, encoding="utf8")
        with self.assertRaisesRegex(ValueError, "Wrong-language hreflang"):
            validate(self.root, min_urls=14)

    def test_official_robots_sitemap_missing_fails(self):
        self.set_robots(False)
        with self.assertRaisesRegex(ValueError, "robots.txt"):
            validate(self.root, min_urls=14)

    def test_empty_sitemap_fails(self):
        (self.root / "sitemap.xml").write_text("", encoding="utf8")
        with self.assertRaisesRegex(ValueError, "small"):
            validate(self.root, min_urls=14)

if __name__ == "__main__":
    unittest.main()
