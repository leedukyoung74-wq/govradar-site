#!/usr/bin/env python3
"""Build /signals/{lang}/ for en, es, fr, ar, vi, id from the Korean master cf/extra/signals/index.html.
UI text is translated per language; content (covers, Simpsons claims, seven outlooks) is English for every
non-Korean language. Arabic gets dir=rtl, with English content blocks laid out by their own direction."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "sig_i18n"))
import en_main, en_p7, en_p7d
from ui import UI, COUNT
SIG = os.path.join(ROOT, "cf", "extra", "signals")
LANGS = ["en"]  # signals content exists in Korean and English only
REDIRECT = ["es", "fr", "ar", "vi", "id"]
HANGUL = re.compile(r"[가-힣]")

def jsobj(path):
    s = open(path, encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))

def build_p7():
    ko = jsobj(os.path.join(SIG, "p7.js"))
    P = []
    for p in ko["P"]:
        e = en_p7.P[p["i"]]
        q = dict(p); q.update(e); P.append(q)
    S = {}
    for k, s in ko["S"].items():
        q = dict(s); q.update(en_p7.S.get(k, {})); S[k] = q
    # TL: the scheduled task adds Korean rows to p7.js; keep English rows, append any new Korean year rows untranslated-free
    TL = en_p7.TL
    return {"P": P, "S": S, "TL": TL, "MX": en_p7.MX}

def build_p7d():
    ko = jsobj(os.path.join(SIG, "p7d.js"))
    out = dict(ko)
    for k in ("D", "KR", "KRNOTE", "TH", "AGREE", "FUT", "FUTSRC", "PREP", "AVOID", "PREPSRC", "LATEST", "DOS"):
        if hasattr(en_p7d, k): out[k] = getattr(en_p7d, k)
    return out

def data_block(ko_html):
    """English replacements for var CV / ECO / SIMP / EXTRA_SIMP / SRC."""
    m = re.search(r"var CV=(\{.*?\});", ko_html); cv = json.loads(m.group(1))
    for y, v in cv.items():
        t = en_main.CV[y]; v[0], v[1] = t[0], t[1]
    eco = []
    for d in en_main.ECO:
        eco.append(d)
    return cv, {d["y"]: d for d in en_main.ECO}

def esc_js(s):  # for text that lands inside a single-quoted JS string
    return s.replace("\\", "\\\\").replace("'", "\\'")

def main():
    ko = open(os.path.join(SIG, "index.html"), encoding="utf-8").read()
    p7, p7d = build_p7(), build_p7d()
    open(os.path.join(SIG, "p7.en.js"), "w", encoding="utf-8").write("window.P7=" + json.dumps(p7, ensure_ascii=False) + ";\n")
    open(os.path.join(SIG, "p7d.en.js"), "w", encoding="utf-8").write("window.P7D=" + json.dumps(p7d, ensure_ascii=False) + ";\n")
    cv, ecomap = data_block(ko)
    bad = []
    for L in LANGS:
        h = ko
        # ---- data (English for every non-Korean language)
        h = re.sub(r"var CV=\{.*?\};", lambda m: "var CV=" + json.dumps(cv, ensure_ascii=False) + ";", h, count=1)
        def eco_line(m):
            line = m.group(0)
            y = int(re.search(r"\{y:(\d{4})", line).group(1)); e = ecomap[y]
            def put(key, val, line):
                js = json.dumps(val, ensure_ascii=False)
                pat = re.compile(r"(\b%s:)(\"(?:[^\"\\]|\\.)*\"|\[(?:\"(?:[^\"\\]|\\.)*\",?)*\])" % key)
                return pat.sub(lambda mm: mm.group(1) + js, line, count=1)
            for k in ("of", "sub", "el", "it", "rl", "vt"):
                if k in e: line = put(k, e[k], line)
            return line
        h = re.sub(r"^\{y:\d{4},(?:of|t):.*$", eco_line, h, flags=re.M)
        def simp_line(m):
            line = m.group(0); y = int(re.search(r"\{y:(\d{4})", line).group(1))
            body = line[line.index("c:") + 2:]
            tail = body[body.rindex("]") + 1:]
            arr = json.loads(body[:body.rindex("]") + 1])
            for i, c in enumerate(arr):
                c[0], c[1] = en_main.SIMP[y][i]
                for s in c[3]: s[0] = en_main.SRCNAME.get(s[0], s[0])
            return line[:line.index("c:") + 2] + json.dumps(arr, ensure_ascii=False) + tail
        h = re.sub(r"^\{y:\d{4},c:.*$", simp_line, h, flags=re.M)
        U = UI[L]
        ex = en_main.EXTRA_SIMP.replace("@MID@", U["◐ 지나고 나서 맞춘 해석"]).replace("@NO@", U["○ 근거 확인 안 됨"]).replace("@SRC@", U["'<p class=\"src\">출처 · '"].strip("'").replace('<p class="src">', ""))
        ex = ex.replace("Other 'they predicted it' claims that keep circulating", U["@extra_h"]).replace("Claims about events before 2015, or with no year.", U["@extra_p"])
        h = re.sub(r"var EXTRA_SIMP=\".*?\";\n", lambda m: "var EXTRA_SIMP=" + json.dumps(ex, ensure_ascii=False) + ";\n", h, count=1, flags=re.S)
        h = re.sub(r"var SRC=\[.*?\];", lambda m: "var SRC=" + json.dumps(en_main.SRC, ensure_ascii=False) + ";", h, count=1)
        for a, b in en_main.SRCNAME.items():
            h = h.replace('"%s"' % a, '"%s"' % b)
        h = re.sub(r"^var KW=.*$", lambda m: KW_EN, h, count=1, flags=re.M)
        # ---- UI strings, longest first
        keys = sorted([k for k in U if not k.startswith("@")], key=len, reverse=True)
        for k in keys:
            v = U[k]
            h = h.replace(k, v)
        h = re.sub(r"최신 업데이트 \(\d{4}년 \d+월 \d+일 기준\)", U["@latest"], h)
        h = h.replace("발언 '+L.length+'건 · 일치 '", COUNT[L][0]).replace("' · 부분 '", COUNT[L][1]).replace("' · 불일치 '", COUNT[L][2]).replace("' · 미래 '", COUNT[L][3])
        h = h.replace('<a href="/hazards/">', '<a href="/hazards/?l=%s">' % L)
        # ---- page shell
        h = h.replace('<html lang="ko">', '<html lang="%s"%s>' % (L, ' dir="rtl"' if L == "ar" else ""), 1)
        h = h.replace('data-l="ko" data-g="world" data-a="signals"', 'data-l="%s" data-g="world" data-a="signals"' % L, 1)
        h = h.replace('<script src="/signals/p7.js"></script>', '<script src="/signals/p7.en.js"></script>').replace('<script src="/signals/p7d.js"></script>', '<script src="/signals/p7d.en.js"></script>')
        h = h.replace("</style>", RTL_CSS + "</style>", 1) if L == "ar" else h
        left = sorted(set(HANGUL.findall(h)))
        if left:
            lines = [l[:160] for l in h.split("\n") if HANGUL.search(l)]
            bad.append((L, lines[:8]))
        os.makedirs(os.path.join(SIG, L), exist_ok=True)
        open(os.path.join(SIG, L, "index.html"), "w", encoding="utf-8").write(h)
    for L in REDIRECT:  # no content in these languages: send to the English page
        os.makedirs(os.path.join(SIG, L), exist_ok=True)
        open(os.path.join(SIG, L, "index.html"), "w", encoding="utf-8").write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/signals/en/"><link rel="canonical" href="https://radar.wmm-hoa.com/signals/en/"><script>location.replace("/signals/en/"+location.hash)</script><a href="/signals/en/">English</a>')
    if bad:
        for L, lines in bad:
            print("[signals_i18n] Korean text left in", L, *lines, sep="\n  ")
        sys.exit(1)
    print("[signals_i18n] built", ", ".join(LANGS))

KW_EN = r'var KW=[["fake",/edited|fake|no such|doctored|stitched|collage/i],["war",/\bwar|invasion|invade|nuclear|missile|tank|weapon|conflict|cannon|north korea|capitol|explosion|beirut|military/i],["health",/vaccine|syringe|covid|virus|pandemic|plague|pill|zika|ebola|medic|psychedelic|blood|epidemic/i],["vote",/election|vote|ballot|impeach|took office|midterm|arrest|indict|president/i],["person",/trump|biden|\bxi\b|putin|zelensky|modi|meloni|von der leyen|le pen|merkel|macron|figures/i],["money",/rate|recession|econom|currency|dollar|yen|bond|bank|price|chart|tariff|purchase|fiscal/i],["tech",/\bai\b|chip|vr|3d|robot|technolog|game|joystick|brain|face-recognition|drone|electric car|doge/i],["trade",/trade|container|lng|ship|tiktok|brexit/i],["space",/rocket|satellite|space|moon|new horizons|probe|james webb|psyche|mars/i],["climate",/climate|wildfire|hurricane|volcano|tsunami|wind|renewable|methane|hourglass|globe|pangolin/i],["culture",/da vinci|austen|coronation|crown|olympic|world cup|curling|film|concert|odyssey|250|tarot|card|expo|cannabis|disney|matrix|alice/i],["eye",/interpret|claim|foretell|read|eye chart|mirror/i]];'

RTL_CSS = """
html[dir=rtl] body{font-family:"WMM Nexon","Noto Sans Arabic","Segoe UI",Tahoma,"Geeza Pro",sans-serif}
html[dir=rtl] main :is(p,li,h3,h4,h5,td,th,small,b,span,summary,.dd,.ds,.dres,.dg,.fy,.fp,.ff,.say,.chk,.krl>div){unicode-bidi:plaintext;text-align:start}
html[dir=rtl] .hero :is(h1,p,.notice){unicode-bidi:plaintext}
html[dir=rtl] .mono,html[dir=rtl] .ini,html[dir=rtl] .cy{direction:ltr;unicode-bidi:isolate}
"""

if __name__ == "__main__":
    main()
