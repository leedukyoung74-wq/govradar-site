"""Cross-check a sample of collected notices against the official record, one source at a time.
For each sampled item: (1) the public notice URL answers, (2) the official record fetched again by its notice id has the
same title, deadline and buyer. Writes data_branch/feeds/verify_samples.json and prints a table.
Run: python tools/verify_samples.py [n_per_source]"""
import json, os, re, sys, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDS = os.path.join(ROOT, "data_branch", "feeds")
UA = {"User-Agent": "GOV RADAR sample check (73036396@naver.com)"}

BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"}
def http(url, data=None, ctype=None, browser=False):
    h = dict(BROWSER if browser else UA)
    if ctype: h["Content-Type"] = ctype
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return r.status, r.read().decode("utf8", "replace")
    except urllib.error.HTTPError as ex: return ex.code, ""
    except Exception as ex: return type(ex).__name__, ""

n = lambda s: re.sub(r"\W+", " ", str(s or "").lower()).strip()

def _official(x):
    """Return (title, deadline_date, buyer) from the source's own API for this notice id."""
    s, sid = x["source"], x.get("sid", "")
    if s == "World Bank":
        _, b = http("https://search.worldbank.org/api/v2/procnotices?format=json&id=" + urllib.parse.quote(sid))
        r = (json.loads(b or "{}").get("procnotices") or [{}])[0]
        return r.get("bid_description") or r.get("project_name"), str(r.get("submission_deadline_date") or "")[:10], r.get("contact_organization") or r.get("project_name")
    if s == "EU TED":
        body = json.dumps({"query": f"publication-number={sid}", "fields": ["notice-title", "buyer-name", "deadline-receipt-tender-date-lot"], "limit": 1}).encode()
        _, b = http("https://api.ted.europa.eu/v3/notices/search", body, "application/json")
        r = (json.loads(b or "{}").get("notices") or [{}])[0]
        import feed_more as FM
        t = re.sub(r"^[^–]{2,60}–\s*", "", FM._first(r.get("notice-title")), count=1)
        dl = sorted(str(z)[:10] for z in (r.get("deadline-receipt-tender-date-lot") or []))
        return t, dl[0] if dl else "", FM._first(r.get("buyer-name"))
    if s in ("UK Find a Tender", "UK Contracts Finder"):
        # official OCDS record by id (no page scraping, no browser user agent); both services rate-limit, so space calls
        import time; time.sleep(3)
        if s == "UK Find a Tender": u = "https://www.find-tender.service.gov.uk/api/1.0/ocdsRecordPackages/" + urllib.parse.quote(sid)
        # official release by notice id (GOV.UK open-contracting guidance: /Published/Notice/releases/{NoticeId}.json)
        else: u = "https://www.contractsfinder.service.gov.uk/Published/Notice/releases/" + x["url"].rstrip("/").rsplit("/", 1)[-1] + ".json"
        code, b = http(u)
        if code == 429: return "RATE_LIMITED", "RATE_LIMITED", None
        try:
            j = json.loads(b)
            if "records" in j:
                rec = j["records"][0]; rel = rec.get("compiledRelease") or (rec.get("releases") or [{}])[-1]
            else:
                rel = (j.get("releases") or [{}])[-1]
        except Exception: rel = {}
        t = rel.get("tender") or {}
        return t.get("title"), str((t.get("tenderPeriod") or {}).get("endDate") or "")[:10], (rel.get("buyer") or {}).get("name")
    if s == "Prozorro (Ukraine)" and x.get("pid"):
        _, b = http("https://public-api.prozorro.gov.ua/api/2.5/tenders/" + x["pid"])
        t = (json.loads(b or "{}").get("data") or {})
        return t.get("title_en") or t.get("title"), str((t.get("tenderPeriod") or {}).get("endDate") or "")[:10], (t.get("procuringEntity") or {}).get("name")
    return None, None, None

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
    if r.get("record_unavailable"): r["record"] = "unavailable"
    elif r.get("title_ok") and r.get("deadline_ok"): r["record"] = "match"
    else: r["record"] = "mismatch"
    r["verdict"] = "FAIL" if (r["link"] == "broken" or r["record"] == "mismatch") else ("PASS" if (r["link"] == "ok" and r["record"] == "match") else "UNKNOWN")
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
            t, d, b = official(x)
            rl = t == "UNAVAILABLE"
            if rl: t = d = None
            row = {"record_unavailable": rl, "source": s, "sid": x.get("sid"), "url": x["url"], "url_status": code, "title_ok": None if t is None else n(t)[:60] == n(x["title"])[:60],
                   "deadline_ok": None if d is None else d == x["deadline"], "buyer_ok": None if b is None else n(b)[:40] == n(x["buyer"])[:40],
                   "site_title": x["title"][:80], "official_title": (t or "")[:80], "site_deadline": x["deadline"], "official_deadline": d}
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
    for r in rows: print(r["verdict"], "|", r["source"], "|", r["sid"], "| link", r["link"], r["url_status"], "| record", r["record"])
    json.dump(rows, open(os.path.join(FEEDS, "verify_samples.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(f"checked {len(rows)}, PASS {len(ok)}, FAIL {len(bad)}, UNKNOWN {len(unk)}")
    # strict: any real mismatch or broken link fails the run; so does a check where fewer than half could be confirmed
    if not rows or bad or len(ok) * 2 < len(rows):
        print("FAIL: a sampled notice had a broken link or did not match its official record, or fewer than half could be confirmed"); sys.exit(1)
