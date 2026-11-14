"""Daily tender collector — no AI, Python standard library only (runs on GitHub Actions).
Pulls open procurement notices from public feeds and writes data_branch/feeds/tenders.json,
which the site's tender board loads in the browser every day.
Sources: World Bank procurement notices API (search.worldbank.org/api/v2/procnotices).
Rules: keep notices whose deadline is 3+ days away; skip contract awards and individual-consultant posts;
remember the first-seen date ("added") so the board can mark new ones in blue."""
import datetime, json, os, re, sys, unicodedata, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "data_branch", "feeds", "tenders.json")
TODAY = datetime.date.today(); MIN_DL = (TODAY + datetime.timedelta(days=3)).isoformat()
NAMES = json.load(open(os.path.join(ROOT, "src", "names.json"), encoding="utf8"))
META = json.load(open(os.path.join(ROOT, "src", "countries_meta.json"), encoding="utf8"))
try:
    from pages3 import classify
except Exception:
    classify = lambda s: []
def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")
SLUG = {c["iso"]: slug(c["en"]) for c in META}
def norm(s): return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())
ALIAS = {"vietnam": "VN", "lao": "LA", "laopeoplesdemocraticrepublic": "LA", "congodemocraticrepublicof": "CD", "democraticrepublicofcongo": "CD",
         "congorepublicof": "CG", "republicofcongo": "CG", "egyptarabrepublicof": "EG", "yemenrepublicof": "YE", "iranislamicrepublicof": "IR",
         "gambiathe": "GM", "bahamasthe": "BS", "kyrgyzrepublic": "KG", "turkiye": "TR", "turkey": "TR", "slovakrepublic": "SK",
         "micronesiafederatedstatesof": "FM", "stluciaa": "LC", "stlucia": "LC", "stvincentandthegrenadines": "VC", "stkittsandnevis": "KN",
         "cotedivoire": "CI", "ivorycoast": "CI", "koreademocraticpeoplesrepublicof": "KP", "korearepublicof": "KR", "venezuelarb": "VE",
         "westbankandgaza": None, "kosovo": None, "caboverde": "CV", "capeverde": "CV", "eswatini": "SZ", "swaziland": "SZ",
         "northmacedonia": "MK", "somaliafederalrepublicof": "SO", "bosniaandherzegovina": "BA", "saotomeandprincipe": "ST", "micronesia": "FM", "syrianarabrepublic": "SY", "russianfederation": "RU", "moldova": "MD", "tanzania": "TZ", "timorleste": "TL"}
IDX = {}
for iso, n in NAMES.items():
    for k in ("en", "fr", "es"):
        if n.get(k): IDX.setdefault(norm(n[k]), iso)
IDX.update({k: v for k, v in ALIAS.items()})
def iso_of(name, desc=""):
    k = norm(name)
    if k in IDX: return IDX[k]
    m = re.match(r"\s*([A-Za-z .,'()-]{3,40}?)\s+[-–:]", desc or "")
    if m and norm(m.group(1)) in IDX: return IDX[norm(m.group(1))]
    return None

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "GOV RADAR tender collector (73036396@naver.com)"})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode("utf8", "replace"))

def worldbank():
    out = []
    for os_ in range(0, 3000, 500):
        q = urllib.parse.urlencode({"format": "json", "rows": 500, "os": os_, "srt": "submission_date", "order": "desc"})
        try: j = get("https://search.worldbank.org/api/v2/procnotices?" + q)
        except Exception as ex: print("worldbank page", os_, "failed:", ex); break
        rows = j.get("procnotices") or []
        if not rows: break
        for r in rows:
            dl = str(r.get("submission_deadline_date") or "")[:10]
            if not re.match(r"\d{4}-\d{2}-\d{2}$", dl) or dl < MIN_DL: continue
            nt = str(r.get("notice_type") or "")
            if "Award" in nt or str(r.get("notice_status") or "") not in ("Published", ""): continue
            if str(r.get("procurement_method_code") or "") == "INDV": continue
            iso = iso_of(r.get("project_ctry_name"), r.get("bid_description"))
            if not iso: continue
            title = re.sub(r"\s+", " ", str(r.get("bid_description") or r.get("project_name") or "")).strip()
            if not title: continue
            out.append({"iso": iso, "title": title[:220], "buyer": str(r.get("contact_organization") or r.get("project_name") or "")[:160],
                        "deadline": dl, "url": "https://projects.worldbank.org/en/projects-operations/procurement-detail/" + str(r.get("id")),
                        "source": "World Bank", "type": nt, "project": str(r.get("project_name") or "")[:160]})
        oldest = str(rows[-1].get("submission_date") or "")[:10]
        if oldest and oldest < (TODAY - datetime.timedelta(days=120)).isoformat(): break
    return out

def main():
    prev = {}
    if os.path.exists(OUT):
        try: prev = {x["url"]: x for x in json.load(open(OUT, encoding="utf8")).get("items", [])}
        except Exception: prev = {}
    items, seen = [], set()
    for src in (worldbank,):
        for x in src():
            if x["url"] in seen: continue
            seen.add(x["url"])
            x["added"] = (prev.get(x["url"]) or {}).get("added") or TODAY.isoformat()
            x["sec"] = classify(x["title"] + " " + x["buyer"] + " " + x.get("project", ""))
            x["n"] = {L: v for L, v in (NAMES.get(x["iso"]) or {}).items()}; x["slug"] = SLUG.get(x["iso"], "")
            items.append(x)
    # if every source failed, keep yesterday's still-open items instead of publishing an empty board
    if not items: items = [x for x in prev.values() if x.get("deadline", "") >= MIN_DL]
    items.sort(key=lambda x: x["deadline"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "count": len(items), "items": items[:600]}, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
    print("tenders", len(items), "countries", len({x["iso"] for x in items}))

if __name__ == "__main__": main()
