#!/usr/bin/env python3
"""Download the chosen photos (1600px thumbnails) and save as web/c-<iso>.webp (max 1600 wide, quality 78)."""
import json, os, sys, time, io, urllib.request
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(ROOT, "src", "photos.json")))
UA = {"User-Agent": "GOV-RADAR-photos/1.0 (https://radar.wmm-hoa.com; 73036396@naver.com)"}
ok = bad = 0
for iso, x in P.items():
    out = os.path.join(ROOT, "web", f"c-{iso.lower()}.webp")
    if os.path.exists(out): ok += 1; continue
    for i in range(6):
        try:
            u = x["thumb"].replace("/1600px-", "/1920px-" if i % 2 == 0 else "/1280px-")
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                im = Image.open(io.BytesIO(r.read())).convert("RGB")
            if im.width > 1600: im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
            im.save(out, "WEBP", quality=78, method=5); ok += 1; break
        except Exception as e:
            print("retry", iso, e, file=sys.stderr, flush=True); time.sleep(120 * (i + 1))
    else:
        bad += 1
    time.sleep(25)
print("saved", ok, "failed", bad)
