"""Six-agency/USGS publish-race resolution: use only synthetic samples."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from merge_official_sources import merge


def official(checked, fast_checked, usgs_ok, gdacs_ok, gdacs_status=True):
    return {
        "v": 1, "checked": checked, "usgs_fast_checked": fast_checked,
        "sources": {
            "usgs": {"ok": True, "last_ok": usgs_ok, "n": 1},
            "gdacs": {"ok": gdacs_status, "last_ok": gdacs_ok, "n": 1},
            "swpc": {"ok": True, "last_ok": checked, "n": 1},
        },
        "items": {
            "usgs": [{"k": "quake", "src": "USGS", "date": usgs_ok}],
            "gdacs": [{"k": "flood", "src": "GDACS", "date": gdacs_ok}],
        },
        "space": {"g": checked},
    }


class SourceAwareHazardMergeTests(unittest.TestCase):
    def setUp(self):
        self.published = official(
            "2026-11-19T06:10", "2026-11-20T06:15",
            "2026-11-20T06:15", "2026-11-19T06:10",
        )
        self.collected = official(
            "2026-11-20T06:10", "2026-11-19T06:15",
            "2026-11-20T06:10", "2026-11-20T06:10",
        )

    def test_keep_newer_fast_usgs_and_renew_all_other_agencies(self):
        result = merge(self.published, self.collected)
        self.assertEqual(self.published["items"]["usgs"], result["items"]["usgs"])
        self.assertEqual(self.collected["items"]["gdacs"], result["items"]["gdacs"])
        self.assertEqual("2026-11-20T06:15", result["usgs_fast_checked"])
        self.assertEqual("2026-11-20T06:10", result["checked"])
        self.assertEqual(self.collected["space"], result["space"])

    def test_daily_failed_agency_is_not_marked_healthy(self):
        self.collected["sources"]["gdacs"]["ok"] = False
        result = merge(self.published, self.collected)
        self.assertFalse(result["sources"]["gdacs"]["ok"])
        self.assertEqual(self.collected["items"]["gdacs"], result["items"]["gdacs"])

    def test_never_revert_a_newer_remote_daily_snapshot(self):
        self.published["checked"] = "2026-11-21T06:10"
        result = merge(self.published, self.collected)
        self.assertEqual(self.published["items"]["gdacs"], result["items"]["gdacs"])
        self.assertEqual("2026-11-21T06:10", result["checked"])

    def test_new_daily_usgs_wins_when_no_later_fast_update(self):
        self.published["usgs_fast_checked"] = "2026-11-19T06:15"
        self.published["sources"]["usgs"]["last_ok"] = "2026-11-19T06:15"
        result = merge(self.published, self.collected)
        self.assertEqual(self.collected["items"]["usgs"], result["items"]["usgs"])

    def test_invalid_feed_refuses_to_merge(self):
        with self.assertRaises(ValueError):
            merge({"sources": {}, "items": {}}, self.collected)
        with self.assertRaises(ValueError):
            merge(self.published, {"sources": {}, "items": {}})

    def test_input_objects_are_not_mutated(self):
        import copy
        remote_copy = copy.deepcopy(self.published)
        daily_copy = copy.deepcopy(self.collected)
        merge(self.published, self.collected)
        self.assertEqual(remote_copy, self.published)
        self.assertEqual(daily_copy, self.collected)


if __name__ == "__main__":
    unittest.main()
