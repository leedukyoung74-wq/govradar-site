"""Public authority finder preview must not promise commercial buyers or unsafe rendering."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"src/web/public_procurement_buyers.html").read_text(encoding="utf-8")

class BuyerFrontendSmoke(unittest.TestCase):
    def test_static_preview_is_mobile_responsive_and_not_live_claim(self):
        self.assertIn('name="viewport"',HTML)
        self.assertIn("@media(max-width:720px)",HTML)
        self.assertIn("noindex",HTML)
        self.assertIn("NOT verified commercial importers",HTML)
        self.assertIn("not_commercial_buyer_directory",HTML)

    def test_source_link_allowlist_and_dom_only_not_raw_html(self):
        self.assertIn("const allowed=new Set",HTML)
        self.assertIn("u.protocol===\"https:\"",HTML)
        self.assertIn('link.rel="noopener noreferrer"',HTML)
        self.assertIn("textContent",HTML)
        self.assertNotIn("innerHTML",HTML)
        self.assertIn("/data/public-procurement-buyers.json",HTML)

    def test_search_is_readonly_without_customer_post(self):
        self.assertNotIn('method="POST"',HTML)
        self.assertNotIn("localStorage",HTML)
        self.assertNotIn("api_key",HTML)

if __name__=="__main__":
    unittest.main()
