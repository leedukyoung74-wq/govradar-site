"""Generated GOV RADAR: no contradictory old KRW 20k/VAT-exclusive analysis prices."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/"cf"/"public"
LANGS=("ko","en","es","fr","ar","vi","id")
OLD=("월 20,000원","₩20,000","₩20.000","20 000 ₩","20,000 وون",
     "연 200,000원","₩200,000","KRW 20,000")
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
    def test_generated_membership_all_seven_locales(self):
        for lang in LANGS:
            path=PUBLIC/lang/"membership/index.html"
            with self.subTest(lang=lang):
                self.assertTrue(path.is_file())
                content=path.read_text("utf8")
                for old in OLD:
                    self.assertNotIn(old,content)
        ko=(PUBLIC/"ko/membership/index.html").read_text("utf8")
        en=(PUBLIC/"en/membership/index.html").read_text("utf8")
        self.assertIn("부가세 포함, 세금계산서 발행",ko)
        self.assertNotIn("부가세 별도, 세금계산서 발행",ko)
        self.assertIn("VAT included; tax invoices issued",en)
        self.assertNotIn("VAT excluded; tax invoices issued",en)
    def test_source_m1_vat_and_price_notes(self):
        src=(ROOT/"pages3.py").read_text("utf8")
        self.assertIn("analysis membership KRW 19,800 a month, VAT included",src)
        self.assertNotIn("analysis membership KRW 20,000",src)
        self.assertNotIn("M1 is the same grade as the GOV RADAR analysis membership (₩19,800/month). VAT excluded",src)
    def test_request_ko_en_price(self):
        for lang in ("ko","en"):
            p=(PUBLIC/lang/"request/index.html").read_text("utf8")
            self.assertIn("19,800",p)
            self.assertNotIn("20,000",p)
if __name__=="__main__":unittest.main()
