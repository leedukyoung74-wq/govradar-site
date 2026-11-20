"""Official government-site coverage: no invented government links, no fake 193/193."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from government_business_sites import load_directory,safe_https


class GovernmentBusinessSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sites,cls.report=load_directory(ROOT)

    def test_has_193_sovereign_country_entries(self):
        self.assertEqual(193,len(self.sites))
        self.assertEqual(579,self.report["target_verified_links"])
        self.assertEqual(193,len(self.report["country_counts"]))

    def test_at_least_152_verified_priority_country_sets(self):
        # Increase this threshold only when independently reviewed additions
        # are made. Do not assert 193/193 before that is actually true.
        self.assertGreaterEqual(self.report["verified_countries"],152)
        self.assertGreaterEqual(self.report["verified_links"],456)
        self.assertEqual(579-self.report["verified_links"],
                         self.report["remaining_required_link_slots"])
        for iso in ("KR","US","GB","JP","IN","AU","CA","FR","SG","SA","KE","ZA","PH","BR","ID","DE","ES","NZ","CH","NL","NO","SE","DK","AE","BD","CL","CO","EG","GH","IT","MY","MX","NG","PK","PE","PL","PT","TH","TR","VN","BG","CZ","FI","HR","IE","LT","LV","SI","SK","AL","AT","BE","EE","GR","HU","CY","LU","RO","RS","UA","AR","GE","BA","KZ","CN","NP","LK","UZ","BH","QA","JO","OM","KW","IL","MA","TN","RW","BW","TZ","ZM","KH","UY","PY","PA","CR","DO","EC","BO","GT","HN","SV","JM","TT","IS","MD","MK","AZ","AM","MT","SN","NA","ET","FJ","PG","UG","MU","WS","SB","VU","ZW","GM","CI","GY","BB","MV","BN","SC","MW","MG","ME","BT","TL","KG","AO","SZ","BS","MN","DZ","BJ","CM","GN","TG","CV","CD","MZ","AG","BZ","DM","GD","KN","LC","VC","AD","LI","MC","SM","DJ","LS","LR","SL","MR","GA"):
            self.assertGreaterEqual(self.report["country_counts"][iso]["verified"],3,iso)

    def test_one_legacy_registry_entry_does_not_count_as_government_verified(self):
        # A portal that returned HTTP 200 is NOT evidence that its operator
        # is an official agency or that the URL serves procurement today.
        self.assertEqual(0,self.report["country_counts"]["AF"]["verified"])
        self.assertGreaterEqual(self.report["country_counts"]["AF"]["gap"],3)
        self.assertTrue(all(x["verification"]!="official_primary"
                            for x in self.sites["AF"]))

    def test_unique_https_urls_and_verification_provenance(self):
        for iso,links in self.sites.items():
            self.assertEqual(len(links),len({x["url"].rstrip("/") for x in links}),iso)
            for row in links:
                self.assertTrue(safe_https(row["url"]),(iso,row["url"]))
                if row["verification"]=="official_primary":
                    self.assertTrue(safe_https(row["evidence_url"]))
                    self.assertTrue(row["verified_on"])

    def test_unverified_sites_cannot_claim_verified(self):
        for links in self.sites.values():
            for x in links:
                if x["verification"]!="official_primary":
                    self.assertFalse(x.get("verified_on"))
                    self.assertFalse(x.get("evidence_url"))

    def test_url_parser_fails_closed(self):
        for url in ("http://example.gov/","javascript:alert(1)",
                    "https://user:pass@legit.gov/", "https://example.gov:444/",
                    "https://example.gov/\n<script>"):
            self.assertFalse(safe_https(url),url)

    def test_country_pages_render_all_sovereign_portals_not_only_six_guides(self):
        build=(ROOT/"build.py").read_text(encoding="utf-8")
        self.assertIn('GOV_BUSINESS_SITES, GOV_SITE_COVERAGE = _load_gov_sites(ROOT)',build)
        self.assertIn('sec("government-business-sites", _title, _html)',build)
        self.assertIn('if not c.get("reg"):',build)
        self.assertIn("government-business-sites-coverage.json",build)


if __name__=="__main__":
    unittest.main()
