#!/usr/bin/env python3
"""GOV RADAR 마무리 손질 (2026-11-22 대표 요청)
1) 탭 아이콘: 모든 페이지를 GOV RADAR 레이더 로고로 통일 (/playground/ 는 자체 로고 유지)
2) 국기: 이모지 국기를 그림 국기로 바꾸는 /assets/flagfix.js 를 모든 페이지에 붙임 (윈도우에서 글자로 보이는 문제)
Usage: python3 tools/site_polish.py cf/public
"""
import os, re, sys, shutil
PUB = sys.argv[1] if len(sys.argv) > 1 else "cf/public"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = ('<link rel="icon" type="image/png" sizes="32x32" href="/assets/gr-icon-32.png">'
        '<link rel="icon" type="image/png" sizes="256x256" href="/assets/gr-icon-512.png">'
        '<link rel="apple-touch-icon" href="/assets/gr-icon-180.png">')
OLD = re.compile(r'<link\b[^>]*\brel=["\'](?:shortcut icon|icon|apple-touch-icon)["\'][^>]*>', re.I)
FLAG = '<script src="/assets/flagfix.js" defer></script>'

def main():
    for f in ("gr-icon-32.png", "gr-icon-180.png", "gr-icon-512.png", "flagfix.js", "newsbox.js"):
        src = os.path.join(ROOT, "cf", "extra", "assets", f)
        if os.path.exists(src): shutil.copy(src, os.path.join(PUB, "assets", f))
    try:
        from PIL import Image
        Image.open(os.path.join(PUB, "assets", "gr-icon-512.png")).save(os.path.join(PUB, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    except Exception as ex:
        print("favicon.ico skipped", ex)
    n = 0
    for d, _, fs in os.walk(PUB):
        if "/playground" in d.replace(os.sep, "/"):
            continue
        for fn in fs:
            if not fn.endswith(".html"): continue
            p = os.path.join(d, fn); s = open(p, encoding="utf-8", errors="ignore").read()
            if "<head" not in s: continue
            t = OLD.sub("", s)
            t = re.sub(r'(<head\b[^>]*>)', lambda m: m.group(1) + ICON, t, count=1)
            mc = re.search(r'data-iso="([A-Z]{2})"', t)
            if mc and '<section class="glance">' in t and "data-newsbox" not in t:
                t = t.replace('<section class="glance">', f'<div data-newsbox="c:{mc.group(1)}" data-n="8" style="margin:8px 0 34px"></div><section class="glance">', 1)
            if "data-newsbox" in t and "/assets/newsbox.js" not in t and "</body>" in t:
                t = t.replace("</body>", '<script src="/assets/newsbox.js" defer></script></body>', 1)
            if "/assets/flagfix.js" not in t:
                t = t.replace("</head>", FLAG + "</head>", 1) if "</head>" in t else t
            if t != s:
                open(p, "w", encoding="utf-8").write(t); n += 1
    print(f"site_polish: {n} pages")

if __name__ == "__main__":
    main()
