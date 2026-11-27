"""Seven-language generated homepage must not claim unsupported live-interval SLA."""
import html
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LANGS=("ko","en","es","fr","ar","vi","id")
NOTICES={
 "ko":"조사·제안 아이디어 · 실시간 입찰 아님",
 "en":"Curated research ideas · not live tenders",
 "es":"Ideas de estudio · no son licitaciones en vivo",
 "fr":"Pistes de recherche · pas des appels d'offres en direct",
 "ar":"أفكار بحثية · ليست مناقصات مباشرة",
 "vi":"Ý tưởng nghiên cứu · không phải gói thầu trực tiếp",
 "id":"Ide riset terkurasi · bukan tender langsung",
}
PERIODIC={
 "ko":"정기 갱신","en":"PERIODIC","es":"PERIÓDICO",
 "fr":"PÉRIODIQUE","ar":"تحديث دوري","vi":"ĐỊNH KỲ","id":"BERKALA"
}

class HomepageSourceTruthTests(unittest.TestCase):
    def test_generated_seven_locale_ticker_no_unsupported_live_label(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                file=ROOT/"dist"/lang/"index.html"
                self.assertTrue(file.exists(),str(file)+" not generated")
                page=file.read_text(encoding="utf-8")
                m=re.search(r'<section class="tick".*?</section>',page,re.S)
                self.assertIsNotNone(m)
                ticker=m.group(0)
                self.assertIn(PERIODIC[lang],ticker)
                self.assertNotIn('>LIVE<',ticker)
                self.assertNotIn('>EN VIVO<',ticker)
                self.assertNotIn('>EN DIRECT<',ticker)
                self.assertNotIn('>TRỰC TIẾP<',ticker)
                self.assertNotIn('>LANGSUNG<',ticker)
                self.assertIn(html.escape(NOTICES[lang], quote=True),page)

    def test_generated_business_notice_not_equated_with_last_feed_update(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                text=(ROOT/"dist"/lang/"index.html").read_text(encoding="utf-8")
                m=re.search(r'<div class="kpis">.*?</div></div>',text,re.S)
                self.assertIsNotNone(m)
                self.assertIn(html.escape(NOTICES[lang], quote=True),text)
                self.assertIn('id="kp-u"',text)
                self.assertIn('id="kp-t"',text)

    def test_source_does_not_change_checkout_or_public_data(self):
        code=(ROOT/"build.py").read_text(encoding="utf-8")
        self.assertIn('BIZ_SNAPSHOT_NOTICE',code)
        self.assertIn('not live tenders',code)
        self.assertIn('not a live list',code)
        self.assertIn('data_branch", "feeds", "today.json"',code)


if __name__=="__main__":
    unittest.main()
