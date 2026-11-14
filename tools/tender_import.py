"""Add newly found tenders to export/countries/ISO.json (dedupe by url+title), stamp 'added' = today,
and register Korean display names in src/ko_names.json.
Usage: python3 tools/tender_import.py rows.py   (file defines R = [(iso,title,buyer,deadline,url,source,ko_title,ko_buyer), ...])"""
import json, os, sys, datetime, runpy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = datetime.date.today().isoformat()
R = runpy.run_path(sys.argv[1])["R"]
kon_p = os.path.join(ROOT, "src", "ko_names.json"); KON = json.load(open(kon_p, encoding="utf8"))
add = skip = 0
for iso, title, buyer, dl, url, src, kt, kb in R:
    p = os.path.join(ROOT, "export", "countries", iso + ".json")
    j = json.load(open(p, encoding="utf8")); d = j.get("data", j)
    T = d.setdefault("tenders", [])
    if any(isinstance(t, dict) and (t.get("url") == url and t.get("title") == title) for t in T): skip += 1; continue
    row = {"title": title, "buyer": buyer, "deadline": dl, "source": src, "url": url, "added": TODAY}
    T.append(row)
    en = d.setdefault("en", {})
    if isinstance(en.get("tenders"), list):
        while len(en["tenders"]) < len(T) - 1: en["tenders"].append({})
        en["tenders"].append(dict(row))
    if kt: KON[title] = kt
    if kb and buyer not in KON: KON[buyer] = kb
    d["updated"] = TODAY
    json.dump(j, open(p, "w", encoding="utf8"), ensure_ascii=False, indent=1); add += 1
json.dump(KON, open(kon_p, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("added", add, "skipped", skip)
