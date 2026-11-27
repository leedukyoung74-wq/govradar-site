"""No network: verify G2B source authorization probe is tightly bounded and redacted."""
import datetime as dt
import io
import json
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wmm_koneps_bounded_probe as P

DATE = dt.date(2026, 11, 27)


class FakeReply:
    status = 200
    def __init__(self, content):
        self.content = io.BytesIO(content.encode())
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.content.read(n)


class FakeOpener:
    def __init__(self, reply, error=False):
        self.urls = []
        self.reply = reply
        self.error = error
    def open(self, request, timeout=0):
        self.urls.append(request.full_url)
        assert request.get_method() == "GET" and timeout <= 14
        if self.error:
            raise HTTPError(request.full_url, 403, "forbidden", None, None)
        return FakeReply(self.reply)


class KonepsOfficialProbeTests(unittest.TestCase):
    def test_exact_official_endpoints_and_three_day_window(self):
        for name in P.OPERATIONS:
            url = P.make_url(name, "SYNTH-KEY", DATE)
            p = urlsplit(url)
            qs = parse_qs(p.query)
            self.assertEqual(p.scheme, "https")
            self.assertEqual(p.hostname, "apis.data.go.kr")
            self.assertTrue(p.path.startswith("/1230000/ad/BidPublicInfoService02/"))
            self.assertTrue(p.path.endswith("02"))
            self.assertEqual(qs["numOfRows"], ["5"])
            self.assertEqual(qs["pageNo"], ["1"])
            self.assertEqual(qs["inqryBgnDt"], ["202611250000"])
            self.assertEqual(qs["inqryEndDt"], ["202611272359"])
        with self.assertRaises(ValueError):
            P.make_url("unknown", "secret", DATE)

    def test_json_success_extracts_only_schema_and_counts(self):
        payload={"response":{"header":{"resultCode":"00"},"body":{
            "totalCount":14,"items":[{"bidNtceNo":"SECRET-CUSTOMER","bidClseDt":"20261201",
                                       "ntceInsttNm":"Private content"}]}}}
        result=P.parse_reply(json.dumps(payload))
        self.assertEqual(result["state"], "OK_ROWS")
        self.assertEqual(result["total"],14)
        self.assertEqual(result["items"],1)
        self.assertEqual(result["fields"],["bidClseDt","bidNtceNo","ntceInsttNm"])
        self.assertNotIn("SECRET-CUSTOMER",json.dumps(result))
        self.assertNotIn("Private content",json.dumps(result))

    def test_xml_denied_and_malformed_response_fail_closed(self):
        d=P.parse_reply("<response><header><resultCode>20</resultCode>"
                        "</header><body></body></response>")
        self.assertEqual(d["state"],"UPSTREAM_ERROR_OR_ACCESS_DENIED")
        self.assertEqual(P.parse_reply("not json or xml")["state"],"UNRECOGNIZED_RESPONSE")
        self.assertEqual(P.parse_reply('{"response":{"header":{},"body":{}}}')["state"],
                         "UPSTREAM_ERROR_OR_ACCESS_DENIED")

    def test_no_key_never_reaches_network(self):
        self.assertEqual(P.probe("",None)["operations_attempted"],0)

    def test_four_gets_maximum_no_publish_or_key_logs(self):
        payload={"response":{"header":{"resultCode":"00"},"body":{
            "totalCount":1,"items":[{"bidNtceNo":"SENSITIVE"}]}}}
        opener=FakeOpener(json.dumps(payload))
        result=P.probe("SECRET-FAKE-KEY",opener,DATE)
        self.assertEqual(len(opener.urls),4)
        self.assertEqual(result["operations_attempted"],4)
        self.assertEqual(result["operations_succeeded"],4)
        self.assertFalse(result["ready_for_live_ingestion"])
        self.assertEqual(result["items_published"],0)
        self.assertNotIn("SECRET-FAKE-KEY",json.dumps(result))
        self.assertNotIn("SENSITIVE",json.dumps(result))

    def test_access_denied_never_ready_even_if_key_configured(self):
        opener=FakeOpener("ignored",error=True)
        result=P.probe("SECRET-FAKE-KEY",opener,DATE)
        self.assertEqual(result["operations_succeeded"],0)
        self.assertFalse(result["schema_accepted_for_review"])
        self.assertEqual(len(opener.urls),4)
        self.assertTrue(all(x["http_status"]==403 for x in result["results"].values()))
        self.assertNotIn("SECRET-FAKE-KEY",json.dumps(result))

    def test_empty_response_is_not_proof_of_customer_ready(self):
        payload={"response":{"header":{"resultCode":"00"},"body":{
            "totalCount":0,"items":[]}}}
        result=P.probe("SYNTH-KEY",FakeOpener(json.dumps(payload)),DATE)
        self.assertEqual(result["operations_succeeded"],4)
        self.assertFalse(result["ready_for_live_ingestion"])
        self.assertTrue(all(x["state"]=="OK_EMPTY" for x in result["results"].values()))


if __name__ == "__main__":
    unittest.main()
