"""Deterministic seven-locale public smoke tests. No network or credentials."""
import importlib.util
from pathlib import Path
import json
import re
import unittest
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"ops"/"wmm_seven_locale_readonly.py"
SPEC=importlib.util.spec_from_file_location("wmm_seven_locale_readonly",SCRIPT)
P=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)

class Resp:
    status=200
    def __init__(self,html):
        self.text=html.encode("utf-8")
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.text[:n]

class FakeOpen:
    def __init__(self,bad=None):
        self.urls=[]
        self.bad=bad
    def open(self,req,timeout=0):
        self.urls.append(req.full_url)
        assert req.get_method()=="GET"
        assert timeout<=12
        locale=req.full_url.split("/")[-2]
        if locale == self.bad:
            raise HTTPError(req.full_url,503,"Unavailable",None,None)
        s=f'<!doctype html><html lang="{locale}"><head><title>GOV RADAR</title></head><body>'
        if locale=="ko":s+="조사·제안 아이디어 · 실시간 입찰 아님"
        if locale=="en":s+="Curated research ideas · not live tenders"
        return Resp(s+"</body></html>")

class LocaleSmokeTests(unittest.TestCase):
    def test_seven_get_only_and_explicit_not_full_e2e(self):
        op=FakeOpen()
        out=P.check(op)
        self.assertEqual(out["result"],"PASS")
        self.assertEqual(len(op.urls),7)
        self.assertEqual(len(set(op.urls)),7)
        self.assertTrue(all(x.startswith(P.ORIGIN+"/") for x in op.urls))
        self.assertFalse(out["identity_roles_verified"])
        self.assertFalse(out["payment_checkout_verified"])
        self.assertFalse(out["mobile_browser_verified"])
        self.assertFalse(out["registered_forms_verified"])
        self.assertTrue(out["locales"]["ko"]["snapshot_disclosure_present"])
        self.assertTrue(out["locales"]["en"]["snapshot_disclosure_present"])
        self.assertEqual(out["customer_posts"],0)

    def test_one_bad_locale_is_full_failure(self):
        op=FakeOpen(bad="ar")
        out=P.check(op)
        self.assertEqual(out["result"],"FAIL")
        self.assertEqual(out["failed_locales"],["ar"])
        self.assertEqual(out["locales"]["ar"]["http_status"],503)

    def test_lang_mismatch_is_not_a_pass(self):
        class Wrong:
            def open(self,req,timeout=0):
                return Resp('<html lang="en"><title>GOV RADAR</title></html>')
        r=P.fetch("ko",Wrong())
        self.assertEqual(r["status"],"FAIL")
        self.assertFalse(r["html_lang_correct"])

    def test_untrusted_locale_never_fetched(self):
        op=FakeOpen()
        with self.assertRaises(ValueError):
            P.fetch("../admin",op)
        self.assertEqual(op.urls,[])

    def test_workflow_no_new_schedule_or_security_expansion(self):
        code=SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("POST",code.split("def fetch(")[1].split("def check(")[0])
        wf=(ROOT/".github"/"workflows"/"wmm_operations_watch.yml").read_text()
        self.assertIn("cron: '17 * * * *'",wf)
        self.assertIn("ops/wmm_seven_locale_readonly.py",wf)
        self.assertIn("persist-credentials: false",wf)
        self.assertNotIn("KONEPS_KEY",code)

if __name__=="__main__":
    unittest.main()
