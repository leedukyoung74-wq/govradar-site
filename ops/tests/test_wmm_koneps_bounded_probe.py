"""No network: verify G2B source authorization probe is tightly bounded and redacted."""
import datetime as dt
import io
import json
import sys
import unittest
from unittest import mock
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

    def test_workflow_passes_only_unescaped_koneps_secret(self):
        path = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "wmm_koneps_bounded_probe_owner.yml"
        workflow = path.read_text(encoding="utf-8")
        self.assertIn("KONEPS_KEY: " + "${{ secrets.KONEPS_KEY }}", workflow)
        self.assertNotIn("KONEPS_KEY: " + chr(92) + "${{ secrets.KONEPS_KEY }}", workflow)
        self.assertNotIn("DAPA_KEY:", workflow)

    def test_dapa_key_only_never_selects_a_koneps_credential(self):
        # The unrelated DAPA service key must not cause four denied G2B GETs.
        with mock.patch.dict(P.os.environ, {"DAPA_KEY": "DAPA-ONLY-SYNTHETIC"}, clear=True):
            with mock.patch.object(P, "probe", return_value={
                "classification": "NO_APPROVED_KEY",
                "operations_attempted": 0,
                "ready_for_live_ingestion": False,
                "items_published": 0,
            }) as probe_mock:
                with mock.patch("builtins.print"):
                    self.assertEqual(P.main(), 2)
        probe_mock.assert_called_once_with("")

    def test_403_official_denial_code_safe_without_raw_secret(self):
        raw = b"<error>SERVICE_ACCESS_DENIED_ERROR?serviceKey=SECRET-CANNOT-LOG</error>"
        error = HTTPError("https://apis.data.go.kr/?serviceKey=SECRET-CANNOT-LOG",
                          403, "Forbidden", None, io.BytesIO(raw))
        result = P.classify_http_error(error)
        self.assertEqual(result["state"], "HTTP_DENIED_OR_ERROR")
        self.assertEqual(result["http_status"], 403)
        self.assertEqual(result["provider_error"], "SERVICE_ACCESS_DENIED_ERROR")
        self.assertNotIn("SECRET-CANNOT-LOG", json.dumps(result))
        self.assertNotIn("serviceKey", json.dumps(result))

    def test_403_unknown_body_never_echoes_provider_text(self):
        error = HTTPError("https://apis.data.go.kr/?serviceKey=VERY-PRIVATE",
                          403, "Forbidden", None,
                          io.BytesIO(b"<html>unexpected body VERY-PRIVATE</html>"))
        result = P.classify_http_error(error)
        self.assertEqual(result["provider_error"], "UNSPECIFIED_HTTP_ERROR")
        self.assertNotIn("VERY-PRIVATE", json.dumps(result))

    def test_403_no_body_and_oversized_body_fail_closed(self):
        empty = HTTPError("https://apis.data.go.kr/secure", 403,
                          "Forbidden", None, None)
        large = HTTPError("https://apis.data.go.kr/secure", 403,
                          "Forbidden", None,
                          io.BytesIO(b"SERVICE_ACCESS_DENIED_ERROR" + b"x" * 32769))
        self.assertEqual(P.classify_http_error(empty)["provider_error"],
                         "UNSPECIFIED_HTTP_ERROR")
        self.assertEqual(P.classify_http_error(large)["provider_error"],
                         "UNSPECIFIED_HTTP_ERROR")

    def test_403_error_classification_in_four_call_probe(self):
        class DenialOpener:
            def open(self, req, timeout=0):
                raise HTTPError(req.full_url, 403, "Forbidden", None,
                                io.BytesIO(b"<result>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</result>"))
        result = P.probe("FAKE-TEST-KEY", DenialOpener(), DATE)
        self.assertEqual(result["operations_succeeded"], 0)
        self.assertEqual(result["operations_attempted"], 4)
        for value in result["results"].values():
            self.assertEqual(value["provider_error"],
                             "SERVICE_KEY_IS_NOT_REGISTERED_ERROR")
        self.assertNotIn("FAKE-TEST-KEY", json.dumps(result))

    def test_403_live_job_fails_not_green(self):
        denied = {"classification": "OWNER_APPROVED_READ_ONLY_KONEPS_PROBE",
                  "operations_attempted": 4, "operations_succeeded": 0,
                  "schema_accepted_for_review": False,
                  "ready_for_live_ingestion": False,
                  "results": {n: {"state": "HTTP_DENIED_OR_ERROR",
                                  "http_status": 403} for n in P.OPERATIONS},
                  "items_published": 0}
        with mock.patch.dict(P.os.environ, {"KONEPS_KEY": "FAKE-KEY"}, clear=True):
            with mock.patch.object(P, "probe", return_value=denied) as probe_mock:
                with mock.patch("builtins.print") as output:
                    self.assertEqual(P.main(), 2)
        probe_mock.assert_called_once_with("FAKE-KEY")
        printed = json.loads(output.call_args.args[0])
        self.assertEqual(printed["authorization_probe_gate"], "BLOCKED_UPSTREAM_RESPONSE")
        self.assertFalse(printed["ready_for_live_ingestion"])
        self.assertNotIn("FAKE-KEY", output.call_args.args[0])

    def test_all_four_api_envelopes_pass_transport_but_not_live(self):
        synthetic = {"classification": "OWNER_APPROVED_READ_ONLY_KONEPS_PROBE",
                     "operations_attempted": 4, "operations_succeeded": 4,
                     "schema_accepted_for_review": True,
                     "ready_for_live_ingestion": False, "items_published": 0}
        with mock.patch.dict(P.os.environ, {"KONEPS_KEY": "FAKE-KEY"}, clear=True):
            with mock.patch.object(P, "probe", return_value=synthetic):
                with mock.patch("builtins.print") as output:
                    self.assertEqual(P.main(), 0)
        printed = json.loads(output.call_args.args[0])
        self.assertEqual(printed["authorization_probe_gate"],
                         "SCHEMA_REVIEW_ONLY_NOT_LIVE")
        self.assertEqual(printed["items_published"], 0)
        self.assertFalse(printed["ready_for_live_ingestion"])

    def test_partial_four_categories_never_green(self):
        partial = {"classification": "OWNER_APPROVED_READ_ONLY_KONEPS_PROBE",
                   "operations_attempted": 4, "operations_succeeded": 3,
                   "schema_accepted_for_review": True,
                   "ready_for_live_ingestion": False, "items_published": 0}
        with mock.patch.dict(P.os.environ, {"KONEPS_KEY": "FAKE-KEY"}, clear=True):
            with mock.patch.object(P, "probe", return_value=partial):
                with mock.patch("builtins.print"):
                    self.assertEqual(P.main(), 2)

    def test_empty_response_is_not_proof_of_customer_ready(self):
        payload={"response":{"header":{"resultCode":"00"},"body":{
            "totalCount":0,"items":[]}}}
        result=P.probe("SYNTH-KEY",FakeOpener(json.dumps(payload)),DATE)
        self.assertEqual(result["operations_succeeded"],4)
        self.assertFalse(result["ready_for_live_ingestion"])
        self.assertTrue(all(x["state"]=="OK_EMPTY" for x in result["results"].values()))


if __name__ == "__main__":
    unittest.main()
