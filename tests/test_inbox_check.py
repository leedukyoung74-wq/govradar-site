import json, sys, pathlib, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
import inbox_check as ic

def good():
    v = {"asof":"2026-11-21","summary":"요약","leader":"대통령","agenda":["과제"],"needs":["필요"],
         "biz":[{"title":"사업","fit":"high","why":"이유","target":"기관","basis":"근거"}],"watch":["일정"],
         "risk":{"level":"low"},"sources":[{"title":"a","url":"https://a.example"},{"title":"b","url":"https://b.example"}],
         "_change":"변경","_change_en":"change",
         "en":{"asof":"2026-11-21","summary":"s","leader":"l","agenda":["a"],"needs":["n"],"biz":[{"title":"t","why":"w","target":"t","basis":"b"}],"watch":["w"]}}
    tr = {L:{"KE":{"s":"s","l":"l","a":["a"],"n":["n"],"b":["b"],"w":["w"],"t":["t"]}} for L in ic.LANGS}
    return v, tr

class T(unittest.TestCase):
    def test_pass(self):
        v, tr = good(); self.assertEqual(ic.check_country("KE", v, tr, net=False), [])
    def test_hangul_in_en(self):
        v, tr = good(); v["en"]["summary"] = "한글"; self.assertIn("en 안에 한글이 있음", ic.check_country("KE", v, tr, net=False))
    def test_counts_and_banned_phone(self):
        v, tr = good(); v["agenda"].append("둘"); v["summary"] = "수주 보장 010-1234-5678"
        w = ic.check_country("KE", v, tr, net=False)
        self.assertTrue(any("agenda 개수" in x for x in w)); self.assertIn("금지어: 수주 보장", w); self.assertIn("휴대폰 번호 형태", w)
    def test_run_split(self):
        v, tr = good(); bad = json.loads(json.dumps(v)); bad["sources"] = []
        d = tempfile.mkdtemp(); o = tempfile.mkdtemp()
        tr2 = {L:{**tr[L], "TZ": tr[L]["KE"]} for L in tr}
        json.dump({"countries":{"KE":v,"TZ":bad},"tr":tr2,"tenders":[["KE","t","b","2026-12-01","https://x","World Bank","제목","발주처"],["TZ","t","b","2026-12-01","https://x","World Bank","제목","발주처"]]},
                  open(f"{d}/GPT_COUNTRY_20261123.json","w",encoding="utf-8"), ensure_ascii=False)
        r = ic.run(d, o, net=False)[0]
        self.assertEqual((r["pass"], r["fail"]), (1, 1))
        ready = json.load(open(f"{o}/GPT_COUNTRY_20261123.ready.json", encoding="utf-8"))
        self.assertEqual(list(ready["d1"]), ["KE"]); self.assertEqual(len(ready["tenders"]), 1)
        self.assertEqual(ic.run(d, o, net=False), [])  # 이미 처리한 파일은 다시 안 봄
    def test_bad_json(self):
        d = tempfile.mkdtemp(); o = tempfile.mkdtemp(); open(f"{d}/GPT_COUNTRY_x.json","w").write("{")
        self.assertIn("JSON 읽기 실패", ic.run(d, o, net=False)[0]["error"])
if __name__ == "__main__": unittest.main()
