"""Regression: country summary must count only verified, non-stale open notices."""
import datetime as dt
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import quality_gate


class CountrySummaryQualityGateTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 11, 20, 8, 0, tzinfo=dt.timezone.utc)
        self.items = []
        for n in range(100):
            self.items.append({
                "iso": "KR", "title": f"Notice {n}", "buyer": "Public buyer",
                "deadline": "2026-11-21", "url": f"https://example.org/tender/{n}",
                "source": "World Bank", "slug": "south-korea", "n": {},
                "added": "2026-11-20", "sec": [], "pg": "GO",
                "stale": n == 0,
            })
        self.feed = {
            "updated": self.now.strftime("%Y-%m-%dT%H:%MZ"),
            "count": len(self.items), "items": self.items,
        }

    def check(self, summary):
        new = {"tenders.json": self.feed, "cty/_summary.json": summary}
        with patch("feed_tenders.valid", return_value=""):
            return quality_gate.check(new, {}, now=self.now)

    def test_stale_not_counted_as_verified_open(self):
        self.assertEqual([], self.check({"t": {"n": 99, "c": 1}}))

    def test_verified_open_count_mismatch_fails_closed(self):
        self.assertTrue(any("open-tender count" in x for x in
                            self.check({"t": {"n": 98, "c": 1}})))

    def test_country_count_mismatch_fails_closed(self):
        self.assertTrue(any("country count" in x for x in
                            self.check({"t": {"n": 99, "c": 2}})))

    def test_missing_summary_fails_closed(self):
        self.assertTrue(any("missing or unreadable" in x for x in self.check(None)))


if __name__ == "__main__":
    unittest.main()
