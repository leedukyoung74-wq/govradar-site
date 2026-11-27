"""Read-only offline safety tests for site health evidence publication.

Never creates worktrees, runs a remote git command, or writes a data branch.
"""
import datetime as dt
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import publish_site_check as P


def fixture(status="PASS", checked="2026-11-27T09:10Z"):
    feeds = {k: {"status": 200, "fresh": True, "issue": "ok", "count": 2}
             for k in ("tenders.json", "cty/_summary.json", "awards.json")}
    return {"checked": checked, "result": status,
            "pages": [{"status": 200, "reads_feed": True} for _ in range(4)],
            "feeds": feeds, "local": {"issue": "ok", "items": 2}}


NOW = dt.datetime(2026, 11, 27, 9, 20, tzinfo=dt.timezone.utc)


class SiteCheckEvidenceTests(unittest.TestCase):
    def test_valid_pass_requires_page_and_feed_evidence(self):
        self.assertEqual(P.clock("2026-11-27T09:10Z"),
                         P.validate_report(fixture(), NOW))
        bad = fixture()
        bad["pages"][0]["reads_feed"] = False
        with self.assertRaises(ValueError):
            P.validate_report(bad, NOW)
        bad = fixture()
        bad["feeds"]["tenders.json"]["fresh"] = False
        with self.assertRaises(ValueError):
            P.validate_report(bad, NOW)
        bad = fixture()
        bad["local"]["issue"] = "invalid_new_items"
        with self.assertRaises(ValueError):
            P.validate_report(bad, NOW)

    def test_failed_probe_is_publishable_as_fail_evidence_not_success(self):
        bad = fixture(status="FAIL")
        bad["pages"][1]["status"] = 503
        self.assertEqual(P.clock("2026-11-27T09:10Z"),
                         P.validate_report(bad, NOW))
        self.assertEqual("FAIL", bad["result"])

    def test_stale_or_future_or_malformed_is_not_publishable(self):
        for checked in ("2026-11-16T06:26Z", "2026-11-27T09:35Z",
                        "2026-11-27", "", None):
            with self.subTest(checked=checked):
                with self.assertRaises((ValueError, TypeError)):
                    P.validate_report(fixture(checked=checked), NOW)

    def test_only_newer_success_or_failure_can_replace_existing(self):
        older = fixture(status="PASS", checked="2026-11-27T09:05Z")
        candidate = fixture(status="FAIL", checked="2026-11-27T09:10Z")
        newer = fixture(status="FAIL", checked="2026-11-27T09:15Z")
        self.assertEqual("publish", P.decision(older, candidate))
        self.assertEqual("skip", P.decision(candidate, candidate))
        self.assertEqual("skip", P.decision(newer, candidate))
        self.assertEqual("publish", P.decision({"checked": "n/a"}, candidate))

    def test_dry_run_and_failed_feed_publish_cannot_write_site_evidence(self):
        s = (ROOT / ".github/workflows/feeds.yml").read_text("utf8")
        self.assertIn("id: publish_feeds", s)
        self.assertIn("inputs.task == 'daily' && !inputs.dry_run", s)
        self.assertIn("steps.publish_feeds.outcome == 'success'", s)
        self.assertIn("python3 tools/publish_site_check.py data_branch", s)
        self.assertLess(s.index("- name: Publish to data branch"),
                        s.index("- name: Check the public site reads fresh feeds"))
        self.assertLess(s.index("- name: Check the public site reads fresh feeds"),
                        s.index("- name: Persist current site probe PASS or FAIL"))


if __name__ == "__main__":
    unittest.main()
