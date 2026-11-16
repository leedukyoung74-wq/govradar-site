"""Daily tender collector — no AI, Python standard library only (runs on GitHub Actions).
Pulls open procurement notices from public feeds and writes data_branch/feeds/tenders.json,
which the site's tender board loads in the browser every day.
Sources: World Bank procurement notices API (search.worldbank.org/api/v2/procnotices).
Rules: keep notices whose deadline is 3+ days away; skip contract awards and individual-consultant posts;
remember the first-seen date ("added") so the board can mark new ones in blue."""
import datetime, json, os, re, sys, unicodedata, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
                        "source": "World Bank", "type": nt, "project": str(r.get("project_name") or "")[:160],
                        # for the per-tender "what to prepare" box: method (RFB/RFP/RFQ/QCBS...), group (GO goods, CW works, CS consulting, NC non-consulting),
                        # market approach (international/national) and the buyer's estimate when published
                        "pm": str(r.get("procurement_method_code") or ""), "pmn": str(r.get("procurement_method_name") or "")[:60],
                        "pg": str(r.get("procurement_group") or ""), "ma": str(r.get("market_approach_name") or "")[:40],
                        "est": str(r.get("bid_estimate_amount") or ""), "cur": str(r.get("bid_currency_code") or "")})
        oldest = str(rows[-1].get("submission_date") or "")[:10]
        if oldest and oldest < (TODAY - datetime.timedelta(days=120)).isoformat(): break
    return out

SRC_NAME = {"worldbank": "World Bank", "ted": "EU TED", "uk": "UK Find a Tender", "ukcf": "UK Contracts Finder", "canada": "CanadaBuys",
            "prozorro": "Prozorro (Ukraine)", "dapa": "DAPA (Korea)", "sam": "SAM.gov (US)"}
MAX_DL = (TODAY + datetime.timedelta(days=730)).isoformat()

def valid(x):
    """Reject notices whose deadline is malformed, already too close, or implausibly far away, and items with no title, country or link."""
    dl = x.get("deadline") or ""
    if not re.match(r"\d{4}-\d{2}-\d{2}$", dl): return "bad-deadline"
    if dl < MIN_DL: return "closing"
    if dl > MAX_DL: return "far-deadline"
    if not x.get("title") or not x.get("iso") or not str(x.get("url", "")).startswith("http"): return "missing-field"
    return ""

def dupkey(x):
    # the same notice republished by two portals (e.g. Find a Tender and Contracts Finder): country + deadline + normalised title
    return x["iso"] + "|" + x["deadline"] + "|" + re.sub(r"[^0-9a-z\u0400-\u04ff\u3131-\uD79D]", "", (x.get("title") or "").lower())[:80]

def main():
    prev = {}
    if os.path.exists(OUT):
        try: prev = {x["url"]: x for x in json.load(open(OUT, encoding="utf8")).get("items", [])}
        except Exception: prev = {}
    import feed_more as FM
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    stp = os.path.join(os.path.dirname(OUT), "sources_status.json")
    try: status = json.load(open(stp, encoding="utf8"))
    except Exception: status = {}
    items, seen, keys = [], set(), set()
    # FM.canada is written and tested but left out: canadabuys.canada.ca robots.txt disallows all agents except search engines
    for src in (worldbank, FM.ted, FM.uk, FM.ukcf, FM.prozorro, FM.dapa, FM.sam):
        nm_ = SRC_NAME[src.__name__]; st = status.get(nm_, {}); err = ""
        try: got = src()
        except Exception as ex: print(src.__name__, "crashed:", ex); got = []; err = type(ex).__name__
        fresh = bool(got)
        if not got:  # a source that failed today keeps its still-open notices from yesterday
            got = [dict(x) for x in prev.values() if x.get("source") == nm_ and x.get("deadline", "") >= MIN_DL]
        rej = {}; kept = dup = 0
        for x in got:
            why = valid(x)
            if why: rej[why] = rej.get(why, 0) + 1; continue
            k = dupkey(x)
            if x["url"] in seen or k in keys: dup += 1; continue
            seen.add(x["url"]); keys.add(k); kept += 1
            x["added"] = (prev.get(x["url"]) or {}).get("added") or TODAY.isoformat()
            x["sec"] = classify(x["title"] + " " + x["buyer"] + " " + x.get("project", ""))
            x["n"] = {L: v for L, v in (NAMES.get(x["iso"]) or {}).items()}; x["slug"] = SLUG.get(x["iso"], "")
            items.append(x)
        st.update({"checked": now, "fresh": fresh, "kept": kept, "duplicates": dup, "rejected": rej, "error": err,
                   "new_today": sum(1 for x in items if x.get("source") == nm_ and x["added"] == TODAY.isoformat())})
        if fresh: st["last_success"] = now
        st["state"] = "PASS" if fresh else ("SKIPPED" if src.__name__ in ("dapa", "sam") and not os.environ.get({"dapa": "DAPA_KEY", "sam": "SAM_KEY"}[src.__name__]) else "FAIL")
        status[nm_] = st
    # if every source failed, keep yesterday's still-open items instead of publishing an empty board
    if not items: items = [x for x in prev.values() if x.get("deadline", "") >= MIN_DL]
    items.sort(key=lambda x: x["deadline"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"updated": now, "count": len(items), "items": items[:3000]}, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
    json.dump(status, open(stp, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("tenders", len(items), "countries", len({x["iso"] for x in items}))
    for k, v in status.items(): print(" ", k, v.get("state"), "kept", v.get("kept"), "dup", v.get("duplicates"), "rej", v.get("rejected"))

if __name__ == "__main__": main()
