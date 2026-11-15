#!/usr/bin/env python3
"""Build /welcome/ (ko) and /welcome/<lang>/ from the Korean source in tools/welcome_src/."""
import importlib, json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "tools", "welcome_src"); OUT = os.path.join(ROOT, "cf", "extra", "welcome")
KEYS = json.load(open(os.path.join(HERE, "keys.json"), encoding="utf-8"))
LANGS = ["ko", "en", "es", "fr", "ar", "vi", "id"]
NAMES = {"ko": "한국어", "en": "English", "es": "Español", "fr": "Français", "ar": "العربية", "vi": "Tiếng Việt", "id": "Bahasa Indonesia"}
SUBS = ["", "about/", "services/", "country/", "membership/", "login/"]
SKIP = {49, 226}
HANGUL = re.compile(r"[가-힣]")
EN_PILL = re.compile(r'<a href="/en/" style="border: 1px solid rgba\(255,255,255,\.5\); border-radius: 20px; padding: 3px 12px(?:; font-size: 13px)?">EN</a>')
sys.path.insert(0, HERE)
def page(L, sub, s):
    base = "/welcome/" if L == "ko" else f"/welcome/{L}/"
    if L != "ko":
        T = importlib.import_module(L).T
        pairs = sorted(((KEYS[i], T[i]) for i in range(len(KEYS)) if i not in SKIP and i in T), key=lambda p: -len(p[0]))
        for k, v in pairs: s = s.replace(k, v)
        left = sorted(set(m.group(0) for m in re.finditer(r"[^<>\"']*[가-힣][^<>\"']*", s)))
        if left: raise SystemExit(f"[welcome] {L}/{sub} untranslated: {left[:5]}")
        s = s.replace('<html lang="ko">', f'<html lang="{L}"' + (' dir="rtl"' if L == "ar" else "") + ">", 1)
        s = s.replace('href="/welcome/', f'href="{base}').replace(f'href="{base}en/', 'href="/en/')
        s = s.replace('https://radar.wmm-hoa.com/welcome/', f'https://radar.wmm-hoa.com{base}')
        s = s.replace("/ko/", f"/{L}/").replace('window.RADAR_LANG="ko"', f'window.RADAR_LANG="{L}"')
    opts = "".join(f'<option value="{"/welcome/" if l == "ko" else "/welcome/" + l + "/"}{sub}"{" selected" if l == L else ""}>{NAMES[l]}</option>' for l in LANGS)
    sel = f'<select aria-label="Language" onchange="location.href=this.value" style="min-height: 32px; border: 1px solid rgba(255,255,255,.5); border-radius: 16px; background: #0b1f3a; color: #ffffff; padding: 0 10px; font: inherit; font-size: 13px">{opts}</select>'
    s, n = EN_PILL.subn(sel, s)
    alts = "".join(f'<link rel="alternate" hreflang="{l}" href="https://radar.wmm-hoa.com{"/welcome/" if l == "ko" else "/welcome/" + l + "/"}{sub}">' for l in LANGS)
    s = s.replace('<link rel="icon"', alts + '<link rel="icon"', 1)
    return s
if os.path.isdir(OUT): shutil.rmtree(OUT)
for L in LANGS:
    for sub in SUBS:
        s = open(os.path.join(SRC, sub, "index.html"), encoding="utf-8").read()
        d = os.path.join(OUT, sub) if L == "ko" else os.path.join(OUT, L, sub)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page(L, sub, s))
print("[welcome] built", ", ".join(LANGS))
