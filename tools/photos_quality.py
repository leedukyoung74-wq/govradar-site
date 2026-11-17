#!/usr/bin/env python3
"""Pick a high-quality free photo of each country's representative city from Wikimedia Commons'
reviewed collections only: 'Featured pictures on Wikimedia Commons' and 'Quality images'.
Free licences only (PD, CC0, CC BY, CC BY-SA); no maps, flags, logos, collages; landscape, >= 2400 px wide.
Writes out/photos_candidates.json (top 3 per country with author/licence/page) and out/sheet-*.jpg contact sheets
of the first choice for a human (Claude) review. Polite pacing with backoff."""
import json, os, re, sys, time, io, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capitals import CAP
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "out"); os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "GOV-RADAR-photos/1.1 (https://radar.wmm-hoa.com; 73036396@naver.com)"}
OVR = {"BR": "Rio de Janeiro", "ZA": "Cape Town", "TZ": "Dar es Salaam", "LK": "Colombo", "VN": "Hanoi", "NZ": "Auckland", "CH": "Zurich", "MA": "Marrakesh"}
FREE = re.compile(r"^(cc0|cc[ -]by(-sa)?([ -]\d(\.\d)?)?|public domain|pd\b|pd-)", re.I)
BAD = re.compile(r"(map|flag|coat of arms|emblem|seal|logo|locator|montage|collage|diagram|interior|inside|ceiling|\bdome|nave|altar|apse|vault|organ|choir|crypt|fresco|mosaic|stained|painting|portrait|statue|sculpture|relief|detail|museum|exhibit|\bbirds?\b(?!.?s.?eye)|\bbats?\b|\bfish|insect|snake|animal|flower|butterfly|monkey|lizard|frog|\bpeople|\bwoman|\bman\b|\bgirl|\bboy\b|tractor|bicycle|\bships?\b|\bcars?\b|aircraft|airport|terminal|\.svg|\.gif|\.png|\.tif)", re.I)
GOOD = re.compile(r"(skyline|panoram|cityscape|city view|view (of|from|over)|aerial|downtown|old town|from above|bird|overview|harbou?r|waterfront|night)", re.I)
def call(p, tries=8):
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({**p, "format": "json", "formatversion": "2", "maxlag": "5"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r: return json.loads(r.read())
        except Exception as e:
            w = min(240, 20 * (i + 1)); print("retry", i, e, file=sys.stderr, flush=True); time.sleep(w)
    return {}
def search(city, cat):
    r = call({"action": "query", "generator": "search", "gsrsearch": f'"{city}" incategory:"{cat}"', "gsrnamespace": 6, "gsrlimit": 50,
              "prop": "imageinfo", "iiprop": "size|extmetadata|url|mime", "iiurlwidth": 1920})
    out = []
    for p in (r.get("query") or {}).get("pages") or []:
        ii = (p.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata") or {}; t = p["title"][5:]
        lic = re.sub("<[^>]+>", "", (m.get("LicenseShortName") or {}).get("value", "")).strip()
        art = re.sub("<[^>]+>", "", (m.get("Artist") or {}).get("value", "")).strip()[:80]
        w, h = ii.get("width", 0), ii.get("height", 1)
        if ii.get("mime") != "image/jpeg" or BAD.search(t) or not FREE.match(lic) or w < 2400 or not (1.35 <= w / h <= 3.2): continue
        if city.split()[0].lower() not in t.lower(): continue   # the city must be named in the title
        s = (3 if cat.startswith("Featured") else 1) + (5 if GOOD.search(t) else 0) + min(w, 8000) / 4000
        out.append({"file": t, "thumb": ii.get("thumburl"), "w": w, "h": h, "artist": art or "unknown", "license": lic,
                    "page": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(t.replace(" ", "_")), "score": round(s, 2), "set": cat})
    return out
cs = json.load(open(os.path.join(ROOT, "src", "photos.json")))   # current choices, kept when nothing better is found
isos = [x["iso"] for x in json.load(open(os.path.join(ROOT, "src", "countries_meta.json")))] if False else sorted(k for k in CAP if len(k) == 2)
res = {}
for n, iso in enumerate(isos):
    city = OVR.get(iso) or CAP[iso]; short = re.sub(r"\s*\(.*?\)", "", city.split(",")[0]).strip()
    c = search(short, "Featured pictures on Wikimedia Commons"); time.sleep(1.2)
    c += search(short, "Quality images"); time.sleep(1.2)
    c = sorted({x["file"]: x for x in c}.values(), key=lambda x: -x["score"])[:3]
    res[iso] = {"city": short, "cands": c}
    print(n, iso, short, len(c), (c[0]["file"][:60] if c else "-"), flush=True)
json.dump(res, open(os.path.join(OUT, "photos_candidates.json"), "w"), ensure_ascii=False, indent=1)
# contact sheets of first choices
from PIL import Image, ImageDraw
items = [(iso, r["cands"][0]) for iso, r in res.items() if r["cands"]]
for s in range(0, len(items), 24):
    sheet = Image.new("RGB", (6 * 320, 4 * 200), "white"); d = ImageDraw.Draw(sheet)
    for i, (iso, c) in enumerate(items[s:s + 24]):
        try:
            u = c["thumb"].replace("/1920px-", "/320px-")
            im = Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read())).convert("RGB")
            im.thumbnail((316, 180)); x, y = (i % 6) * 320, (i // 6) * 200; sheet.paste(im, (x + 2, y + 2)); d.rectangle([x + 2, y + 182, x + 120, y + 198], fill="black"); d.text((x + 6, y + 184), f"{iso} {res[iso]['city'][:12]}", fill="white")
        except Exception as e: print("thumb", iso, e, file=sys.stderr)
        time.sleep(0.5)
    sheet.save(os.path.join(OUT, f"sheet-{s // 24 + 1}.jpg"), quality=82)
print("found", len(items), "of", len(res))
