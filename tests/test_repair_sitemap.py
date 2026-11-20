import sys
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from finalize_sitemap import ORIGIN, LANGS, validate
from repair_sitemap import repair

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
X = "http://www.w3.org/1999/xhtml"
ET.register_namespace("", NS)
ET.register_namespace("xhtml", X)

def write_page(root, lang, slug="", *, canonical=None, noindex=False):
    path = root / lang / slug / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"{ORIGIN}/{lang}/" + (slug + "/" if slug else "")
    canonical = canonical or url
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    path.write_text(f'<html><head><link rel="canonical" href="{canonical}">{robots}</head><body>test</body></html>', "utf8")
    return url

class ReconcileSitemapTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.valid = []
        for lang in LANGS:
            self.valid.append(write_page(self.root, lang))
            self.valid.append(write_page(self.root, lang, "ghana"))
        # Spanish MDB is a NOINDEX redirect to English; not a canonical page.
        self.redirect = write_page(self.root, "es", "mdb",
                                   canonical=ORIGIN + "/en/mdb/", noindex=True)
        root = ET.Element(f"{{{NS}}}urlset")
        for url in self.valid + [self.redirect]:
            entry = ET.SubElement(root, f"{{{NS}}}url")
            ET.SubElement(entry, f"{{{NS}}}loc").text = url
            ET.SubElement(entry, f"{{{X}}}link", attrib={
                "rel":"alternate", "hreflang":"es", "href":self.redirect
            })
        (self.root / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root,encoding="unicode"), "utf8")
        (self.root / "robots.txt").write_text("User-agent: *\nDisallow: /widget/\n", "utf8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_remove_bad_redirect_then_validate_full_sitemap(self):
        with self.assertRaises(ValueError):
            validate(self.root, min_urls=14)
        result = repair(self.root, min_urls=14, max_removed=3)
        self.assertEqual(result["removed_urls"],1)
        self.assertEqual(result["original_urls"],15)
        self.assertEqual(result["urls"],14)
        xml_text=(self.root / "sitemap.xml").read_text("utf8")
        self.assertNotIn(self.redirect, xml_text)
        self.assertEqual(xml_text.count("<url>"),14)
        self.assertNotIn('hreflang="es"',xml_text)
        self.assertEqual((self.root / "robots.txt").read_text("utf8").count("Sitemap:"),1)
        self.assertEqual(validate(self.root, min_urls=14)["urls"],14)

    def test_fail_closed_does_not_change_files(self):
        previous_xml = (self.root / "sitemap.xml").read_bytes()
        previous_robots = (self.root / "robots.txt").read_bytes()
        with self.assertRaisesRegex(ValueError,"Unsafe sitemap loss"):
            repair(self.root, min_urls=14, max_removed=0)
        self.assertEqual((self.root / "sitemap.xml").read_bytes(),previous_xml)
        self.assertEqual((self.root / "robots.txt").read_bytes(),previous_robots)

    def test_repair_idempotent_and_robots_preserved(self):
        repair(self.root,min_urls=14,max_removed=3)
        second = repair(self.root,min_urls=14,max_removed=3)
        self.assertEqual(second["removed_urls"],0)
        self.assertIn("Disallow: /widget/", (self.root / "robots.txt").read_text("utf8"))

    def test_repair_missing_canonical_file_only_removes_matching_entry(self):
        (self.root / "es" / "ghana" / "index.html").unlink()
        result = repair(self.root,min_urls=13,max_removed=3,max_removed_ratio=0.2)
        self.assertEqual(result["removed_urls"],2)
        self.assertEqual(result["urls"],13)

    def test_bad_xml_refuses_changes(self):
        p=self.root / "sitemap.xml"
        p.write_text("<bad", "utf8")
        with self.assertRaises((ET.ParseError,ValueError)):
            repair(self.root,min_urls=14,max_removed=3)
        self.assertEqual(p.read_text("utf8"),"<bad")

if __name__ == "__main__":
    unittest.main()
