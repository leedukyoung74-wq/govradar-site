"""Synthetic no-network proof surgical copy patch preserves live auth/forms/JS."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "wmm_seven_home_surgical_copy",
    ROOT/"ops"/"wmm_seven_home_surgical_copy.py")
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def htmlpage(lang,source=False,source_form_change=False):
    if source:
        hero="193 country overviews · source verification varies"
        tick="PERIODIC"
        country="Country overviews · verification varies"
        disclaimer="<small>Curated research ideas · not live tenders</small>"
    else:
        hero="Tracking 193 governments · 193 researched in depth"
        tick="LIVE"
        country="countries researched"
        disclaimer=""
    form="/different-generated-form" if source_form_change else "/nfform?next=/ko/thanks/"
    return (
      f'<html lang="{lang}" dir="{"rtl" if lang=="ar" else "ltr"}">'
      f'<p class="eb"><i class="live"></i>{hero}</p>'
      f'<div class="kpis"><div><b>193<small>/193</small></b><span>{country}</span></div>'
      '<div><b id="kp-t">—</b><span>open tenders</span></div>'
      f'<div><b>631</b><span>business opportunities</span>{disclaimer}</div>'
      '<div><b id="kp-u">—</b><span>last update</span></div></div>'
      f'<section class="tick" aria-label="{tick}" data-l="{lang}">'
      f'<div class="tick-l"><i></i>{tick}<span>Source summary</span></div>'
      '<div class="tick-w"><div class="tick-t" id="tickt"></div></div></section>'
      f'<form method="POST" action="{form}"><input name="hi"></form>'
      '<script src="/assets/auth.js"></script>'
      '<script>window.__test="untouched"</script>'
      '</html>'
    )


class SurgicalSevenCopyTests(unittest.TestCase):
    def test_preserves_live_forms_scripts_counts_and_endpoints(self):
        old=htmlpage("ko")
        new=htmlpage("ko",source=True,source_form_change=True)
        patched,check=M.patch("ko",new,old)
        self.assertIn("193 country overviews",patched)
        self.assertIn("Curated research ideas",patched)
        self.assertIn("PERIODIC",patched)
        self.assertEqual(M.FORM.findall(patched),M.FORM.findall(old))
        self.assertEqual(M.SCRIPT.findall(patched),M.SCRIPT.findall(old))
        self.assertIn("631",patched)
        self.assertTrue(check["original_numeric_kpis_preserved"])
        self.assertTrue(check["source_generated_form_changes_intentionally_excluded"])
        self.assertEqual(check["forms_byte_identical"],True)

    def test_refuses_unapproved_changed_ticker_markup(self):
        old=htmlpage("en")
        src=htmlpage("en",source=True).replace(
            '<div class="tick-w">','<aside class="tick-w">')
        with self.assertRaises(ValueError):
            M.patch("en",src,old)

    def test_refuses_missing_or_ambiguous_page_anchors(self):
        old=htmlpage("ar")
        src=htmlpage("ar",source=True)
        with self.assertRaises(ValueError):
            M.patch("ar",src,old.replace('class="kpis"','class="other"'))
        with self.assertRaises(ValueError):
            M.patch("ar",src+src,old)

    def test_all_seven_patch_zip_with_no_web_writes(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);source=base/"source";live=base/"live";out=base/"out"
            for lang in M.LANGS:
                (source/lang).mkdir(parents=True)
                (live/lang).mkdir(parents=True)
                (source/lang/"index.html").write_text(
                    htmlpage(lang,source=True,source_form_change=True),encoding="utf-8")
                (live/lang/"index.html").write_text(htmlpage(lang),encoding="utf-8")
            snapshots={l:(live/l/"index.html").read_bytes() for l in M.LANGS}
            report=M.generate(source,live,out)
            self.assertEqual(report["result"],"OWNER_REVIEW_REQUIRED_NOT_DEPLOYED")
            self.assertEqual(report["patched_locales"],7)
            self.assertFalse(report["live_site_modified"])
            self.assertFalse(report["new_charges"])
            self.assertEqual(snapshots,{l:(live/l/"index.html").read_bytes() for l in M.LANGS})
            with zipfile.ZipFile(out/"wmm-seven-homepages-COPY-ONLY-REVIEW.zip") as z:
                self.assertEqual(len(z.namelist()),8)
                self.assertIn("public/ar/index.html",z.namelist())

    def test_surgical_script_and_workflow_cannot_deploy(self):
        workflow=(ROOT/".github"/"workflows"/"wmm_seven_home_release_candidate.yml").read_text()
        self.assertIn("wmm_seven_home_surgical_copy.py",workflow)
        self.assertIn("actions/upload-artifact@",workflow)
        self.assertNotIn("  schedule:",workflow)
        self.assertNotIn("wrangler deploy",workflow)
        self.assertNotIn("git push",workflow)
        self.assertNotIn("secrets.",workflow)


if __name__=="__main__":
    unittest.main()
