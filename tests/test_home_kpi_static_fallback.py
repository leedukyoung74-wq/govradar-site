"""Ensure home KPI build defaults never misrepresent stale numbers as live."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "tools" / "home_clean.py").read_text(encoding="utf8")
IDS = ("kp-t", "kp-u", "td-new", "td-urg", "td-open", "td-al")


class HomeKPIStaticFallback(unittest.TestCase):
    def test_generator_clears_six_preloaded_metrics(self):
        self.assertIn('for element_id in ("kp-t", "kp-u", "td-new", "td-urg", "td-open", "td-al")', SCRIPT)
        html = "".join(f'<b id="{i}">1022</b>' for i in IDS)
        for element_id in IDS:
            html = re.sub(r'(<b id="' + re.escape(element_id) + r'">)[^<]*(</b>)',
                          lambda m: m.group(1) + "—" + m.group(2), html, count=1)
        self.assertEqual(html.count(">—</b>"), len(IDS))

    def test_existing_fetch_refresh_is_preserved(self):
        self.assertNotIn('replace("data/feeds/today.json"', SCRIPT)
        self.assertIn('s = s[:a] +', SCRIPT)


if __name__ == "__main__":
    unittest.main()
