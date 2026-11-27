"""Seven-language source-status labelling contract (no provider network calls)."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"pages3.py").read_text(encoding="utf8")


class SourceLabelsTests(unittest.TestCase):
    def test_historical_only_is_not_shown_as_a_source_failure(self):
        self.assertIn('st==="HISTORICAL_ONLY"?HS', SOURCE)
        self.assertIn('w=st==="HISTORICAL_ONLY"?HS:c===""?S[10]:c==="p"?S[11]:S[12]',SOURCE)

    def test_labels_exist_for_each_public_language(self):
        for token in ('ko:"과거 자료만"', 'en:"Archive only"', 'es:"Solo histórico"',
                      'fr:"Archives uniquement"', 'ar:"أرشيف فقط"',
                      'vi:"Chỉ dữ liệu cũ"', 'id:"Hanya arsip"'):
            with self.subTest(token=token):
                self.assertIn(token,SOURCE)

    def test_partial_and_success_have_their_original_meanings(self):
        self.assertIn('st==="SUCCESS"||st==="EMPTY_SUCCESS"',SOURCE)
        self.assertIn('st==="PARTIAL"?"p":"f"',SOURCE)
        self.assertIn('var HS=',SOURCE)


if __name__=="__main__":
    unittest.main()
