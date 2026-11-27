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
            # A 429 means the UK official endpoint has explicitly refused more
            # requests for this run. Deferring the rest is safer than retrying
            # 2 minutes later and continuing the same already-too-large scan.
            if code == 429 and src == "SAM.gov (US)":
                # Respect provider rate limits: one 429 is enough to defer.
                # Repeated retries worsen exhausted daily free quotas.
                stat(src)["failed"] += 1
                stat(src)["notes"].append("upstream_429_deferred: await provider quota reset")
                raise
            if code == 429 and src == "UK Find a Tender":
                raw = (getattr(ex, "headers", None) or {}).get("Retry-After")
                try: seconds = max(0, min(86400, int(raw)))
                except (TypeError, ValueError): seconds = None
                stat(src)["failed"] += 1
                stat(src)["notes"].append("upstream_429_deferred: retry_after_seconds=" +
                                          str(seconds if seconds is not None else "unknown") +
                                          "; no further requests this run")
                raise
            retryable = code is None or code == 429 or code >= 500
            if i < tries - 1 and retryable:
                wait = 5 if i == 0 else 15
                if code == 429:  # rate limit (Contracts Finder asks for about 2 minutes): honour Retry-After, at most 120 s
                    try: wait = min(120, int((getattr(ex, "headers", None) or {}).get("Retry-After") or 60))
                    except Exception: wait = 60
                stat(src)["notes"].append(mask(f"retry {i + 1} after {wait}s: {type(ex).__name__}: {ex}")[:160]); time.sleep(wait); continue
            stat(src)["failed"] += 1; stat(src)["notes"].append(mask(f"{type(ex).__name__}: {ex}")[:160]); raise
def _post(src, url, body, tries=3, timeout=90):
    def f():
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**UA, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode("utf8", "replace"))
    return _retry(src, f, tries)
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
    import time
    S = "EU TED"; out = []; d = lambda n: (TODAY - datetime.timedelta(days=n)).strftime("%Y%m%d")
    deadline = time.monotonic() + 140
    base = f"notice-type IN (cn-standard cn-social) AND deadline-receipt-tender-date-lot>={TODAY.strftime('%Y%m%d')}"
    queries = [(f"{base} AND publication-date>={d(30)} AND estimated-value-proc>=1000000", 2e6, 12),
               (f"{base} AND publication-date>={d(45)} AND NOT buyer-country IN ({' '.join(EEA)})", 0, 6)]
    fields = ["publication-number", "notice-title", "buyer-name", "buyer-country", "deadline-receipt-tender-date-lot", "deadline-receipt-tender-time-lot",
              "contract-nature", "estimated-value-proc", "estimated-value-cur-proc"]
    for q, minv, pages in queries:
        for page in range(1, pages + 1):
            if time.monotonic() >= deadline:
                stat(S)["failed"] += 1
                stat(S)["notes"].append("source_time_budget_exceeded: TED partial results; previous notices need verification")
                break
            try: j = _post(S, "https://api.ted.europa.eu/v3/notices/search",
                           {"query": q, "fields": fields, "limit": 250, "page": page},
                           tries=2, timeout=30)
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

def _ocds(S, url, mk, *, max_pages=40, timeout=30, tries=2, time_budget=140, min_interval=0):
    """Bound pagination and forbid cross-origin/downgrade/repeating source URLs."""
    import time
    base = urllib.parse.urlsplit(url)
    if base.scheme != "https" or not base.hostname or base.username or base.password:
        stat(S)["failed"] += 1
        stat(S)["notes"].append("invalid_ocds_source_url")
        return []
    out, seen = [], set()
    deadline = time.monotonic() + time_budget
    last_request_at = None
    for _ in range(max_pages):
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname != base.hostname
                or parsed.port != base.port or parsed.username or parsed.password or url in seen):
            stat(S)["failed"] += 1
            stat(S)["notes"].append("unsafe_or_repeated_ocds_pagination_blocked")
            break
        if time.monotonic() >= deadline:
            stat(S)["failed"] += 1
            stat(S)["notes"].append("source_time_budget_exceeded: OCDS partial results")
            break
        # Pace official API requests. A strict time budget takes precedence;
        # if we cannot wait politely, mark PARTIAL rather than press the API.
        if min_interval and last_request_at is not None:
            wait = max(0, min_interval - (time.monotonic() - last_request_at))
            if time.monotonic() + wait >= deadline:
                stat(S)["failed"] += 1
                stat(S)["notes"].append("rate_pacing_time_budget: OCDS partial results")
                break
            if wait: time.sleep(wait)
        last_request_at = time.monotonic()
        seen.add(url)
        before_failed = stat(S)["failed"]
        try: j = json.loads(_get(S, url, tries=tries, timeout=timeout))
        except Exception as ex:
            # If a test adapter or unexpected upstream error skips _retry,
            # still treat a mid-pagination exception as PARTIAL, not SUCCESS.
            if stat(S)["failed"] == before_failed:
                stat(S)["failed"] += 1
                stat(S)["notes"].append("ocds_request_exception: " + type(ex).__name__)
            break
        # A provider error object or a malformed/empty cursor page must not
        # look like a successful complete scan after earlier valid pages.
        if (not isinstance(j, dict) or not isinstance(j.get("releases"), list)
                or not isinstance(j.get("links", {}), dict)):
            stat(S)["failed"] += 1
            stat(S)["notes"].append("malformed_ocds_release_page: partial results")
            break
        rels = j["releases"]; stat(S)["raw"] += len(rels)
        nxt = j.get("links", {}).get("next")
        if not rels and nxt:
            stat(S)["failed"] += 1
            stat(S)["notes"].append("empty_ocds_page_with_next_cursor: partial results")
            break
        for r in rels:
            it = mk(r)
            if it: out.append(it)
        if not nxt or not rels: break
        url = urllib.parse.urljoin(url, str(nxt))
    else:
        # Reaching a configured cap with another page pending is PARTIAL,
        # never a confirmed complete official release snapshot.
        stat(S)["failed"] += 1
        stat(S)["notes"].append("source_page_cap_reached: OCDS partial results")
    return out

def _ocds_item(S, r, url, minv_eur=1.2e6):
    t = r.get("tender") or {}
    if t.get("status") != "active": drop(S, "not-active"); return None
    raw = str((t.get("tenderPeriod") or {}).get("endDate") or "")
    if not raw: drop(S, "no-deadline"); return None
    if not _keep(S, raw): return None
    v = t.get("value") or {}
    # Newer UK Procurement Act notices may publish amountGross instead of amount.
    # Preserve the distinction in the record rather than implying a net estimate.
    gross_only = v.get("amount") is None and v.get("amountGross") is not None
    try: amt = float(v.get("amount") if v.get("amount") is not None else (v.get("amountGross") or 0))
    except (ValueError, TypeError): drop(S, "invalid-estimate"); return None
    if amt * EUR.get(v.get("currency", "GBP"), 1.17) < minv_eur: drop(S, "below-size"); return None
    return {"iso": "GB", "title": str(t.get("title") or "")[:220], "buyer": str((r.get("buyer") or {}).get("name") or "")[:160],
            "deadline": raw[:10], "deadline_at": raw, "url": url, "sid": str(r.get("ocid") or r.get("id") or ""), "source": S,
            "type": "Tender notice", "project": "", "pm": "", "pmn": str(t.get("procurementMethodDetails") or "")[:60],
            "pg": PG.get(t.get("mainProcurementCategory"), ""), "ma": "", "est": str(round(amt)) if amt else "", "cur": v.get("currency", ""),
            "est_gross": gross_only}

def uk_backfill_shard(cutoff, *, pieces=4):
    """Choose one rotating slice of the 19-day historical UK update window.

    Four successive UTC days use all four relative slices while respecting the
    upstream's reported 12-request/2-minute throttling. Every single-day result
    is PARTIAL: shards rotate with each day and are never an exhaustive scan.
    """
    if cutoff.tzinfo is None or pieces < 1:
        raise ValueError("cutoff must be timezone-aware and pieces positive")
    recent_start = cutoff - datetime.timedelta(days=2)
    older_start = cutoff - datetime.timedelta(days=21)
    slot = cutoff.date().toordinal() % pieces
    span = recent_start - older_start
    start = older_start + span * slot / pieces
    end = older_start + span * (slot + 1) / pieces
    return slot, start, end


def uk():
    """Latest 48h first; rotate four historical 19-day shards without extra calls.

    Never claim a single run exhaustively covers UK opportunities. Source
    cap, provider 429, and skip policies remain strict.
    """
    S = "UK Find a Tender"
    endpoint = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?"
    cutoff = datetime.datetime.now(datetime.timezone.utc)
    recent_start = cutoff - datetime.timedelta(days=2)
    shard, shard_from, shard_to = uk_backfill_shard(cutoff)
    fmt = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
    recent_url = endpoint + urllib.parse.urlencode({
        "limit": 100, "updatedFrom": fmt(recent_start), "updatedTo": fmt(cutoff)})
    mk = lambda r: _ocds_item(S, r, f"https://www.find-tender.service.gov.uk/Notice/{r.get('id')}")

    out = _ocds(S, recent_url, mk, max_pages=8, timeout=20, tries=2,
                time_budget=70, min_interval=2)
    st = stat(S)
    st["coverage"] = "RECENT_48H_PLUS_ONE_OF_FOUR_ROTATING_19D_BACKFILL_SHARDS"
    st["coverage_partial"] = True
    st["backfill_shard_index"] = shard + 1
    st["backfill_shard_total"] = 4
    st["backfill_window_start"] = fmt(shard_from)
    st["backfill_window_end"] = fmt(shard_to)
    st["notes"].append("split_48h_recent_plus_rotating_19d_backfill: at_most_12_source_pages; not a full UK scan")

    timeout_seen = any("TimeoutError" in n or "timed out" in n.lower() for n in st["notes"])
    rate_limited = any("429" in n or "upstream_429_deferred" in n for n in st["notes"])
    if not out and st["raw"] == 0 and st["failed"] and timeout_seen and not rate_limited:
        # Preserve existing resilience with a smaller 48-hour page.
        st["notes"].append("partial_48h_fallback_after_recent_timeout: coverage incomplete")
        fallback_url = endpoint + urllib.parse.urlencode({
            "limit": 10, "updatedFrom": fmt(recent_start), "updatedTo": fmt(cutoff)})
        spare_pages = max(0, min(4, 12 - st["requests"]))
        if spare_pages:
            out = _ocds(S, fallback_url, mk, max_pages=spare_pages,
                        timeout=20, tries=1, time_budget=40, min_interval=2)
        # No older 19d scan after a failure: don't amplify load on a slow source.
    elif not rate_limited and st["requests"] < 12:
        older_url = endpoint + urllib.parse.urlencode({
            "limit": 100, "updatedFrom": fmt(shard_from), "updatedTo": fmt(shard_to)})
        spare_pages = min(4, 12 - st["requests"])
        if spare_pages > 0:
            out.extend(_ocds(S, older_url, mk, max_pages=spare_pages, timeout=20,
                             tries=1, time_budget=40, min_interval=2))
    # The UK source releases can contain several updates for the same OCDS ID.
    # Keep only the latest encountered release, without inventing a complete scan.
    seen = {}
    for x in out:
        if x["sid"] in seen: drop(S, "same-notice-update")
        seen[x["sid"]] = x
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
    import time as _clock
    list_deadline = _clock.monotonic() + 140
    seen_pages = set()
    for _ in range(25):
        page_url = urllib.parse.urlsplit(url)
        if (page_url.scheme != "https" or page_url.hostname != "public-api.prozorro.gov.ua"
                or page_url.username or page_url.password or url in seen_pages):
            stat(S)["failed"] += 1
            stat(S)["notes"].append("unsafe_or_repeated_prozorro_pagination_blocked")
            break
        if _clock.monotonic() >= list_deadline:
            stat(S)["failed"] += 1
            stat(S)["notes"].append("source_time_budget_exceeded: Prozorro list partial")
            break
        seen_pages.add(url)
        try: j = json.loads(_get(S, url, tries=1, timeout=25))
        except Exception: break
        d = j.get("data") or []; stat(S)["raw"] += len(d)
        for x in d:
            if x.get("status") != "active.tendering": continue
            if x.get("procurementMethodType") not in ("aboveThreshold", "aboveThresholdEU", "competitiveDialogueEU", "requestForProposal"): continue
            raw = str((x.get("tenderPeriod") or {}).get("endDate") or "")
            if still_open(raw): cands.append(x)
        if not d or str(d[-1].get("dateModified", ""))[:10] < stop: break
        nxt = (j.get("next_page") or {}).get("uri")
        if not nxt: break
        url = urllib.parse.urljoin(url, str(nxt))
    # re-check a cached tender when Prozorro says it changed since we read it (deadline extended, title edited);
    # changed ones go first, then new candidates, 400 detail calls at most per run
    changed = [x for x in cands if x["id"] in cache and str(x.get("dateModified") or "") > str(cache[x["id"]].get("mod") or "")]
    todo = (changed + [x for x in cands if x["id"] not in cache])[:400]
    import concurrent.futures as cf
    # bounded: one 30-second attempt, 8 workers, 4-minute batch budget.
    import time as _t
    t0, fails = _t.monotonic(), [0]
    def one(x):
        if fails[0] >= 20 or _t.monotonic() - t0 > 240: return None
        try: return json.loads(_get(S, "https://public-api.prozorro.gov.ua/api/2.5/tenders/" + x["id"], tries=1, timeout=30))["data"]
        except Exception: fails[0] += 1; return None
    with cf.ThreadPoolExecutor(8) as ex: details = list(ex.map(one, todo))
    if fails[0] >= 20 or _t.monotonic() - t0 > 240: stat(S)["notes"].append("detail batch stopped early (failures or 4-minute limit)")
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

def _dapa_day(raw):
    """DAPA GW uses bidTo='YYYYMMDD', not generic EndDt aliases."""
    digits = re.sub(r"[^0-9]", "", str(raw or ""))[:8]
    if len(digits) != 8: return ""
    try: return datetime.date(int(digits[:4]), int(digits[4:6]), int(digits[6:])).isoformat()
    except ValueError: return ""


def dapa():
    """DAPA overseas tenders: list seqn/bidTo/orgPlace; resolve official oriUrl via detail ONLY for open rows.
    The upstream list is historical (observed latest pages in 2019 during 2026-11-25 audit).
    Do not relabel archived 2015–2019 bids as newly open, and never fabricate notice links.
    """
    S = "DAPA (Korea)"; key = os.environ.get("DAPA_KEY")
    if not key:
        stat(S)["skipped"] = True
        stat(S)["notes"].append("not_configured:DAPA_KEY")
        return []
    today = TODAY
    def get_list(page, rows=500):
        q = {"serviceKey": key, "pageNo": page, "numOfRows": rows,
             "inqryBgnDt": (today-datetime.timedelta(days=60)).strftime("%Y%m%d"),
             "inqryEndDt": today.strftime("%Y%m%d")}
        raw = _get(S, "https://apis.data.go.kr/1690000/DCAIBidInfoService/getDCAIBidInfoList?" + urllib.parse.urlencode(q, safe="%"))
        root = ET.fromstring(raw)
        items = [{c.tag.rsplit("}", 1)[-1]: (c.text or "").strip() for c in item} for item in root.findall(".//item")]
        stat(S)["raw"] += len(items)
        return items, int(root.findtext(".//totalCount") or len(items))
    try:
        first, total = get_list(1)
    except Exception:
        stat(S)["notes"].append("list_first_page_failed")
        return []
    last_page = max(1, (total + 499) // 500)
    latest = first
    if last_page > 1:
        try: latest, _ = get_list(last_page)
        except Exception: stat(S)["notes"].append("list_latest_page_failed")
    stat(S)["notes"].append("upstream_total=" + str(total) + "; latest_page=" + str(last_page))
    # The upstream's sort order is not guaranteed. A historic last page
    # does NOT prove the first page (or unscanned middle pages) are historic.
    first_dates = [_dapa_day(x.get("bidTo")) for x in first]
    last_dates = [_dapa_day(x.get("bidTo")) for x in latest]
    first_dates = [d for d in first_dates if d]
    last_dates = [d for d in last_dates if d]
    if first_dates:
        stat(S)["sampled_first_page_max_bid_to"] = max(first_dates)
    if last_dates:
        stat(S)["notes"].append("latest_page_max_bidTo=" + max(last_dates))
        stat(S)["sampled_last_page_max_bid_to"] = max(last_dates)
    sampled_dates = first_dates + (last_dates if last_page > 1 else [])
    if sampled_dates:
        sampled_latest = max(sampled_dates)
        stat(S)["sampled_latest_bid_to"] = sampled_latest
        # A status applies only to the bounded sample, never to all DAPA.
        if sampled_latest < today.isoformat():
            stat(S)["data_freshness"] = "HISTORICAL_SAMPLE"
            stat(S)["notes"].append("upstream_historical_sample: both sampled pages have no future deadline")
    stat(S)["coverage"] = "FIRST_AND_LAST_PAGES_ONLY"
    stat(S)["date_filter_verified"] = False
    # The date-filter parameters previously returned the same 7,205 historic
    # rows with and without filters. Do not assert that the provider applied them.
    # First and last pages give a bounded sample without exhausting the free quota.
    # A skipped or failed page is not proof there are zero open bids elsewhere.
    candidates = list(latest) + (first if last_page > 1 else [])
    seen_seq = set(); out = []
    for row in candidates:
        seqn = str(row.get("seqn") or "").strip()
        if not seqn or seqn in seen_seq: continue
        seen_seq.add(seqn)
        deadline = _dapa_day(row.get("bidTo"))
        if not _keep(S, deadline): continue
        place = (row.get("orgPlace") or "").upper()
        iso = place if len(place) == 2 and place.isalpha() else ISO3.get(place)
        if not iso:
            drop(S, "no-country"); continue
        title = (row.get("bidNameEng") or row.get("bidNameKor") or "").strip()
        if not title:
            drop(S, "no-title"); continue
        # List responses do NOT include an original notice URL; official detail does.
        q = urllib.parse.urlencode({"serviceKey": key, "seqn": seqn}, safe="%")
        try:
            xml = _get(S, "https://apis.data.go.kr/1690000/DCAIBidInfoService/getDCAIBidInfoDetail?" + q, tries=2)
            item = ET.fromstring(xml).find(".//item")
            det = {c.tag.rsplit("}", 1)[-1]: (c.text or "").strip() for c in item} if item is not None else {}
        except Exception:
            drop(S, "detail-failed"); continue
        original = str(det.get("oriUrl") or "").strip()
        parts = urllib.parse.urlsplit(original)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            drop(S, "missing-official-original-url"); continue
        verified_end = _dapa_day(det.get("bidTo") or row.get("bidTo"))
        if not _keep(S, verified_end): continue
        out.append({"iso": iso, "title": title[:220], "buyer": (det.get("orderOrgan") or row.get("orgPlaceNm") or "DAPA")[:160],
                    "deadline": verified_end, "deadline_at": verified_end, "url": original, "sid": seqn,
                    "source": S, "type": (row.get("anucTypeNm") or "Bid notice")[:80], "project": "",
                    "pm": "", "pmn": "", "pg": "", "ma": "", "est": "", "cur": ""})
    if not out: stat(S)["notes"].append("no_verified_open_notice_in_bounded_pages")
    return out

def sam():
    """SAM.gov public solicitations: preserve official active state, posted/deadline filters,
    bounded pagination and explicitly report incomplete provider coverage.
    3 requests/day, maximum 1000 rows/request; NEVER imply the first 80
    records represent all U.S. procurement opportunities.
    """
    S = "SAM.gov (US)"; key = os.environ.get("SAM_KEY")
    if not key:
        stat(S)["skipped"] = True
        stat(S)["notes"].append("not_configured:SAM_KEY")
        return []
    f = lambda d: d.strftime("%m/%d/%Y")
    per_page, max_pages, cap = 1000, 3, 80
    # Date filtering is supported in the official v2 API. We focus on recently
    # posted solicitations closing within 180 days, not archival awards.
    base = {"api_key": key, "postedFrom": f(TODAY - datetime.timedelta(days=30)),
            "postedTo": f(TODAY), "rdlfrom": f(TODAY),
            "rdlto": f(TODAY + datetime.timedelta(days=180)),
            "ptype": "o,k", "limit": per_page}
    collected = {}
    total = None
    scanned_pages = 0
    for page in range(max_pages):
        if total is not None and page * per_page >= total: break
        # SAM.gov offset is the zero-based PAGE INDEX, not an absolute row offset.
        q = dict(base, offset=page)
        try:
            result = json.loads(_get(S, "https://api.sam.gov/opportunities/v2/search?" + urllib.parse.urlencode(q),
                                     tries=2, timeout=35))
            if not isinstance(result, dict) or not isinstance(result.get("opportunitiesData"), list):
                stat(S)["failed"] += 1
                stat(S)["notes"].append("sam_unexpected_response_schema")
                break
        except Exception:
            break
        rows = result["opportunitiesData"]
        scanned_pages += 1
        stat(S)["raw"] += len(rows)
        if total is None:
            try: total = max(0, int(result.get("totalRecords", len(rows))))
            except (TypeError, ValueError): total = len(rows)
        for r in rows:
            # The response's 'active' field denotes official current state.
            # Unknown state must NOT be quietly advertised as active.
            active = str(r.get("active") or "").strip().lower()
            if active not in ("yes", "true"):
                drop(S, "inactive" if active in ("no", "false") else "active-unverified")
                continue
            raw = str(r.get("responseDeadLine") or r.get("reponseDeadLine") or "").strip()
            if not _keep(S, raw[:25].replace(" ", "T") if raw else ""): continue
            url = str(r.get("uiLink") or "").strip()
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme != "https" or parsed.hostname not in ("sam.gov", "www.sam.gov"):
                drop(S, "nonofficial-or-missing-url")
                continue
            sid = str(r.get("noticeId") or "").strip()
            title = str(r.get("title") or "").strip()
            if not sid or not title:
                drop(S, "missing-id-or-title")
                continue
            # If the same notice appears twice, latest API version is published.
            collected[sid] = {"iso": "US", "title": title[:220],
                              "buyer": str(r.get("fullParentPathName") or "")[:160],
                              "deadline": raw[:10], "deadline_at": raw,
                              "url": url, "sid": sid, "source": S,
                              "type": str(r.get("type") or "")[:40],
                              "project": "", "pm": "", "pmn": "",
                              "pg": "", "ma": "", "est": "", "cur": ""}
        if len(rows) < per_page: break
    out = sorted(collected.values(), key=lambda r: (r["deadline"], r["sid"]))
    st = stat(S)
    st["upstream_total"] = total if total is not None else 0
    st["pages_scanned"] = scanned_pages
    st["rows_scanned"] = st["raw"]
    st["selection_cap"] = cap
    st["search_window_days"] = 30
    st["closing_window_days"] = 180
    st["coverage"] = "BOUNDED_PAGES_NOT_ALL_US_NOTICES"
    st["coverage_partial"] = bool(total is not None and total > st["raw"])
    if st["coverage_partial"]:
        st["notes"].append("upstream_pagination_not_exhaustive; not an all-US count")
    if len(out) > cap:
        for unused in out[cap:]: drop(S, "source-cap")
    # Some official uiLink pages require SAM.gov login/role; this is not
    # evidence that an unauthenticated visitor can open the record.
    return out[:cap]

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
