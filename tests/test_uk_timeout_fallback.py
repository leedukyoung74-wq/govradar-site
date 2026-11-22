"""UK FTS timeouts fall back conservatively without misreporting completion."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import feed_more as FM
import feed_tenders as FT

SOURCE="UK Find a Tender"


class UKTimeoutFallbackTests(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def example(self):
        return {"sid":"ocds-fake","iso":"GB","est":"2500000","source":SOURCE,
                "url":"https://www.find-tender.service.gov.uk/Notice/valid"}

    def test_first_window_timeout_retries_short_and_marks_partial(self):
        calls=[]
        def fake_ocds(source,url,mk,**kwargs):
            calls.append((url,kwargs))
            st=FM.stat(source)
            st["requests"]+=1
            if len(calls)==1:
                st["failed"]+=1
                st["notes"].append("TimeoutError: The read operation timed out")
                return []
            st["raw"]+=1
            return [self.example()]
        with patch.object(FM,"_ocds",side_effect=fake_ocds):
            result=FM.uk()
        self.assertEqual(1,len(result))
        self.assertEqual(2,len(calls))
        first=parse_qs(urlsplit(calls[0][0]).query)
        second=parse_qs(urlsplit(calls[1][0]).query)
        self.assertEqual(["100"],first["limit"])
        self.assertEqual(["10"],second["limit"])
        self.assertIn("updatedTo",first)
        self.assertEqual(first["updatedTo"],second["updatedTo"])
        self.assertEqual(6,calls[1][1]["max_pages"])
        self.assertEqual(20,calls[1][1]["timeout"])
        self.assertEqual("PARTIAL",FT.classify_state(FM.stat(SOURCE)))
        self.assertIn("partial_48h",FM.stat(SOURCE)["notes"][-1])

    def test_rate_limited_source_never_tries_more_requests(self):
        with patch.object(FM,"_ocds",side_effect=lambda source,url,mk,**kwargs: self._fail("HTTPError: HTTP Error 429")) as call:
            self.assertEqual([],FM.uk())
        self.assertEqual(1,call.call_count)

    def _fail(self,note):
        st=FM.stat(SOURCE)
        st.update({"requests":1,"failed":1,"raw":0})
        st["notes"].append(note)
        return []

    def test_good_primary_source_skips_fallback(self):
        with patch.object(FM,"_ocds",return_value=[self.example()]) as call:
            result=FM.uk()
        self.assertEqual(1,len(result))
        self.assertEqual(1,call.call_count)

    def test_no_reply_is_not_labeled_success(self):
        with patch.object(FM,"_ocds",side_effect=lambda source,url,mk:self._fail("TimeoutError")):
            with patch.object(FM,"_ocds",side_effect=lambda *args,**kwargs:self._fail("TimeoutError")) as call:
                self.assertEqual([],FM.uk())
                self.assertEqual(2,call.call_count)
        self.assertEqual("ERROR",FT.classify_state(FM.stat(SOURCE)))

    def test_configured_page_cap_is_reported_partial(self):
        seen=[]
        def get(source,url,**kwargs):
            seen.append(url)
            return json.dumps({"releases":[{"id":str(len(seen))}],
                               "links":{"next":"?cursor="+str(len(seen))}})
        with patch.object(FM,"_get",side_effect=get):
            result=FM._ocds(SOURCE,"https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages",
                            lambda x:x,max_pages=2)
        self.assertEqual(2,len(result))
        self.assertEqual(2,len(seen))
        self.assertGreaterEqual(FM.stat(SOURCE)["failed"],1)
        self.assertTrue(any("page_cap" in n for n in FM.stat(SOURCE)["notes"]))


if __name__=="__main__":
    unittest.main()
