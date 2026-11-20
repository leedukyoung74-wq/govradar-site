"""Emergency feed-publishing regression coverage. No network or production data writes."""
import datetime as dt
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import quality_gate

NOW = dt.datetime(2026, 11, 20, 8, 0, tzinfo=dt.timezone.utc)


class VerifiedOpenParity(unittest.TestCase):
    def setUp(self):
        self.items = []
        for i in range(100):
            self.items.append({
                "iso": "KR", "title": f"Notice {i}", "buyer": "Verified buyer",
                "deadline": "2026-11-21", "url": f"https://example.org/{i}",
                "source": "World Bank", "slug": "south-korea", "n": {},
                "added": "2026-11-20", "sec": [], "pg": "GO",
                "stale": i == 0,
            })
        self.feed = {"updated": "2026-11-20T08:00Z", "count": 100, "items": self.items}

    def gate(self, summary):
        with patch("feed_tenders.valid", return_value=""):
            return quality_gate.check(
                {"tenders.json": self.feed, "cty/_summary.json": summary},
                {}, now=NOW, require_country_summary=True,
            )

    def test_unverified_carried_item_is_not_counted_open(self):
        self.assertEqual([], self.gate({"t": {"n": 99, "c": 1}}))

    def test_future_dated_feed_timestamp_blocks_publication(self):
        self.feed["updated"] = "2026-11-21T08:00Z"
        self.assertTrue(any("in the future" in s for s in
                            self.gate({"t": {"n": 99, "c": 1}})))

    def test_notice_mismatch_blocks_publication(self):
        self.assertTrue(any("open-tender count" in s for s in self.gate({"t": {"n": 98, "c": 1}})))

    def test_country_mismatch_blocks_publication(self):
        self.assertTrue(any("country count" in s for s in self.gate({"t": {"n": 99, "c": 2}})))

    def test_missing_summary_blocks_publication(self):
        self.assertTrue(any("missing or unreadable" in s for s in self.gate(None)))


class SafeConcurrentPublication(unittest.TestCase):
    def test_daily_publisher_reconciles_both_feeds_and_official_sources(self):
        workflow = (ROOT / ".github/workflows/feeds.yml").read_text(encoding="utf-8")
        self.assertIn("git add feeds hz/official.json", workflow)
        self.assertIn("merge_official_sources.py", workflow)
        self.assertIn("git reset --hard origin/data", workflow)
        self.assertIn("python ../tools/quality_gate.py .", workflow)
        self.assertNotIn("git push --force", workflow)

    def test_review_runs_have_own_queue_and_live_writer_cannot_be_cancelled(self):
        workflow = (ROOT / ".github/workflows/feeds.yml").read_text(encoding="utf-8")
        self.assertIn("github.head_ref || github.ref_name", workflow)
        self.assertIn('cancel-in-progress: "${{ inputs.dry_run }}"', workflow)

    def test_dedicated_hazard_publisher_still_stages_official_json(self):
        workflow = (ROOT / ".github/workflows/wmm_fast_official.yml").read_text(encoding="utf-8")
        self.assertIn("git add hz/official.json", workflow)


if __name__ == "__main__":
    unittest.main()
