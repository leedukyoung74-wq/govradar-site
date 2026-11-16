"""One deadline rule for the feeds (Python side of web/dl.js).
A deadline_at with a time and offset closes at that instant. A date with no time stays open until that date has
ended everywhere (23:59:59 at UTC-12). Used by feed_cty.py and feed_today.py so server counts match the pages."""
import datetime as dt, re

RX = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$")

def closes_at(deadline_at="", deadline=""):
    a = str(deadline_at or "")
    if RX.match(a):
        try: return dt.datetime.fromisoformat(a.replace("Z", "+00:00")), True
        except ValueError: pass
    m = re.match(r"^\d{4}-\d{2}-\d{2}", a or str(deadline or ""))
    if not m: return None, False
    try: d = dt.date.fromisoformat(m.group(0))
    except ValueError: return None, False
    return dt.datetime.combine(d, dt.time(23, 59, 59), dt.timezone(dt.timedelta(hours=-12))), False

def state(x, now=None):
    """"open" (exact time ahead) | "date_only" (date without time, kept until the day ends at UTC-12) | "closed" | "unknown"."""
    now = now or dt.datetime.now(dt.timezone.utc)
    c, timed = closes_at(x.get("deadline_at"), x.get("deadline"))
    if c is None: return "unknown"
    if now >= c: return "closed"
    return "open" if timed else "date_only"

def is_open(x, now=None):
    """Counts as an open tender: a readable deadline still ahead. Unknown or impossible deadlines are NOT open."""
    return state(x, now) in ("open", "date_only")

def is_listed_open(x, now=None):
    """Open AND verified: items whose re-verification is delayed (stale) are shown with a label but kept out of
    open counts, new/urgent lists and alerts."""
    return is_open(x, now) and not x.get("stale")
