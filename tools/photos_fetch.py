#!/usr/bin/env python3
"""Pick one free-licence hero photo per country/region from the capital's English Wikipedia lead image.
Only public domain / CC0 / CC BY / CC BY-SA files are kept; maps, flags, logos and SVGs are skipped.
Writes src/photos.json {iso: {file, thumb, w, h, artist, license, page}}. Batches of 50 titles, polite pacing."""
import json, os, re, sys, time, urllib.parse, urllib.request, html
sys.path.insert(0, os.path.dirname(__file__))
from capitals import CAP, ALT, ALT3
MINW = int(os.environ.get('MINW', '1400')); ROUND2 = os.environ.get('ROUND2') == '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "photos.json")
UA = {"User-Agent": "GOV-RADAR-photos/1.0 (https://radar.wmm-hoa.com; 73036396@naver.com)"}
API = "https://en.wikipedia.org/w/api.php?"

def call(params, tries=14):
    url = API + urllib.parse.urlencode({**params, "format": "json", "formatversion": "2", "maxlag": "5"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.loads(r.read())
        except Exception as e:
            wait = min(300, 45 * (i + 1)); print("retry", i, e, "wait", wait, file=sys.stderr, flush=True); time.sleep(wait)
    raise SystemExit("API unavailable")

FREE = re.compile(r"^(cc0|cc[ -]by(-sa)?( |-|$)|cc[ -]by[ -]\d|cc[ -]by-sa[ -]\d|public domain|pd\b|pd-)", re.I)
BAD = re.compile(r"(map|flag|coat|emblem|seal|logo|locator|location|\.svg$|\.gif$|montage|collage|collection)", re.I)

def main():
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    R3 = os.environ.get('ROUND3') == '1'
    todo = {k: (ALT3.get(k, v) if R3 else ALT.get(k, v) if ROUND2 else v) for k, v in CAP.items() if k not in old}
    titles = list(dict.fromkeys(todo.values()))
    page_img = {}
    for i in range(0, len(titles), 50):
        d = call({"action": "query", "titles": "|".join(titles[i:i + 50]), "prop": "pageimages", "piprop": "name", "redirects": "1"})
        q = d["query"]; rmap = {}
        for n in q.get("normalized", []) + q.get("redirects", []): rmap[n["from"]] = n["to"]
        got = {p["title"]: p.get("pageimage") for p in q.get("pages", [])}
        for t in titles[i:i + 50]:
            tt = t
            for _ in range(3): tt = rmap.get(tt, tt)
            page_img[t] = got.get(tt)
        time.sleep(4)
    files = sorted({f for f in page_img.values() if f and not BAD.search(f)})
    info = {}
    for i in range(0, len(files), 50):
        d = call({"action": "query", "titles": "|".join("File:" + f for f in files[i:i + 50]), "prop": "imageinfo",
                  "iiprop": "url|size|extmetadata", "iiurlwidth": "1600", "iiextmetadatafilter": "LicenseShortName|Artist|Credit"})
        for p in d["query"].get("pages", []):
            ii = (p.get("imageinfo") or [None])[0]
            if ii: info[p["title"].replace(" ", "_")[5:]] = ii
        time.sleep(4)
    res = dict(old)
    for iso, cap in todo.items():
        f = page_img.get(cap)
        if not f or BAD.search(f): continue
        ii = info.get(f.replace(" ", "_"))
        if not ii: continue
        md = ii.get("extmetadata", {})
        lic = (md.get("LicenseShortName", {}).get("value") or "").strip()
        if not FREE.search(lic): print("skip licence", iso, f, lic); continue
        if ii.get("width", 0) < MINW: print("skip small", iso, f, ii.get("width")); continue
        artist = re.sub(r"<[^>]+>", "", html.unescape(md.get("Artist", {}).get("value") or "")).strip()[:80] or "Wikimedia Commons"
        res[iso] = {"file": f, "thumb": ii.get("thumburl"), "w": ii.get("thumbwidth"), "h": ii.get("thumbheight"),
                    "artist": artist, "license": lic, "page": ii.get("descriptionurl"), "place": cap.split(",")[0]}
    json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("photos:", len(res), "/", len(CAP), "missing:", sorted(set(CAP) - set(res)))

if __name__ == "__main__":
    main()
