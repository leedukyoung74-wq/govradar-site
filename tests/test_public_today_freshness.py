"""Public today counters fail closed when fetched data is stale or future-dated."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class PublicTodayTimestampGateTests(unittest.TestCase):
    def test_home_dynamic_zero_is_not_ignored(self):
        source=(ROOT/"build.py").read_text(encoding="utf-8")
        self.assertIn("Number.isInteger(d.n.open)&&d.n.open>=0",source)
        self.assertNotIn("if(a&&d.n.open)a.textContent",source)

    def test_home_requires_current_source_before_overwriting_static_fallback(self):
        source=(ROOT/"build.py").read_text(encoding="utf-8")
        self.assertIn("age>108000000)return",source)
        self.assertIn("age< -300000",source)
        self.assertIn("Date.parse(String(d.updated",source)

    def test_today_band_never_marks_old_feed_as_today(self):
        source=(ROOT/"pages3.py").read_text(encoding="utf-8")
        self.assertIn("age>108000000)throw 0",source)
        self.assertIn("age< -300000",source)


if __name__=="__main__":
    unittest.main()
