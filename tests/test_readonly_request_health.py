"""Offline tests for read-only public API probe. Never access network here."""
import pathlib
import sys
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import readonly_request_health as H


class RequestHealthTests(unittest.TestCase):
    def test_anonymous_401_is_not_full_d1_or_inbox_proof(self):
        result=H.interpret(401,405)
        self.assertEqual(result["d1_binding_evidence"],"PROBABLE_BOUND_AUTH_GUARD_PRESENT")
        self.assertFalse(result["d1_write_verified"])
        self.assertFalse(result["submission_tested"])
        self.assertFalse(result["netlify_inbox_verified"])

    def test_missing_binding_and_unsafe_anonymous_get(self):
        self.assertEqual(H.interpret(503,405)["d1_binding_evidence"],"UNAVAILABLE_OR_D1_UNBOUND")
        self.assertEqual(H.interpret(200,405)["d1_binding_evidence"],"SECURITY_ALERT_ANONYMOUS_GET_SUCCEEDED")

    def test_only_allowlisted_anonymous_get_used(self):
        seen=[]
        class Opener:
            def open(self, request, timeout):
                seen.append(request)
                raise HTTPError(request.full_url,401,"Unauthorized",{},None)
        self.assertEqual(H.anonymous_get("/api/req",opener=Opener()),401)
        self.assertEqual(seen[0].get_method(),"GET")
        self.assertNotIn("Authorization",seen[0].headers)
        with self.assertRaises(ValueError):
            H.anonymous_get("/api/req?token=secret",opener=Opener())

    def test_form_get_never_claims_delivery(self):
        self.assertEqual(H.interpret(401,200)["form_get_evidence"],"INCONCLUSIVE_NO_POST_SENT")
        self.assertFalse(H.interpret(401,200)["netlify_inbox_verified"])


if __name__ == "__main__":
    unittest.main()
