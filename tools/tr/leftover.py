import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import i18n_extract as X, i18n_want as W
X.want = W.want
src = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src_index.json"), encoding="utf-8")))
for p in sys.argv[1:]:
    st = [x for x in X.strings(open(p, encoding="utf-8").read()) if x in src]
    print(p, len(st), st)
