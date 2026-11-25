"""Official SAM.gov HTTP 429 must not be retried; avoid exhausting free quota."""
import pathlib
import sys
import unittest
import urllib.error
from unittest.mock import Mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
import feed_more as FM

class SamRateLimitTests(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def test_sam_rate_limit_one_attempt_without_backoff(self):
        def limited():
            raise urllib.error.HTTPError("https://sam.gov",429,"Too Many Requests",None,None)
        f=Mock(side_effect=limited)
        with self.assertRaises(urllib.error.HTTPError):
            FM._retry("SAM.gov (US)",f,tries=3)
        self.assertEqual(f.call_count,1)
        st=FM.stat("SAM.gov (US)")
        self.assertEqual(st["requests"],1)
        self.assertEqual(st["failed"],1)
        self.assertTrue(any("upstream_429_deferred" in n for n in st["notes"]))

    def test_sam_429_diagnostics_reveal_no_key(self):
        def limited():
            raise urllib.error.HTTPError("https://sam.gov",429,"Too Many Requests",None,None)
        with self.assertRaises(urllib.error.HTTPError):
            FM._retry("SAM.gov (US)",limited,tries=3)
        self.assertNotIn("api_key=",str(FM.stat("SAM.gov (US)")["notes"]))

    def test_source_code_excludes_stale_as_new_and_disables_push_dispatch(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        source=(root/"tools"/"feed_tenders.py").read_text(encoding="utf8")
        self.assertIn('not x.get("stale")',source)
        self.assertIn('x.get("verify") != "partial"',source)
        schedule=(root/".github"/"workflows"/"tenders.yml").read_text(encoding="utf8")
        self.assertNotIn("  push:\n",schedule)
        self.assertIn("  workflow_dispatch:",schedule)
if __name__=="__main__":
    unittest.main()
