"""Protect independent data writers against overlapping staged paths."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PublisherOwnershipTests(unittest.TestCase):
    def test_daily_feed_commit_does_not_stage_official_hazard_data(self):
        daily = (ROOT / ".github/workflows/feeds.yml").read_text(encoding="utf-8")
        self.assertIn("git add feeds", daily)
        for line in daily.splitlines():
            if line.lstrip().startswith("git add "):
                self.assertNotIn("hz/official.json", line)

    def test_fast_official_publisher_owns_official_hazard_data(self):
        fast = (ROOT / ".github/workflows/wmm_fast_official.yml").read_text(encoding="utf-8")
        self.assertIn("git add hz/official.json", fast)

if __name__ == "__main__":
    unittest.main()
