"""Network-free checks for optional DAPA and SAM.gov official-source collectors."""
import datetime
import json
import os
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import feed_more as FM


class OfficialKeyedSourcesTests(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def test_dapa_missing_key_reports_skipped_without_http(self):
        with mock.patch.dict(os.environ, {"DAPA_KEY": ""}, clear=False), mock.patch.object(FM, "_get") as get:
            self.assertEqual(FM.dapa(), [])
            get.assert_not_called()
        self.assertTrue(FM.stat("DAPA (Korea)")["skipped"])
        self.assertIn("not_configured:DAPA_KEY", FM.stat("DAPA (Korea)")["notes"])

    def test_sam_missing_key_reports_skipped_without_http(self):
        with mock.patch.dict(os.environ, {"SAM_KEY": ""}, clear=False), mock.patch.object(FM, "_get") as get:
            self.assertEqual(FM.sam(), [])
            get.assert_not_called()
        self.assertTrue(FM.stat("SAM.gov (US)")["skipped"])
        self.assertIn("not_configured:SAM_KEY", FM.stat("SAM.gov (US)")["notes"])

    def test_sam_accepts_official_documented_deadline_alias(self):
        deadline = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
        fixture = {"opportunitiesData": [{
            "noticeId": "test-future-001",
            "title": "Future official API test",
            "reponseDeadLine": deadline,
            "fullParentPathName": "US Government",
            "uiLink": "https://sam.gov/opportunities",
            "type": "Solicitation"
        }]}
        with mock.patch.dict(os.environ, {"SAM_KEY": "fixture-only-no-network"}, clear=False), \
             mock.patch.object(FM, "_get", return_value=json.dumps(fixture)) as get:
            rows = FM.sam()
        get.assert_called_once()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["deadline"], deadline)
        self.assertEqual(rows[0]["source"], "SAM.gov (US)")


if __name__ == "__main__":
    unittest.main()
