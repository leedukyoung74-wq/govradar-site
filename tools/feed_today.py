#!/usr/bin/env python3
"""Home "today's changes" — no AI. Reads the feeds this run just wrote and writes one small file,
data_branch/feeds/today.json, so the home page needs a single request:
new tenders first seen today, tenders closing within 2 days, newest official hazard alerts (48 h),
and the state of every data source. Nothing here is estimated: every number is a count of items in the feeds."""
import datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deadline import is_listed_open as is_open, state as DLs
from reporting_clock import reporting_day

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data_branch")
NOW = dt.datetime.now(dt.timezone.utc)

def load(p):
    try: return json.load(open(os.path.join(D, p), encoding="utf8"))
    except Exception: return {}

def slim(x):
    n = x.get("n") or {}
    return {"t": (x.get("title") or "")[:140], "iso": x.get("iso", ""), "n": {k: n.get(k, "") for k in ("ko", "en", "es", "fr", "ar", "vi", "id")} if n else {},
            "dl": x.get("deadline", ""), "dla": x.get("deadline_at", ""), "url": x.get("url", ""), "src": x.get("source", ""), "sec": list(x.get("sec") or [])[:2]}

def num(v):
    try: return float(v or 0)
    except Exception: return 0.0

def iso_date(v):
    """'2026-11-13', '2026-Nov-21 04:10' or '2026-11-13T..' -> '2026-11-13' ('' if unreadable)"""
    v = str(v or "")[:11]
    for f, n in (("%Y-%m-%d", 10), ("%Y-%b-%d", 11)):
        try: return dt.datetime.strptime(v[:n], f).date().isoformat()
        except ValueError: pass
    return ""

def public_source_state(name, record):
    """Public coverage label, not merely whether the provider HTTP call succeeded.

    Preserve raw ingestion status separately. Historical samples are not current
    opportunities, and bounded US pagination is not comprehensive US coverage.
    """
    raw = str(record.get("state") or "UNKNOWN")
    if raw in ("SUCCESS", "EMPTY_SUCCESS", "PARTIAL"):
        if (name == "DAPA (Korea)" and
                record.get("data_freshness") == "HISTORICAL_SAMPLE" and
                record.get("date_filter_verified") is False and
                record.get("kept", 0) in (0, "0")):
            return "HISTORICAL_ONLY"
        if (name == "SAM.gov (US)" and
                (record.get("coverage_partial") is True or
                 record.get("coverage") == "BOUNDED_PAGES_NOT_ALL_US_NOTICES")):
            return "PARTIAL"
    return raw


def build():
    today = reporting_day(NOW).isoformat()
    items = (load("feeds/tenders.json").get("items") or [])
    open_ = [x for x in items if is_open(x, NOW)]   # real closing time (deadline_at), not just the date
    new = [x for x in open_ if x.get("added") == today]
    urgent = sorted([x for x in open_ if x.get("urgent")], key=lambda x: x.get("deadline_at") or x.get("deadline") or "")
    # one of each source in turn, largest estimate first, so a single big source cannot fill the list
    by = {}
    for x in sorted(new, key=lambda x: -num(x.get("est"))): by.setdefault(x.get("source"), []).append(x)
    pick = []
    while len(pick) < 6 and any(by.values()):
        for k in list(by):
            if by[k] and len(pick) < 6: pick.append(by[k].pop(0))
    off = load("hz/official.json")
    cut = (NOW - dt.timedelta(hours=48)).date().isoformat()
    # Alert event timestamps remain UTC; never promote tomorrow UTC as an observed past alert.
    alert_utc_today = NOW.date().isoformat()
    # alerts dated in the last 48 h (future dates, e.g. an asteroid's approach day, are not "new")
    alerts = sorted([dict(a, date=iso_date(a.get("date"))) for v in (off.get("items") or {}).values() for a in v
                     if cut <= iso_date(a.get("date")) <= alert_utc_today], key=lambda a: a["date"], reverse=True)
    src = []
    for k, v in (load("feeds/sources_status.json") or {}).items():
        if not isinstance(v, dict) or v.get("state") == "SKIPPED": continue
        src.append({"name": k, "state": public_source_state(k, v),
                    "ingestion_state": v.get("state", "UNKNOWN"),
                    "coverage": v.get("coverage"),
                    "data_freshness": v.get("data_freshness"),
                    "kept": v.get("kept", 0), "new": v.get("new_today", 0)})
    for k, v in (off.get("sources") or {}).items():
        src.append({"name": k.upper(), "state": "SUCCESS" if v.get("ok") else "ERROR", "kept": v.get("n", 0), "new": None})
    for f, nm in (("feeds/econ.json", "World Bank indicators / FX"), ("feeds/sanctions.json", "Sanctions lists")):
        s = load(f).get("src") or {}
        if s: src.append({"name": nm, "state": "SUCCESS" if all(x.get("ok") for x in s.values()) else ("PARTIAL" if any(x.get("ok") for x in s.values()) else "ERROR"), "kept": None, "new": None})
    return {"updated": NOW.strftime("%Y-%m-%dT%H:%MZ"), "date": today,
            "n": {"open": len(open_), "new": len(new), "urgent": len(urgent), "countries": len({x.get("iso") for x in open_ if x.get("iso")}), "alerts": len(alerts),
                  "stale": sum(1 for x in items if x.get("stale")), "unknown_deadline": sum(1 for x in items if DLs(x, NOW) == "unknown")},
            "new": [slim(x) for x in pick], "urgent": [slim(x) for x in urgent[:6]],
            "alerts": [{"t": (a.get("t") or "")[:120], "date": a.get("date", ""), "src": a.get("src", ""), "url": a.get("url", ""), "k": a.get("k", "")} for a in alerts[:6]],
            "src": src}

if __name__ == "__main__":
    d = build()
    json.dump(d, open(os.path.join(D, "feeds", "today.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print("today:", d["n"], "sources", len(d["src"]))
