import json, pathlib, shutil, subprocess, sys, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import inbox_check as ic

class RegionDaily(unittest.TestCase):
    def test_region_code_accepted_country_rule_kept(self):
        self.assertTrue(ic.ISO.match("PH-BARMM")); self.assertTrue(ic.ISO.match("KE"))
        self.assertFalse(ic.ISO.match("ph-barmm")); self.assertFalse(ic.ISO.match("KEN"))
    def test_region_import_goes_to_regions_and_keeps_status(self):
        t = pathlib.Path(tempfile.mkdtemp())
        (t / "tools").mkdir(); (t / "export" / "regions").mkdir(parents=True); (t / "export" / "countries").mkdir()
        shutil.copy(ROOT / "tools" / "country_import.py", t / "tools")
        (t / "export" / "regions" / "PH-BARMM.json").write_text(json.dumps({"parent": "PH", "type": "auto", "status": {"capital": "Cotabato"}, "agenda": ["old"]}), "utf-8")
        src = t / "in.json"
        src.write_text(json.dumps({"PH-BARMM": {"summary": "새 요약", "agenda": ["새 과제"], "risk": {"level": "medium"}, "_change": "변경", "_change_en": "changed"}}, ensure_ascii=False), "utf-8")
        subprocess.run([sys.executable, str(t / "tools" / "country_import.py"), str(src)], check=True, capture_output=True)
        d = json.loads((t / "export" / "regions" / "PH-BARMM.json").read_text("utf-8"))
        self.assertEqual((d["parent"], d["type"], d["status"]["capital"]), ("PH", "auto", "Cotabato"))
        self.assertEqual(d["agenda"], ["새 과제"]); self.assertFalse((t / "export" / "countries" / "PH-BARMM.json").exists())

if __name__ == "__main__": unittest.main()
