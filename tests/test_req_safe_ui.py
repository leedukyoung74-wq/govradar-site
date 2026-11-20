"""GOV RADAR buyer request safety: no fake receipt and no unauthenticated status updates."""
import pathlib
import shutil
import subprocess
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class RequestIntegrity(unittest.TestCase):
    def test_all_locales_send_to_existing_verified_relay(self):
        import sys
        sys.path.insert(0,str(ROOT))
        import pages_req
        locales=("ko","en","es","fr","ar","vi","id")
        for lang in locales:
            with self.subTest(lang=lang):
                page=pages_req.request_page(lang,lambda *a:"<html><body>",lambda *a:"</body></html>",locales)
                self.assertIn('action="/nfform?next=/'+lang+'/thanks/"',page)
                self.assertIn('src="/assets/req-safe.js"',page)
                self.assertIn("WMM_REQUEST_TEXT",page)
                self.assertNotIn('a.unshift({{id:id',page)

    def test_request_api_disables_unauthenticated_status_forgery(self):
        source=(ROOT/"cf/functions/api/req.js").read_text(encoding="utf8")
        self.assertIn('unverified_relay_status_not_supported',source)
        self.assertIn("export async function onRequestPatch() {",source)
        self.assertNotIn('update requests set status=? where req_no=?',source)

    def test_js_syntax_and_runtime_submission_states(self):
        if not shutil.which("node"):
            self.skipTest("node unavailable")
        for args in ([ "node","--check",str(ROOT/"web/req-safe.js")],
                     [ "node",str(ROOT/"tests/js/req_safe_ui_test.mjs")]):
            with self.subTest(cmd=args):
                done=subprocess.run(args,capture_output=True,text=True,cwd=ROOT)
                self.assertEqual(done.returncode,0,done.stdout+done.stderr)

if __name__=="__main__":
    unittest.main()
