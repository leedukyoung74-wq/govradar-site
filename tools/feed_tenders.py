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
from reporting_clock import reporting_day, utc_source_day
OUT = os.path.join(ROOT, "data_branch", "feeds", "tenders.json")
# Upstream official API windows stay on UTC. Korean user-facing 'new today'
# and urgent date labels use KST to match the advertised 06:10 KST schedule.
TODAY = utc_source_day(); MIN_DL = TODAY.isoformat()
REPORT_DATE = reporting_day()
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
    req = urllib.request.Request(url, headers={"User-Agent": "GOV RADAR tender collector (leedukyoung74@gmail.com)"})
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
    """No attempted request is never proof of successful collection."""
    if st.get("skipped"): return "SKIPPED"
    requests, failed, raw = st.get("requests", 0), st.get("failed", 0), st.get("raw", 0)
    if requests == 0: return "ERROR"
    # A time-budget stop may be recorded separately from network requests. If
    # any real rows arrived, preserve PARTIAL rather than claiming total failure.
    if failed and failed >= requests and not raw: return "ERROR"
    if failed: return "PARTIAL"
    # A successfully contacted bounded sample is not complete coverage.
    # UK rotating shards and SAM.gov page caps must never claim full success.
    if st.get("coverage_partial") is True: return "PARTIAL"
    if not raw: return "EMPTY_SUCCESS"
    return "SUCCESS"

def source_answered(st):
    """Evidence of at least one usable upstream reply, never an inferred refresh."""
    return st.get("raw", 0) > 0 or st.get("requests", 0) > st.get("failed", 0)

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
            x["added"] = (prev.get(x["url"]) or {}).get("added") or REPORT_DATE.isoformat()
            items.append(x); c["kept"] += 1
    return items, counts

# ---- open catalogue: what happens to yesterday's notices that today's search did not return -----------------------------
# A source answering 0 (or failing, or searching only recently published notices) is NOT proof that its earlier notices
# closed. Such notices are re-checked one by one against the source's official record (verify_samples.official):
#   confirmed            -> kept as a normal open notice, last_verified_at = now (official deadline wins if it moved)
#   not confirmable now  -> kept for at most 48 h as stale: shown with "verification delayed · last checked …" and a link
#                           to the original, but left out of open counts, new/urgent lists and alerts
#   still unconfirmed after 48 h, closed, or deadline unknown -> dropped (counted in the source status)
# Carried notices keep their first-seen date, so they are never counted as new.
WINDOWED = {"UK Contracts Finder", "UK Find a Tender"}   # their search only covers recently published notices
STALE_MAX_H, VERIFY_CAP = 48, 40

def _key(x): return (x.get("source"), x.get("sid") or x.get("url"))

def carry(nm_, got, state, prev, now, stamp, lookup, budget):
    """Returns (items to add, counts). lookup(x) -> verify_samples.official_record(x) (dict).
    Verification grades kept on each item ("verify"):
      search  — returned by today's official search
      full    — re-read by id: publisher status ACTIVE + exact deadline instant with offset, still ahead
      date    — re-read by id: status ACTIVE but the publisher gives a date without a time zone (World Bank): open, "time not given"
      partial — re-read but status not given (TED) or not readable: NOT confirmed -> stale
    Cancelled / withdrawn / closed at the publisher -> dropped at once. The official deadline always replaces ours, so a
    same-day change of time (earlier or later) is applied."""
    import deadline as DL
    import time as _clock
    c = {"carried_verified": 0, "carried_stale": 0, "dropped_unverified": 0, "dropped_closed": 0, "dropped_cancelled": 0, "verify_lookups": 0}
    if not (state in ("ERROR", "PARTIAL", "EMPTY_SUCCESS") or nm_ in WINDOWED): return [], c
    have = {_key(x) for x in got} | {x.get("url") for x in got}
    out = []
    norm = lambda t: re.sub(r"\W+", " ", str(t or "").lower()).strip()[:40]
    for x in prev.values():
        if x.get("source") != nm_ or _key(x) in have or x.get("url") in have: continue
        if not DL.is_open(x, now): c["dropped_closed"] += 1; continue
        x = dict(x); r = None
        # Optional second budget slot is a monotonic wall-clock deadline shared
        # across all sources. When exhausted, carry stays STALE, never verified.
        can_verify = budget[0] > 0 and (len(budget) < 2 or _clock.monotonic() < budget[1])
        if can_verify:
            budget[0] -= 1; c["verify_lookups"] += 1
            try: r = lookup(x)
            except Exception: r = None
        if r and r.get("ok") and norm(r.get("title")) == norm(x.get("title")):
            if r.get("status") in ("CANCELLED", "CLOSED"): c["dropped_cancelled"] += 1; continue
            if r.get("status") == "ACTIVE":
                y = dict(x, deadline_at=r["deadline_at"], deadline=r["deadline_at"][:10])   # official time wins, same day too
                if not DL.is_open(y, now): c["dropped_closed"] += 1; continue
                y.update(last_verified_at=r.get("checked_at") or stamp, verify="full" if r.get("timed") else "date", official_status=r.get("status_raw"))
                y.pop("stale", None); y.pop("stale_since", None)
                out.append(y); c["carried_verified"] += 1; continue
        # not confirmed (unreadable, rate limited, title differs, status not given): stale, never a normal open notice
        since = x.get("stale_since") or stamp
        try: age_h = (now - datetime.datetime.strptime(since, "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc)).total_seconds() / 3600
        except ValueError: age_h = 0
        if age_h >= STALE_MAX_H: c["dropped_unverified"] += 1; continue
        x.update(stale=True, stale_since=since, verify="partial")
        x["last_verified_at"] = x.get("last_verified_at", "")      # the last real check, never the first-seen date
        out.append(x); c["carried_stale"] += 1
    return out, c

def all_empty_fallback(prev, now, stamp):
    """Every source returned nothing (or failed): keep yesterday's still-valid notices so the site is not blanked, but ALL as
    stale (shown with "verification delayed", out of counts and alerts). Invalid or closed notices are never restored.
    The quality gate still sees the drop in fresh notices."""
    keep = []
    for x in prev.values():
        if valid(x, now): continue          # valid() returns a reason when the notice is NOT valid (closed, bad date, …)
        y = dict(x, stale=True, stale_since=x.get("stale_since") or stamp, verify="partial"); y["last_verified_at"] = x.get("last_verified_at", "")
        keep.append(y)
    return keep

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
    import verify_samples as VS
    import time as _clock
    # The entire carry-verification stage gets a shared 120-second envelope.
    # A timed-out lookup cannot turn unverified notices into open opportunities.
    budget = [VERIFY_CAP, _clock.monotonic() + 120]
    # FM.canada is written and tested but not run: canadabuys.canada.ca robots.txt disallows all agents except search engines
    for src in (worldbank, FM.ted, FM.uk, FM.ukcf, FM.prozorro, FM.dapa, FM.sam):
        nm_ = SRC_NAME[src.__name__]
        try: got = src()
        except Exception as ex: got = []; FM.stat(nm_)["failed"] += 1; FM.stat(nm_)["notes"].append(FM.mask(f"crashed: {type(ex).__name__}: {ex}")[:160])
        state = classify_state(FM.stat(nm_))
        for x in got:   # seen in today's official search = verified now
            x["last_verified_at"] = stamp; x["verify"] = "search"
        extra, cc = carry(nm_, got, state, prev, now, stamp, VS.official_record, budget)
        got = got + extra
        groups.append((nm_, got)); FM.stat(nm_)["state"] = state; FM.stat(nm_).update(cc)
        FM.stat(nm_)["carried_from_yesterday"] = cc["carried_verified"] + cc["carried_stale"]
    items, counts = merge(groups, prev, now)
    for x in items:
        x["sec"] = classify(x["title"] + " " + x["buyer"] + " " + x.get("project", ""))
        x["n"] = {L: v for L, v in (NAMES.get(x["iso"]) or {}).items()}; x["slug"] = SLUG.get(x["iso"], "")
        d = datetime.date.fromisoformat(x["deadline"]); x["urgent"] = (d - REPORT_DATE).days <= 2
    for nm_, c in counts.items():
        st = dict(FM.stat(nm_)); st.update(c); st["checked"] = stamp
        st["new_today"] = sum(1 for x in items if x["source"] == nm_ and
                              x.get("added") == REPORT_DATE.isoformat() and
                              not x.get("stale") and x.get("verify") != "partial")
        # A PARTIAL source can contain valid rows, but a source that never
        # answered cannot advance its last truly successful check.
        answered = source_answered(st)
        if st["state"] in ("SUCCESS", "EMPTY_SUCCESS", "PARTIAL") and answered:
            st["last_success"] = stamp
        else:
            st["last_success"] = (status.get(nm_) or {}).get("last_success", "")
        status[nm_] = st
    if not any(x.get("verify") == "search" for x in items):   # no source answered with a single notice today
        items = all_empty_fallback(prev, now, stamp)
        for st in status.values(): st.setdefault("notes", []).append("all sources empty: yesterday's valid notices kept as stale")
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
