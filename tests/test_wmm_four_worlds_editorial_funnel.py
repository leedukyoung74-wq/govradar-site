"""Static isolated checks: no false edition, no production edits, no PII collection."""
import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"ops/editorial_cover_prophecy_index.json"
PROTOTYPE=ROOT/"prototypes/four-worlds-conversion/index.html"
class FourWorldsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.html=PROTOTYPE.read_text(encoding="utf-8")
    def test_41_year_coverage(self):
        years=[x["cover_year"] for x in self.data["cover_index"]]
        self.assertEqual(years,list(range(1987,2028)))
    def test_2028_not_misrepresented(self):
        self.assertFalse(self.data["upcoming_2028"]["official_publication_verified"])
        self.assertIsNone(self.data["upcoming_2028"]["official_cover_url"])
    def test_unverified_covers_not_claimed(self):
        self.assertTrue(all(not x["artwork_analysis_verified"] for x in self.data["cover_index"]))
        self.assertTrue(all(x["cover_image_license"]=="NOT_CLEARED_FOR_WMM_REPUBLICATION" for x in self.data["cover_index"]))
    def test_official_2027_release(self):
        d=self.data["world_ahead_2027"]
        self.assertEqual(d["announcement"],"2026-11-16")
        self.assertEqual(len(d["themes"]),10)
        self.assertIn("economistgroup.com",d["source"])
        self.assertEqual(d["classification"],"EDITORIAL_FORECAST_NOT_EVENT_OR_PROPHECY")
    def test_seven_named_people(self):
        a=self.data["seven_ministers"]
        self.assertEqual(len(a),7)
        self.assertEqual(len(set(x["en"] for x in a)),7)
        self.assertTrue(all(x["current_2028_claim_status"]=="NOT_VERIFIED" for x in a))
    def test_preview_not_search_indexed(self):
        self.assertIn('name="robots" content="noindex,nofollow"',self.html)
        self.assertIn("비공개 검토용 시안",self.html)
    def test_four_independent_flows(self):
        self.assertTrue(all('data-site="'+k+'"' in self.html for k in ["wmm","radar","playground","miracle"]))
        self.assertTrue(all(k+':{code:' in self.html for k in ["wmm","radar","playground","miracle"]))
    def test_no_form_network_exfiltration(self):
        self.assertNotRegex(self.html,r'<form[^>]+action=')
        self.assertNotRegex(self.html,r'\bfetch\s*\(')
        self.assertNotIn("XMLHttpRequest",self.html)
        self.assertNotIn("localStorage",self.html)
        self.assertNotIn("sessionStorage",self.html)
        self.assertNotIn("analytics.track",self.html)
    def test_no_payment_or_donation_collection(self):
        self.assertNotIn('type="payment"',self.html)
        self.assertNotIn('type="email"',self.html)
        self.assertNotIn('type="tel"',self.html)
        self.assertNotIn("payment_intent",self.html)
        self.assertNotIn("Stripe(",self.html)
        self.assertIn("기부·후원금 결제",self.html)
    def test_mail_draft_requires_explicit_click(self):
        self.assertIn('$("#email").addEventListener("click"',self.html)
        self.assertIn('mailto:73036396@naver.com',self.html)
        self.assertNotIn('window.location.href="mailto:',self.html[:self.html.index('$("#email").addEventListener("click"')])
    def test_no_invented_playground_or_foundation_domains(self):
        self.assertNotRegex(self.html,r'https://(?:playground|miracle)\.wmm-hoa\.com')
    def test_mobile_breakpoints_and_accessibility(self):
        for bp in ("900px","530px","aria-live","aria-pressed","focus-visible","@media"):self.assertIn(bp,self.html)
if __name__=="__main__":unittest.main()
