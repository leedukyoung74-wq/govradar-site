#!/usr/bin/env python3
"""GOV RADAR map-first entry (/map/, /map/<lang>/) — 2026-11-22 대표 승인.

첫 화면은 세계지도 한 장. 나라를 누르면 그 나라의 요약·입찰·유망 사업·정부 과제·
필요한 것·큰 사업·위험·출처가 한 판에 열리고, '이 나라 전체 페이지'로 기존 페이지에 간다.
기존 페이지·메뉴·회원 기능은 그대로 둔다.

Input : cf/public/data/c/<ISO>.json (public preview data), export/countries (open-tender counts only),
        data_branch/hz/hazards.json, src/names.json, cf/public/hazards/world.js (topology)
Output: cf/public/map/{index.html,<lang>/index.html,countries.json,i18n-<lang>.json,world.json,d3.min.js,topojson.min.js}
Usage : python3 tools/map_page.py cf/public
"""
import datetime as dt, glob, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "cf", "public")
OUT = os.path.join(PUB, "map")
LANGS = ["ko", "en", "es", "fr", "ar", "vi", "id"]
TODAY = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=9)).date().isoformat()


def L(x, n):
    return [i for i in (x or []) if i][:n]


def tit(b):
    return b.get("title") if isinstance(b, dict) else str(b)


def projects(arr):
    return [{"t": x.get("title"), "m": x.get("ministry"), "g": x.get("budget")} for x in L(arr, 3) if isinstance(x, dict)]


def main():
    os.makedirs(OUT, exist_ok=True)
    names = json.load(open(os.path.join(ROOT, "src", "names.json"), encoding="utf-8"))
    iso_db = json.load(open("/usr/share/iso-codes/json/iso_3166-1.json"))["3166-1"] if os.path.exists("/usr/share/iso-codes/json/iso_3166-1.json") else []
    n2a = {c["numeric"]: c["alpha_2"] for c in iso_db}
    # topology: numeric ids -> ISO2 (fallback: keep the name map from the topology itself)
    raw = open(os.path.join(PUB, "hazards", "world.js"), encoding="utf-8").read()
    topo = json.loads(raw[raw.index("{"):raw.rstrip().rstrip(";").rindex("}") + 1])
    en2iso = {v.get("en"): k for k, v in names.items() if isinstance(v, dict)}
    geoms = []
    for g in topo["objects"]["countries"]["geometries"]:
        iso = n2a.get(str(g.get("id", "")).zfill(3)) or en2iso.get((g.get("properties") or {}).get("name"), "")
        if iso == "AQ":
            continue
        g["id"] = iso or ""
        g.pop("properties", None)
        geoms.append(g)
    topo["objects"]["countries"]["geometries"] = geoms
    json.dump(topo, open(os.path.join(OUT, "world.json"), "w"), separators=(",", ":"))

    hzp = os.path.join(ROOT, "data_branch", "hz", "hazards.json")
    hot = {h["iso"]: h.get("level", "") for h in json.load(open(hzp, encoding="utf-8")).get("hotspots", [])} if os.path.exists(hzp) else {}
    slugs = {}
    for p in glob.glob(os.path.join(PUB, "ko", "*", "index.html")):
        s = open(p, encoding="utf-8", errors="ignore").read(60000)
        r = re.search(r"data/c/([A-Z]{2})\.json", s)
        if r:
            slugs.setdefault(r.group(1), p.split(os.sep)[-2])

    base, per = {}, {l: {} for l in LANGS[2:]}
    for p in sorted(glob.glob(os.path.join(PUB, "data", "c", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        iso = d.get("iso") or os.path.basename(p)[:-5]
        if len(iso) != 2:
            continue
        en = d.get("en") or {}
        nm = names.get(iso) if isinstance(names.get(iso), dict) else {}
        def tenders(arr):
            rows = [{"t": x.get("title"), "b": x.get("buyer"), "d": x.get("deadline"), "u": x.get("url")} for x in (arr or []) if isinstance(x, dict)]
            return sorted(rows, key=lambda r: ((r["d"] or "9999") < TODAY, r["d"] or "9999"))
        to = 0
        ep = os.path.join(ROOT, "export", "countries", iso + ".json")
        if os.path.exists(ep):
            ed = json.load(open(ep, encoding="utf-8"))
            ed = ed.get("data", ed)
            to = sum(1 for x in ed.get("tenders") or [] if isinstance(x, dict) and (x.get("deadline") or "9999") >= TODAY)
        else:
            to = sum(1 for r in tenders(d.get("tenders")) if (r["d"] or "9999") >= TODAY)
        rk = d.get("risk") or {}
        rke = d.get("risk_en") or {}
        base[iso] = {
            "n": {l: nm.get(l) or nm.get("en") or d.get("name") for l in LANGS},
            "sl": slugs.get(iso, ""), "up": d.get("updated", ""), "to": to, "hz": hot.get(iso, ""), "rk": rk.get("level", ""),
            "ko": {"s": d.get("summary", ""), "ld": d.get("leader", ""), "ag": L(d.get("agenda"), 4), "nd": L(d.get("needs"), 4),
                   "bz": [tit(b) for b in L(d.get("biz"), 5)], "pj": projects(d.get("projects")), "td": tenders(d.get("tenders"))[:6],
                   "rc": L(rk.get("conflict"), 2) + L(rk.get("disaster"), 1)},
            "en": {"s": en.get("summary", ""), "ld": en.get("leader", ""), "ag": L(en.get("agenda"), 4), "nd": L(en.get("needs"), 4),
                   "bz": [tit(b) for b in L(en.get("biz"), 5)], "pj": projects(en.get("projects")), "td": tenders(en.get("tenders"))[:6],
                   "rc": L(rke.get("conflict"), 2) + L(rke.get("disaster"), 1)},
            "sr": [{"t": x.get("title"), "u": x.get("url")} for x in L(d.get("sources"), 3) if isinstance(x, dict)],
        }
        for l in LANGS[2:]:
            t = (d.get("i18n") or {}).get(l) or {}
            if t:
                per[l][iso] = {"s": t.get("summary", ""), "ld": t.get("leader", ""), "ag": L(t.get("agenda"), 4),
                               "bz": [tit(b) for b in L(t.get("biz"), 5)], "pj": projects(t.get("projects"))}
    json.dump(base, open(os.path.join(OUT, "countries.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for l, v in per.items():
        json.dump(v, open(os.path.join(OUT, f"i18n-{l}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for f in ("d3.min.js", "topojson.min.js"):
        shutil.copy(os.path.join(ROOT, "cf", "map_assets", f), os.path.join(OUT, f))
    tpl = open(os.path.join(ROOT, "cf", "map_assets", "map.html"), encoding="utf-8").read()
    for l in LANGS:
        html = tpl.replace("{{LANG}}", l).replace("{{DIR}}", "rtl" if l == "ar" else "ltr")
        d = OUT if l == "ko" else os.path.join(OUT, l)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
    print(f"map_page: {len(base)} countries, {sum(v['to'] for v in base.values())} open tenders, {len(geoms)} shapes")


if __name__ == "__main__":
    main()
