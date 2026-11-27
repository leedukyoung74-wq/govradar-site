"""Seven-language feedback form privacy agreement release guard (NO SUBMISSION)."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
LANGS=("ko","en","es","fr","ar","vi","id")

class FeedbackConsentRelease(unittest.TestCase):
    def test_source_has_required_checkbox_and_privacy_link(self):
        src=(ROOT/"pages3.py").read_text("utf8")
        self.assertIn('name="privacy_agree" value="yes" required',src)
        self.assertIn('href="/{L}/legal/privacy/"',src)
        self.assertIn('name="feedback"',src)

    def test_generated_feedback_all_locales(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                s=(ROOT/"cf"/"public"/lang/"how"/"index.html").read_text("utf8")
                m=re.search(r'<form\\b[^>]*name="feedback"[^>]*>[\\s\\S]*?</form>',s)
                self.assertIsNotNone(m,"feedback form missing")
                form=m.group(0)
                self.assertIn('name="privacy_agree" value="yes" required',form)
                self.assertIn(f'/{lang}/legal/privacy/',form)

if __name__=="__main__":unittest.main()
