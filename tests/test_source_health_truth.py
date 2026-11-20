"""Truthful source-health evidence is separate from generated-feed timestamps."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import feed_tenders as FT


class SourceHealthTruthTests(unittest.TestCase):
    def test_skipped_remains_skipped(self):
        self.assertEqual("SKIPPED", FT.classify_state({"skipped": True}))

    def test_timeout_before_any_request_is_not_partial_success(self):
        self.assertEqual("ERROR", FT.classify_state({"requests": 0, "failed": 1, "raw": 0}))
        self.assertFalse(FT.source_answered({"requests": 0, "failed": 1, "raw": 0}))

    def test_no_request_no_response_never_looks_like_empty_success(self):
        self.assertEqual("ERROR", FT.classify_state({"requests": 0, "failed": 0, "raw": 0}))

    def test_real_partial_rows_stay_partial_even_with_budget_penalty(self):
        state = {"requests": 1, "failed": 1, "raw": 2}
        self.assertEqual("PARTIAL", FT.classify_state(state))
        self.assertTrue(FT.source_answered(state))

    def test_genuine_empty_success_is_still_successful_poll(self):
        state = {"requests": 2, "failed": 0, "raw": 0}
        self.assertEqual("EMPTY_SUCCESS", FT.classify_state(state))
        self.assertTrue(FT.source_answered(state))

    def test_all_requests_failed_does_not_advance_last_success(self):
        state = {"requests": 3, "failed": 3, "raw": 0}
        self.assertEqual("ERROR", FT.classify_state(state))
        self.assertFalse(FT.source_answered(state))

    def test_partial_request_without_rows_is_not_unconditionally_healthy(self):
        self.assertTrue(FT.source_answered({"requests": 3, "failed": 1, "raw": 0}))


if __name__ == "__main__":
    unittest.main()
