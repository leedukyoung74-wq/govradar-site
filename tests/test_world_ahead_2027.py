"""Zero-network GOV RADAR World Ahead 2027 canonical-source regression checks."""
import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
EXTRA=ROOT/"cf"/"extra"
PAGE=EXTRA/"ko"/"world-ahead-2027"/"index.html"
RESEARCH=EXTRA/"ko"/"world-ahead-2027"/"world_ahead_2027_research.json"
SIG=EXTRA/"signals"

class WorldAhead2027(unittest.TestCase):
    def test_source_and_editorial_claims(self):
        html=PAGE.read_text(encoding="utf-8")
        data=json.loads(RESEARCH.read_text(encoding="utf-8"))
        self.assertEqual(10,len(data["items"]))
        self.assertEqual(10,len({x["id"] for x in data["items"]}))
        self.assertIn('id="dataset"',html)
        embedded=re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S)
        self.assertIsNotNone(embedded)
        self.assertEqual(10,len(json.loads(embedded.group(1))["items"]))
        self.assertIn("https://www.economist.com/syndication/permissions",html)
        self.assertIn("2027 표지는 미래 예고인가",html)
        self.assertNotIn('content="noindex,nofollow"',html)
        self.assertNotIn("sk-proj-",html)
        for row in data["items"]:
            self.assertTrue(row["sourceDetails"],row["id"])
            for source in row["sourceDetails"]:
                self.assertTrue(source["url"].startswith("https://"),source)

    def test_signals_ui_has_editorial_entry_point(self):
        ko=(SIG/"index.html").read_text(encoding="utf-8")
        self.assertEqual(1,ko.count("<!-- WMM_WORLD_AHEAD_2027_START -->"))
        self.assertEqual(1,ko.count("<!-- WMM_WORLD_AHEAD_2027_END -->"))
        self.assertIn('href="/ko/world-ahead-2027/"',ko)
        self.assertIn("공식 표지 보기",ko)

    def test_english_generation_remains_korean_free(self):
        proc=subprocess.run([sys.executable,"tools/signals_i18n.py"],cwd=ROOT,text=True,capture_output=True,timeout=35)
        self.assertEqual(0,proc.returncode,proc.stdout+"\n"+proc.stderr)
        en=(SIG/"en"/"index.html").read_text(encoding="utf-8")
        self.assertIn("The World Ahead 2027",en)
        self.assertIn("2027 special report",en)
        self.assertIn('href="/ko/world-ahead-2027/"',en)
        self.assertIsNone(re.search(r"[가-힣]",en))

if __name__=="__main__":
    unittest.main()
