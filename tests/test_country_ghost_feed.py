"""Expired country rows must never leave misleading cached country counters."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import feed_cty as FC


class CountryGhostFeedTests(unittest.TestCase):
    def test_previous_country_with_no_more_records_gets_zeroed(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds = Path(tmp)
            cty = feeds / "cty"
            cty.mkdir()
            (cty / "CA.json").write_text(json.dumps({
                "updated": "2026-11-18T00:00Z", "t": {"n": 7},
                "p": {"n": 2}, "a": {"n": 3}, "v": {"n": 4}
            }), encoding="utf-8")
            (cty / "_summary.json").write_text('{"t":{"n":99}}', encoding="utf-8")
            (feeds / "tenders.json").write_text(json.dumps({
                "items": [{"iso": "KR", "title": "New active notice",
                           "deadline": "2090-02-20",
                           "deadline_at": "2090-02-20T12:00:00Z",
                           "buyer": "Gov", "url": "https://example.org/kr"}]
            }), encoding="utf-8")
            with patch.object(FC, "FEEDS", str(feeds)):
                FC.main()
            ca = json.loads((cty / "CA.json").read_text(encoding="utf-8"))
            kr = json.loads((cty / "KR.json").read_text(encoding="utf-8"))
            summary = json.loads((cty / "_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(0, ca["t"]["n"])
            self.assertEqual(0, ca["p"]["n"])
            self.assertEqual(0, ca["a"]["n"])
            self.assertEqual(0, ca["v"]["n"])
            self.assertEqual(1, kr["t"]["n"])
            self.assertEqual({"n": 1, "c": 1}, summary["t"])
            self.assertNotEqual("2026-11-18T00:00Z", ca["updated"])

    def test_non_iso_files_are_not_treated_as_countries(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds = Path(tmp)
            cty = feeds / "cty"
            cty.mkdir()
            (cty / "_summary.json").write_text('{"t":{"n":200}}', encoding="utf-8")
            (cty / "INTERNAL.json").write_text('{"t":{"n":7}}', encoding="utf-8")
            (feeds / "tenders.json").write_text('{"items":[]}', encoding="utf-8")
            with patch.object(FC, "FEEDS", str(feeds)):
                FC.main()
            self.assertFalse((cty / "IN.json").exists())
            self.assertEqual('{"t":{"n":7}}',
                             (cty / "INTERNAL.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
