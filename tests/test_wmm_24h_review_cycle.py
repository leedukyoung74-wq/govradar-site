"""Offline acceptance tests for review-only hourly 24h GitHub Actions plan."""
import datetime as dt
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from wmm_24h_review_cycle import UTC, evaluate, phase_for_cycle, review

START = dt.datetime(2026, 11, 20, 7, 0, tzinfo=UTC)
START_TEXT = "2026-11-20T07:00:00Z"

class ReviewCycleSafetyTests(unittest.TestCase):
    def test_unapproved_schedule_does_not_run(self):
        for flag in ("", "false", "yes", "1"):
            with self.subTest(flag=flag):
                result = evaluate("schedule", flag, START_TEXT, START)
                self.assertFalse(result["run"])
                self.assertEqual(result["reason"], "explicit_enable_required")

    def test_missing_invalid_and_naive_start_fail_closed(self):
        for text in ("", "not-a-date", "2026-11-20T07:00:00"):
            with self.subTest(value=text):
                result = evaluate("schedule", "true", text, START)
                self.assertFalse(result["run"])
                self.assertEqual(result["reason"], "invalid_utc_start")

    def test_window_excludes_past_and_after_24h(self):
        for moment, expected in (
            (START - dt.timedelta(seconds=1), "window_not_started"),
            (START + dt.timedelta(hours=24), "window_expired"),
            (START + dt.timedelta(hours=48), "window_expired"),
        ):
            with self.subTest(moment=moment):
                result=evaluate("schedule","true",START_TEXT,moment)
                self.assertFalse(result["run"])
                self.assertEqual(result["reason"],expected)

    def test_each_valid_hour_gets_one_phase_and_no_restart(self):
        for cycle in range(24):
            with self.subTest(hour=cycle):
                moment=START+dt.timedelta(hours=cycle, minutes=16)
                result=evaluate("schedule","true",START_TEXT,moment)
                self.assertTrue(result["run"])
                self.assertEqual(result["cycle"],cycle)
                self.assertIn(phase_for_cycle(cycle)[0], {x[0] for x in __import__("wmm_24h_review_cycle").PHASES})

    def test_manual_and_pr_preview_safe_without_schedule_activation(self):
        for event in ("pull_request", "workflow_dispatch"):
            r=evaluate(event,"", "", START, requested_cycle=8)
            self.assertTrue(r["run"])
            self.assertEqual(r["cycle"],8)
            self.assertEqual(r["reason"],"review_preview_only")
        for bad in (-1,24,100):
            self.assertFalse(evaluate("workflow_dispatch","true",START_TEXT,START,bad)["run"])

    def test_no_unexpected_event(self):
        self.assertFalse(evaluate("push","true",START_TEXT,START)["run"])

    def test_all_six_phases_read_only_and_no_live_data(self):
        for cycle in (0,4,8,12,16,20):
            with self.subTest(cycle=cycle):
                report=review(cycle)
                self.assertTrue(report["passed"],report["missingFiles"])
                self.assertFalse(report["productionDeployment"])
                self.assertFalse(report["customerDataCollection"])
                self.assertFalse(report["aiApiCalls"])
        for bad in (-1,24):
            with self.assertRaises(ValueError):
                phase_for_cycle(bad)

    def test_missing_phase_source_is_reported_not_fabricated(self):
        with tempfile.TemporaryDirectory() as temp:
            report=review(0,root=pathlib.Path(temp))
            self.assertFalse(report["passed"])
            self.assertTrue(report["missingFiles"])

    def test_workflow_permissions_cost_limit_and_no_deploy(self):
        wf=(ROOT/".github/workflows/wmm_24h_review_only.yml").read_text(encoding="utf8")
        self.assertIn("contents: read",wf)
        self.assertIn("persist-credentials: false",wf)
        self.assertIn("timeout-minutes: 4",wf)
        self.assertIn("cancel-in-progress: true",wf)
        self.assertIn("vars.WMM_24H_REVIEW_ENABLED == 'true'",wf)
        self.assertIn("WMM_24H_REVIEW_START_UTC",wf)
        self.assertIn("cron: '17 * * * *'",wf)
        self.assertNotIn("pull_request_target:",wf)
        self.assertNotIn("contents: write",wf)
        self.assertNotIn("git push",wf)
        self.assertNotIn("wrangler",wf)
        self.assertNotIn("ANTHROPIC_API_KEY",wf)
        self.assertNotIn("OPENAI_API_KEY",wf)
        self.assertNotIn("npm install",wf)

if __name__=="__main__":
    unittest.main()
