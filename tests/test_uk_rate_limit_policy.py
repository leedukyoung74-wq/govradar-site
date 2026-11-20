"""UK official FTS source: a 429 must end the run without another request."""
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import feed_more as FM
import feed_tenders as FT

SRC="UK Find a Tender"
URL="https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?limit=100"

class UKRateSafety(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def test_429_never_retries_in_same_run_even_with_retry_after(self):
        count=[0]
        def deny():
            count[0]+=1
            raise HTTPError(URL,429,"Too Many Requests",{"Retry-After":"120"},None)
        with patch("time.sleep") as sleep:
            with self.assertRaises(HTTPError):
                FM._retry(SRC,deny,tries=4)
        self.assertEqual(count[0],1)
        sleep.assert_not_called()
        self.assertEqual(FM.stat(SRC)["requests"],1)
        self.assertEqual(FM.stat(SRC)["failed"],1)
        self.assertIn("retry_after_seconds=120",FM.stat(SRC)["notes"][-1])
        self.assertEqual("ERROR",FT.classify_state(FM.stat(SRC)))

    def test_uk_main_scan_is_paced_and_bounded(self):
        with patch.object(FM,"_ocds",return_value=[]) as fn:
            FM.uk()
        self.assertEqual(fn.call_count,1)
        self.assertEqual(fn.call_args.kwargs["max_pages"],12)
        self.assertEqual(fn.call_args.kwargs["tries"],1)
        self.assertGreaterEqual(fn.call_args.kwargs["min_interval"],1)
        self.assertLessEqual(fn.call_args.kwargs["time_budget"],120)

    def test_pacing_sleep_and_page_cap_remain_partial(self):
        urls=[]
        def data(_source,url,**kw):
            urls.append(url)
            return json.dumps({"releases":[{"id":str(len(urls))}],
                               "links":{"next":"?page="+str(len(urls)+1)}})
        with patch.object(FM,"_get",side_effect=data),patch("time.sleep") as sleep:
            rows=FM._ocds(SRC,URL+"&page=1",lambda r:r,max_pages=2,min_interval=1,
                          time_budget=100)
        self.assertEqual(len(rows),2)
        self.assertEqual(len(urls),2)
        sleep.assert_called_once()
        self.assertEqual("PARTIAL",FT.classify_state(FM.stat(SRC)))
        self.assertTrue(any("page_cap" in x for x in FM.stat(SRC)["notes"]))

    def test_429_after_first_page_never_confirms_complete(self):
        calls=[0]
        def source(_name,_url,**kw):
            calls[0]+=1
            if calls[0]>1: raise HTTPError(URL,429,"Too Many Requests",
                                          {"Retry-After":"120"},None)
            return json.dumps({"releases":[{"id":"one"}],"links":{"next":"?page=2"}})
        with patch.object(FM,"_get",side_effect=source):
            rows=FM._ocds(SRC,URL,lambda x:x,max_pages=5)
        self.assertEqual(calls[0],2)
        self.assertEqual(len(rows),1)
        self.assertEqual("PARTIAL",FT.classify_state(FM.stat(SRC)))
        self.assertTrue(any("ocds_request_exception" in v for v in FM.stat(SRC)["notes"]))

if __name__=="__main__":
    unittest.main()
