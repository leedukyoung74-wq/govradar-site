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

def official(x):
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
        # the notice page itself (server-rendered): title and the deadline date must appear on it
        _, b = http(x["url"], browser=True)
        txt = n(re.sub(r"<[^>]+>", " ", b))
        import datetime as _dt
        dl = _dt.date.fromisoformat(x["deadline"]); human = n(f"{dl.day} {dl.strftime('%B %Y')}")
        return (x["title"] if n(x["title"])[:50] in txt else "(not found on page)"), (x["deadline"] if human in txt else "(not found on page)"), None
    if s == "Prozorro (Ukraine)" and x.get("pid"):
        _, b = http("https://public-api.prozorro.gov.ua/api/2.5/tenders/" + x["pid"])
        t = (json.loads(b or "{}").get("data") or {})
        return t.get("title_en") or t.get("title"), str((t.get("tenderPeriod") or {}).get("endDate") or "")[:10], (t.get("procuringEntity") or {}).get("name")
    return None, None, None

if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    items = json.load(open(os.path.join(FEEDS, "tenders.json"), encoding="utf8"))["items"]
    by = {}
    for x in items: by.setdefault(x["source"], []).append(x)
    quota = {"World Bank": k + 2, "EU TED": k + 2, "UK Find a Tender": k, "UK Contracts Finder": 10, "Prozorro (Ukraine)": 2}
    rows = []
    for s, q in quota.items():
        pool = by.get(s, []); step = max(1, len(pool) // max(1, q))
        for x in pool[::step][:q]:
            code, _ = http(x["url"], browser=True)
            t, d, b = official(x)
            row = {"source": s, "sid": x.get("sid"), "url": x["url"], "url_status": code, "title_ok": None if t is None else n(t)[:60] == n(x["title"])[:60],
                   "deadline_ok": None if d is None else d == x["deadline"], "buyer_ok": None if b is None else n(b)[:40] == n(x["buyer"])[:40],
                   "site_title": x["title"][:80], "official_title": (t or "")[:80], "site_deadline": x["deadline"], "official_deadline": d}
            rows.append(row)
    json.dump(rows, open(os.path.join(FEEDS, "verify_samples.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    for r in rows:
        print(r["source"], "|", r["sid"], "|", r["url_status"], "| title", r["title_ok"], "| deadline", r["deadline_ok"], "| buyer", r["buyer_ok"])
    ok = [r for r in rows if str(r["url_status"]).startswith("2") and r["title_ok"] is not False and r["deadline_ok"] is not False]
    print(f"checked {len(rows)}, passed {len(ok)}")
