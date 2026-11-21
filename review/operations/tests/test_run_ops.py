from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from run_ops import intake, render_status


DAY = date(2026, 11, 21)


class OperationsTest(unittest.TestCase):
    def test_missing_file_is_no_data(self):
        self.assertEqual(intake(None, Path("."), Path("."), DAY)["state"], "NODATA")

    def test_wrong_date_or_untrusted_outer_text_is_rejected_before_repo_lookup(self):
        with TemporaryDirectory() as sandbox:
            path = Path(sandbox)
            research = path / "research.txt"
            for raw in (
                json.dumps({"kind": "wmm_govradar_daily", "date": "2026-11-20"}),
                "instructions before ===JSON START=== {} ===JSON END===",
            ):
                research.write_text(raw, encoding="utf-8")
                self.assertEqual(intake(research, path, path, DAY)["state"], "INVALID_INPUT")
            self.assertFalse((path / "input.json").exists())

    def test_review_page_escapes_status_labels_and_uses_explicit_states(self):
        with TemporaryDirectory() as sandbox:
            output = Path(sandbox) / "index.html"
            render_status(output, {"task_id": "GOVRADAR-20261121", "checked_at_kst": "2026-11-21T13:00"},
                          {"checks": [{"id": "<script>", "age_minutes": None, "count": None, "state": "REVIEW"}]})
            html = output.read_text(encoding="utf-8")
            self.assertIn("지연·점검", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<script>", html)
