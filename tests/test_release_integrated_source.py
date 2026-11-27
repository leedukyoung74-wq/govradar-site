"""Integrated verification for GOV RADAR src builds, no live customer or API writes."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"cf"/"public"
LIVE=ROOT/"live-reference"/"public"

class Integration(unittest.TestCase):
    def test_backend_requires_consent_before_sql(self):
        f=(ROOT/"cf/functions/api/req.js").read_text("utf-8")
        self.assertIn('b.privacy_consent !== true',f)
        self.assertIn('error: "consent_required"',f)
        self.assertLess(f.index('b.privacy_consent !== true'),f.index('const key = u ?'))
        self.assertIn('body.length > 4000',f)
    def test_ko_en_request_json_consent(self):
        for lang in ("ko","en"):
            with self.subTest(lang=lang):
                page=(GEN/lang/"request/index.html").read_text("utf-8")
                self.assertIn('name="privacy_agree"',page)
                self.assertIn('privacy_consent:f.querySelector(',page)
                self.assertIn('method="POST"',page)
                self.assertIn('name="form-name" value="order"',page)
                self.assertIn('"/api/req"',page)
    def test_7_locale_home_safe_kpi_and_price(self):
        for lang in ("ko","en","es","fr","ar","vi","id"):
            with self.subTest(lang=lang):
                page=(GEN/lang/"index.html").read_text("utf-8")
                self.assertIn('id="kp-t">—</b>',page)
                self.assertIn('id="kp-u">—</b>',page)
                self.assertIn('data/feeds/today.json',page)
                self.assertNotIn('id="kp-t">1022',page)
                self.assertIn('19',page)
    def test_live_index_and_request_preserved_in_snapshot(self):
        for lang in ("ko","en","es","fr","ar","vi","id"):
            with self.subTest(lang=lang):
                self.assertTrue((LIVE/lang/"index.html").exists())
                self.assertTrue((LIVE/lang/"request/index.html").exists())
    def test_original_api_compatibility_still_present(self):
        f=(ROOT/"cf/functions/api/req.js").read_text("utf-8")
        for name in ('onRequestGet','onRequestPost','onRequestPatch','const quotaSql','"gateway_reported"'):
            self.assertIn(name,f)

if __name__ == "__main__":
    unittest.main()
