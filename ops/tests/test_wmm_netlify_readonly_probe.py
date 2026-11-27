"""No network, no customer submissions: Netlify GET-only evidence classification."""
import io
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import wmm_netlify_readonly_probe as P

class FakeReply:
    def __init__(self,status,body):
        self.status=status
        self.stream=io.BytesIO(body)
    def __enter__(self):
        return self
    def __exit__(self,*a):
        return False
    def read(self,n):
        return self.stream.read(n)

class FakeOpener:
    def __init__(self):
        self.calls=[]
    def open(self,request,timeout=0):
        self.calls.append((request.full_url,request.get_method(),timeout))
        if request.full_url==P.ORIGIN+"/":
            return FakeReply(200,b'<form name="order" data-netlify="true">'
                                   b'<input type="hidden" name="form-name" value="order"></form>')
        if request.full_url.endswith("/.netlify/identity/settings"):
            return FakeReply(200,b'{"external":{"google":true}}')
        return FakeReply(401,b'{"error":"login_required"}')

class NetlifyReadOnlyTests(unittest.TestCase):
    def test_only_three_exact_gets_and_no_customer_payload(self):
        op=FakeOpener()
        result=P.run(op)
        self.assertEqual(len(op.calls),3)
        self.assertEqual([x[1] for x in op.calls],["GET"]*3)
        self.assertTrue(all(x[2]<=15 for x in op.calls))
        self.assertTrue(all(x[0].startswith(P.ORIGIN+"/") for x in op.calls))
        self.assertEqual(result["site"]["http_status"],200)
        self.assertTrue(result["site"]["html_form_markup"])
        self.assertTrue(result["site"]["form_name_hidden_inputs_present"])
        self.assertTrue(result["identity_settings"]["external_google_explicit_true"])
        self.assertTrue(result["anonymous_identity"]["anonymous_identity_guard"])
    def test_positive_html_never_claims_inbox_or_google_auth_success(self):
        result=P.run(FakeOpener())
        self.assertFalse(result["assessment"]["netlify_registered_form_verified"])
        self.assertFalse(result["assessment"]["inbox_item_verified"])
        self.assertFalse(result["assessment"]["notification_email_verified"])
        self.assertFalse(result["assessment"]["member_google_login_verified"])
    def test_missing_static_html_and_identity_are_inconclusive(self):
        r=P.analyze({"site":(404,b""),"identity_settings":(404,b""),
                    "anonymous_identity":(404,b"")})
        self.assertFalse(r["assessment"]["netlify_site_public_get_ok"])
        self.assertFalse(r["site"]["html_form_markup"])
        self.assertFalse(r["identity_settings"]["json_settings_readable"])
        self.assertFalse(r["anonymous_identity"]["anonymous_identity_guard"])
    def test_no_dynamic_urls_allowed(self):
        with self.assertRaises(ValueError):
            P.fetch_code("/custom-path",FakeOpener())
    def test_no_record_or_secret_leak_from_upstream_html(self):
        response={"site":(200,b'<form name="order"><input name="api_key" value="SECRET-SAMPLE">'
                                b'<p>customer@example.com</p></form>'),
                  "identity_settings":(200,b'{"site_url":"https://private.test","external":{}}'),
                  "anonymous_identity":(401,b'{"token":"SECRET"}')}
        summary=json.dumps(P.analyze(response),sort_keys=True)
        for secret in ("SECRET-SAMPLE","customer@example.com","private.test","SECRET"):
            self.assertNotIn(secret,summary)

if __name__=="__main__":unittest.main()
