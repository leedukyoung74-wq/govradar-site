"""Synthetic-only GOV RADAR 7-homepage release candidate safety regression."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "wmm_seven_home_release_candidate",
    ROOT/"ops"/"wmm_seven_home_release_candidate.py")
P=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def page(lang,*,extra="",form="/nfform?next=/ko/thanks/"):
    dr="rtl" if lang=="ar" else "ltr"
    return (
        f'<!doctype html><html lang="{lang}" dir="{dr}">'
        f'<head><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<script src="/assets/site.js"></script></head>'
        f'<body><main><h1>GOV RADAR</h1>'
        f'<span>{P.PERIODIC[lang]}</span>'
        f'<p>{P.COUNTRY[lang]}</p>'
        f'<small>{P.COPY[lang]}</small>'
        '<b id="kp-t">—</b><span id="kp-u"></span>'
        f'<form method="POST" action="{form}"></form>{extra}</main></body></html>'
    )


class SevenHomeCandidateTests(unittest.TestCase):
    def fixtures(self,src,live):
        for lang in P.LANGS:
            for root in (src,live):
                (root/lang).mkdir(parents=True,exist_ok=True)
                (root/lang/"index.html").write_text(page(lang),encoding="utf-8")
        (live/"assets").mkdir(parents=True)
        (live/"assets"/"site.js").write_text("console.log('existing');",encoding="utf-8")

    def test_clean_fixture_is_still_owner_review_not_deployed(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);src=base/"candidate";live=base/"live";out=base/"out"
            self.fixtures(src,live)
            report=P.build(src,live,out)
            self.assertEqual(report["state"],"OWNER_RELEASE_REVIEW_REQUIRED")
            self.assertEqual(report["blocked_locales"],[])
            self.assertFalse(report["safety"]["production_changed"])
            self.assertFalse(report["safety"]["real_payments_executed"])
            self.assertTrue((out/"wmm-seven-language-homepages-REVIEW-ONLY.zip").exists())
            with zipfile.ZipFile(out/"wmm-seven-language-homepages-REVIEW-ONLY.zip") as z:
                self.assertEqual(len(z.namelist()),8)
                self.assertIn("public/ar/index.html",z.namelist())
                self.assertNotIn("live_token",z.namelist())

    def test_form_endpoint_drift_blocks_copy_only_release(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);src=base/"candidate";live=base/"live";out=base/"out"
            self.fixtures(src,live)
            (live/"ko"/"index.html").write_text(
                page("ko",form="/legacy-unverified-post"),encoding="utf-8")
            report=P.build(src,live,out)
            self.assertEqual(report["state"],"BLOCKED_REVIEW")
            self.assertIn("ko",report["blocked_locales"])
            self.assertFalse(report["checks"]["ko"]["form_tags_identical"])
            self.assertFalse(report["safety"]["production_changed"])

    def test_missing_live_asset_blocks_new_html_release(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);src=base/"candidate";live=base/"live";out=base/"out"
            self.fixtures(src,live)
            (src/"en"/"index.html").write_text(
                page("en",extra='<script src="/assets/brand-new-risk.js"></script>'),
                encoding="utf-8")
            report=P.build(src,live,out)
            self.assertIn("en",report["blocked_locales"])
            self.assertEqual(report["checks"]["en"]["new_local_asset_refs_missing_in_live"],
                             ["assets/brand-new-risk.js"])

    def test_wrong_lang_rtl_or_missing_disclosure_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);src=base/"candidate";live=base/"live";out=base/"out"
            self.fixtures(src,live)
            (src/"ar"/"index.html").write_text(
                page("ar").replace('dir="rtl"','dir="ltr"'),encoding="utf-8")
            (src/"ko"/"index.html").write_text(
                page("ko").replace(P.COPY["ko"],""),encoding="utf-8")
            r=P.build(src,live,out)
            self.assertEqual(set(r["blocked_locales"]),{"ar","ko"})
            self.assertFalse(r["checks"]["ar"]["check_results"]["html_direction"])
            self.assertFalse(r["checks"]["ko"]["check_results"]["research_disclosure"])

    def test_release_workflow_does_not_deploy_or_create_cron(self):
        s=(ROOT/".github"/"workflows"/"wmm_seven_home_release_candidate.yml").read_text()
        self.assertIn("ref: src",s)
        self.assertIn("ref: live",s)
        self.assertIn("persist-credentials: false",s)
        self.assertIn("actions/upload-artifact@",s)
        self.assertNotIn("  schedule:",s)
        self.assertNotIn("wrangler deploy",s)
        self.assertNotIn("netlify deploy",s)
        self.assertNotIn("git push",s)
        self.assertNotIn("secrets.",s)

if __name__=="__main__":
    unittest.main()
