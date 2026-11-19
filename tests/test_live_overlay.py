"""Verify staging protects existing Cloudflare live routes and surgical safety corrections."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("live_overlay",ROOT/"tools/stage_live_overlay.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

OLD_WATER_NOTE={
    "ko":"물은 이 표에서 1인 하루 3L로 잡았습니다.",
    "en":"Water here is 3 L per person per day.",
    "es":"Aquí el agua se calcula en 3 L por persona al día.",
    "fr":"L'eau est comptée ici à 3 L par personne et par jour.",
    "ar":"المياه هنا 3 لترات للشخص يوميًا.",
    "vi":"Ở đây tính 3 L nước mỗi người mỗi ngày.",
    "id":"Air di sini dihitung 3 L per orang per hari.",
}

class LiveOverlayTests(unittest.TestCase):
    def setup_trees(self,td):
        live=td/"live";new=td/"new";out=td/"out"
        for rel in mod.PROTECTED:
            p=live/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("LIVE PRIVATE CORE "+rel,encoding="utf-8")
        for rel in mod.ALLOW:
            p=new/rel;p.parent.mkdir(parents=True,exist_ok=True)
            if rel.endswith("/prepare/index.html"): value="<html>new 106.4L</html>"
            elif rel.endswith("/resilience/index.html"): value="<html><meta content='noindex, nofollow'>wmm-resilience</html>"
            elif rel.endswith("primary-guidance-reviewed.json"): value=json.dumps({"countries":[{"iso":x} for x in ("KR","JP","US")]})
            elif rel.endswith("country-profiles.json"):
                value=json.dumps([{"iso":str(i),"local_official_guidance_verified":False,
                    "retail_availability_verified":False,"shelf_life_verified":False} for i in range(193)])
            else: value="new app asset"
            p.write_text(value,encoding="utf-8")
        for lang,spec in mod.PREPARE_PATCHES.items():
            page=live/lang/"prepare/index.html"
            page.parent.mkdir(parents=True,exist_ok=True)
            page.write_text(
                '<html><main><div class="future-live-feature">KEEP THIS EXACTLY</div>'
                '<table><tr><td><b>84L 이상</b></td></tr></table>'
                '<h2 id="s5">Safety</h2><ul><li>'+OLD_WATER_NOTE[lang]+'</li></ul>'
                '<p>'+spec["oldProduct"]+'</p>'
                '<p>'+spec["oldStove"]+'</p>'
                '<li>'+spec["oldOutage"]+'</li>'
                '</main></html>',encoding="utf-8")
        p=live/"hazards/safe.html";p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text("existing hazard feed untouched",encoding="utf-8")
        return live,new,out

    def test_stages_only_allowlist_preserving_live_pages(self):
        with TemporaryDirectory() as tmp:
            live,new,out=self.setup_trees(Path(tmp))
            original={lang:(live/lang/"prepare/index.html").read_bytes() for lang in mod.LANGS}
            summary=mod.stage(new,live,out)
            self.assertFalse(summary["deployable"])
            self.assertFalse(summary["publication_performed"])
            self.assertEqual(summary["changed_or_added_files"],18)
            for lang in mod.LANGS:
                self.assertEqual((live/lang/"prepare/index.html").read_bytes(),original[lang])
                reviewed=(out/lang/"prepare/index.html").read_text(encoding="utf-8")
                self.assertIn("KEEP THIS EXACTLY",reviewed)
                self.assertIn("106.4L",reviewed)
                self.assertNotIn("84L",reviewed)
                self.assertIn(mod.PREPARE_PATCHES[lang]["water"],reviewed)
                self.assertIn(mod.PREPARE_PATCHES[lang]["newStove"],reviewed)
                self.assertIn(mod.PREPARE_PATCHES[lang]["newOutage"],reviewed)
                self.assertNotIn(mod.PREPARE_PATCHES[lang]["oldStove"],reviewed)
                self.assertNotIn(mod.PREPARE_PATCHES[lang]["oldOutage"],reviewed)
            self.assertEqual((out/"hazards/safe.html").read_text(),"existing hazard feed untouched")
            self.assertEqual((out/"assets/auth.js").read_text(),(live/"assets/auth.js").read_text())
            self.assertFalse((out/"quality/index.html").exists())
            self.assertFalse((out/"review/index.html").exists())

    def test_rejects_stale_generated_water_before_copying(self):
        with TemporaryDirectory() as tmp:
            live,new,out=self.setup_trees(Path(tmp))
            (new/"ko/prepare/index.html").write_text("84L old")
            with self.assertRaisesRegex(RuntimeError,"water baseline"):
                mod.stage(new,live,out)
            self.assertFalse(out.exists())

    def test_rejects_ambiguous_existing_safety_text(self):
        with TemporaryDirectory() as tmp:
            live,new,out=self.setup_trees(Path(tmp))
            target=live/"ko/prepare/index.html"
            target.write_text(target.read_text()+" "+mod.PREPARE_PATCHES["ko"]["oldStove"],encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"ambiguous/missing Stove"):
                mod.stage(new,live,out)

    def test_requires_protected_live_paths(self):
        with TemporaryDirectory() as tmp:
            live,new,out=self.setup_trees(Path(tmp))
            (live/"assets/auth.js").unlink()
            with self.assertRaisesRegex(RuntimeError,"protected live file"):
                mod.stage(new,live,out)
            self.assertFalse(out.exists())

if __name__=="__main__": unittest.main()
