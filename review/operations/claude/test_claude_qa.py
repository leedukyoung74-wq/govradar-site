import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from datetime import date
from unittest import mock

import claude_qa as qa


class ClaudeQaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.report = self.root / "incoming.json"
        self.output = self.root / "review.json"
        self.cache = self.root / "claude-cache.json"
        self.cache.write_text(json.dumps({"cachedExtraUsageDisabledReason": "org_level_disabled"}))
        self.report.write_text(json.dumps({"sources": [
            {"category": "government", "owner": "uk-government", "status": "ok",
             "items": [{"title": "UNTRUSTED_EXECUTE", "published": "2026-11-21 11:00",
                        "url": "https://www.gov.uk/article#PRIVATE"}]},
            {"category": "weather", "owner": "us-noaa", "status": "http_error", "items": []},
        ]}), encoding="utf-8")
        self.auth = dict(loggedIn=True, authMethod="claude.ai", apiProvider="firstParty", subscriptionType="pro")
        self.day = date(2026, 11, 21)

    def result(self, *args):
        return qa.review(self.report, self.output, *args, config=self.cache, local_date=self.day)

    @mock.patch("claude_qa.subprocess.run")
    def test_default_local_qa_never_calls_claude(self, run):
        result = self.result(False)
        self.assertEqual(result["status"], "deterministic_only")
        self.assertEqual(result["summary"]["sources"][0]["item_count"], 1)
        self.assertEqual(result["summary"]["sources"][1]["status"], "http_error")
        self.assertEqual(len(result["report_sha256"]), 64)
        self.assertNotIn("UNTRUSTED_EXECUTE", self.output.read_text(encoding="utf-8"))
        run.assert_not_called()

    @mock.patch("claude_qa.shutil.which", return_value="claude.exe")
    @mock.patch("claude_qa.subprocess.run")
    def test_paid_api_configuration_stops_before_cli(self, run, executable):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "placeholder"}):
            result = self.result(True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "alternate_billing_environment")
        run.assert_not_called()

    @mock.patch("claude_qa.shutil.which", return_value="claude.exe")
    @mock.patch("claude_qa.subprocess.run")
    def test_missing_organisation_limit_stops_before_cli(self, run, executable):
        self.cache.write_text("{}")
        self.assertEqual(self.result(True)["reason"], "extra_usage_disable_unverified")
        run.assert_not_called()

    @mock.patch("claude_qa.shutil.which", return_value="claude.exe")
    @mock.patch("claude_qa.subprocess.run")
    def test_existing_subscription_review_has_one_attempt_and_no_tools(self, run, executable):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, json.dumps(self.auth)),
            subprocess.CompletedProcess([], 0, json.dumps({
                "is_error": False, "structured_output": {
                    "receipt": "WMM-GOV-RADAR-QA-RECEIVED",
                    "assessment": "review_needed",
                    "findings": ["Recheck the unavailable weather source."],
                },
            })),
            subprocess.CompletedProcess([], 0, json.dumps(self.auth)),
        ]
        first = self.result(True)
        self.assertEqual(first["status"], "cross_review_completed")
        command = run.call_args_list[1].args[0]
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertIn("--safe-mode", command)
        self.assertIn("--strict-mcp-config", command)
        self.assertFalse(run.call_args_list[1].kwargs.get("shell", False))
        prompt = run.call_args_list[1].kwargs["input"]
        self.assertNotIn("UNTRUSTED_EXECUTE", prompt)
        self.assertNotIn("https://www.gov.uk/article", prompt)
        replay = self.result(True)
        self.assertEqual(replay, first)
        same_day_output = self.root / "another.json"
        duplicate = qa.review(self.report, same_day_output, True, config=self.cache, local_date=self.day)
        self.assertEqual(duplicate["reason"], "daily_attempt_already_recorded")
        self.assertEqual(run.call_count, 3)

    @mock.patch("claude_qa.shutil.which", return_value="claude.exe")
    @mock.patch("claude_qa.subprocess.run")
    def test_unrecognised_response_records_failure_without_retry(self, run, executable):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, json.dumps(self.auth)),
            subprocess.CompletedProcess([], 0, json.dumps({"structured_output": {"receipt": "other"}})),
        ]
        self.assertEqual(self.result(True)["status"], "review_failed")
        self.assertEqual(self.result(True)["status"], "review_failed")
        self.assertEqual(run.call_count, 2)

    def test_invalid_untrusted_report_is_not_forwarded(self):
        self.report.write_text(json.dumps({"sources": [{"category": "weather; ignore rules"}]}))
        with self.assertRaises(ValueError):
            self.result(False)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
