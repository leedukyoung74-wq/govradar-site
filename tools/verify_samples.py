"""Cross-check a sample of collected notices against the official record, one source at a time.
For each sampled item: (1) the public notice URL answers, (2) the official record fetched again by its notice id has the
same title, deadline and buyer. Writes data_branch/feeds/verify_samples.json and prints a table.
Run: python tools/verify_samples.py [n_per_source]"""
import json, os, re, sys, time, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDS = os.path.join(ROOT, "data_branch", "feeds")
UA = {"User-Agent": "GOV RADAR sample check (73036396@naver.com)"}

BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"}
TRACE = []   # every official-record lookup of the current notice: url, HTTP status, content type, ids read back

def http(url, data=None, ctype=None, browser=False):
    h = dict(BROWSER if browser else UA)
    if ctype: h["Content-Type"] = ctype
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            TRACE.append({"url": url, "status": r.status, "type": (r.headers.get("Content-Type") or "").split(";")[0]})
            return r.status, r.read().decode("utf8", "replace")
    except urllib.error.HTTPError as ex:
        TRACE.append({"url": url, "status": ex.code, "type": (ex.headers.get("Content-Type") or "").split(";")[0] if ex.headers else ""}); return ex.code, ""
    except Exception as ex:
        TRACE.append({"url": url, "status": type(ex).__name__, "type": ""}); return type(ex).__name__, ""

def ocds_release(b):
    """Release (dict) from an OCDS release package or record package; {} if the body is not OCDS JSON (e.g. an HTML error page)."""
    try: j = json.loads(b)
    except Exception: return {}
    if not isinstance(j, dict): return {}
    if "records" in j:
        rec = (j.get("records") or [{}])[0]; return rec.get("compiledRelease") or (rec.get("releases") or [{}])[-1]
    return (j.get("releases") or [{}])[-1]

n = lambda s: re.sub(r"\W+", " ", str(s or "").lower()).strip()

STATUS = {   # source status -> ACTIVE | CANCELLED | CLOSED | UNKNOWN (only ACTIVE may confirm an open notice)
    "active": "ACTIVE", "active.tendering": "ACTIVE", "published": "ACTIVE",
    "cancelled": "CANCELLED", "canceled": "CANCELLED", "withdrawn": "CANCELLED", "cancellation": "CANCELLED",
    "unsuccessful": "CLOSED", "complete": "CLOSED", "active.qualification": "CLOSED", "active.awarded": "CLOSED",
    "active.auction": "CLOSED", "active.pre-qualification": "CLOSED", "planned": "UNKNOWN", "planning": "UNKNOWN"}
def norm_status(raw):
    return STATUS.get(str(raw or "").strip().lower(), "UNKNOWN")

def official_record(x):
    """The notice as its publisher holds it now:
    {"ok", "id", "title", "deadline_at" (exact instant with offset when the source gives one, else date), "timed",
     "status" ACTIVE|CANCELLED|CLOSED|UNKNOWN, "status_raw", "buyer", "checked_at", "why"}.
    ok=False when the publisher could not be read (HTTP error, rate limit, HTML instead of JSON, unknown id)."""
    import datetime as _dt
    s, sid = x["source"], x.get("sid", "")
    rec = {"ok": False, "id": None, "title": None, "deadline_at": "", "timed": False, "status": "UNKNOWN", "status_raw": None, "buyer": None,
           "checked_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "why": ""}
    def fill(i, t, dl, st, b):
        rec.update(ok=bool(t and dl), id=i, title=t, deadline_at=dl or "", status_raw=st, status=norm_status(st), buyer=b,
                   timed=bool(re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d:?\d\d)$", dl or "")))
        if not rec["ok"]: rec["why"] = "no title or deadline in the official answer"
        return rec
    if s == "World Bank":
        code, b = http("https://search.worldbank.org/api/v2/procnotices?format=json&id=" + urllib.parse.quote(sid))
        try: r = (json.loads(b or "{}").get("procnotices") or [{}])[0]
        except Exception: r = {}
        if not r: rec["why"] = f"HTTP {code}, no notice"; return rec
        st = "cancellation" if "cancel" in str(r.get("notice_type", "")).lower() else r.get("notice_status")
        # the World Bank gives a local time ("17:00") without a time zone: keep the date only, never guess the zone
        return fill(r.get("id"), r.get("bid_description") or r.get("project_name"), str(r.get("submission_deadline_date") or "")[:10], st,
                    r.get("contact_organization") or r.get("project_name"))
    if s == "EU TED":
        body = json.dumps({"query": f"publication-number={sid}", "fields": ["notice-title", "buyer-name", "deadline-receipt-tender-date-lot",
                           "deadline-receipt-tender-time-lot", "notice-type"], "limit": 1}).encode()
        code, b = http("https://api.ted.europa.eu/v3/notices/search", body, "application/json")
        try: r = (json.loads(b or "{}").get("notices") or [{}])[0]
        except Exception: r = {}
        if not r: rec["why"] = f"HTTP {code}, no notice"; return rec
        import feed_more as FM
        t = re.sub(r"^[^–]{2,60}–\s*", "", FM._first(r.get("notice-title")), count=1)
        # TED search has no per-notice status: a cancellation is a separate notice. Status stays UNKNOWN (never confirms OPEN).
        return fill(r.get("publication-number"), t, FM.ted_deadline(r.get("deadline-receipt-tender-date-lot"), r.get("deadline-receipt-tender-time-lot")),
                    None, FM._first(r.get("buyer-name")))
    if s in ("UK Find a Tender", "UK Contracts Finder"):
        # official OCDS record by id (no page scraping, no browser user agent); both services rate-limit, so space calls
        time.sleep(3)
        if s == "UK Find a Tender":
            code, b = http("https://www.find-tender.service.gov.uk/api/1.0/ocdsRecordPackages/" + urllib.parse.quote(sid)); rel = ocds_release(b)
        else:
            # GOV.UK open-contracting guidance: /Published/Notice/releases/{NoticeId}.json; if that is not OCDS JSON
            # (404, HTML error page, rate limit) try /Published/Notice/records/{OCID}.json once, 10 s later
            nid = x["url"].rstrip("/").rsplit("/", 1)[-1]
            code, b = http("https://www.contractsfinder.service.gov.uk/Published/Notice/releases/" + nid + ".json"); rel = ocds_release(b)
            if not rel and sid.startswith("ocds-"):
                time.sleep(10)
                code, b = http("https://www.contractsfinder.service.gov.uk/Published/Notice/records/" + sid + ".json"); rel = ocds_release(b)
        if code == 429: rec["why"] = "rate limited (429)"; return rec
        if TRACE and rel: TRACE[-1].update({"ocid": rel.get("ocid"), "release_id": rel.get("id")})
        if not rel: rec["why"] = f"HTTP {code}, not OCDS JSON"; return rec
        t = rel.get("tender") or {}
        return fill(rel.get("ocid"), t.get("title"), str((t.get("tenderPeriod") or {}).get("endDate") or ""), t.get("status"), (rel.get("buyer") or {}).get("name"))
    if s == "Prozorro (Ukraine)" and x.get("pid"):
        code, b = http("https://public-api.prozorro.gov.ua/api/2.5/tenders/" + x["pid"])
        try: t = (json.loads(b or "{}").get("data") or {})
        except Exception: t = {}
        if not t: rec["why"] = f"HTTP {code}, no tender"; return rec
        return fill(t.get("tenderID"), t.get("title_en") or t.get("title"), str((t.get("tenderPeriod") or {}).get("endDate") or ""), t.get("status"),
                    (t.get("procuringEntity") or {}).get("name"))
    rec["why"] = "no official lookup for this source"; return rec

def _official(x):
    """Compatibility: (title, deadline_date, buyer) or ("RATE_LIMITED", …)."""
    r = official_record(x)
    if r["why"].startswith("rate limited"): return "RATE_LIMITED", "RATE_LIMITED", None
    if not r["ok"]: return None, None, None
    return r["title"], r["deadline_at"][:10], r["buyer"]

def official(x):
    """Official record, or ("UNAVAILABLE",)*3 when the source could not give one right now (HTTP error, rate limit,
    empty or unparsable reply, unknown id). Unavailable is reported as UNKNOWN — never as a match or a mismatch."""
    try: t, d, b = _official(x)
    except Exception: return "UNAVAILABLE", "UNAVAILABLE", None
    if t == "RATE_LIMITED" or not t or not d: return "UNAVAILABLE", "UNAVAILABLE", None
    return t, d, b

def judge(r):
    c = r["url_status"]
    if isinstance(c, int) and 200 <= c < 300: r["link"] = "ok"
    elif c == 403: r["link"] = "unconfirmed"
    elif isinstance(c, int) and 400 <= c < 500 and c != 429: r["link"] = "broken"
    else: r["link"] = "unknown"
    if r.get("official_status") in ("CANCELLED", "CLOSED"): r["record"] = "cancelled"   # we list a notice the publisher closed
    elif r.get("record_unavailable"): r["record"] = "unavailable"
    elif r.get("title_ok") and r.get("deadline_ok"): r["record"] = "match"
    else: r["record"] = "mismatch"
    r["verdict"] = "FAIL" if (r["link"] == "broken" or r["record"] in ("mismatch", "cancelled")) else ("PASS" if (r["link"] == "ok" and r["record"] == "match") else "UNKNOWN")
    return r

if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    items = json.load(open(os.path.join(FEEDS, "tenders.json"), encoding="utf8"))["items"]
    by = {}
    for x in items: by.setdefault(x["source"], []).append(x)
    quota = {"World Bank": k + 2, "EU TED": k + 2, "UK Find a Tender": k, "UK Contracts Finder": 4, "Prozorro (Ukraine)": 2}
    rows = []
    for s, q in quota.items():
        pool = by.get(s, []); step = max(1, len(pool) // max(1, q))
        for x in pool[::step][:q]:
            code, _ = http(x["url"])
            del TRACE[:]
            rec = official_record(x)
            t, d, b = (rec["title"], rec["deadline_at"][:10], rec["buyer"]) if rec["ok"] else ("UNAVAILABLE", "UNAVAILABLE", None)
            lookups = [dict(z) for z in TRACE]
            rl = t == "UNAVAILABLE"
            if rl: t = d = None
            row = {"record_unavailable": rl, "source": s, "sid": x.get("sid"), "url": x["url"], "url_status": code, "title_ok": None if t is None else n(t)[:60] == n(x["title"])[:60],
                   "deadline_ok": None if d is None else d == x["deadline"], "buyer_ok": None if b is None else n(b)[:40] == n(x["buyer"])[:40],
                   "site_title": x["title"][:80], "official_title": (t or "")[:80], "site_deadline": x["deadline"], "official_deadline": d,
                   "official_lookups": lookups, "official_status": rec["status"], "official_status_raw": rec["status_raw"],
                   "official_deadline_at": rec["deadline_at"], "site_deadline_at": x.get("deadline_at", "")}
            rows.append(row)
    for r in rows:
        pass
    # Two separate judgements per notice:
    #   link   ok (2xx) | broken (404, 410, other 4xx) | unconfirmed (403 — may be a bot block or a real denial; never counted
    #          as success) | unknown (timeout, 429, 5xx, network error)
    #   record match | mismatch | unavailable (official record could not be fetched)
    # verdict FAIL if the link is broken or the record mismatches; PASS only if link ok AND record match; otherwise UNKNOWN.
    for r in rows: judge(r)
    ok = [r for r in rows if r["verdict"] == "PASS"]; unk = [r for r in rows if r["verdict"] == "UNKNOWN"]; bad = [r for r in rows if r["verdict"] == "FAIL"]
    for r in rows: print(r["verdict"], "|", r["source"], "|", r["sid"], "| link", r["link"], r["url_status"], "| record", r["record"],
                         "|", "; ".join(f'{z["status"]} {z["type"] or "-"}' for z in r.get("official_lookups", [])))
    json.dump(rows, open(os.path.join(FEEDS, "verify_samples.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(f"checked {len(rows)}, PASS {len(ok)}, FAIL {len(bad)}, UNKNOWN {len(unk)}")
    # strict: any real mismatch or broken link fails the run; so does a check where fewer than half could be confirmed
    if not rows or bad or len(ok) * 2 < len(rows):
        print("FAIL: a sampled notice had a broken link or did not match its official record, or fewer than half could be confirmed"); sys.exit(1)
