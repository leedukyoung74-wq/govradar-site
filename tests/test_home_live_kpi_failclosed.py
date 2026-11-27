"""Ensure initial GOV RADAR home HTML never asserts stale tender counts or dates."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class HomepageSafeFallbackTests(unittest.TestCase):
    def setUp(self):
        self.source=(ROOT/"build.py").read_text(encoding="utf-8")

    def test_live_tender_and_update_start_unknown_not_old_values(self):
        self.assertIn('<b id="kp-t">—</b>',self.source)
        self.assertIn('<b id="kp-u">—</b>',self.source)
        self.assertNotIn('<b id="kp-t">{n_t}</b>',self.source)

    def test_only_recent_valid_feed_can_set_metric(self):
        self.assertIn('data/feeds/today.json',self.source)
        self.assertIn('age>108000000',self.source)
        self.assertIn('Number.isInteger(d.n.open)&&d.n.open>=0',self.source)
        self.assertIn('Date.parse(String(d.updated||""))',self.source)
        self.assertNotIn('replace(/Z$/,":00Z")',self.source)

    def test_member_price_consistent_with_published_krw(self):
        self.assertIn('분석 회원 월 19,800원',self.source)
        self.assertIn('analysis member ₩19,800/mo',self.source)
        self.assertNotIn('분석 회원 월 20,000원',self.source)

if __name__=="__main__":
    unittest.main()
