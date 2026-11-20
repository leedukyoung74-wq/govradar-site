import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from check_research_coverage import check_coverage

class CoverageAuditTests(unittest.TestCase):
    def setup_data(self,base):
        meta=base/"meta.json"
        meta.write_text(json.dumps([{"iso":"KR"},{"iso":"US"}]),encoding="utf8")
        exports=base/"export"
        exports.mkdir()
        return meta,exports

    def test_empty_input_not_complete(self):
        with tempfile.TemporaryDirectory() as d:
            meta,exports=self.setup_data(pathlib.Path(d))
            result=check_coverage(exports,meta,1)
            self.assertFalse(result["passed"])
            self.assertEqual(result["researchedCountries"],0)
            self.assertEqual(len(result["missingCountryCodes"]),2)

    def test_metadata_only_does_not_count_as_research(self):
        with tempfile.TemporaryDirectory() as d:
            meta,exports=self.setup_data(pathlib.Path(d))
            (exports/"KR.json").write_text(json.dumps({"id":"KR","data":{"events":[{"title":"test"}]}}))
            result=check_coverage(exports,meta,1)
            self.assertEqual(result["presentCountries"],1)
            self.assertEqual(result["researchedCountries"],0)
            self.assertFalse(result["passed"])

    def test_country_with_agenda_counts_as_locally_researched(self):
        with tempfile.TemporaryDirectory() as d:
            meta,exports=self.setup_data(pathlib.Path(d))
            (exports/"KR.json").write_text(json.dumps({"id":"KR","data":{"agenda":"research summary"}}))
            result=check_coverage(exports,meta,1)
            self.assertTrue(result["passed"])
            self.assertEqual(result["researchedCountries"],1)

    def test_unknown_and_encrypted_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            meta,exports=self.setup_data(pathlib.Path(d))
            (exports/"ZZ.json").write_text(json.dumps({"id":"ZZ","data":{"agenda":"test"}}))
            (exports/"KR.json").write_text(json.dumps({"iv":"test","c":"encrypted"}))
            result=check_coverage(exports,meta,0)
            self.assertFalse(result["passed"])
            self.assertEqual(len(result["issues"]),2)

if __name__=="__main__":
    unittest.main()
