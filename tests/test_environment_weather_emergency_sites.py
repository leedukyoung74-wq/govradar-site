"""193-country national environment, weather and emergency source contract tests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from environment_weather_emergency_sites import CATEGORIES, load_catalog, safe_https

class NationalEnvironmentWeatherEmergencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records,cls.report=load_catalog(ROOT)

    def test_every_country_has_three_distinct_categories_even_if_missing(self):
        self.assertEqual(193,len(self.records))
        self.assertEqual(193,len(self.report["country_counts"]))
        self.assertEqual(("environment","weather","emergency"),CATEGORIES)
        self.assertEqual(579,self.report["target_category_links"])
        for iso,row in self.records.items():
            self.assertEqual(set(CATEGORIES),set(row),iso)
            self.assertEqual(3,sum(bool(row[k]) for k in CATEGORIES)
                             +self.report["country_counts"][iso]["missing"],iso)

    def test_directory_is_not_an_api_or_live_verified_claim(self):
        total=sum(self.report["candidate_links_by_category"].values())
        self.assertEqual(total,self.report["linked_candidate_total"])
        self.assertEqual(579-total,self.report["missing_national_category_links"])
        self.assertEqual(0,self.report["live_verified_total"])
        self.assertGreater(total,150,"Existing sources and curated primary links should load")
        self.assertLess(total,579,"Never silently declare all world agencies verified")
        for iso,meta in self.report["country_counts"].items():
            self.assertEqual(meta["live_verified"],0,iso)
        self.assertTrue("not independently live-verified" in self.report["warning"])

    def test_existing_korea_and_verified_2026_sweden_name(self):
        self.assertEqual("https://www.mcee.go.kr/",self.records["KR"]["environment"]["url"])
        self.assertEqual("https://www.weather.go.kr/",self.records["KR"]["weather"]["url"])
        self.assertEqual("https://www.safekorea.go.kr/",self.records["KR"]["emergency"]["url"])
        self.assertTrue("MCF" in self.records["SE"]["emergency"]["name"])
        self.assertEqual("https://www.mcf.se/en/",self.records["SE"]["emergency"]["url"])

    def test_missing_countries_have_honest_international_directory_fallbacks(self):
        directories=self.report["international_directory_refs"]
        self.assertEqual(set(CATEGORIES),set(directories))
        self.assertIn("worldweather.wmo.int",directories["weather"])
        self.assertIn("undrr.org",directories["emergency"])
        self.assertIn("unep.org",directories["environment"])
        for iso,c in self.records.items():
            for kind in CATEGORIES:
                if c[kind] is None:
                    self.assertTrue(safe_https(directories[kind]))
                    self.assertGreaterEqual(self.report["country_counts"][iso]["missing"],1)

    def test_all_national_links_https_and_access_unverified(self):
        for iso,c in self.records.items():
            for kind,item in c.items():
                if item is None:continue
                self.assertTrue(safe_https(item["url"]),(iso,kind))
                self.assertTrue(item["name"],(iso,kind))
                self.assertEqual("curated_candidate",item["review"],(iso,kind))
                self.assertEqual("not_live_tested",item["access"],(iso,kind))
        for invalid in ("http://unsafe.example/","javascript:alert(1)",
                        "https://someone:password@official.gov/","https://official.gov:8443/",
                        "https://official.gov/#spoof","https://official.gov/\n<script>"):
            self.assertFalse(safe_https(invalid),invalid)

    def test_missing_country_or_false_verified_link_fails_closed(self):
        source=json.loads((ROOT/"src/environment_weather_emergency_sites.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"src";target.mkdir()
            (target/"countries_meta.json").write_text(
                (ROOT/"src/countries_meta.json").read_text(encoding="utf-8"),encoding="utf-8")
            data=target/"environment_weather_emergency_sites.json"
            missing=json.loads(json.dumps(source))
            del missing["countries"]["KR"]
            data.write_text(json.dumps(missing),encoding="utf8")
            with self.assertRaises(ValueError):load_catalog(tmp)
            unsafe=json.loads(json.dumps(source))
            unsafe["countries"]["KR"]["environment"]["url"]="https://evil.example#spoof"
            data.write_text(json.dumps(unsafe),encoding="utf8")
            with self.assertRaises(ValueError):load_catalog(tmp)
            false=json.loads(json.dumps(source))
            false["countries"]["KR"]["environment"]["access"]="verified_live"
            data.write_text(json.dumps(false),encoding="utf8")
            with self.assertRaises(ValueError):load_catalog(tmp)

    def test_country_page_includes_new_public_cards_and_machine_readable_evidence(self):
        s=(ROOT/"build.py").read_text(encoding="utf8")
        self.assertIn('body.append(sec("environment-weather-emergency", _head, _ewe_html))',s)
        self.assertIn('EWE_SITES, EWE_COVERAGE = _load_ewe_catalog(ROOT)',s)
        self.assertIn('environment-weather-emergency-coverage.json',s)
        self.assertIn('environment-weather-emergency-directory.json',s)
        self.assertIn("rel=\"noopener noreferrer nofollow\"",s)
        self.assertIn("국가기관 미연결 · 국제기구 디렉터리에서 검색",s)

if __name__=="__main__":
    unittest.main()
