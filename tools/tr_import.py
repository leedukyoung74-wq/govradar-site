"""scratch 번역 묶음(JSON: {ISO:{s,l,a,n,b[,w,t]}} — w: biz why list, t: biz target list) -> src/i18n_data/{L}/{ISO}.json"""
import json, sys, pathlib
L, f = sys.argv[1], sys.argv[2]
out = pathlib.Path(__file__).resolve().parent.parent / "src" / "i18n_data" / L; out.mkdir(parents=True, exist_ok=True)
for iso, v in json.load(open(f, encoding="utf-8")).items():
    d = {"summary": v["s"], "leader": v["l"], "agenda": v["a"], "needs": v["n"], "biz": [dict({"title": t}, **({"why": v["w"][i]} if i < len(v.get("w") or []) and v["w"][i] else {}), **({"target": v["t"][i]} if i < len(v.get("t") or []) and v["t"][i] else {})) for i, t in enumerate(v["b"])]}
    (out / f"{iso}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    print(L, iso, "ok")
