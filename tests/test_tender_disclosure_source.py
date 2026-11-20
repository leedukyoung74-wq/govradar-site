"""Offline source tests: rendered tender disclaimers and existing expiry guard."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LANGS = ("ko", "en", "es", "fr", "ar", "vi", "id")

class TenderDisclosureSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = (ROOT / "build.py").read_text(encoding="utf-8")
        cls.pages = (ROOT / "pages3.py").read_text(encoding="utf-8")
        cls.build_ast = ast.parse(cls.build, filename="build.py")
        cls.pages_ast = ast.parse(cls.pages, filename="pages3.py")
        entries = [
            node.value for node in cls.pages_ast.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "TENDER_DISCLOSURE"
                    for target in node.targets)
        ]
        cls.labels = ast.literal_eval(entries[0]) if len(entries) == 1 else None

    def test_source_python_syntax(self):
        self.assertIsNotNone(self.build_ast)
        self.assertIsNotNone(self.pages_ast)

    def test_tender_page_disclaims_live_status(self):
        self.assertIn('P3.TENDER_DISCLOSURE.get(L, P3.TENDER_DISCLOSURE["en"])["heading"]', self.build)
        self.assertIn('P3.TENDER_DISCLOSURE.get(L, P3.TENDER_DISCLOSURE["en"])["warning"]', self.build)
        self.assertIn('TENDER_DISCLOSURE.get(L, TENDER_DISCLOSURE["en"])["external"]', self.pages)
        self.assertIn("입찰 일정 목록 — 실제 접수 상태 재확인", self.pages)
        self.assertIn("Tender listings by deadline — confirm live status", self.pages)

    def test_all_seven_locales_have_complete_disclosures(self):
        self.assertEqual(set(self.labels), set(LANGS))
        for lang in LANGS:
            with self.subTest(lang=lang):
                self.assertEqual(set(self.labels[lang]), {"heading", "warning", "external"})
                for item in self.labels[lang].values():
                    self.assertIsInstance(item, str)
                    self.assertGreaterEqual(len(item.strip()), 5)
                self.assertNotIn("Open tenders by deadline", self.labels[lang]["heading"])

    def test_external_links_are_not_automatically_official(self):
        self.assertIn('rel="noopener nofollow"', self.pages)
        self.assertIn("발주기관 공식 원문", self.labels["ko"]["warning"])
        self.assertIn("issuing authority", self.labels["en"]["warning"])
        self.assertNotIn('{"원문" if ko else "Notice"} ↗</a>\' if str(x["t"].get("url", "")).startswith("https://")', self.pages)

    def test_existing_date_and_feed_safety_kept(self):
        self.assertIn('def all_tenders(DATA, BY, today):', self.pages)
        self.assertIn('if not re.match(r"\\d{4}-\\d{2}-\\d{2}$", dl) or dl < today: continue', self.pages)
        self.assertIn('GRDL.info(s.dataset.at,s.dataset.dl)', self.pages)
        self.assertIn('if(I.state==="closed")', self.pages)

if __name__ == "__main__":
    unittest.main()


class SecondarySourceLabelTest(__import__("unittest").TestCase):
    def test_aggregator_and_press_are_secondary(self):
        import importlib, sys, pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
        P3 = importlib.import_module("pages3")
        self.assertTrue(P3.is_secondary({"url": "https://www.mangofetch.com/x"}))
        self.assertTrue(P3.is_secondary({"url": "https://ted.europa.eu/x", "source": "EU TED (TenderMetric에서 확인)"}))
        self.assertFalse(P3.is_secondary({"url": "https://projects.worldbank.org/x", "source": "World Bank"}))
        self.assertFalse(P3.is_secondary({"url": "https://www.etenders.gov.ie/x"}))
