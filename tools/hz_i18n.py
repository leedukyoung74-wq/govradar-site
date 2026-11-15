#!/usr/bin/env python3
"""Write cf/extra/hazards/tr-{L}.js (window.HZTR: English text -> L) for es, fr, ar, vi, id from tools/tr/hz_{L}.tsv
plus the alerts dictionary (the hazards page shows the English alerts strip)."""
import os, json
H = os.path.dirname(os.path.abspath(__file__)); TR = os.path.join(H, "tr")
src = json.load(open(os.path.join(TR, "hz_src_index.json"), encoding="utf-8"))
for L in ["es", "fr", "ar", "vi", "id"]:
    d = {}
    p = os.path.join(TR, L + ".json")
    if os.path.exists(p): d.update(json.load(open(p, encoding="utf-8")))
    for ln in open(os.path.join(TR, f"hz_{L}.tsv"), encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln.strip(): continue
        k, t = ln.split("\t", 1); d[k[2:] if k.startswith("K:") else src[int(k)]] = t
    open(os.path.join(H, "..", "cf", "extra", "hazards", f"tr-{L}.js"), "w", encoding="utf-8").write("window.HZTR=" + json.dumps(d, ensure_ascii=False) + ";")
    print("[hz]", L, len(d))
