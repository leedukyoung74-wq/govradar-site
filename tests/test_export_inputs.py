"""Offline checks for fail-closed exporter freshness; no publication or network."""
import datetime as dt
import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from check_export_inputs import audit_inputs

TODAY=dt.date(2026,11,20)

def write(root,name,iso,updated,**extra):
    doc={"id":iso,"data":{"updated":updated,**extra}}
    (root/name).write_text(json.dumps(doc),encoding="utf8")

class ExportFreshnessGate(unittest.TestCase):
    def test_empty_export_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            r=audit_inputs(temp,min_countries=1,today=TODAY)
            self.assertFalse(r["passed"])
            self.assertIn("INSUFFICIENT_COUNTRY_EXPORTS",r["errors"])

    def test_recent_valid_export_passes_explicit_threshold(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            write(root,"KR.json","KR","2026-11-19")
            write(root,"US.json","US","2026-11-18")
            r=audit_inputs(root,min_countries=2,max_age_days=3,today=TODAY)
            self.assertTrue(r["passed"])
            self.assertEqual(r["countries"],2)

    def test_old_and_missing_timestamps_block_release(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            write(root,"KR.json","KR","2026-10-01")
            write(root,"US.json","US","")
            r=audit_inputs(root,min_countries=2,max_age_days=7,today=TODAY)
            self.assertFalse(r["passed"])
            self.assertEqual(len(r["stale"]),1)
            self.assertEqual(len(r["missingDate"]),1)

    def test_invalid_future_date_and_corruption_block_release(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            write(root,"KR.json","KR","2026-11-21")
            (root/"US.json").write_text("{bad json",encoding="utf8")
            r=audit_inputs(root,min_countries=1,today=TODAY)
            self.assertFalse(r["passed"])
            self.assertEqual(r["futureDated"],["KR.json"])
            self.assertEqual(len(r["malformed"]),1)

    def test_duplicate_country_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            write(root,"KR.json","KR","2026-11-20")
            write(root,"K1.json","KR","2026-11-20")
            r=audit_inputs(root,min_countries=1,today=TODAY)
            self.assertFalse(r["passed"])
            self.assertEqual(len(r["duplicate"]),1)

if __name__=="__main__":
    unittest.main()
