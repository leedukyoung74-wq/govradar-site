"""A late closing time must not cause the next valid feed publication to fail."""
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import reconcile_expiring_tenders as R


class ExpiringNoticeReconcileTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 11, 20, 10, 5, tzinfo=dt.timezone.utc)

    def notice(self, deadline_at):
        return {"iso": "GB", "title": "Verified notice", "deadline": "2026-11-20",
                "deadline_at": deadline_at, "url": "https://example.org/notice"}

    def test_exact_closed_removed_date_only_remains_until_end_everywhere(self):
        items = [self.notice("2026-11-20T10:00:00Z"),
                 self.notice("2026-11-20T10:10:00Z"),
                 self.notice("2026-11-20"),
                 self.notice("bad-date")]
        kept, removed = R.prune_closed(items, self.now)
        self.assertEqual(1, removed)
        self.assertEqual(items[1:], kept)  # unknown remains for the quality gate

    def test_reconcile_updates_counts_but_never_fakes_upstream_freshness(self):
        with tempfile.TemporaryDirectory() as d:
            data_root = Path(d)
            feed_dir = data_root / "feeds"
            feed_dir.mkdir()
            items = [self.notice("2026-11-20T10:00:00Z"),
                     self.notice("2026-11-21T11:00:00Z")]
            before = {"updated": "2026-11-20T09:30Z", "count": 2,
                      "items": items, "other_field": "preserved"}
            path = feed_dir / "tenders.json"
            path.write_text(json.dumps(before), encoding="utf-8")
            with patch.object(R.subprocess, "run") as rebuild:
                removed = R.reconcile(data_root, now=self.now)
            after = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, removed)
            self.assertEqual(1, after["count"])
            self.assertEqual(items[1:], after["items"])
            self.assertEqual(before["updated"], after["updated"])
            self.assertEqual("preserved", after["other_field"])
            self.assertEqual(2, rebuild.call_count)
            self.assertTrue(all(c.kwargs["check"] for c in rebuild.call_args_list))
            self.assertFalse(any(feed_dir.glob(".tenders-reconciled-*")))

    def test_no_closures_leaves_feed_unmodified_and_skips_rebuild(self):
        with tempfile.TemporaryDirectory() as d:
            feed_dir = Path(d) / "feeds"
            feed_dir.mkdir()
            path = feed_dir / "tenders.json"
            original = '{"updated":"2026-11-20T09:30Z","count":1,"items":[{"deadline_at":"2026-11-21T00:00:00Z"}]}'
            path.write_text(original, encoding="utf-8")
            with patch.object(R.subprocess, "run") as rebuild:
                self.assertEqual(0, R.reconcile(d, now=self.now))
            self.assertEqual(original, path.read_text(encoding="utf-8"))
            rebuild.assert_not_called()

    def test_bad_feed_fails_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as d:
            feed_dir = Path(d) / "feeds"
            feed_dir.mkdir()
            path = feed_dir / "tenders.json"
            content = '{"items":"not a list","count":0}'
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(ValueError):
                R.reconcile(d, now=self.now)
            self.assertEqual(content, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
