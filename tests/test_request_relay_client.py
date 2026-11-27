"""Offline regression for GOV RADAR request forms; does not send customer mail."""
import re
import shutil
import subprocess
import unittest
import pages_req

LANGS=("ko","en","es","fr","ar","vi","id")

def page(lang):
    return pages_req.request_page(lang,
        lambda *_args: "<!doctype html><html><body><main>",
        lambda *_args: "</main></body></html>", LANGS)

class RequestRelayClientTests(unittest.TestCase):
    def test_all_locales_keep_authenticated_status_patch(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html=page(lang)
                self.assertIn('method:"PATCH",headers:hdr({{"content-type":"application/json"}})'.replace('{{','{').replace('}}','}'),html)
                self.assertIn('var mark=tok()?fetch("/api/req"',html)
                self.assertIn('r2.type==="opaqueredirect"||r2.status===303',html)
                self.assertNotIn('r2.status<400',html)

    def test_relay_failure_does_not_false_confirm_or_fallback_to_duplicate_native_post(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html=page(lang)
                self.assertIn("btn.textContent=K.retry",html)
                self.assertIn("if(prev&&!prev.relay_failed)",html)
                self.assertIn("a[0].relay_failed=true",html)
                self.assertIn("msg.textContent=K.sending+\" \"+id",html)
                self.assertIn("}).catch(relayFailed);",html)
                self.assertIn("x.relay_failed?K.delivery_failed:(x.gateway_only?K.gateway:K.st)",html)

    def test_d1_missing_fallback_is_verified_not_native_submission(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html=page(lang)
                self.assertIn("if(r.status===503){SRV=false",html)
                self.assertIn("function relayWithoutD1()",html)
                self.assertIn('r.status!==303',html)
                self.assertNotIn("f.submit()",html)
                self.assertIn("gateway_only=true",html)
                self.assertIn("gateway_only?K.gateway",html)
                self.assertIn("else relayWithoutD1();",html)

    def test_member_access_codes_never_enter_any_locale_request(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html=page(lang)
                self.assertNotIn('data-k="code"',html)
                self.assertNotIn('lines.push("member code: "',html)
                self.assertIn("Membership is determined by verified sign-in",html)

    def test_gateway_receipt_never_claims_staff_delivery(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html=page(lang)
                self.assertIn('"gateway_reported":',html)
                self.assertIn('"gateway_failed_reported":',html)
                self.assertIn(pages_req.K[lang].get("gateway", "전송 서버가 요청을 받았습니다. 관리자 확인 전입니다. 요청번호" if lang == "ko" else "Gateway accepted the request; staff receipt not verified. Request number"),html)

    def test_explicit_privacy_consent_sent_and_checked_in_all_locales(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html=page(lang)
                self.assertIn('if(!ok||!f.querySelector(\'input[name="privacy_agree"]\').checked)',html)
                self.assertIn('privacy_consent:f.querySelector(\'input[name="privacy_agree"]\').checked',html)
                self.assertIn('name="privacy_agree" value="yes" required',html)

    def test_member_request_price_matches_live_krw_pricing(self):
        ko=page("ko")
        en=page("en")
        self.assertIn("월 20,000원",ko)
        self.assertNotIn("월 19,800원",ko)
        self.assertIn("KRW 20,000",en)
        self.assertNotIn("KRW 19,800",en)

    @unittest.skipUnless(shutil.which("node"),"node unavailable")
    def test_all_locales_inline_js_syntax(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html=page(lang)
                scripts=re.findall(r"<script[^>]*>(.*?)</script>",html,re.S)
                self.assertTrue(scripts)
                for js in scripts:
                    proc=subprocess.run(["node","--check"],input=js,capture_output=True,text=True,timeout=12)
                    self.assertEqual(proc.returncode,0,proc.stderr)

if __name__ == "__main__":
    unittest.main()
