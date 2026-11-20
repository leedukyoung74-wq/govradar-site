"""Read-only unit tests for source-generated tender disclosure wording."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class TenderDisclosureSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = (ROOT / "build.py").read_text(encoding="utf-8")
        cls.pages = (ROOT / "pages3.py").read_text(encoding="utf-8")

    def test_source_python_syntax(self):
        ast.parse(self.build, filename="build.py")
        ast.parse(self.pages, filename="pages3.py")

    def test_tender_page_disclaims_live_status(self):
        self.assertIn("입찰 일정 목록 — 실제 접수 상태 재확인", self.build)
        self.assertIn("Tender listings by deadline — confirm live status", self.build)
        self.assertIn("발주기관 공식 원문에서 마감 시간대·연장·취소·접수 상태를 확인하세요", self.build)
        self.assertIn("Confirm the issuing authority's original notice, deadline timezone, amendments and cancellation", self.build)

    def test_rendered_links_are_not_misrepresented_as_official(self):
        self.assertIn('"외부 공고 링크" if ko else "External listing"', self.pages)
        self.assertNotIn('{"원문" if ko else "Notice"} ↗</a>\' if str(x["t"].get("url", "")).startswith("https://")', self.pages)
        self.assertIn('rel="noopener nofollow"', self.pages)

    def test_existing_date_and_feed_safety_kept(self):
        self.assertIn('def all_tenders(DATA, BY, today):', self.pages)
        self.assertIn('if not re.match(r"\\d{4}-\\d{2}-\\d{2}$", dl) or dl < today: continue', self.pages)
        self.assertIn('GRDL.info(s.dataset.at,s.dataset.dl)', self.pages)
        self.assertIn('if(I.state==="closed")', self.pages)

if __name__ == "__main__":
    unittest.main()
