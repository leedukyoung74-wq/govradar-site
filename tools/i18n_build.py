#!/usr/bin/env python3
"""Make /cyber/{L}/ and /alerts/{L}/ for es, fr, ar, vi, id from the English pages, and translate leftover English on
some dist/{L}/ pages, using tools/tr/{L}.json (English text -> translation). Languages without a dictionary get a
redirect stub to the English page."""
import os, re, json, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import i18n_extract as X
ROOT = os.path.join(HERE, "..")
LANGS = ["es", "fr", "ar", "vi", "id"]
STAND = ["cyber", "alerts"]
DIST_PAGES = {"ar": ["conflict", "pricing", "request", "angola", "mdb"]}  # pages fully covered by the dictionary
RTL_CSS = '<style>html[dir=rtl] body{text-align:right}html[dir=rtl] .hlstrip,html[dir=rtl] .jump,html[dir=rtl] .flt{direction:rtl}html[dir=rtl] svg,html[dir=rtl] canvas,html[dir=rtl] .map,html[dir=rtl] #map{direction:ltr}</style>'
def load(L):
    p = os.path.join(HERE, "tr", L + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
def relink(s, L):
    s = s.replace("/cyber/en/", f"/cyber/{L}/").replace("/alerts/en/", f"/alerts/{L}/").replace("/hazards/?l=en", f"/hazards/?l={L}")
    s = re.sub(r'(href=")/en/', rf'\1/{L}/', s).replace('data-l="en"', f'data-l="{L}"')
    return s
def subnav(s, tr):
    def f(m):
        try: a = json.loads(m.group(1))
        except Exception: return m.group(0)
        return "GVH_SUB=function(){return " + json.dumps([[k, tr.get(v, v)] for k, v in a], ensure_ascii=False) + "};"
    return re.sub(r'GVH_SUB=function\(\)\{return (\[.*?\])\};', f, s, count=1)
def stub(dst, url):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={url}"><link rel="canonical" href="https://radar.wmm-hoa.com{url}"><script>location.replace("{url}"+location.search+location.hash)</script>')
def main():
    for L in LANGS:
        tr = load(L)
        for p in STAND:
            src = os.path.join(ROOT, "cf", "extra", p, "en", "index.html"); dst = os.path.join(ROOT, "cf", "extra", p, L, "index.html")
            if not tr: stub(dst, f"/{p}/en/"); continue
            s = subnav(X.apply(open(src, encoding="utf-8").read(), tr), tr)
            s = relink(s, L)
            s = re.sub(r'<html lang="en"[^>]*>', f'<html lang="{L}"' + (' dir="rtl"' if L == "ar" else "") + ">", s, count=1)
            if L == "ar": s = s.replace("</head>", RTL_CSS + "</head>", 1)
            os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, "w", encoding="utf-8").write(s)
        if tr:
            for p in DIST_PAGES.get(L, []):
                f = os.path.join(ROOT, "dist", L, p, "index.html")
                if os.path.exists(f):
                    s = open(f, encoding="utf-8").read()
                    if "http-equiv=\"refresh\"" in s: continue
                    open(f, "w", encoding="utf-8").write(X.apply(s, tr).replace("<head>", '<head><meta name="gv-tr" content="1">', 1))
        print("[i18n]", L, "dictionary" if tr else "stub", len(tr or {}))
if __name__ == "__main__": main()
