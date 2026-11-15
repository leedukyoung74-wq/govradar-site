"""tr/<L>_*.tsv (index<TAB>translation, index into src_index.json; 'K:English<TAB>translation' for extra keys) -> tr/<L>.json"""
import json, glob, os, sys
H = os.path.dirname(os.path.abspath(__file__)); src = json.load(open(os.path.join(H, "src_index.json"), encoding="utf-8"))
for L in sys.argv[1:]:
    d = {}
    for f in sorted(glob.glob(os.path.join(H, f"{L}_*.tsv"))):
        for ln in open(f, encoding="utf-8"):
            ln = ln.rstrip("\n")
            if not ln.strip(): continue
            k, t = ln.split("\t", 1)
            d[k[2:] if k.startswith("K:") else src[int(k)]] = t
    json.dump(d, open(os.path.join(H, f"{L}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0); print(L, len(d))
