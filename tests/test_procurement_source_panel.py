"""Offline quality checks for the public DAPA/SAM status panel."""
import pathlib
import shutil
import subprocess
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
JS=ROOT/"cf"/"extra"/"assets"/"official-procurement-status.js"
GEN=ROOT/"tools"/"home_clean.py"

class OfficialSourcePanelTest(unittest.TestCase):
    def test_generator_loads_public_status_panel(self):
        body=GEN.read_text("utf-8")
        self.assertIn('official-procurement-status.js',body)
        self.assertIn('s = s.replace("</body>"',body)
    def test_no_secret_or_unsafe_data_writes(self):
        text=JS.read_text("utf-8")
        self.assertIn('data/feeds/',text)
        self.assertIn('sources_status.json',text)
        self.assertIn('tenders.json',text)
        self.assertIn('data.items.filter',text)
        self.assertIn('q.source==="SAM.gov (US)"',text)
        self.assertIn('q.source===name',text)
        self.assertIn('q.stale',text)
        self.assertNotIn('api_key=',text)
        self.assertNotIn('DAPA_KEY',text)
        self.assertNotIn('SAM_KEY',text)
        self.assertNotIn('innerHTML=q.',text)
    def test_seven_languages_and_mobile_layout(self):
        body=JS.read_text("utf-8")
        for language in ('ko:', 'en:', 'es:', 'fr:', 'ar:', 'vi:', 'id:'):
            self.assertIn(language,body)
        self.assertIn('grid-template-columns:repeat(auto-fit',body)
    def test_valid_javascript_syntax(self):
        if not shutil.which("node"): self.skipTest("node missing")
        result=subprocess.run(["node","--check",str(JS)],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__=="__main__":unittest.main()
