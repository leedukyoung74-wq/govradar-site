"""Daily tender collector — no AI, Python standard library only (runs on GitHub Actions).
Pulls open procurement notices from public feeds and writes data_branch/feeds/tenders.json,
which the site's tender board loads in the browser every day.
Sources: World Bank procurement notices API (search.worldbank.org/api/v2/procnotices).
Rules: keep notices until their published deadline has passed (D-0 included, flagged "urgent" when 2 days or less remain);
skip contract awards and individual-consultant posts; remember the first-seen date ("added") so the board can mark new ones.
More sources live in feed_more.py. Per-source status goes to feeds/sources_status.json."""
import datetime, json, os, re, sys, unicodedata, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "data_branch", "feeds", "tenders.json")
TODAY = datetime.date.today(); MIN_DL = TODAY.isoformat()
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
    import feed_more as FM
    S = "World Bank"; out = []
    for os_ in range(0, 3000, 500):
        q = urllib.parse.urlencode({"format": "json", "rows": 500, "os": os_, "srt": "submission_date", "order": "desc"})
        FM.stat(S)["requests"] += 1
        try: j = get("https://search.worldbank.org/api/v2/procnotices?" + q)
        except Exception as ex: FM.stat(S)["failed"] += 1; FM.stat(S)["notes"].append(f"{type(ex).__name__}"); break
        rows = j.get("procnotices") or []
        if not rows: break
        FM.stat(S)["raw"] += len(rows)
        for r in rows:
            nt = str(r.get("notice_type") or "")
            if "Award" in nt: FM.drop(S, "award-notice"); continue
            if str(r.get("notice_status") or "") not in ("Published", ""): FM.drop(S, "not-published"); continue
            if str(r.get("procurement_method_code") or "") == "INDV": FM.drop(S, "individual-consultant"); continue
            d = str(r.get("submission_deadline_date") or "")[:10]; tm = str(r.get("submission_deadline_time") or "")
            if not d: FM.drop(S, "no-deadline"); continue
            # World Bank gives the date and a local clock time without a time zone
            raw = d + ("T" + tm if re.match(r"\d{2}:\d{2}$", tm) and tm != "00:00" else "")
            if not FM._keep(S, raw): continue
            iso = iso_of(r.get("project_ctry_name"), r.get("bid_description"))
            if not iso: FM.drop(S, "no-country"); continue
            title = re.sub(r"\s+", " ", str(r.get("bid_description") or r.get("project_name") or "")).strip()
            if not title: FM.drop(S, "no-title"); continue
            out.append({"iso": iso, "title": title[:220], "buyer": str(r.get("contact_organization") or r.get("project_name") or "")[:160],
                        "deadline": d, "deadline_at": raw, "url": "https://projects.worldbank.org/en/projects-operations/procurement-detail/" + str(r.get("id")),
                        "sid": str(r.get("id") or ""), "source": S, "type": nt, "project": str(r.get("project_name") or "")[:160],
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

def valid(x, now=None):
    """Return "" for a usable notice, else the reason it is rejected."""
    import feed_more as FM
    d, _ = FM.parse_deadline(x.get("deadline_at") or x.get("deadline"))
    if d is None: return "bad-deadline"
    if d.isoformat() > MAX_DL: return "far-deadline"
    if not FM.still_open(x.get("deadline_at") or x.get("deadline"), now): return "closed"
    if not x.get("title") or not x.get("iso") or not str(x.get("url", "")).startswith("http"): return "missing-field"
    return ""

def norm_url(u):
    p = urllib.parse.urlsplit(str(u or "").strip())
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), p.query, ""))

def confirmed_key(x):
    """Two items are the SAME notice only if they share the source's own notice id, or the same normalised original URL."""
    return (x.get("source"), x.get("sid")) if x.get("sid") else ("url", norm_url(x.get("url")))

def similar_key(x):
    """Looks-alike across sources (country + deadline + buyer + title). Never used to delete — only to flag for review."""
    n = lambda s: re.sub(r"[^0-9a-z\u0400-\u04ff\u3131-\ud79d]", "", (s or "").lower())
    return "|".join((x.get("iso", ""), x.get("deadline", ""), n(x.get("buyer"))[:40], n(x.get("title"))[:80]))

def classify_state(st):
    if st.get("skipped"): return "SKIPPED"
    if st.get("requests", 0) and st.get("failed", 0) >= st.get("requests", 0): return "ERROR"
    if st.get("failed", 0): return "PARTIAL"
    if not st.get("raw", 0): return "EMPTY_SUCCESS"
    return "SUCCESS"

def merge(groups, prev=None, now=None):
    """groups: list of (source name, items). Returns (items, per-source counts). Confirmed duplicates are dropped;
    look-alikes from different sources are kept and flagged with "dupc" (the other item's URL) for human review."""
    prev = prev or {}; items, seen, sim = [], set(), {}; counts = {}
    for nm_, got in groups:
        c = counts.setdefault(nm_, {"in": len(got), "rejected": {}, "duplicates": 0, "flagged_similar": 0, "kept": 0})
        for x in got:
            why = valid(x, now)
            if why: c["rejected"][why] = c["rejected"].get(why, 0) + 1; continue
            k = confirmed_key(x); u = ("url", norm_url(x.get("url")))
            if k in seen or u in seen: c["duplicates"] += 1; continue
            seen.add(k); seen.add(u)
            sk = similar_key(x)
            if sk in sim and sim[sk]["source"] != x["source"]:
                x["dupc"] = sim[sk]["url"]; c["flagged_similar"] += 1
            sim.setdefault(sk, x)
            x["added"] = (prev.get(x["url"]) or {}).get("added") or TODAY.isoformat()
            items.append(x); c["kept"] += 1
    return items, counts

def main():
    import feed_more as FM
    prev = {}
    if os.path.exists(OUT):
        try: prev = {x["url"]: x for x in json.load(open(OUT, encoding="utf8")).get("items", [])}
        except Exception: prev = {}
    now = datetime.datetime.now(datetime.timezone.utc); stamp = now.strftime("%Y-%m-%dT%H:%MZ")
    stp = os.path.join(os.path.dirname(OUT), "sources_status.json")
    try: status = json.load(open(stp, encoding="utf8"))
    except Exception: status = {}
    groups = []
    # FM.canada is written and tested but not run: canadabuys.canada.ca robots.txt disallows all agents except search engines
    for src in (worldbank, FM.ted, FM.uk, FM.ukcf, FM.prozorro, FM.dapa, FM.sam):
        nm_ = SRC_NAME[src.__name__]
        try: got = src()
        except Exception as ex: got = []; FM.stat(nm_)["failed"] += 1; FM.stat(nm_)["notes"].append(FM.mask(f"crashed: {type(ex).__name__}: {ex}")[:160])
        state = classify_state(FM.stat(nm_))
        carried = 0
        if state == "ERROR":  # a source that failed today keeps its still-open notices from yesterday
            got = [dict(x) for x in prev.values() if x.get("source") == nm_]; carried = len(got)
        groups.append((nm_, got)); FM.stat(nm_)["state"] = state; FM.stat(nm_)["carried_from_yesterday"] = carried
    items, counts = merge(groups, prev, now)
    for x in items:
        x["sec"] = classify(x["title"] + " " + x["buyer"] + " " + x.get("project", ""))
        x["n"] = {L: v for L, v in (NAMES.get(x["iso"]) or {}).items()}; x["slug"] = SLUG.get(x["iso"], "")
        d = datetime.date.fromisoformat(x["deadline"]); x["urgent"] = (d - TODAY).days <= 2
    for nm_, c in counts.items():
        st = dict(FM.stat(nm_)); st.update(c); st["checked"] = stamp
        st["new_today"] = sum(1 for x in items if x["source"] == nm_ and x["added"] == TODAY.isoformat())
        if st["state"] in ("SUCCESS", "EMPTY_SUCCESS", "PARTIAL"): st["last_success"] = stamp
        else: st["last_success"] = (status.get(nm_) or {}).get("last_success", "")
        status[nm_] = st
    if not items: items = [x for x in prev.values() if not valid(x, now)]
    items.sort(key=lambda x: x["deadline"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"updated": stamp, "count": len(items), "items": items[:3000]}, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
    json.dump(status, open(stp, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("tenders", len(items), "countries", len({x["iso"] for x in items}))
    print("source | state | requests | failed | raw | filtered | in | rejected | duplicates | similar(flagged) | kept")
    for k, v in status.items():
        print(" | ".join(str(z) for z in (k, v.get("state"), v.get("requests"), v.get("failed"), v.get("raw"), v.get("filtered"), v.get("in"),
                                           v.get("rejected"), v.get("duplicates"), v.get("flagged_similar"), v.get("kept"))))

if __name__ == "__main__": main()
