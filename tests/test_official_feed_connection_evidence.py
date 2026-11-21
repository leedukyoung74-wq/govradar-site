"""Evidence-backed provider registry; a source URL is NOT a running website feed."""
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]

class OfficialFeedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/"src/official_feed_connection_evidence.json").read_text(encoding="utf-8"))

    def test_six_distinct_official_sources_and_geographic_scopes(self):
        x=self.data
        self.assertEqual(x["schema"],"wmm.official-feed-connection-evidence.v1")
        self.assertEqual(len(x["providers"]),6)
        ids=[p["provider_id"] for p in x["providers"]]
        self.assertEqual(len(set(ids)),6)
        scopes={p["provider_id"]:p["geo_scope"] for p in x["providers"]}
        self.assertEqual(scopes,{
            "gb_ea_flood":"GB-ENG","jp_jma_bulletins":"JP",
            "cn_hk_hko_warnings":"CN-HK","nz_geonet_quakes":"NZ",
            "gb_metoffice_uk":"GB","ca_eccc_toronto":"CA-ON-TORONTO"
        })

    def test_each_source_is_official_but_no_live_website_publication(self):
        for p in self.data["providers"]:
            with self.subTest(p["provider_id"]):
                self.assertEqual(p["connection_state"],"ACTUAL_OFFICIAL_GET_VERIFIED_INTERNAL_ONLY")
                self.assertTrue(p["official_source_verified"])
                self.assertTrue(p["test_result_url"].startswith("https://github.com/leedukyoung74-wq/govradar-site/actions/runs/"))
                self.assertFalse(p["gov_radar_public_page_published"])
                self.assertFalse(p["customer_alerts_active"])
                self.assertFalse(p["government_cyberattack_confirmed"])
                self.assertTrue(p["accessed_at_utc"].endswith("Z"))
                self.assertIn("rights_source_url",p)
                self.assertEqual(urlsplit(p["api_url"]).scheme,"https")

    def test_hk_is_special_region_and_ca_is_one_city(self):
        rows={p["provider_id"]:p for p in self.data["providers"]}
        self.assertEqual(rows["cn_hk_hko_warnings"]["special_region_parent"],"CN")
        self.assertEqual(rows["ca_eccc_toronto"]["coverage_note"],"City of Toronto only, not Canada-wide")
        self.assertEqual(rows["gb_ea_flood"]["coverage_note"],"England only, not all United Kingdom")
        self.assertTrue(rows["jp_jma_bulletins"]["not_confirmed_active_alerts"])
        self.assertTrue(rows["nz_geonet_quakes"]["not_confirmed_active_alerts"])

    def test_registry_total_does_not_claim_193_countries_live(self):
        self.assertFalse(self.data["all_193_sovereigns_connected"])
        self.assertFalse(self.data["all_23_special_regions_connected"])
        self.assertFalse(self.data["website_live_feed_published"])
        self.assertEqual(self.data["actual_internal_feeds_verified"],6)
        self.assertIn("daily_schedule",self.data)
        self.assertEqual(self.data["daily_schedule"]["time_kst"],"08:05")

if __name__=="__main__":unittest.main()
