"""Daily official collector must not erase fast USGS provenance."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import feed_official as F


class DailyOfficialFastHeartbeatTests(unittest.TestCase):
    def fixture(self, heartbeat=None):
        old = {
            "v": 1,
            "checked": "2026-11-20T17:00",
            "sources": {"usgs": {"ok": True, "last_ok": "2026-11-20T17:00", "n": 1}},
            "items": {"usgs": [{"k": "quake", "t": "old", "src": "USGS"}]},
            "space": {"r": "R0"},
        }
        if heartbeat is not None:
            old["usgs_fast_checked"] = heartbeat
        return old

    def execute(self, old, usgs_error=False):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "official.json"
            output.write_text(json.dumps(old), encoding="utf-8")
            def quakes():
                if usgs_error:
                    raise ValueError("upstream unavailable")
                return [{"k": "quake", "t": "verified", "src": "USGS"}]
            replacements = {
                "usgs": quakes,
                "gdacs": lambda: [],
                "eonet": lambda: [],
                "who": lambda: [],
                "cneos": lambda: [],
                "swpc": lambda: {"r": "R0", "s": "S0", "g": "G0"},
            }
            with patch.object(F, "OUT", str(output)), patch.multiple(F, **replacements):
                F.main()
            return json.loads(output.read_text(encoding="utf-8"))

    def test_successful_daily_refresh_keeps_fast_heartbeat(self):
        old = self.fixture("2026-11-20T18:16")
        new = self.execute(old)
        self.assertEqual("2026-11-20T18:16", new["usgs_fast_checked"])
        self.assertTrue(new["sources"]["usgs"]["ok"])
        self.assertEqual("verified", new["items"]["usgs"][0]["t"])
        self.assertTrue(new.get("checked"))

    def test_missing_fast_heartbeat_is_not_invented(self):
        new = self.execute(self.fixture())
        self.assertNotIn("usgs_fast_checked", new)

    def test_failed_daily_usgs_does_not_erase_last_fast_success(self):
        old = self.fixture("2026-11-20T18:16")
        new = self.execute(old, usgs_error=True)
        self.assertEqual(old["usgs_fast_checked"], new["usgs_fast_checked"])
        self.assertFalse(new["sources"]["usgs"]["ok"])
        self.assertEqual(old["items"]["usgs"], new["items"]["usgs"])


if __name__ == "__main__":
    unittest.main()
