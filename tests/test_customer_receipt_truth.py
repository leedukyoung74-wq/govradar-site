"""Offline regression: source generator must match seven locale truthful receipt semantics."""
import json
import html
import re
import unittest
from pathlib import Path
import pages2 as P2
import pages3 as P3

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/"src/customer_receipts.json").read_text("utf-8"))
LANGS=("ko","en","es","fr","ar","vi","id")

class SourceReceiptTruth(unittest.TestCase):
    def test_all_seven_locales_and_two_receipt_routes(self):
        self.assertEqual(set(DATA),set(LANGS))
        def head(*_args,**_kw):return "<html><main>"
        def foot(_l):return "</main></html>"
        for lang in LANGS:
            label=DATA[lang]
            self.assertEqual(set(label),{"title","notice"})
            self.assertGreater(len(label["notice"]),50)
            self.assertIn("73036396@naver.com",label["notice"])
            a=P2.thanks_page(lang,head,foot,html.escape,LANGS)
            b=P3.thanks2_page(lang,{"head":head,"foot":foot,"LANGS":LANGS})
            for path,markup in [("consortium/thanks",a),("thanks",b)]:
                with self.subTest(language=lang,path=path):
                    self.assertIn(html.escape(label["title"]),html.unescape(markup))
                    self.assertIn("role=\"status\"",markup)
                    self.assertIn("73036396@naver.com",markup)
                    self.assertNotRegex(markup,r"<h1>\s*(신청을 받았습니다|Thank you — application received|Thank you — we've got your request)")
                    self.assertNotIn("ticket ID:",markup)

    def test_customer_entrypoints_while_original_map_first_retained(self):
        source=(ROOT/"build.py").read_text("utf-8")
        self.assertIn("W(\"/support/index.html\", _support.read())",source)
        self.assertIn('href="/support/?lang={L}"',source)
        self.assertIn('(legal|member|pay|mdb)',source)
        self.assertIn("(thanks|pricing|how|request|",source)
        self.assertIn("|consortium|",source)
        self.assertNotRegex(source,r"\|about\)\)")

if __name__=="__main__":unittest.main()
