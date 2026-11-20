"""Extra tender sources for feed_tenders.py — standard library only.
- EU TED (Tenders Electronic Daily) search API v3: EU/EEA notices of about EUR 2M+, and every notice from buyers outside the EU/EEA.
- UK Find a Tender Service and UK Contracts Finder OCDS APIs: open UK notices of about GBP 1M+.
- Ukraine Prozorro public API: open tenders of about US$1M+.
- Korea DAPA overseas tender information (data.go.kr) and US SAM.gov, only when the DAPA_KEY / SAM_KEY secrets are set.
- CanadaBuys (written, not run: robots.txt allows only search engines).

Every item carries "sid" (the source's own notice id) and "deadline_at" (the deadline exactly as published, with time and
time zone when the source gives them). Every collector records requests, failures and filter counts in STATS so
feed_tenders can report SUCCESS / EMPTY_SUCCESS / PARTIAL / ERROR / SKIPPED per source."""
import datetime, json, os, re, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISO3 = json.load(open(os.path.join(ROOT, "src", "iso3.json")))
FEEDS = os.path.join(ROOT, "data_branch", "feeds")
TODAY = datetime.date.today()
MIN_DL = TODAY.isoformat()  # D-0 notices stay; still_open() drops those whose published deadline has passed
UA = {"User-Agent": "GOV RADAR tender collector (73036396@naver.com)"}
EEA = "AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE NOR ISL LIE CHE".split()
# rough EUR rates, only to rank and filter by size (labelled "approx." on the site)
EUR = {"EUR": 1, "SEK": .087, "NOK": .085, "DKK": .134, "PLN": .23, "CZK": .04, "RON": .2, "HUF": .0025, "BGN": .51, "CHF": 1.05,
       "ISK": .0066, "GBP": 1.17, "USD": .92, "MKD": .016, "MDL": .051, "RSD": .0085, "TRY": .027, "ALL": .0098, "UAH": .022}
PG = {"works": "CW", "supplies": "GO", "services": "NC"}

# ---------------------------------------------------------------- bookkeeping
STATS = {}
def stat(src):
    return STATS.setdefault(src, {"requests": 0, "failed": 0, "raw": 0, "filtered": {}, "notes": []})
def drop(src, why):
    f = stat(src)["filtered"]; f[why] = f.get(why, 0) + 1

SECRET_PARAMS = re.compile(r"((?:serviceKey|api_key|apikey|key)=)[^&\s'\"]+", re.I)
def mask(text):
    """Remove API keys from anything that may reach a log: query parameters and the raw secret values themselves."""
    s = SECRET_PARAMS.sub(r"\1***", str(text))
    for k in ("DAPA_KEY", "SAM_KEY"):
        v = os.environ.get(k)
        if v: s = s.replace(v, "***").replace(urllib.parse.quote(v, safe=""), "***")
    return s

def _retry(src, fn, tries=3):
    """One logical request = up to 3 attempts (timeouts, connection errors, HTTP 429/5xx), 5 s then 15 s apart.
    It counts as failed only if every attempt fails; retries are noted in the source status."""
    import time
    stat(src)["requests"] += 1
    for i in range(tries):
        try: return fn()
        except Exception as ex:
            code = getattr(ex, "code", None)
            retryable = code is None or code == 429 or code >= 500
            if i < tries - 1 and retryable:
                wait = 5 if i == 0 else 15
                if code == 429:  # rate limit (Contracts Finder asks for about 2 minutes): honour Retry-After, at most 120 s
                    try: wait = min(120, int((getattr(ex, "headers", None) or {}).get("Retry-After") or 60))
                    except Exception: wait = 60
                stat(src)["notes"].append(mask(f"retry {i + 1} after {wait}s: {type(ex).__name__}: {ex}")[:160]); time.sleep(wait); continue
            stat(src)["failed"] += 1; stat(src)["notes"].append(mask(f"{type(ex).__name__}: {ex}")[:160]); raise
def _post(src, url, body):
    def f():
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**UA, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r: return json.loads(r.read().decode("utf8", "replace"))
    return _retry(src, f)
def _get(src, url, tries=3, timeout=90):
    def f():
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r: return r.read().decode("utf8", "replace")
    return _retry(src, f, tries)
def _first(v):
    if isinstance(v, dict):
        for k in ("eng", "ENG", "en"):
            if v.get(k): return _first(v[k])
        return _first(next(iter(v.values()), ""))
    if isinstance(v, list): return _first(v[0]) if v else ""
    return str(v or "")

# ---------------------------------------------------------------- deadlines
def parse_deadline(raw):
    """Return (date, aware datetime or None) from a published deadline such as '2026-12-10', '2026-12-10+02:00',
    '2026-12-15T14:00:00', '2026-11-23T17:00:00Z'. Impossible dates (2026-02-31) return (None, None)."""
    s = str(raw or "").strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})(?:[T ](\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?))?(Z|[+-]\d{2}:?\d{2})?$", s)
    if not m: return None, None
    try: d = datetime.date.fromisoformat(m.group(1))
    except ValueError: return None, None
    tz = m.group(3)
    tzinfo = None
    if tz:
        if tz == "Z": tzinfo = datetime.timezone.utc
        else:
            sign = 1 if tz[0] == "+" else -1; hh, mm = int(tz[1:3]), int(tz[-2:])
            tzinfo = datetime.timezone(sign * datetime.timedelta(hours=hh, minutes=mm))
    if m.group(2) and tzinfo:
        t = datetime.time.fromisoformat(m.group(2)[:8])
        return d, datetime.datetime.combine(d, t, tzinfo)
    if tzinfo:  # date with offset only: open until the end of that local day
        return d, datetime.datetime.combine(d, datetime.time(23, 59, 59), tzinfo)
    return d, None

def still_open(raw, now=None):
    """True while the published deadline may not have passed. With a time zone we compare exactly; without one we keep
    the notice until that date has ended everywhere (UTC-12), so no live notice is dropped early."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    d, at = parse_deadline(raw)
    if d is None: return False
    if at is not None: return at > now
    end = datetime.datetime.combine(d, datetime.time(23, 59, 59), datetime.timezone(datetime.timedelta(hours=-12)))
    return end > now

def _keep(src, raw):
    d, _ = parse_deadline(raw)
    if d is None: drop(src, "bad-deadline"); return False
    if not still_open(raw): drop(src, "closed"); return False
    return True

# ---------------------------------------------------------------- sources
def ted():
    S = "EU TED"; out = []; d = lambda n: (TODAY - datetime.timedelta(days=n)).strftime("%Y%m%d")
    base = f"notice-type IN (cn-standard cn-social) AND deadline-receipt-tender-date-lot>={TODAY.strftime('%Y%m%d')}"
    queries = [(f"{base} AND publication-date>={d(30)} AND estimated-value-proc>=1000000", 2e6, 12),
               (f"{base} AND publication-date>={d(45)} AND NOT buyer-country IN ({' '.join(EEA)})", 0, 6)]
    fields = ["publication-number", "notice-title", "buyer-name", "buyer-country", "deadline-receipt-tender-date-lot", "deadline-receipt-tender-time-lot",
              "contract-nature", "estimated-value-proc", "estimated-value-cur-proc"]
    for q, minv, pages in queries:
        for page in range(1, pages + 1):
            try: j = _post(S, "https://api.ted.europa.eu/v3/notices/search", {"query": q, "fields": fields, "limit": 250, "page": page})
            except Exception: break
            ns = j.get("notices") or []; stat(S)["raw"] += len(ns)
            for n in ns:
                it = ted_item(n, minv)
                if it is None: continue
                out.append(it)
            if len(ns) < 250: break
    by = {}
    for x in sorted(out, key=lambda x: -x["eur"]): by.setdefault(x["iso"], []).append(x)
    res = []
    for v in by.values():
        res += v[:25]
        for _ in v[25:]: drop(S, "country-cap")
    return res

def ted_deadline(dates, times):
    """TED gives lot deadlines as separate date ("2026-11-16+01:00") and time ("17:00:00+01:00") lists.
    Returns the earliest lot deadline as one ISO instant ("2026-11-16T17:00:00+01:00"), or the earliest date when no time."""
    best = None
    for i, d in enumerate(dates or []):
        m = re.match(r"(\d{4}-\d\d-\d\d)(Z|[+-]\d\d:\d\d)?$", str(d))
        if not m: continue
        t = (times or [])[i] if i < len(times or []) else None
        tm = re.match(r"(\d\d:\d\d(?::\d\d)?)(Z|[+-]\d\d:\d\d)?$", str(t or ""))
        if tm:
            hhmmss = tm.group(1) + (":00" if len(tm.group(1)) == 5 else ""); off = tm.group(2) or m.group(2)
            iso = f"{m.group(1)}T{hhmmss}{off}" if off else None
        else: iso = None
        key = iso or m.group(1) + "T23:59:59-12:00"
        try: inst = datetime.datetime.fromisoformat(key.replace("Z", "+00:00"))
        except ValueError: continue
        if best is None or inst < best[0]: best = (inst, iso or str(d))
    return best[1] if best else ""

def ted_item(n, minv=0):
    S = "EU TED"
    c3 = (n.get("buyer-country") or [""])[0]; iso = ISO3.get(c3)
    if not iso: drop(S, "no-country"); return None
    raw = ted_deadline(n.get("deadline-receipt-tender-date-lot"), n.get("deadline-receipt-tender-time-lot"))
    if not raw: drop(S, "no-deadline"); return None
    if not _keep(S, raw): return None
    cur = str(n.get("estimated-value-cur-proc") or "")
    try: val = float(n.get("estimated-value-proc") or 0)
    except Exception: val = 0
    eur = val * EUR.get(cur, 0)
    if minv and eur < minv: drop(S, "below-size"); return None
    title = re.sub(r"^[^–]{2,60}–\s*", "", _first(n.get("notice-title")), count=1)
    pn = n.get("publication-number", ""); nat = (n.get("contract-nature") or [""])[0]
    return {"iso": iso, "title": title[:220], "buyer": _first(n.get("buyer-name"))[:160], "deadline": raw[:10], "deadline_at": raw,
            "url": f"https://ted.europa.eu/en/notice/-/detail/{pn}", "sid": pn, "source": S, "type": "Contract notice", "project": "",
            "pm": "", "pmn": "", "pg": PG.get(nat, ""), "ma": "", "est": str(round(val)) if val else "", "cur": cur, "eur": round(eur)}

def _ocds(S, url, mk):
    """Only follow HTTPS pagination on the originating official host.
    Never follow malformed/external, repeating or non-HTTPS pagination URLs."""
    origin = urllib.parse.urlsplit(url)
    if origin.scheme != "https" or not origin.hostname or origin.username or origin.password:
        stat(S)["notes"].append("invalid OCDS source URL")
        return []
    out, seen = [], set()
    for _ in range(40):
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname != origin.hostname
                or parsed.port != origin.port or parsed.username or parsed.password
                or url in seen):
            stat(S)["notes"].append("unsafe or repeated OCDS pagination URL blocked")
            break
        seen.add(url)
        try: j = json.loads(_get(S, url))
        except Exception: break
        rels = j.get("releases") or []; stat(S)["raw"] += len(rels)
        for r in rels:
            it = mk(r)
            if it: out.append(it)
        nxt = (j.get("links") or {}).get("next")
        if not nxt or not rels: break
        url = urllib.parse.urljoin(url, str(nxt))
    return out

def _ocds_item(S, r, url, minv_eur=1.2e6):
    t = r.get("tender") or {}
    if t.get("status") != "active": drop(S, "not-active"); return None
    raw = str((t.get("tenderPeriod") or {}).get("endDate") or "")
    if not raw: drop(S, "no-deadline"); return None
    if not _keep(S, raw): return None
    v = t.get("value") or {}; amt = v.get("amount") or 0
    if amt * EUR.get(v.get("currency", "GBP"), 1.17) < minv_eur: drop(S, "below-size"); return None
    return {"iso": "GB", "title": str(t.get("title") or "")[:220], "buyer": str((r.get("buyer") or {}).get("name") or "")[:160],
            "deadline": raw[:10], "deadline_at": raw, "url": url, "sid": str(r.get("ocid") or r.get("id") or ""), "source": S,
            "type": "Tender notice", "project": "", "pm": "", "pmn": str(t.get("procurementMethodDetails") or "")[:60],
            "pg": PG.get(t.get("mainProcurementCategory"), ""), "ma": "", "est": str(round(amt)) if amt else "", "cur": v.get("currency", "")}

def uk():
    S = "UK Find a Tender"
    url = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?" + urllib.parse.urlencode(
        {"stages": "tender", "limit": 100, "updatedFrom": (TODAY - datetime.timedelta(days=21)).isoformat() + "T00:00:00"})
    out = _ocds(S, url, lambda r: _ocds_item(S, r, f"https://www.find-tender.service.gov.uk/Notice/{r.get('id')}"))
    seen = {}
    for x in out:
        if x["sid"] in seen: drop(S, "same-notice-update")
        seen[x["sid"]] = x  # the latest release of a notice wins
    res = sorted(seen.values(), key=lambda x: -float(x["est"] or 0))
    for _ in res[40:]: drop(S, "source-cap")
    return res[:40]

def cf_notice_url(release_id):
    """Contracts Finder release ids are '<notice uuid>-<release number>'; the public notice page uses the uuid."""
    m = re.match(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", str(release_id or ""), re.I)
    return f"https://www.contractsfinder.service.gov.uk/Notice/{m.group(1)}" if m else ""

def ukcf():
    S = "UK Contracts Finder"
    url = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?" + urllib.parse.urlencode(
        {"publishedFrom": (TODAY - datetime.timedelta(days=21)).isoformat() + "T00:00:00", "stages": "tender", "limit": 100})
    def mk(r):
        u = cf_notice_url(r.get("id"))
        if not u: drop(S, "bad-id"); return None
        return _ocds_item(S, r, u)
    out = _ocds(S, url, mk); seen = {}
    for x in out:
        if x["sid"] in seen: drop(S, "same-notice-update")
        seen[x["sid"]] = x
    return list(seen.values())

def prozorro():
    """Open above-threshold tenders of about US$1M+. The list API has no value field, so each candidate needs a detail call.
    Checked tenders are cached in data_branch/feeds/prozorro_seen.json, so each daily run checks up to 400 NEW candidates
    and reuses earlier results — over a few days every candidate is checked instead of always the most recent 400."""
    S = "Prozorro (Ukraine)"; cache_p = os.path.join(FEEDS, "prozorro_seen.json")
    try: cache = json.load(open(cache_p, encoding="utf8"))
    except Exception: cache = {}
    cands, url = [], "https://public-api.prozorro.gov.ua/api/2.5/tenders?" + urllib.parse.urlencode(
        {"descending": 1, "limit": 1000, "opt_fields": "status,procurementMethodType,tenderPeriod,tenderID"})
    stop = (TODAY - datetime.timedelta(days=4)).isoformat()
    for _ in range(25):
        try: j = json.loads(_get(S, url))
        except Exception: break
        d = j.get("data") or []; stat(S)["raw"] += len(d)
        for x in d:
            if x.get("status") != "active.tendering": continue
            if x.get("procurementMethodType") not in ("aboveThreshold", "aboveThresholdEU", "competitiveDialogueEU", "requestForProposal"): continue
            raw = str((x.get("tenderPeriod") or {}).get("endDate") or "")
            if still_open(raw): cands.append(x)
        if not d or str(d[-1].get("dateModified", ""))[:10] < stop: break
        url = (j.get("next_page") or {}).get("uri")
        if not url: break
    # re-check a cached tender when Prozorro says it changed since we read it (deadline extended, title edited);
    # changed ones go first, then new candidates, 400 detail calls at most per run
    changed = [x for x in cands if x["id"] in cache and str(x.get("dateModified") or "") > str(cache[x["id"]].get("mod") or "")]
    todo = (changed + [x for x in cands if x["id"] not in cache])[:400]
    import concurrent.futures as cf
    # bounded: detail calls get one 30 s attempt each, and the batch stops after 20 failures or 8 minutes,
    # so a Prozorro outage can never push the whole daily job past its time limit
    import time as _t
    t0, fails = _t.time(), [0]
    def one(x):
        if fails[0] >= 20 or _t.time() - t0 > 480: return None
        try: return json.loads(_get(S, "https://public-api.prozorro.gov.ua/api/2.5/tenders/" + x["id"], tries=1, timeout=30))["data"]
        except Exception: fails[0] += 1; return None
    with cf.ThreadPoolExecutor(8) as ex: details = list(ex.map(one, todo))
    if fails[0] >= 20 or _t.time() - t0 > 480: stat(S)["notes"].append("detail batch stopped early (failures or 8-minute limit)")
    for t in details:
        if not t: continue
        v = t.get("value") or {}
        cache[t["id"]] = {"amt": v.get("amount") or 0, "cur": v.get("currency", "UAH"), "dl": str((t.get("tenderPeriod") or {}).get("endDate") or ""),
                          "title": str(t.get("title_en") or t.get("title") or "")[:220], "buyer": str((t.get("procuringEntity") or {}).get("name") or "")[:160],
                          "tid": t.get("tenderID"), "pid": t.get("id"), "pmt": t.get("procurementMethodType"), "cat": t.get("mainProcurementCategory"),
                          "mod": str(t.get("dateModified") or "")}
    out = []
    for x in cands:
        c = cache.get(x["id"])
        if not c: drop(S, "not-checked-yet"); continue
        if c["amt"] * EUR.get(c["cur"], .022) < 1e6: drop(S, "below-size"); continue
        dl = str((x.get("tenderPeriod") or {}).get("endDate") or "") or c["dl"]   # today's list wins over the cached detail
        if dl != c["dl"]: c["dl"] = dl; st_ = stat(S); st_["deadline_updated"] = st_.get("deadline_updated", 0) + 1
        out.append({"iso": "UA", "title": c["title"], "buyer": c["buyer"], "deadline": c["dl"][:10], "deadline_at": c["dl"],
                    "url": f"https://prozorro.gov.ua/tender/{c['tid']}", "sid": c["tid"], "pid": c.get("pid") or "", "source": S, "type": "Tender notice", "project": "",
                    "pm": "", "pmn": str(c.get("pmt") or "")[:60], "pg": {"works": "CW", "goods": "GO", "services": "NC"}.get(c.get("cat"), ""),
                    "ma": "", "est": str(round(c["amt"])), "cur": c["cur"]})
    # forget tenders that have closed
    cache = {k: v for k, v in cache.items() if still_open(v.get("dl"))}
    try:
        os.makedirs(FEEDS, exist_ok=True); json.dump(cache, open(cache_p, "w", encoding="utf8"), ensure_ascii=False)
    except Exception: pass
    st = stat(S); st["candidates"] = len(cands); st["checked_now"] = len(todo); st["rechecked_changed"] = min(len(changed), 400); st["unchecked"] = sum(1 for x in cands if x["id"] not in cache)
    out.sort(key=lambda x: -float(x["est"] or 0))
    for _ in out[60:]: drop(S, "source-cap")
    return out[:60]

def dapa():
    S = "DAPA (Korea)"; key = os.environ.get("DAPA_KEY")
    if not key: stat(S)["skipped"] = True; return []
    q = {"serviceKey": key, "pageNo": 1, "numOfRows": 500,
         "inqryBgnDt": (TODAY - datetime.timedelta(days=60)).strftime("%Y%m%d"), "inqryEndDt": TODAY.strftime("%Y%m%d")}
    try: x = _get(S, "https://apis.data.go.kr/1690000/DCAIBidInfoService/getDCAIBidInfoList?" + urllib.parse.urlencode(q, safe="%"))
    except Exception: return []
    try: root = ET.fromstring(x)
    except Exception: stat(S)["notes"].append("not XML: " + mask(x[:200])); stat(S)["failed"] += 1; return []
    items = root.findall(".//item"); stat(S)["raw"] += len(items)
    if items: stat(S)["notes"].append("fields: " + ",".join(c.tag for c in items[0]))
    out = []
    from feed_tenders import iso_of
    for it in items:
        d = {c.tag: (c.text or "").strip() for c in it}
        g = lambda *ks: next((d[k] for k in d for kk in ks if kk.lower() in k.lower() and d[k]), "")
        dd = re.sub(r"\D", "", g("EndDt", "endDate", "clseDt", "Deadline"))[:8]
        raw = f"{dd[:4]}-{dd[4:6]}-{dd[6:8]}" if len(dd) == 8 else ""
        if not _keep(S, raw): continue
        cn = g("ntnNm", "cntry", "country", "nation"); iso = iso_of(cn) or ISO3.get(cn.upper())
        if not iso: drop(S, "no-country"); continue
        out.append({"iso": iso, "title": (g("EngNm", "engTitle", "Eng") or g("Nm", "title"))[:220], "buyer": g("ordrInst", "agency", "dmnd")[:160],
                    "deadline": raw, "deadline_at": raw, "url": g("url", "Url", "link") or "https://www.dapa.go.kr", "sid": g("bidNo", "ntceNo", "No", "id"),
                    "source": S, "type": g("ntceType", "type", "Form") or "Bid notice", "project": "", "pm": "", "pmn": "", "pg": "GO", "ma": "", "est": "", "cur": ""})
    return out

def sam():
    """US SAM.gov Get Opportunities public API — runs only when the SAM_KEY secret is set."""
    S = "SAM.gov (US)"; key = os.environ.get("SAM_KEY")
    if not key: stat(S)["skipped"] = True; return []
    f = lambda d: d.strftime("%m/%d/%Y")
    q = {"api_key": key, "postedFrom": f(TODAY - datetime.timedelta(days=30)), "postedTo": f(TODAY), "ptype": "o,k", "limit": 1000}
    try: j = json.loads(_get(S, "https://api.sam.gov/opportunities/v2/search?" + urllib.parse.urlencode(q)))
    except Exception: return []
    rows = j.get("opportunitiesData") or []; stat(S)["raw"] += len(rows); out = []
    for r in rows:
        raw = str(r.get("responseDeadLine") or "")
        if not _keep(S, raw[:25].replace(" ", "T") if raw else ""): continue
        out.append({"iso": "US", "title": str(r.get("title") or "")[:220], "buyer": str(r.get("fullParentPathName") or "")[:160],
                    "deadline": raw[:10], "deadline_at": raw, "url": r.get("uiLink") or "https://sam.gov", "sid": str(r.get("noticeId") or ""),
                    "source": S, "type": str(r.get("type") or "")[:40], "project": "", "pm": "", "pmn": "", "pg": "", "ma": "", "est": "", "cur": ""})
    return out[:80]

def canada():
    """CanadaBuys open tender notices (open data CSV) — NOT RUN: canadabuys.canada.ca robots.txt allows only search engines.
    Kept so the owner can decide after checking the terms; contact names, e-mails and phones are never stored."""
    import csv, io
    S = "CanadaBuys"
    try: txt = _get(S, "https://canadabuys.canada.ca/opendata/pub/openTenderNotice-ouvertAvisAppelOffres.csv")
    except Exception: return []
    out = []
    for r in csv.DictReader(io.StringIO(txt.lstrip("﻿"))):
        stat(S)["raw"] += 1
        ta = r.get("tradeAgreements-accordsCommerciaux-eng") or ""
        if not re.search(r"World Trade Organization|WTO|Korea", ta): drop(S, "no-trade-agreement"); continue
        raw = r.get("tenderClosingDate-appelOffresDateCloture") or ""
        if not _keep(S, raw): continue
        cat = r.get("procurementCategory-categorieApprovisionnement") or ""
        out.append({"iso": "CA", "title": (r.get("title-titre-eng") or "")[:220], "buyer": (r.get("contractingEntityName-nomEntitContractante-eng") or "")[:160],
                    "deadline": raw[:10], "deadline_at": raw, "url": r.get("noticeURL-URLavis-eng") or "https://canadabuys.canada.ca",
                    "sid": r.get("referenceNumber-numeroReference") or "", "source": S, "type": "Tender notice", "project": "",
                    "pm": "", "pmn": (r.get("procurementMethod-methodeApprovisionnement-eng") or "")[:60],
                    "pg": "CW" if "CNST" in cat else "GO" if "GD" in cat else "NC", "ma": "WTO-GPA" if "World Trade" in ta else "", "est": "", "cur": ""})
    return out[:100]
