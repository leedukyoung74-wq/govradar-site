"""Verify staging never mutates existing Cloudflare live site files."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("live_overlay",ROOT/"tools/stage_live_overlay.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class LiveOverlayTests(unittest.TestCase):
    def setup_trees(self,td):
        live=td/"live";new=td/"new";out=td/"out"
        for rel in mod.PROTECTED:
            p=live/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("LIVE PRIVATE CORE "+rel)
        for rel in mod.ALLOW:
            p=new/rel;p.parent.mkdir(parents=True,exist_ok=True)
            if rel.endswith("/prepare/index.html"): text="new 106.4L"
            elif rel.endswith("/resilience/index.html"): text="<html><meta content='noindex, nofollow'>wmm-resilience</html>"
            elif rel.endswith("primary-guidance-reviewed.json"): text=json.dumps({"countries":[{"iso":x} for x in ("KR","JP","US")]})
            elif rel.endswith("country-profiles.json"): text=json.dumps([{"iso":str(i),"local_official_guidance_verified":False,"retail_availability_verified":False,"shelf_life_verified":False} for i in range(193)])
            else: text="new app asset"
            p.write_text(text,encoding="utf-8")
        (live/"ko/prepare/index.html").parent.mkdir(parents=True,exist_ok=True)
        (live/"ko/prepare/index.html").write_text("84L old")
        (live/"hazards/safe.html").parent.mkdir(parents=True,exist_ok=True)
        (live/"hazards/safe.html").write_text("existing hazard feed untouched")
        return live,new,out
    def test_stages_only_allowlist(self):
        with TemporaryDirectory() as d:
            live,new,out=self.setup_trees(Path(d))
            original=(live/"ko/prepare/index.html").read_bytes()
            summary=mod.stage(new,live,out)
            self.assertFalse(summary["deployable"])
            self.assertFalse(summary["publication_performed"])
            self.assertEqual(summary["changed_or_added_files"],18)
            self.assertEqual((live/"ko/prepare/index.html").read_bytes(),original)
            self.assertIn("106.4L",(out/"ko/prepare/index.html").read_text())
            self.assertEqual((out/"hazards/safe.html").read_text(),"existing hazard feed untouched")
            self.assertEqual((out/"assets/auth.js").read_text(),(live/"assets/auth.js").read_text())
            self.assertFalse((out/"quality/index.html").exists())
            self.assertFalse((out/"review/index.html").exists())
    def test_rejects_stale_generated_water_before_copying(self):
        with TemporaryDirectory() as d:
            live,new,out=self.setup_trees(Path(d))
            (new/"ko/prepare/index.html").write_text("84L old")
            with self.assertRaisesRegex(RuntimeError,"water baseline"):
                mod.stage(new,live,out)
            self.assertFalse(out.exists())
    def test_requires_protected_live_paths(self):
        with TemporaryDirectory() as d:
            live,new,out=self.setup_trees(Path(d))
            (live/"assets/auth.js").unlink()
            with self.assertRaisesRegex(RuntimeError,"protected live file"):
                mod.stage(new,live,out)
            self.assertFalse(out.exists())

if __name__=="__main__":unittest.main()
