import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nws_cisa_due import LIMITS, needs_refresh, should_refresh

UTC = dt.timezone.utc


class NWSAndCISAFallbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name)
        (self.data / "hz").mkdir()
        self.now = dt.datetime(2026, 11, 20, 11, 0, tzinfo=UTC)

    def set_feed(self, name, *, age_minutes=0, ok=True, stale=False, bad_time=False, checked_age_minutes=None):
        when = self.now - dt.timedelta(minutes=age_minutes)
        stamp = "not-a-date" if bad_time else when.isoformat().replace("+00:00", "Z")
        checked = ((self.now - dt.timedelta(minutes=checked_age_minutes)).isoformat().replace("+00:00", "Z")
                   if checked_age_minutes is not None else None)
        (self.data / "hz" / name).write_text(json.dumps({
            "source_health": {"ok": ok, "stale": stale, "last_ok": stamp, "checked_at": checked},
            "items": []
        }), encoding="utf-8")

    def fill(self, nws_age=10, cisa_age=30):
        self.set_feed("nws_active.json", age_minutes=nws_age)
        self.set_feed("cisa_kev.json", age_minutes=cisa_age)

    def test_recent_good_feeds_do_not_create_duplicate_fallback(self):
        self.fill()
        self.assertFalse(should_refresh("workflow_run", self.data, self.now))

    def test_old_nws_needs_fallback(self):
        self.fill(nws_age=91)
        self.assertTrue(should_refresh("workflow_run", self.data, self.now))

    def test_old_cisa_needs_fallback(self):
        self.fill(cisa_age=481)
        self.assertTrue(should_refresh("workflow_run", self.data, self.now))

    def test_one_failed_source_forces_retry(self):
        self.fill()
        self.set_feed("nws_active.json", age_minutes=2, ok=False, stale=True)
        self.assertTrue(should_refresh("workflow_run", self.data, self.now))

    def test_recent_failure_is_rate_limited_without_marking_healthy(self):
        self.fill()
        self.set_feed("nws_active.json", age_minutes=300, ok=False, stale=True, checked_age_minutes=4)
        self.assertFalse(should_refresh("workflow_run", self.data, self.now))

    def test_failed_source_retries_after_30_minute_cooldown(self):
        self.fill()
        self.set_feed("nws_active.json", age_minutes=300, ok=False, stale=True, checked_age_minutes=31)
        self.assertTrue(should_refresh("workflow_run", self.data, self.now))

    def test_malformed_timestamp_fails_closed(self):
        self.fill()
        self.set_feed("nws_active.json", bad_time=True)
        self.assertTrue(should_refresh("workflow_run", self.data, self.now))

    def test_future_dated_timestamp_fails_closed(self):
        self.fill()
        self.set_feed("nws_active.json", age_minutes=-30)
        self.assertTrue(should_refresh("workflow_run", self.data, self.now))

    def test_missing_file_fails_closed(self):
        self.assertTrue(should_refresh("workflow_run", self.data, self.now))

    def test_manual_and_cron_always_preserve_prior_behavior(self):
        self.fill()
        for event in ("schedule", "workflow_dispatch", "push"):
            self.assertTrue(should_refresh(event, self.data, self.now))

    def test_naive_datetime_is_rejected(self):
        self.fill()
        with self.assertRaises(ValueError):
            should_refresh("workflow_run", self.data, dt.datetime(2026, 11, 20))

    def test_limits_keep_public_source_checks_separate(self):
        self.assertEqual(90*60, dict(LIMITS)["nws_active.json"])
        self.assertEqual(8*3600, dict(LIMITS)["cisa_kev.json"])


if __name__ == "__main__":
    unittest.main()
