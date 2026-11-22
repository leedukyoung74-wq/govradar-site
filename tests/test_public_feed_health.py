"""Read-only public-feed health check classification (no external network)."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_site


class PublicFeedHealthTests(unittest.TestCase):
    def run_probe(self, stamp):
        with tempfile.TemporaryDirectory() as d:
            feeds = Path(d) / "data_branch" / "feeds"
            feeds.mkdir(parents=True)
            (feeds / "tenders.json").write_text(json.dumps({
                "items": [{"iso": "KR", "title": "A", "buyer": "B", "deadline": "2090-01-01",
                           "url": "https://example.org", "source": "World Bank", "slug": "kr",
                           "n": {}, "added": "2026-11-20", "sec": [], "pg": "GO"}]}), encoding="utf-8")
            out = str(feeds / "site_check.json")
            def fake_get(url):
                if url.startswith(check_site.SITE):
                    # Every page links to the expected feed, as in production templates.
                    return 200, check_site.RAW + "tenders.json " + check_site.RAW + "cty/" + " " + check_site.RAW + "cty/_summary.json"
                return 200, json.dumps({"updated": stamp, "count": 100})
            with patch.object(check_site, "ROOT", d), patch.object(check_site, "get", side_effect=fake_get):
                passed = check_site.main(out)
            return passed, json.loads(Path(out).read_text(encoding="utf-8"))

    def test_future_timestamp_must_fail_closed(self):
        passed, result = self.run_probe("2090-01-01T00:00Z")
        self.assertFalse(passed)
        self.assertEqual("invalid_or_future_timestamp", result["feeds"]["tenders.json"]["issue"])
        self.assertIn("tenders.json", result["failed_public_feeds"])

    def test_old_public_feed_must_fail_closed(self):
        passed, result = self.run_probe("2020-01-01T00:00Z")
        self.assertFalse(passed)
        self.assertEqual("stale_publication", result["feeds"]["tenders.json"]["issue"])

    def test_invalid_timestamp_must_fail_closed(self):
        passed, result = self.run_probe("not-a-date")
        self.assertFalse(passed)
        self.assertEqual("invalid_or_future_timestamp", result["feeds"]["tenders.json"]["issue"])


if __name__ == "__main__":
    unittest.main()
