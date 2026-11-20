"""Official-source directory integrity checks. Link candidates are not live verification."""
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit
ROOT = Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((ROOT / "src" / name).read_text(encoding="utf-8"))
class RegionAndDefenceDirectoryQA(unittest.TestCase):
    def test_all_regions_separate_and_empty_fields_are_explicit(self):
        regions = read("regions.json")
        directory = read("territory_official_sources.json")
        items = directory["territories"]
        self.assertEqual(len(regions), 23)
        self.assertEqual(set(items), {x["iso"] for x in regions})
        fields = directory["categories"]
        self.assertEqual(len(fields), 8)
        for r in regions:
            item = items[r["iso"]]
            self.assertEqual(item["parent_iso"], r["parent"])
            for f in fields:
                self.assertIsInstance(item[f], list)
                seen = set()
                for src in item[f]:
                    self.check_url(src["url"])
                    self.check_url(src["evidence_url"])
                    self.assertNotIn(src["url"], seen)
                    seen.add(src["url"])
                    self.assertEqual(src["access"], "not_live_tested")
    def test_193_country_defence_registry(self):
        meta = read("countries_meta.json")
        registry = read("country_defence_official_sources.json")
        entries = registry["countries"]
        self.assertEqual(len(meta), 193)
        self.assertEqual(set(entries), {x["iso"] for x in meta})
        self.assertEqual(registry["target_minimum_sites_per_country"], 3)
        for iso, item in entries.items():
            urls = set()
            for src in item["official_sites"]:
                self.check_url(src["url"])
                self.check_url(src["evidence_url"])
                self.assertNotIn(src["url"], urls, iso)
                urls.add(src["url"])
                self.assertEqual(src["access"], "not_live_tested")
            if len(item["official_sites"]) == 0:
                self.assertEqual(item["status"], "research_pending")
        self.assertEqual(sum(len(c["official_sites"]) for c in entries.values()), 39)
        self.assertEqual(sum(len(c["official_sites"]) >= 3 for c in entries.values()), 13)
    def check_url(self, value):
        u = urlsplit(value)
        self.assertEqual(u.scheme, "https")
        self.assertTrue(u.hostname)
        self.assertFalse(u.username)
        self.assertFalse(u.password)
        self.assertFalse(u.fragment)
if __name__ == "__main__":
    unittest.main()
