"""Source-of-truth preparedness safety check (no network, no deployment)."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class StockpileSafetySourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = json.loads((ROOT / "src" / "stock.json").read_text(encoding="utf-8"))

    def test_emergency_water_baseline(self):
        water = next(x for x in self.stock["qty"] if x["id"] == "q1")
        self.assertEqual(water["per"], 3.8)
        self.assertEqual(round(water["per"] * 2 * 14, 1), 106.4)
        self.assertEqual(f'{water["per"]*28:g}', "106.4")
        self.assertIn("106.4", water["base_ko"])
        self.assertIn("106.4", water["base_en"])

    def test_water_product_and_safety_notes(self):
        water = next(x for x in self.stock["products"] if x["cat"] == "water" and "생수" in x["ko"])
        self.assertIn("3.8L", water["spec_ko"])
        self.assertIn("3.8 L", water["spec_en"])
        self.assertIn("3.8L", self.stock["safety_ko"][0])
        self.assertIn("3.8 L", self.stock["safety_en"][0])

    def test_no_indoor_camping_stove_guidance(self):
        stove = next(x for x in self.stock["products"] if x["cat"] == "cook")
        self.assertIn("실외에서만", stove["spec_ko"])
        self.assertIn("outdoors only", stove["spec_en"])
        self.assertIn("20 ft (6 m)", self.stock["safety_en"][2])

    def test_generated_water_format_is_decimal_safe(self):
        source = (ROOT / "build.py").read_text(encoding="utf-8")
        self.assertIn('q["per"]*28:g', source)

if __name__ == "__main__":
    unittest.main()
