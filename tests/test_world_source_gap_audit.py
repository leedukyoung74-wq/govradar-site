"""GOV RADAR source coverage integrity and no-false-live-connection guarantees."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from world_source_coverage_audit import build_coverage, export_coverage


class GlobalCoverageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = build_coverage(ROOT)

    def test_all_193_countries_and_23_special_regions_distinct(self):
        a = self.audit
        self.assertEqual(a["scope"]["sovereign_countries"], 193)
        self.assertEqual(a["scope"]["special_regions"], 23)
        self.assertEqual(len(a["countries"]), 193)
        self.assertEqual(len(a["territories"]), 23)
        self.assertEqual(set(a["countries"]) & set(a["territories"]), set())

    def test_most_recent_government_and_news_source_coverage_not_live(self):
        a = self.audit
        self.assertEqual(a["government"]["source_evidence_countries_with_3"], 191)
        self.assertEqual(a["government"]["source_evidence_links"], 573)
        self.assertEqual(a["government"]["missing_minimum_slots"], 6)
        self.assertEqual(a["government"]["incomplete_countries"], ["ER", "KP"])
        self.assertEqual(a["news"]["publisher_links_recorded"], 531)
        self.assertEqual(a["news"]["countries_with_3"], 177)
        self.assertEqual(a["news"]["remaining_minimum_slots"], 48)
        self.assertEqual(a["live_verified_url_count"], 0)

    def test_six_new_country_environment_weather_emergency_directories(self):
        a = self.audit
        for iso in ("DZ", "AO", "BJ", "BW", "BF", "BI"):
            self.assertEqual(a["environment_weather_emergency"]["countries"][iso]["candidate_total"], 3, iso)
            self.assertEqual(a["environment_weather_emergency"]["countries"][iso]["missing"], 0, iso)
        self.assertEqual(a["environment_weather_emergency"]["complete_countries"], 79)
        self.assertEqual(a["environment_weather_emergency"]["candidate_links"], 238)
        self.assertEqual(a["environment_weather_emergency"]["missing_national_category_links"], 341)

    def test_territory_counts_are_separate_and_greenland_news_gap_not_filled(self):
        a = self.audit
        self.assertEqual(a["territories"]["DK-GL"]["parent_iso"], "DK")
        self.assertEqual(a["territories"]["DK-GL"]["category_counts"]["news_media"], 2)
        self.assertEqual(a["territory_coverage"]["government_business_links"], 69)
        self.assertEqual(a["territory_coverage"]["news_media_links"], 68)
        self.assertEqual(a["territory_coverage"]["news_media_remaining_to_3"], 1)

    def test_national_defence_sources_not_mistaken_for_live_alert_feeds(self):
        a = self.audit
        self.assertEqual(a["national_defence"]["countries_with_any_candidate"], 65)
        self.assertEqual(a["national_defence"]["countries_with_3_candidates"], 47)
        self.assertEqual(a["national_defence"]["candidate_links"], 173)
        self.assertFalse(a["production_feed_connected"])

    def test_export_has_1342_records_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "reports"
            exported = export_coverage(self.audit, path)
            self.assertEqual(len(self.audit["records"]), 193 * 6 + 23 * 8)
            self.assertTrue(Path(exported["json"]).is_file())
            self.assertTrue(Path(exported["csv"]).is_file())
            with self.assertRaises(FileExistsError):
                export_coverage(self.audit, path)

    def test_public_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                export_coverage(self.audit, Path(d) / "dist" / "data")

if __name__ == "__main__":
    unittest.main()
