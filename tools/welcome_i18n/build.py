#!/usr/bin/env python3
"""Build /welcome/ (ko) and /welcome/<lang>/ from the Korean source in tools/welcome_src/."""
import importlib, json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "tools", "welcome_src"); OUT = os.path.join(ROOT, "cf", "extra", "welcome")
KEYS = json.load(open(os.path.join(HERE, "keys.json"), encoding="utf-8"))
LANGS = ["ko", "en", "es", "fr", "ar", "vi", "id"]
NAMES = {"ko": "한국어", "en": "English", "es": "Español", "fr": "Français", "ar": "العربية", "vi": "Tiếng Việt", "id": "Bahasa Indonesia"}
SUBS = ["", "about/", "services/", "country/", "projects/", "membership/", "login/"]
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
        if L == "vi":
            s = s.replace("</head>", '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;700&display=swap"><style>body *,body{font-family:"Be Vietnam Pro","WMM Nexon",sans-serif!important}</style></head>', 1)
    opts = "".join(f'<option value="{"/welcome/" if l == "ko" else "/welcome/" + l + "/"}{sub}"{" selected" if l == L else ""}>{NAMES[l]}</option>' for l in LANGS)
    sel = f'<select aria-label="Language" onchange="location.href=this.value" style="min-height: 32px; border: 1px solid rgba(255,255,255,.5); border-radius: 16px; background: #0b1f3a; color: #ffffff; padding: 0 10px; font: inherit; font-size: 13px">{opts}</select>'
    s, n = EN_PILL.subn(sel, s)
    t = re.search(r"<title>(.*?)</title>", s).group(1); dsc = re.search(r'<meta name="description" content="([^"]*)"', s).group(1)
    url = "https://radar.wmm-hoa.com" + base + sub
    t = "GOV RADAR" if sub == "" else (t if "GOV RADAR" in t else t + " · GOV RADAR")
    og = (f'<meta property="og:type" content="website"><meta property="og:site_name" content="GOV RADAR"><meta property="og:title" content="{t}"><meta property="og:description" content="{dsc}">'
          f'<meta property="og:url" content="{url}"><meta property="og:image" content="https://radar.wmm-hoa.com/assets/og-govradar.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
          f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://radar.wmm-hoa.com/assets/og-govradar.jpg">')
    s = s.replace('<link rel="icon" href="/assets/govradar-logo.webp">', og + '<link rel="icon" href="/assets/mark.png">', 1)
    alts = "".join(f'<link rel="alternate" hreflang="{l}" href="https://radar.wmm-hoa.com{"/welcome/" if l == "ko" else "/welcome/" + l + "/"}{sub}">' for l in LANGS)
    s = s.replace('<link rel="icon"', alts + '<link rel="icon"', 1)
    # top bar always visible: sticky header; on phones the menu links become one swipeable row so the bar stays short
    s = s.replace("</head>", '<style id="gv-sticky">header{position:sticky;top:0;z-index:1000;box-shadow:0 2px 12px rgba(0,0,0,.25)}'
                  '@media (max-width:760px){header>nav{gap:6px 10px!important;padding:6px 12px!important;min-height:0!important}header>nav>a img{height:34px!important}'
                  'header>nav>div:nth-child(2){order:3;flex:1 1 100%!important;flex-wrap:nowrap!important;justify-content:flex-start!important;overflow-x:auto;gap:18px!important;font-size:14px!important;padding:2px 0 6px;scrollbar-width:none;white-space:nowrap}'
                  'header>nav>div:nth-child(2)::-webkit-scrollbar{display:none}header>nav>div:nth-child(3){margin-inline-start:auto}}'
                  '@media (min-width:761px){header>nav{flex-wrap:nowrap!important;gap:12px clamp(12px,2vw,28px)!important;max-width:1320px!important}header>nav>div:nth-child(2){flex-wrap:nowrap!important;white-space:nowrap;gap:8px clamp(10px,1.5vw,28px)!important;font-size:clamp(13px,1.1vw,15px)!important;flex:1 1 auto!important;min-width:0;overflow-x:auto;scrollbar-width:none;justify-content:safe center!important}header>nav>div:nth-child(2)::-webkit-scrollbar{display:none}header>nav>div:nth-child(3){flex-wrap:nowrap!important;white-space:nowrap;flex:none;gap:10px!important;align-items:center}header>nav{min-height:72px!important}header>nav>a img{height:40px!important}header>nav>div:nth-child(2) a{padding:6px 0;font-weight:400;letter-spacing:-.2px}header>nav>div:nth-child(3) select{width:auto!important;max-width:118px;height:34px;min-height:34px!important;border-radius:17px!important;padding:0 28px 0 14px!important;font-size:13px!important;-webkit-appearance:none;appearance:none;background:#0b1f3a url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2710%27 height=%276%27%3E%3Cpath d=%27M1 1l4 4 4-4%27 stroke=%27%23fff%27 fill=%27none%27 stroke-width=%271.5%27/%3E%3C/svg%3E") no-repeat right 12px center!important}header>nav>div:nth-child(3)>a:not([aria-label]){display:inline-flex!important;align-items:center;height:34px;box-sizing:border-box;padding:0 16px!important;border-radius:17px;font-size:13px!important}header>nav>div:nth-child(3)>a[href$="login/"]:not(:last-of-type){border:1px solid rgba(255,255,255,.35)}header>nav>div:nth-child(3)>a[aria-label]{width:34px!important;height:34px!important}html[dir=rtl] header>nav>div:nth-child(3) select{padding:0 14px 0 28px!important;background-position:left 12px center!important}}'
                  '@media (min-width:761px) and (max-width:1180px){header>nav{gap:10px 16px!important;padding:0 16px!important}header>nav>a img{height:36px!important}header>nav>div:nth-child(3) a[aria-label]{display:none!important}}'
                  '@media (min-width:761px) and (max-width:960px){header>nav>div:nth-child(3) select{max-width:84px}}'
                  '[id]{scroll-margin-top:84px}@media (max-width:760px){[id]{scroll-margin-top:110px}}</style>'
                  '<script>document.addEventListener("DOMContentLoaded",function(){var a=document.querySelector(\'header nav>div a[style*="8fb4ff"]\');if(a&&a.parentNode.scrollWidth>a.parentNode.clientWidth)a.parentNode.scrollLeft=a.offsetLeft-a.parentNode.offsetLeft-16})</script></head>', 1)
    return s
if os.path.isdir(OUT): shutil.rmtree(OUT)
for L in LANGS:
    for sub in SUBS:
        s = open(os.path.join(SRC, sub, "index.html"), encoding="utf-8").read()
        d = os.path.join(OUT, sub) if L == "ko" else os.path.join(OUT, L, sub)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page(L, sub, s))
print("[welcome] built", ", ".join(LANGS))
