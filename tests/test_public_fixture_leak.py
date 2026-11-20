"""Synthetic test fixture must never reach publicly generated assets."""
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from check_public_fixture_leak import check_release_assets

class PublicFixtureLeakTests(unittest.TestCase):
    def test_missing_assets_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            result=check_release_assets(pathlib.Path(d)/"not-built")
            self.assertFalse(result["passed"])

    def test_empty_build_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            result=check_release_assets(d)
            self.assertFalse(result["passed"])

    def test_ordinary_html_is_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            pathlib.Path(d,"ko").mkdir()
            pathlib.Path(d,"ko","index.html").write_text("<h1>GOV RADAR</h1>")
            result=check_release_assets(d)
            self.assertTrue(result["passed"])

    def test_synthetic_data_blocks_release(self):
        with tempfile.TemporaryDirectory() as d:
            pathlib.Path(d,"ko","mdb").mkdir(parents=True)
            pathlib.Path(d,"ko","mdb","index.html").write_text("<li>WMM_QA_SYNTHETIC_FUTURE_TENDER</li>")
            result=check_release_assets(d)
            self.assertFalse(result["passed"])
            self.assertEqual(result["issues"][0]["code"],"SYNTHETIC_FIXTURE_IN_PUBLIC_OUTPUT")

    def test_rejects_fixture_in_json_and_js(self):
        with tempfile.TemporaryDirectory() as d:
            pathlib.Path(d,"data.json").write_text('{"url":"https://example.org/wmm-qa-past"}')
            pathlib.Path(d,"a.js").write_text('const src="wmm-qa-future";')
            result=check_release_assets(d)
            self.assertFalse(result["passed"])
            self.assertEqual(len(result["issues"]),2)

if __name__=="__main__":
    unittest.main()
