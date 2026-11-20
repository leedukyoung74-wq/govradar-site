"""The listed special/autonomous regions must all have source-backed research."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import regions_20261114 as RR


class SpecialRegionsCoverageTests(unittest.TestCase):
    def test_all_regions_have_a_research_entry_under_the_right_parent(self):
        rows=json.loads((ROOT/"src"/"regions.json").read_text(encoding="utf-8"))
        countries={x["iso"] for x in json.loads((ROOT/"src"/"countries_meta.json").read_text(encoding="utf-8"))}
        ids={x["iso"] for x in rows}
        self.assertEqual(193,len(countries))
        self.assertEqual(23,len(ids))
        self.assertEqual(ids,set(RR.D))
        for row in rows:
            self.assertIn(row["parent"],countries)
            record=RR.D[row["iso"]]
            self.assertEqual(row["parent"],record["parent"])
            self.assertEqual(row["type"],record["type"])
            self.assertTrue(record["sources"],row["iso"])
            self.assertTrue(all(x["url"].startswith("https://") for x in record["sources"]),row["iso"])

    def test_builder_falls_back_only_when_barmm_export_absent(self):
        build=(ROOT/"build.py").read_text(encoding="utf-8")
        self.assertIn('if "PH-BARMM" not in DATA:',build)
        self.assertIn('DATA["PH-BARMM"] = _region_research["PH-BARMM"]',build)

    def test_barmm_budget_is_not_falsely_marked_as_confirmed_tender(self):
        item=RR.D["PH-BARMM"]
        self.assertEqual([],item["tenders"])
        self.assertEqual("PH",item["parent"])
        self.assertIn("입찰 공고 아님",item["projects"][0]["status"])
        self.assertGreaterEqual(len(item["sources"]),2)


if __name__=="__main__":
    unittest.main()
