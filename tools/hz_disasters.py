#!/usr/bin/env python3
"""Refresh the disaster part of the live situation board every day — no AI (2026-11-22).

Why: data_branch/hz/hazards.json (the "지금 세계 상황" board on the home and /conflict/ pages) was
only rewritten when the editorial summary was updated. When the daily editorial input was missing
or failed checks, the disaster cards stayed at 2026-11-16 although the agencies' own feeds
(hz/official.json) were collected every day.

What it does
- Rebuilds hazards.json "disasters" from hz/official.json (USGS, GDACS, NASA EONET, WHO, NASA JPL):
  items dated within the last 10 days (near-Earth objects: next 60 days), newest first.
- Sets "checked" to the official feed's collection time. "editorial_updated", "summary_*", "hotspots"
  and "countries" are kept as they are, so the site still says honestly when the editorial summary
  was last updated.
Usage: python3 tools/hz_disasters.py [data_branch/hz]
"""
import datetime as dt, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HZ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data_branch", "hz")
NAMES = json.load(open(os.path.join(ROOT, "src", "names.json"), encoding="utf-8"))
KST = dt.timezone(dt.timedelta(hours=9))
TODAY = dt.datetime.now(KST).date()
KIND = {"quake": "quake", "tsunami": "tsunami", "storm": "storm", "flood": "flood", "volcano": "volcano",
        "wildfire": "fire", "fire": "fire", "drought": "drought", "epidemic": "epidemic", "impact": "asteroid"}
KO = {"quake": "지진", "tsunami": "해일 경보 지진", "storm": "열대저기압", "flood": "홍수", "volcano": "화산",
      "fire": "산불", "drought": "가뭄", "epidemic": "감염병 발생 소식", "asteroid": "지구 근접 천체"}
ALIAS = {"Timor Leste": "TL", "Timor-Leste": "TL", "Democratic Republic of the Congo": "CD", "DR Congo": "CD",
         "Republic of the Congo": "CG", "Congo": "CG", "United States": "US", "USA": "US", "Russia": "RU",
         "South Korea": "KR", "North Korea": "KP", "Vietnam": "VN", "Iran": "IR", "Syria": "SY", "Laos": "LA",
         "Tanzania": "TZ", "Bolivia": "BO", "Venezuela": "VE", "Micronesia": "FM", "Moldova": "MD",
         "Papua New Guinea": "PG", "Solomon Islands": "SB", "Taiwan": "TW", "Türkiye": "TR", "Turkey": "TR",
         "Cape Verde": "CV", "Ivory Coast": "CI", "Côte d'Ivoire": "CI", "Brunei": "BN", "Czechia": "CZ",
         "Alaska": "US", "Hawaii": "US", "Puerto Rico": "PR", "Guam": "GU", "Northern Mariana Islands": "MP",
         "Kermadec Islands": "NZ", "South Sandwich Islands": "GS", "Fiji region": "FJ", "Tonga region": "TO",
         "Vanuatu region": "VU", "CA": "US", "Japan region": "JP", "Kuril Islands": "RU", "Svalbard": "NO"}
EN2ISO = {v["en"]: k for k, v in NAMES.items() if isinstance(v, dict) and v.get("en")}
EN2ISO.update(ALIAS)
US_STATES = ("Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida Georgia Hawaii Idaho Illinois "
             "Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana "
             "Nebraska Nevada Ohio Oklahoma Oregon Pennsylvania Tennessee Texas Utah Vermont Virginia Washington Wisconsin Wyoming").split()
EN2ISO.update({st: "US" for st in US_STATES if st != "Georgia"})
EN2ISO.update({"New Hampshire": "US", "New Jersey": "US", "New Mexico": "US", "New York": "US", "North Carolina": "US",
               "North Dakota": "US", "Rhode Island": "US", "South Carolina": "US", "South Dakota": "US", "West Virginia": "US"})


def iso_of(text):
    """Country from the agency's own place text: 'M6.8 105 km NE of Lospalos, Timor Leste' -> TL."""
    t = re.sub(r"\s*\(.*?\)\s*$", "", text or "").strip()
    tail = t.rsplit(",", 1)[-1].strip() if "," in t else ""
    for cand in (tail, t.rsplit(" - ", 1)[-1].strip() if " - " in t else ""):
        if cand in EN2ISO:
            return EN2ISO[cand]
    for name, iso in sorted(EN2ISO.items(), key=lambda kv: -len(kv[0])):
        if len(name) > 3 and re.search(r"\b" + re.escape(name) + r"\b", t):
            return iso
    return ""


def day(s):
    for f in ("%Y-%m-%d", "%Y-%b-%d"):
        try:
            return dt.datetime.strptime(str(s)[:11].strip(), f).date()
        except ValueError:
            pass
    return None


def main():
    off = json.load(open(os.path.join(HZ, "official.json"), encoding="utf-8"))
    p = os.path.join(HZ, "hazards.json")
    hz = json.load(open(p, encoding="utf-8"))
    out, seen = [], set()
    for src in ("usgs", "gdacs", "eonet", "who", "cneos"):
        for x in (off.get("items") or {}).get(src) or []:
            k = KIND.get(x.get("k"))
            d = day(x.get("date"))
            if not k or not d:
                continue
            age = (TODAY - d).days
            if (k == "asteroid" and not (-60 <= age <= 0)) or (k != "asteroid" and not (0 <= age <= 10)):
                continue
            t = (x.get("t") or "").strip()
            key = (k, t.lower()[:60])
            if not t or key in seen or re.match(r"prescribed (fire|burn)|\S+ rx\b", t, re.I):
                continue
            seen.add(key)
            iso = "" if k == "asteroid" else (x.get("iso") or iso_of(t))
            ko = f'{x.get("src")}: {KO[k]} — {t}'
            out.append({"kind": k, "iso": iso or "", "date": d.strftime("%m-%d") if k != "asteroid" else d.isoformat(),
                        "ko": ko, "en": f'{x.get("src")}: {t}', "url": x.get("url") or "", "src": x.get("src"), "_d": d.isoformat()})
    if not out:
        print("hz_disasters: official feed empty — hazards.json left unchanged")
        return
    out.sort(key=lambda r: (r["kind"] == "asteroid", r["_d"]), reverse=False)
    out = sorted([r for r in out if r["kind"] != "asteroid"], key=lambda r: r["_d"], reverse=True) + \
          sorted([r for r in out if r["kind"] == "asteroid"], key=lambda r: r["_d"])
    for r in out:
        r.pop("_d")
    hz["disasters"] = out
    ck = (off.get("checked") or "").strip()
    if ck:
        hz["checked"] = ck
        hz["disasters_checked"] = ck
    hz.setdefault("editorial_updated", hz.get("updated", ""))
    json.dump(hz, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"hz_disasters: {len(out)} disaster items from official feeds, checked {ck}")


if __name__ == "__main__":
    main()
