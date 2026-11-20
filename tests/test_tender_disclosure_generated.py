"""Verify the seven actually generated MDB HTML pages, not just Python source text.

Run after: python build.py --base https://radar.wmm-hoa.com
No network, deployment, database writes, customer messages, or payments.
"""
import ast
import html as html_lib
import os
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
LANGS=("ko","en","es","fr","ar","vi","id")

@unittest.skipUnless(os.environ.get("WMM_GENERATED_QA") == "1", "Generated HTML QA runs only after build")
class TenderDisclosureGeneratedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=ast.parse((ROOT/"pages3.py").read_text(encoding="utf8"))
        vals=[n.value for n in source.body if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id=="TENDER_DISCLOSURE" for t in n.targets)]
        if len(vals)!=1:
            raise RuntimeError("TENDER_DISCLOSURE dictionary must have one direct assignment")
        cls.labels=ast.literal_eval(vals[0])

    def test_mdb_generated_pages_contain_localized_disclosure(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                path=ROOT/"dist"/lang/"mdb"/"index.html"
                self.assertTrue(path.is_file(),f"Missing generated page: {path}")
                html=path.read_text(encoding="utf8")
                visible=html_lib.unescape(html)
                for key in ("heading","warning"):
                    value=self.labels[lang][key]
                    self.assertIn(value,visible,f"{lang}: {key} not found in generated HTML")
                # A build with no currently-open tenders can contain zero source anchors;
                # ensure links are correctly labelled only when there are rendered source cards.
                if '<a class="src" href="https://' in visible:
                    self.assertIn(self.labels[lang]["external"],visible,
                                  f"{lang}: external source label missing for rendered cards")
                self.assertIn('id="deadlines"',html)
                self.assertIn('data-dl=',html)

    def test_generated_pages_do_not_use_unqualified_open_headline(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html=(ROOT/"dist"/lang/"mdb"/"index.html").read_text(encoding="utf8")
                self.assertNotIn('<h2 id="deadlines">Open tenders by deadline</h2>',html)
                self.assertNotIn('<h2 id="deadlines">마감일 순 열린 입찰</h2>',html)

if __name__=="__main__":
    unittest.main()
