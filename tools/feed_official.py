#!/usr/bin/env python3
"""Official situation feed — no AI. Pulls agencies' own feeds and writes data_branch/hz/official.json.

Sources: USGS (M5.5+ quakes, tsunami flag), GDACS RSS (orange/red alerts), NASA EONET (open storms,
volcanoes, floods, wildfires), WHO Disease Outbreak News, NASA JPL CNEOS close approaches (<0.05 au, 60 days),
NOAA SWPC space-weather scales.
A source that fails keeps its last good items and is marked ok=false with its last success time,
so the site can say "delayed" instead of showing old data as new.
"""
import json, os, re, sys, urllib.request, datetime as dt, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_branch", "hz", "official.json")
ISO3 = json.load(open(os.path.join(ROOT, "tools", "iso3.json")))
KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(dt.timezone.utc)
UA = {"User-Agent": "GOV-RADAR-feed/1.0 (73036396@naver.com)"}


def get(url, t=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t) as r:
        return r.read()


def iso_from_text(s):
    m = re.search(r",\s*([A-Za-z .'-]+)$", s or "")
    return None if not m else None


def usgs():
    d = json.loads(get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"))
    out = []
    for f in d["features"]:
        p = f["properties"]
        if (p.get("mag") or 0) < 5.5 and not p.get("tsunami"):
            continue
        out.append({"k": "tsunami" if p.get("tsunami") else "quake", "t": f"M{p['mag']:.1f} {p.get('place') or ''}".strip(),
                    "date": dt.datetime.fromtimestamp(p["time"] / 1000, dt.timezone.utc).strftime("%Y-%m-%d"),
                    "lvl": {"red": "red", "orange": "orange"}.get(p.get("alert") or "", ""), "url": p.get("url"),
                    "x": f["geometry"]["coordinates"][0], "y": f["geometry"]["coordinates"][1], "src": "USGS", "mag": p["mag"]})
    out.sort(key=lambda x: -x["mag"])
    return out[:12]


GD = {"EQ": "quake", "TC": "storm", "FL": "flood", "VO": "volcano", "WF": "wildfire", "DR": "drought", "TS": "tsunami"}


def gdacs():
    root = ET.fromstring(get("https://www.gdacs.org/xml/rss.xml", 60))
    ns = {"gdacs": "http://www.gdacs.org"}
    out = []
    for it in root.iter("item"):
        lv = (it.findtext("gdacs:alertlevel", "", ns) or "").lower()
        if lv not in ("orange", "red"):
            continue
        ty = it.findtext("gdacs:eventtype", "", ns)
        to = it.findtext("gdacs:todate", "", ns) or it.findtext("pubDate", "")
        try:
            end = dt.datetime.strptime(to[:25].strip(), "%a, %d %b %Y %H:%M:%S")
            if (NOW.replace(tzinfo=None) - end).days > 14:
                continue
            date = end.strftime("%Y-%m-%d")
        except Exception:
            date = ""
        i3 = (it.findtext("gdacs:iso3", "", ns) or "").strip().upper()
        out.append({"k": GD.get(ty, "storm"), "t": (it.findtext("title") or "").strip(), "date": date, "lvl": lv,
                    "iso": ISO3.get(i3), "url": (it.findtext("link") or "").strip(), "src": "GDACS"})
    out.sort(key=lambda x: (x["lvl"] != "red", x["date"]), reverse=False)
    return out[:20]


EO = {"severeStorms": "storm", "volcanoes": "volcano", "floods": "flood", "wildfires": "wildfire", "drought": "drought", "landslides": "landslide"}


def eonet():
    d = json.loads(get("https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=10&limit=200"))
    out, wf = [], []
    for e in d["events"]:
        k = EO.get(e["categories"][0]["id"])
        if not k:
            continue
        g = e["geometry"][-1]
        it = {"k": k, "t": e["title"], "date": g["date"][:10], "url": (e.get("sources") or [{}])[0].get("url"), "src": "NASA EONET"}
        if g.get("type") == "Point":
            it["x"], it["y"] = g["coordinates"][0], g["coordinates"][1]
        (wf if k == "wildfire" else out).append(it)
    return out[:14] + wf[:6]


def who():
    q = "https://www.who.int/api/news/diseaseoutbreaknews?sf_culture=en&$top=8&$orderby=PublicationDateAndTime%20desc"
    d = json.loads(get(q))
    out = []
    for v in d.get("value", []):
        date = (v.get("PublicationDateAndTime") or "")[:10]
        u = v.get("ItemDefaultUrl") or ""
        out.append({"k": "epidemic", "t": (v.get("Title") or "").strip(), "date": date,
                    "url": "https://www.who.int/emergencies/disease-outbreak-news/item" + u if u.startswith("/") else u, "src": "WHO"})
    return out[:6]


def cneos():
    d = json.loads(get("https://ssd-api.jpl.nasa.gov/cad.api?dist-max=0.05&date-min=now&date-max=%2B60&sort=dist"))
    f = d.get("fields", [])
    out = []
    for r in d.get("data", [])[:6]:
        o = dict(zip(f, r))
        ld = float(o["dist"]) * 389.17
        out.append({"k": "impact", "t": f"{o['des']} — {ld:.1f} LD", "date": o["cd"][:11].strip().replace(" ", ""), "ld": round(ld, 1),
                    "url": "https://cneos.jpl.nasa.gov/ca/", "src": "NASA JPL"})
    return out


def swpc():
    d = json.loads(get("https://services.swpc.noaa.gov/products/noaa-scales.json"))
    c = d.get("0", {})
    return {"r": "R" + str(c.get("R", {}).get("Scale") or 0), "s": "S" + str(c.get("S", {}).get("Scale") or 0), "g": "G" + str(c.get("G", {}).get("Scale") or 0),
            "url": "https://www.swpc.noaa.gov/"}


def main():
    try:
        old = json.load(open(OUT))
    except Exception:
        old = {"sources": {}, "items": {}}
    stamp = NOW.astimezone(KST).strftime("%Y-%m-%dT%H:%M")
    res = {"v": 1, "checked": stamp, "sources": {}, "items": {}, "space": old.get("space")}
    for name, fn in (("usgs", usgs), ("gdacs", gdacs), ("eonet", eonet), ("who", who), ("cneos", cneos), ("swpc", swpc)):
        prev = old.get("sources", {}).get(name, {})
        try:
            data = fn()
            if name == "swpc":
                res["space"] = data
            else:
                res["items"][name] = data
            res["sources"][name] = {"ok": True, "last_ok": stamp, "n": len(data) if isinstance(data, list) else 1}
        except Exception as e:
            if name != "swpc":
                res["items"][name] = old.get("items", {}).get(name, [])
            res["sources"][name] = {"ok": False, "last_ok": prev.get("last_ok"), "err": type(e).__name__, "n": prev.get("n", 0)}
            print(f"{name} failed: {e}", file=sys.stderr)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
    ok = sum(1 for s in res["sources"].values() if s["ok"])
    print(f"official feed: {ok}/6 sources ok, " + ", ".join(f"{k} {v['n']}" for k, v in res["sources"].items()))


if __name__ == "__main__":
    main()
