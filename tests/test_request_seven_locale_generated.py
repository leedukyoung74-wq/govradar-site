"""Seven-language member request generator release contract. No real submissions."""
import re,subprocess,shutil,unittest
from pathlib import Path
import pages_req
ROOT=Path(__file__).resolve().parents[1]
LANGS=("ko","en","es","fr","ar","vi","id")
TEXT={"ko":"회원 분석 의뢰","en":"Member analysis requests","es":"Solicitudes de análisis","fr":"Demandes d’analyse","ar":"طلبات التحليل","vi":"Yêu cầu phân tích","id":"Permintaan analisis"}
class LocalizedRequestTests(unittest.TestCase):
    def test_all_locales_are_real_and_localized(self):
        for lang in LANGS:
            k=pages_req.K[lang]
            with self.subTest(lang=lang):
                self.assertIn(TEXT[lang],k["t"])
                self.assertEqual(len(k["types"]),4)
                self.assertEqual([x[0] for x in k["types"]],["tender","country","family","partner"])
                self.assertIn("19",k["who"])
                self.assertEqual(len(k["S"]),9)
                self.assertIn("{n}",k["left"])
                for original,localized in zip(pages_req.K["en"]["types"],k["types"]):
                    self.assertEqual(original[0],localized[0])
                    self.assertEqual([(x[0],x[2],x[3]) for x in original[4]],[(x[0],x[2],x[3]) for x in localized[4]])
    def test_generated_cf_html_preserves_identifiers_and_privacy(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                p=ROOT/"cf/public"/lang/"request/index.html"
                self.assertTrue(p.is_file(),str(p))
                html=p.read_text(encoding="utf8")
                self.assertIn(TEXT[lang],html)
                self.assertIn('class="cform rq-form"',html)
                self.assertIn('name="form-name" value="order"',html)
                self.assertIn('name="privacy_agree" value="yes" required',html)
                self.assertIn('privacy_consent:f.querySelector(',html)
                self.assertIn('action="/nfform?next=',html)
                self.assertIn('method="POST"',html)
                for typ in ["tender","country","family","partner"]:
                    self.assertIn('name="rqt" value="'+typ+'"',html)
                self.assertIn('fetch("/api/req"',html)
                self.assertNotIn('http-equiv="refresh"',html)
    @unittest.skipUnless(shutil.which("node"),"node unavailable")
    def test_all_generated_inline_js_parses(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                html=(ROOT/"cf/public"/lang/"request/index.html").read_text("utf8")
                for tags,body in re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S):
                    if "application/ld+json" in tags:continue
                    p=subprocess.run(["node","--check"],input=body,text=True,capture_output=True,timeout=12)
                    self.assertEqual(p.returncode,0,(lang,p.stderr[:500]))

if __name__=="__main__":unittest.main()
