"""Build the live situation-board feed (verified facts only) for the GitHub data branch.

Input : an ArtifactData out_dir export with hazards/{conflict,current}.json and countries/*.json
Output: <out>/hz/hazards.json  (read by the site from raw.githubusercontent.com — no Netlify deploy)

Rules
- Conflict facts: only verdict "ok" (2+ independent sources, one tier 1/2) and "official" (one tier-1 statement,
  labelled as such). "claim", "single", "part", "unv", "false", "nobasis" are dropped.
- Country risk lines: dropped when marked "(단일 출처)", "(당사자 주장)", "single source" or "party claim".
- Disasters/epidemics come from the daily monitor (USGS/EMSC, GDACS, PAGASA, NHC, WHO DON, GVP …).
Usage: python3 tools/hazards_feed.py IN_DIR OUT_DIR
"""
import glob, json, os, re, sys

DROP = re.compile(r"단일 출처|당사자 주장|single source|party claim|\(claim\)", re.I)


def load(p):
    j = json.load(open(p, encoding="utf8"))
    return j.get("data", j)


def main(src, out):
    conf = load(os.path.join(src, "hazards", "conflict.json"))
    cur = load(os.path.join(src, "hazards", "current.json"))
    cur_en = cur.get("en") or {}
    hot = []
    for h in conf.get("hotspots", []):
        facts = [{"ko": f.get("ko"), "en": f.get("en"), "v": f.get("v")} for f in h.get("facts", []) if f.get("v") in ("ok", "official")]
        if not facts: continue
        hot.append({"iso": h.get("iso"), "level": h.get("level"), "ko": h.get("ko"), "en": h.get("en"),
                    "status_ko": h.get("status_ko"), "status_en": h.get("status_en"), "facts": facts[:6]})
    dis = []
    for k in ("tsunami", "quake", "storm", "volcano", "weather", "fire", "epidemic"):
        en_list = cur_en.get(k) or []
        for i, x in enumerate(cur.get(k) or []):
            if k == "quake":
                t = f'규모 {x.get("mag")} 지진 — {x.get("place")}' + (" · 해일 경보" if x.get("tsunami") else "")
                te = f'M{x.get("mag")} earthquake — {x.get("place")}' + (" · tsunami alert" if x.get("tsunami") else "")
            else:
                t = x.get("text"); te = (en_list[i].get("text") if i < len(en_list) and isinstance(en_list[i], dict) else None) or t
            if t and not DROP.search(t):
                dis.append({"kind": k, "iso": x.get("iso"), "date": x.get("date"), "ko": t, "en": te, "url": x.get("url")})
    # flood is shown with its own animation: split it out of storm/weather by wording
    for x in dis:
        if x["kind"] in ("storm", "weather") and re.search(r"홍수|폭우|범람|flood|inundat", (x.get("ko") or "") + (x.get("en") or ""), re.I): x["kind"] = "flood"
    # near-Earth asteroids / comets (NASA CNEOS / JPL), closest first
    for a in sorted(cur.get("asteroid") or [], key=lambda a: float(a.get("ld") or 999))[:3]:
        dis.append({"kind": "asteroid", "iso": "", "date": a.get("date"),
                    "ko": f'소행성 {a.get("name")} 지구 근접 — 달 거리의 {a.get("ld")}배, 크기 {a.get("size","?")} (NASA 근접 통과 목록)',
                    "en": f'Asteroid {a.get("name")} passes Earth — {a.get("ld")} lunar distances, size {a.get("size","?")} (NASA close-approach list)', "url": "https://cneos.jpl.nasa.gov/ca/"})
    ctry = []
    for f in glob.glob(os.path.join(src, "countries", "*.json")):
        d = load(f); r = d.get("risk") or {}; re_ = d.get("risk_en") or {}
        if r.get("level") not in ("high", "medium"): continue
        item = {"iso": os.path.basename(f)[:2], "level": r.get("level"), "checked": r.get("checked")}
        for k in ("conflict", "disaster", "epidemic"):
            ko = [s for s in (r.get(k) or []) if s and not DROP.search(s)]
            en = [s for s in (re_.get(k) or []) if s and not DROP.search(s)]
            if ko: item[k] = {"ko": ko[:3], "en": en[:3]}
        if any(k in item for k in ("conflict", "disaster", "epidemic")): ctry.append(item)
    ctry.sort(key=lambda x: (x["level"] != "high", x["iso"]))
    feed = {"v": 1, "updated": max(conf.get("updated", ""), (cur.get("checked") or "")[:10]),
            "checked": cur.get("checked"), "summary_ko": conf.get("summary_ko"), "summary_en": conf.get("summary_en"),
            "hotspots": hot, "disasters": dis, "countries": ctry}
    os.makedirs(os.path.join(out, "hz"), exist_ok=True)
    json.dump(feed, open(os.path.join(out, "hz", "hazards.json"), "w", encoding="utf8"), ensure_ascii=False)
    print(f"hotspots {len(hot)} · disasters {len(dis)} · countries {len(ctry)} · updated {feed['updated']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
