"""Canonical 193-country official-agency candidate import safety regression.

Does not prove a site URL is accessible, contains CAP/RSS, or is commercially licensed.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from environment_weather_emergency_sites import CATEGORIES,load_catalog,safe_https

CODES={
    "DZ":3,"AO":3,"BJ":3,"BW":3,"BF":3,"BI":3,
    "CV":3,"CM":3,"ET":3,"MV":3,
    "JO":3,"GE":3,"LU":3,"MD":3,"SK":3,
    "FJ":2,
}


class CanonicalAgencyImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records,cls.report=load_catalog(ROOT)
        cls.raw=json.loads((ROOT/"src/environment_weather_emergency_sites.json").read_text(encoding="utf8"))

    def test_total_candidate_slots_267_and_no_live_claims(self):
        r=self.report
        self.assertEqual(r["target_category_links"],579)
        self.assertEqual(r["linked_candidate_total"],267)
        self.assertEqual(r["missing_national_category_links"],312)
        self.assertEqual(r["live_verified_total"],0)
        self.assertEqual(len(self.records),193)

    def test_sixteen_newly_filled_countries_have_expected_slots(self):
        self.assertEqual(len(CODES),16)
        self.assertEqual(sum(CODES.values()),47)
        for iso,count in CODES.items():
            row=self.records[iso]
            self.assertEqual(sum(item is not None for item in row.values()),3,iso)
            self.assertEqual(self.report["country_counts"][iso]["missing"],0,iso)
            for kind,item in row.items():
                self.assertTrue(item and safe_https(item["url"]),(iso,kind))
                self.assertEqual(item["access"],"not_live_tested",(iso,kind))
                self.assertEqual(item["review"],"curated_candidate",(iso,kind))

    def test_existing_important_korea_and_fiji_weather_preserved(self):
        r=self.records
        self.assertEqual(r["KR"]["environment"]["url"],"https://www.mcee.go.kr/")
        self.assertEqual(r["KR"]["weather"]["url"],"https://www.weather.go.kr/")
        self.assertEqual(r["KR"]["emergency"]["url"],"https://www.safekorea.go.kr/")
        self.assertEqual(r["FJ"]["weather"]["url"],"https://www.met.gov.fj/")
        self.assertEqual(r["SE"]["emergency"]["url"],"https://www.mcf.se/en/")

    def test_added_institution_not_misrepresented_as_feed(self):
        v=self.raw["countries"]
        self.assertEqual(v["MV"]["weather"]["access"],"not_live_tested")
        self.assertEqual(v["FJ"]["emergency"]["access"],"not_live_tested")
        self.assertEqual(v["JO"]["emergency"]["access"],"not_live_tested")
        self.assertEqual(v["CV"]["weather"]["access"],"not_live_tested")
        self.assertTrue("source" in v["MD"]["environment"])
        self.assertEqual(self.raw["policy"]["default_access"],"not_live_tested")

if __name__=="__main__":
    unittest.main()
