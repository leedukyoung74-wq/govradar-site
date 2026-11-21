import json, sys, pathlib, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
import gpt_daily_split as gs
import inbox_check as ic

def sample():
    v = {"asof":"2026-11-22","summary":"요약","leader":"대통령","agenda":["과제"],"needs":["필요"],
         "biz":[{"title":"사업","fit":"high","why":"이유","target":"기관","basis":"근거"}],"watch":["일정"],
         "risk":{"level":"low"},"sources":[{"title":"a","url":"https://a.example"},{"title":"b","url":"https://b.example"}],
         "_change":"변경","_change_en":"change",
         "en":{"asof":"2026-11-22","summary":"s","leader":"l","agenda":["a"],"needs":["n"],"biz":[{"title":"t","why":"w","target":"t","basis":"b"}],"watch":["w"]}}
    tr = {L:{"KE":{"s":"s","l":"l","a":["a"],"n":["n"],"b":["b"],"w":["w"],"t":["t"]}} for L in gs.LANGS}
    return {"kind":"wmm_govradar_daily","date":"2026-11-22","by":"ChatGPT","schema_version":2,
            "country":{"kind":"country","date":"2026-11-22","by":"ChatGPT","countries":{"KE":v},"tr":tr,"tenders":[]},
            "official_directory_updates":{"sovereign":{"KE":{"news_media":[]}},"territories":{}},
            "hazard":{"kind":"hazard","date":"2026-11-22","summary_ko":"요약","summary_en":"s","hotspots":[],"disasters":[]},
            "cyber":{"source_advisories":[]},"marketing":{"items":[]},"notes":{"countries_researched":["KE"]}}

def doc(d): return "머리말\n===JSON START===\n" + json.dumps(d, ensure_ascii=False) + "\n===JSON END===\n꼬리"

class T(unittest.TestCase):
    def test_split_then_inbox_check_passes(self):
        o = tempfile.mkdtemp(); r = gs.split(doc(sample()), o)
        self.assertEqual(r["status"], "SPLIT_OK"); self.assertEqual(r["countries"], 1); self.assertTrue(r["hazard"]); self.assertEqual(r["directory"], 1)
        rep = ic.run(pathlib.Path(o) / "country", pathlib.Path(o) / "qa", net=False)[0]
        self.assertEqual((rep["pass"], rep["fail"]), (1, 0))
    def test_empty_is_nodata(self):
        self.assertEqual(gs.split("", tempfile.mkdtemp())["status"], "NODATA")
        d = sample(); d["country"]["countries"] = {}; d["hazard"] = {}; d["official_directory_updates"] = {}
        self.assertEqual(gs.split(doc(d), tempfile.mkdtemp())["status"], "NODATA")
    def test_duplicate_blocked(self):
        o = tempfile.mkdtemp(); seen = pathlib.Path(o) / "seen.json"
        self.assertEqual(gs.split(doc(sample()), o, seen)["status"], "SPLIT_OK")
        self.assertEqual(gs.split(doc(sample()), tempfile.mkdtemp(), seen)["status"], "DUPLICATE")
    def test_schema_fail(self):
        self.assertEqual(gs.split("===JSON START===\n{bad\n===JSON END===", tempfile.mkdtemp())["status"], "SCHEMA_FAIL")
        d = sample(); d["kind"] = "x"; d["date"] = "22-11-2026"
        r = gs.split(doc(d), tempfile.mkdtemp()); self.assertEqual(r["status"], "SCHEMA_FAIL"); self.assertEqual(len(r["errors"]), 2)

if __name__ == "__main__": unittest.main()
