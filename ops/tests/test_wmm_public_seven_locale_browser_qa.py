"""Offline-only checks for seven-locale real-browser policy; no Chromium or network."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "wmm_public_seven_locale_browser_qa",
    ROOT/"ops"/"wmm_public_seven_locale_browser_qa.py")
P=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def classify(locale="ko", **kwargs):
    params=dict(label=locale,code=200,lang=locale,
                direction="rtl" if locale=="ar" else "ltr",
                viewport=True,h1=True,main_count=1,
                overflow_px=0,denied_posts=False,copy_present=True)
    params.update(kwargs)
    return P.classify(**params)


class PublicMobileBrowserPolicyTests(unittest.TestCase):
    def test_seven_language_manifest_and_viewports(self):
        self.assertEqual(P.LOCALES,("ko","en","es","fr","ar","vi","id"))
        self.assertEqual(P.SIZES,((390,844),(1366,768)))

    def test_good_mobile_render_and_arabic_rtl(self):
        for locale in P.LOCALES:
            with self.subTest(locale=locale):
                x=classify(locale)
                self.assertEqual(x["status"],"PASS")
                self.assertEqual(x["failures"],[])

    def test_wrong_language_or_arabic_ltr_fails(self):
        self.assertEqual(classify("ko",lang="en")["status"],"FAIL")
        self.assertIn("WRONG_DOCUMENT_DIRECTION",
                      classify("ar",direction="ltr")["failures"])

    def test_overflow_not_hidden_by_http_200(self):
        self.assertEqual(classify(overflow_px=21)["status"],"FAIL")
        self.assertEqual(classify(overflow_px=20)["status"],"PASS")

    def test_missing_main_and_viewport_not_ignored(self):
        self.assertIn("MISSING_VIEWPORT_META",
                      classify(viewport=False)["failures"])
        self.assertIn("MAIN_HEADING_NOT_VISIBLE",
                      classify(h1=False)["failures"])

    def test_background_post_blocking_is_not_silent(self):
        self.assertIn("BACKGROUND_POST_BLOCKED",
                      classify(denied_posts=True)["failures"])
        self.assertIn('route.request.method.upper() != "GET"',
                      (ROOT/"ops"/"wmm_public_seven_locale_browser_qa.py")
                      .read_text(encoding="utf-8"))

    def test_undeployed_reviewed_copy_is_pending_not_page_outage(self):
        x=classify("ko",copy_present=False)
        self.assertEqual(x["status"],"PASS")
        self.assertEqual(x["copy_review"],"PENDING_NOT_DEPLOYED")
        y=classify("en",copy_present=False)
        self.assertEqual(y["copy_review"],"PENDING_NOT_DEPLOYED")

    def test_no_paid_checkouts_or_schedule_created(self):
        wf=(ROOT/".github"/"workflows"/"wmm_seven_locale_mobile_browser_qa.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:",wf)
        self.assertIn("branches: [main]",wf)
        self.assertNotIn("  schedule:",wf)
        self.assertIn("persist-credentials: false",wf)
        self.assertIn("ops/wmm_public_seven_locale_browser_qa.py",wf)
        self.assertNotIn("CLOUDFLARE_API_TOKEN",wf)
        self.assertNotIn("secrets.",wf)

if __name__=="__main__":
    unittest.main()
