"""Generated GOV RADAR: no contradictory old KRW 20k/VAT-exclusive analysis prices."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/"cf"/"public"
LANGS=("ko","en","es","fr","ar","vi","id")
OLD=("월 20,000원","₩20,000","₩20.000","20 000 ₩","20,000 وون",
     "연 200,000원","₩200,000")
class MemberPriceSource(unittest.TestCase):
    def test_source_price_canonical(self):
        for name in ("pages3.py","src/i18n.py","src/i18n2.py","build.py","pages_req.py"):
            data=(ROOT/name).read_text("utf8")
            for old in OLD:
                with self.subTest(file=name,price=old):self.assertNotIn(old,data)
    def test_generated_home_all_seven_locales_no_old_price(self):
        for lang in LANGS:
            page=(PUBLIC/lang/"index.html").read_text("utf8")
            for old in OLD:
                with self.subTest(lang=lang,old=old): self.assertNotIn(old,page)
            self.assertIn('id="kp-t">—',page)
    def test_generated_pricing_ko_en_amount_and_vat(self):
        ko=(PUBLIC/"ko/pricing/index.html").read_text("utf8")
        en=(PUBLIC/"en/pricing/index.html").read_text("utf8")
        for value in ("19,800원","198,000원","VAT 포함"):
            self.assertIn(value,ko)
        for value in ("₩19,800","₩198,000","VAT incl."):
            self.assertIn(value,en)
        self.assertNotIn("All prices exclude VAT",en)
        self.assertNotIn("모든 가격 VAT 별도",ko)
    def test_request_ko_en_price(self):
        for lang in ("ko","en"):
            p=(PUBLIC/lang/"request/index.html").read_text("utf8")
            self.assertIn("19,800",p)
            self.assertNotIn("20,000",p)
if __name__=="__main__":unittest.main()
