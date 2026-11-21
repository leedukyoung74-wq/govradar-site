import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("ewe_html",ROOT/"ops/wmm_ewe_static_page_overlay.py")
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

KINDS=("environment","weather","emergency")


class CardOnlyOverlayTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=pathlib.Path(tmp.name)
        self.catalog={"countries":{}}
        self.countries=[{"iso":"DZ","slug":"algeria"},{"iso":"FJ","slug":"fiji"}]
        self.countries.extend({"iso":f"T{i}","slug":f"test-{i}"} for i in range(191))
        self.before={}
        for iso in ("DZ","FJ"):
            self.catalog["countries"][iso]={}
            for kind in KINDS:
                self.catalog["countries"][iso][kind]={
                    "name":f"Official {iso} {kind} & <Ministry>",
                    "url":f"https://official.{iso.lower()}.gov.example/{kind}",
                    "access":"not_live_tested",
                    "review":"curated_candidate"}
            for lang in M.LANGS:
                path=self.root/"public"/lang/("algeria" if iso=="DZ" else "fiji")/"index.html"
                path.parent.mkdir(parents=True,exist_ok=True)
                cards="".join(
                    '<a class="card" href="https://directory.example/source" target="_blank" '
                    'rel="noopener noreferrer nofollow" style="display:block;text-decoration:none">'
                    f'<b>{kind}</b><p>Global directory</p><p class="note">No official source</p></a>'
                    for kind in KINDS)
                section='<section class="sec" id="environment-weather-emergency"><h2>Existing title</h2>'\
                        '<p class="note">Existing government warning</p><div class="cards">'+cards+'</div></section>'
                original='<html><script>AUTH_SAFE</script><main>PRIOR_CONTENT</main>'+section+'<footer>AFTER_CONTENT</footer></html>'
                if iso=="DZ" and lang=="vi":
                    original='<!doctype html><meta name="robots" content="noindex">'\
                             '<meta http-equiv="refresh" content="0;url=/en/algeria/">'\
                             '<script>location.replace("/en/algeria/")</script>'
                path.write_text(original,encoding="utf8")
                self.before[str(path)]=original
        self.catalog_path=self.root/"catalog.json"
        self.countries_path=self.root/"countries.json"
        self.catalog_path.write_text(json.dumps(self.catalog),encoding="utf8")
        self.countries_path.write_text(json.dumps(self.countries),encoding="utf8")

    def test_exactly_one_section_per_real_page_and_redirect_byte_preserved(self):
        v=M.plan_changes(self.root,self.catalog,self.countries,("DZ","FJ"))
        self.assertEqual(v["expected_pages"],14)
        self.assertEqual(len(v["changes"]),13)
        self.assertEqual(len(v["redirects_preserved"]),1)
        for _,p,updated in v["changes"]:
            before=self.before[str(p)]
            self.assertIn("AUTH_SAFE",updated)
            self.assertIn("PRIOR_CONTENT",updated)
            self.assertIn("AFTER_CONTENT",updated)
            self.assertEqual(updated.count('class="card"'),3)
            self.assertEqual(updated.count("National agency candidate"),3 if "/en/" in str(p) else 0)
            self.assertIn("Official",updated)
            self.assertNotIn("<Ministry>",updated)
            self.assertIn("&lt;Ministry&gt;",updated)
            self.assertEqual(updated.count("<script>"),before.count("<script>"))
        untouched=self.root/"public"/"vi"/"algeria"/"index.html"
        self.assertEqual(untouched.read_text(encoding="utf8"),self.before[str(untouched)])

    def test_local_apply_is_idempotent_and_does_not_touch_redirect(self):
        with mock.patch.object(M,"COUNTRIES",("DZ","FJ")):
            r=M.run(self.root,self.catalog_path,self.countries_path,dry_run=False)
            self.assertEqual(r["updated_country_page_count"],13)
            self.assertFalse(r["site_published"])
            self.assertEqual(len(r["redirect_pages_preserved"]),1)
            retry=M.run(self.root,self.catalog_path,self.countries_path,dry_run=True)
            self.assertEqual(retry["updated_country_page_count"],0)
            self.assertEqual(len(retry["already_current_pages"]),13)
        path=self.root/"public"/"vi"/"algeria"/"index.html"
        self.assertEqual(path.read_text(encoding="utf8"),self.before[str(path)])

    def test_dry_run_does_not_change_any_file(self):
        with mock.patch.object(M,"COUNTRIES",("DZ","FJ")):
            result=M.run(self.root,self.catalog_path,self.countries_path,dry_run=True)
            self.assertEqual(result["updated_country_page_count"],13)
        for p,s in self.before.items():
            self.assertEqual(pathlib.Path(p).read_text(encoding="utf8"),s)

    def test_missing_cards_fails_before_mutating_any_page(self):
        path=self.root/"public"/"en"/"fiji"/"index.html"
        broken=path.read_text(encoding="utf8").replace('<b>emergency</b>','<b>INVALID</b>').replace('class="card"','class="broken"',1)
        path.write_text(broken,encoding="utf8")
        with mock.patch.object(M,"COUNTRIES",("DZ","FJ")):
            with self.assertRaises(ValueError):
                M.run(self.root,self.catalog_path,self.countries_path,dry_run=False)
        sample=self.root/"public"/"ko"/"algeria"/"index.html"
        self.assertEqual(sample.read_text(encoding="utf8"),self.before[str(sample)])

    def test_non_redirect_missing_section_is_a_release_blocker(self):
        p=self.root/"public"/"en"/"fiji"/"index.html"
        p.write_text("<html>empty not redirect</html>",encoding="utf8")
        with self.assertRaises(ValueError):
            M.plan_changes(self.root,self.catalog,self.countries,("DZ","FJ"))

    def test_unsafe_agency_url_or_false_live_mark_blocked(self):
        base=self.catalog["countries"]["DZ"]["weather"]
        base["url"]="javascript:alert(1)"
        self.assertFalse(M.safe_source(base))
        base["url"]="https://official.dz.gov.example/weather"
        base["access"]="verified_live"
        self.assertFalse(M.safe_source(base))
        with self.assertRaises(ValueError):
            M.plan_changes(self.root,self.catalog,self.countries,("DZ","FJ"))


if __name__=="__main__":
    unittest.main()
