"""Country-specific publisher links, not invented official government news claims."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from country_news_sources import load_directory,safe_url

class NewsDirectoryQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources,cls.report=load_directory(ROOT)

    def test_193_countries_are_individually_audited(self):
        self.assertEqual(len(self.sources),193)
        self.assertEqual(self.report["target_links"],579)
        self.assertEqual(len(self.report["country_counts"]),193)
        self.assertEqual(self.report["registered_publisher_links"],360)
        self.assertEqual(self.report["countries_with_at_least_three_recorded"],120)
        self.assertEqual(self.report["remaining_minimum_link_slots"],219)
        self.assertEqual(len(self.report["uncatalogued_countries"]),73)

    def test_publishers_distinct_and_not_gov_procurement_numbers(self):
        for iso,rows in self.sources.items():
            self.assertEqual(len({r["url"].rstrip("/").lower() for r in rows}),len(rows),iso)
            self.assertEqual(len(rows),self.report["country_counts"][iso]["publisher_links_recorded"])
            for record in rows:
                self.assertEqual(record["verification"],"publisher_link_recorded")
                self.assertTrue(safe_url(record["url"]),(iso,record["url"]))
                self.assertTrue(safe_url(record["evidence_url"]),(iso,record["evidence_url"]))
        self.assertTrue(self.report["not_government_site_count"])
        self.assertTrue(self.report["not_live_news_feed"])

    def test_closed_country_cannot_have_fake_three_news_publishers(self):
        self.assertEqual(self.report["country_counts"]["KP"]["publisher_links_recorded"],0)
        self.assertEqual(self.report["country_counts"]["ER"]["publisher_links_recorded"],0)
        self.assertEqual(self.report["country_counts"]["AF"]["remaining_to_three"],3)

    def test_url_parser_blocks_unsafe_schemes_and_credentials(self):
        for url in ("javascript:alert(1)","http://news.example.com",
                    "https://a:b@news.example.com/","https://news.example.com:444/",
                    "https://news.example.com/\n<script>", "https://news.example.com/#fake"):
            self.assertFalse(safe_url(url),url)
        self.assertTrue(safe_url("https://news.example.com/news"))

    def test_build_wires_sources_into_country_pages(self):
        build=(ROOT/"build.py").read_text(encoding="utf-8")
        self.assertIn("COUNTRY_NEWS_SITES, COUNTRY_NEWS_COVERAGE = _load_country_news(ROOT)",build)
        self.assertIn('sec("country-news-sources"',build)
        self.assertIn("country-news-coverage.json",build)

if __name__=="__main__":
    unittest.main()
