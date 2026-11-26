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
    def test_deadline_filter_includes_future_but_not_expired(self):
        if not shutil.which("node"): self.skipTest("node missing")
        js=JS.read_text("utf-8")
        start=js.index("function ok(q){")
        end=js.index("Promise.all(",start)
        logic=js[start:end]
        runner=logic+'''
if(!ok({deadline:"2099-12-01",source:"SAM.gov (US)"}))process.exit(11);
if(ok({deadline:"2000-01-01",source:"SAM.gov (US)"}))process.exit(12);
if(ok({deadline_at:"2000-01-01T15:00:00-04:00",deadline:"2000-01-01"}))process.exit(13);
if(!ok({deadline_at:"2099-12-01T15:00:00-04:00",deadline:"2099-12-01"}))process.exit(14);
if(ok({deadline:"2099-12-01",stale:true}))process.exit(15);
'''
        p=subprocess.run(["node","-e",runner],capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_stale_snapshot_guard(self):
        if not shutil.which("node"): self.skipTest("node missing")
        js=JS.read_text("utf-8")
        start=js.index("function recentStamp(raw){")
        end=js.index("Promise.all(",start)
        logic=js[start:end]
        runner=logic+'''
const now=Date.now();
if(!recentStamp(new Date(now-1000).toISOString()))process.exit(21);
if(recentStamp(new Date(now-37*60*60*1000).toISOString()))process.exit(22);
if(recentStamp(new Date(now+10*60*1000).toISOString()))process.exit(23);
if(recentStamp("not-a-date"))process.exit(24);
'''
        p=subprocess.run(["node","-e",runner],capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_stale_counts_not_presented_as_live(self):
        js=JS.read_text("utf-8")
        self.assertIn("feedFresh&&recentStamp(st.last_success)",js)
        self.assertIn('st.state==="SUCCESS"',js)
        self.assertIn("current?arr.length",js)
        self.assertIn("feedFresh&&recentStamp((states",js)
        self.assertIn("갱신 지연",js)

    def test_valid_javascript_syntax(self):
        if not shutil.which("node"): self.skipTest("node missing")
        result=subprocess.run(["node","--check",str(JS)],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__=="__main__":unittest.main()
