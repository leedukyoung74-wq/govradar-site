"""Offline regression tests for source/export versus generated output comparison."""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from check_build_consistency import inspect_build

class OutputConsistencyTests(unittest.TestCase):
    def fixture(self, root):
        exports=root/"export"
        output=root/"public"
        exports.mkdir()
        (output/"data"/"c").mkdir(parents=True)
        (exports/"KR.json").write_text(json.dumps({"id":"KR","data":{"agenda":["test"],"tenders":[{"title":"test","deadline":"2026-11-30"}]}}))
        (output/"data"/"countries.json").write_text(json.dumps([{"iso":"KR","slug":"south-korea","done":True}]))
        (output/"data"/"opps.json").write_text(json.dumps({"items":[{"iso":"KR","kind":"tenders"}]}))
        (output/"data"/"c"/"KR.json").write_text(json.dumps({"iso":"KR"}))
        for lang in ("ko","en","es","fr","ar","vi","id"):
            (output/lang/"south-korea").mkdir(parents=True)
            (output/lang/"south-korea"/"index.html").write_text("<h1>synthetic</h1>")
        return exports,output

    def test_matching_inputs_and_outputs_pass(self):
        with tempfile.TemporaryDirectory() as d:
            exports,out=self.fixture(pathlib.Path(d))
            r=inspect_build(exports,out)
            self.assertTrue(r["passed"],r["errors"])
            self.assertEqual(r["expectedOpportunityItems"],1)

    def test_expired_snapshot_wrong_done_flag_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            exports,out=self.fixture(pathlib.Path(d))
            (out/"data"/"countries.json").write_text(json.dumps([{"iso":"KR","slug":"south-korea","done":False}]))
            r=inspect_build(exports,out)
            self.assertFalse(r["passed"])
            self.assertIn("STALE_COUNTRY_DONE_FLAG:KR",r["errors"])

    def test_missing_language_page_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            exports,out=self.fixture(pathlib.Path(d))
            (out/"ar"/"south-korea"/"index.html").unlink()
            r=inspect_build(exports,out)
            self.assertIn("MISSING_LOCALIZED_COUNTRY_PAGE:ar:KR",r["errors"])

    def test_stale_opportunity_count_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            exports,out=self.fixture(pathlib.Path(d))
            (out/"data"/"opps.json").write_text(json.dumps({"items":[]}))
            r=inspect_build(exports,out)
            self.assertIn("PUBLISHED_OPPORTUNITY_COUNT_MISMATCH",r["errors"])

    def test_empty_build_and_empty_export_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            exports=pathlib.Path(d)/"not-exported"
            out=pathlib.Path(d)/"not-built"
            self.assertFalse(inspect_build(exports,out)["passed"])
            exports.mkdir()
            (out/"data").mkdir(parents=True)
            (out/"data"/"countries.json").write_text("[]")
            (out/"data"/"opps.json").write_text('{"items":[]}')
            self.assertIn("INSUFFICIENT_RESEARCHED_EXPORTS",inspect_build(exports,out)["errors"])

if __name__=="__main__":
    unittest.main()
