"""Offline one-GET-only regression. Never use a live key or official endpoint."""
import io
import json
import pathlib
import sys
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import wmm_koneps_whitespace_one_get as M


class FakeResponse:
    status=200
    def __init__(self, data):
        self._data=io.BytesIO(data)
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def read(self,n):
        return self._data.read(n)


class FakeOpen:
    def __init__(self,error=False):
        self.urls=[]
        self.error=error
    def open(self,req,timeout=0):
        self.urls.append(req.full_url)
        assert req.get_method()=="GET" and timeout<=14
        if self.error:
            raise HTTPError(req.full_url,403,"Forbidden",None,
                            io.BytesIO(b"SERVICE_KEY_IS_NOT_REGISTERED_ERROR"))
        payload={"response":{"header":{"resultCode":"00"},"body":{
            "totalCount":1,"items":[{"bidNtceNo":"PRIVATE_NOTICE_NOT_FOR_PRINT"}]}}}
        return FakeResponse(json.dumps(payload).encode())


class TestKonepsWhitespaceOneGet(unittest.TestCase):
    def test_white_space_only_normalization(self):
        value, state=M.clean_key("AB" + chr(0x00a0) + "CD\nEF")
        self.assertEqual(value,"ABCDEF")
        self.assertEqual(state,"WHITESPACE_NORMALIZED")
        value,state=M.clean_key("ABCDEF")
        self.assertEqual(value,"ABCDEF")
        self.assertEqual(state,"NO_WHITESPACE_REPAIR_NEEDED")

    def test_unrelated_visible_unicode_is_not_rewritten(self):
        value,state=M.clean_key("AB"+chr(0xac00)+"CD")
        self.assertIsNone(value)
        self.assertEqual(state,"UNSUPPORTED_CHARACTERS")

    def test_wrapped_or_invalid_key_makes_zero_requests(self):
        for raw in (None,"", "serviceKey=ABC", "https://example.test/?serviceKey=ABC",
                    "ABC%ZZ", "ABC"+chr(0x200b)+"DEF"):
            op=FakeOpen()
            result=M.one_get(raw,op)
            self.assertEqual(result["requests_made"],0)
            self.assertEqual(op.urls,[])
            self.assertFalse(result["provider_authorization_verified"])
            self.assertFalse(result["live_ingestion_enabled"])

    def test_at_most_one_get_and_no_secret_in_output(self):
        key="PRIVATE_SYNTHETIC_"+chr(0x00a0)+"KEY"
        op=FakeOpen()
        result=M.one_get(key,op)
        self.assertEqual(result["requests_made"],1)
        self.assertEqual(len(op.urls),1)
        query=parse_qs(urlsplit(op.urls[0]).query)
        self.assertEqual(query["serviceKey"],["PRIVATE_SYNTHETIC_KEY"])
        self.assertEqual(result["outcome"],"TRANSPORT_SCHEMA_ONLY_NOT_LIVE")
        self.assertTrue(result["single_endpoint_schema_accepted"])
        self.assertFalse(result["provider_authorization_verified"])
        self.assertFalse(result["live_ingestion_enabled"])
        self.assertEqual(result["items_published"],0)
        self.assertNotIn("PRIVATE_SYNTHETIC_KEY",json.dumps(result))
        self.assertNotIn("PRIVATE_NOTICE_NOT_FOR_PRINT",json.dumps(result))

    def test_error_30_stays_blocked_after_one_call(self):
        op=FakeOpen(error=True)
        result=M.one_get("RAW"+chr(0x00a0)+"KEY",op)
        self.assertEqual(len(op.urls),1)
        self.assertEqual(result["response"]["provider_error"],
                         "SERVICE_KEY_IS_NOT_REGISTERED_ERROR")
        self.assertFalse(result["single_endpoint_schema_accepted"])
        self.assertEqual(result["outcome"],"BLOCKED_UPSTREAM")

    def test_no_key_main_fails_without_network_or_output_of_key(self):
        with mock.patch.dict(M.os.environ, {}, clear=True):
            with mock.patch("builtins.print") as output:
                self.assertEqual(M.main(),2)
        data=json.loads(output.call_args.args[0])
        self.assertEqual(data["requests_made"],0)
        self.assertFalse(data["provider_authorization_verified"])

    def test_owner_only_workflow_has_no_schedule_and_single_endpoint_command(self):
        s=(ROOT.parent/".github"/"workflows"/"wmm_koneps_whitespace_one_get_owner.yml").read_text()
        for needle in ("github.event.issue.number == 80",
                       "github.event.comment.author_association == 'OWNER'",
                       "/govradar-probe-koneps-whitespace-once",
                       "KONEPS_KEY: "+"${{ secrets.KONEPS_KEY }}"):
            self.assertIn(needle,s)
        self.assertNotIn("schedule:",s)
        self.assertNotIn("DAPA_KEY:",s)
        self.assertNotIn("wmm_koneps_bounded_probe.py",s)


if __name__=="__main__":
    unittest.main()
