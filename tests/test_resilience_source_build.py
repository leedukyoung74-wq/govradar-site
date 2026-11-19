"""Non-deploying source contract for WMM Resilience 7-language build integration.

Tests only immutable local artifacts and builder wiring. Does not run a live build,
assert translations are complete, certify food products, or deploy.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ("ko", "en", "es", "fr", "ar", "vi", "id")

class ResilienceSourceBuildContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = (ROOT / "build.py").read_text(encoding="utf8")
        cls.foods = json.loads((ROOT / "src/wmm-food-country-profiles.json").read_text(encoding="utf8"))
        cls.guides = json.loads((ROOT / "src/wmm-food-primary-guidance-reviewed.json").read_text(encoding="utf8"))
        cls.master = json.loads((ROOT / "src/countries_meta.json").read_text(encoding="utf8"))
        cls.regions = json.loads((ROOT / "src/regions.json").read_text(encoding="utf8"))

    def test_preserves_legacy_routes_and_adds_separate_review_route(self):
        for route, marker in [
            ("ready", 'W(f"/{L}/ready/index.html", ready_page(L))'),
            ("prepare", 'W(f"/{L}/prepare/index.html", stock_page(L))'),
            ("resilience", 'W(f"/{L}/resilience/index.html", open(_rs, encoding="utf8").read())'),
        ]:
            with self.subTest(route=route):
                self.assertIn(marker, self.builder)
        self.assertIn('os.path.join(SRC, "resilience_pages", L + ".html")', self.builder)
        self.assertIn('"wmm-food-country-profiles.json"', self.builder)
        self.assertIn('"wmm-food-primary-guidance-reviewed.json"', self.builder)
        self.assertNotIn('urls.append((f"/{L}/resilience/"', self.builder, "Do not publish review-only route in sitemap")

    def test_seven_localized_pages_noindex_and_correct_links(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html = (ROOT / "src/resilience_pages" / (lang + ".html")).read_text(encoding="utf8")
                self.assertIn('<html lang="' + lang + '"', html)
                self.assertIn('noindex, nofollow', html)
                self.assertIn('href="/' + lang + '/ready/"', html)
                self.assertIn('href="/' + lang + '/prepare/"', html)
                self.assertIn('id="wmm-resilience"', html)
                self.assertIn('/assets/wmm-resilience.js', html)
                self.assertIn('/assets/wmm-resilience.css', html)
                self.assertNotIn('href="/ko/ready/"', html) if lang != "ko" else None

    def test_assets_flow_through_existing_web_asset_copier(self):
        self.assertIn('os.path.join(ROOT, "web", "*")', self.builder)
        for file in ("wmm-resilience.js", "wmm-resilience.css"):
            self.assertTrue((ROOT / "web" / file).is_file())
        js = (ROOT / "web/wmm-resilience.js").read_text(encoding="utf8")
        self.assertIn('fetch("/data/wmm-food-country-profiles.json")', js)
        self.assertIn('fetch("/data/wmm-food-primary-guidance-reviewed.json")', js)

    def test_draft_safety_translations_and_food_name_suppression(self):
        js = (ROOT / "web/wmm-resilience.js").read_text(encoding="utf8")
        self.assertIn("var provisionalSafetyLocales=", js)
        self.assertIn("languageReviewNote", js)
        self.assertIn('L==="ko"?"<p><b>"+e(t.countryExamples)', js)
        for locale in ("es", "fr", "ar", "vi", "id"):
            with self.subTest(locale=locale):
                self.assertIn('"' + locale + '":{"calcNote":', js)
        self.assertIn("if(provisionalSafetyLocales[L])Object.assign(t,provisionalSafetyLocales[L]);", js)

    def test_193_countries_23_regions_and_zero_product_validation(self):
        master_ids = {x["iso"] for x in self.master}
        food_ids = {x["iso"] for x in self.foods}
        self.assertEqual(len(master_ids), 193)
        self.assertEqual(master_ids, food_ids)
        self.assertEqual(len(self.regions), 23)
        self.assertEqual(len({x["iso"] for x in self.regions}), 23)
        self.assertEqual(sum(x["status"] == "illustrative" for x in self.foods), 42)
        self.assertEqual(sum(x["status"] == "pending" for x in self.foods), 151)
        for x in self.foods:
            self.assertFalse(x["local_official_guidance_verified"])
            self.assertFalse(x["retail_availability_verified"])
            self.assertFalse(x["shelf_life_verified"])
            self.assertEqual(x["sources"], [])
        sources = self.guides["countries"]
        self.assertEqual({x["iso"] for x in sources}, {"KR", "JP", "US"})
        self.assertTrue(all(x["product_review_status"] == "not_checked" for x in sources))

if __name__ == "__main__":
    unittest.main()
