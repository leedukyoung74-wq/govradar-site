"""Review-only quality pages must survive the canonical GOV RADAR rebuild."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SourceReviewPages(unittest.TestCase):
    def test_review_sources_and_coverage(self):
        b=(ROOT/'build.py').read_text(encoding='utf8')
        self.assertIn('for _review_name in ("quality", "review"):', b)
        self.assertIn('W("/" + _review_name + "/index.html"', b)
        self.assertNotIn('urls.append(("/quality/"',b)
        self.assertNotIn('urls.append(("/review/"',b)
        for page in ('quality','review'):
            html=(ROOT/'src'/'review_pages'/(page+'.html')).read_text(encoding='utf8')
            self.assertIn('noindex,nofollow',html)
            self.assertIn('<main',html)
        self.assertTrue((ROOT/'web'/'review-status.js').is_file())
        self.assertIn('/assets/review-status.js',(ROOT/'src/review_pages/review.html').read_text(encoding='utf8'))
if __name__=='__main__': unittest.main()
