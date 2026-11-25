"""Offline regression tests for seven-language GOV RADAR /live/ generator.
The test is deliberately network-free and does not deploy.
"""
import pathlib
import runpy
import subprocess
import shutil
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "live_page.py"
BOARD = runpy.run_path(str(SCRIPT), run_name="wmm_live_board_test")


class LivePageGeneratorP0Tests(unittest.TestCase):
    def test_languages_and_html_render(self):
        for lang in BOARD["LANGS"]:
            with self.subTest(lang=lang):
                html = BOARD["page"](lang, None)
                self.assertIn(f'<html lang="{lang}"', html)
                self.assertIn('data-hours="24"', html)
                self.assertIn('data-hours="168"', html)
                self.assertIn('data-hours="240"', html)
                self.assertIn('feed-controls button', html)
                self.assertIn("D.editorialUpdated", html)
                self.assertIn('F0[8]', html)  # SKIPPED collector, not inferred missing key
                self.assertIn('plannedExcluded++', html)
                self.assertNotIn('st(true,new Date().toISOString())', html)
                self.assertNotIn('Date.parse(g.date)||Date.now()', html)
                self.assertIn('dir="rtl"' if lang == "ar" else 'dir="ltr"', html)

    def test_provider_rules_and_data_honesty(self):
        js = BOARD["JS"]
        for expected in (
            'if(!r.ok)throw Error("USGS HTTP "',
            'if(!r.ok)throw Error("NASA HTTP "',
            '["prescribed fire","prescribed burn","controlled burn","pile burn","rx burn"]',
            'v.state==="SKIPPED"',
            'v.state==="PARTIAL"',
            'F0[7]',
        ):
            self.assertIn(expected, js)
        self.assertIn('H.disasters_checked', js)
        self.assertIn('H.editorial_updated', js)

    def test_js_parses_without_network(self):
        if not shutil.which("node"):
            self.skipTest("node runtime unavailable")
        p = subprocess.run(
            ["node", "--check"], input=BOARD["JS"], text=True,
            capture_output=True, timeout=15, check=False
        )
        self.assertEqual(p.returncode, 0, p.stderr)


if __name__ == "__main__":
    unittest.main()
