"""Is the public site wired to the data feeds, and would today's feed render on it?
1. Public pages answer and still load the feed files from the data branch (tender board, home, a country page).
2. The data-branch feed that the site reads right now is recent and non-empty.
3. The freshly collected local tenders.json has every field the site's tender board script uses.
Writes the result to the path given (default data_branch/feeds/site_check.json). Read-only: it changes nothing."""
import datetime, json, os, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://radar.wmm-hoa.com"
RAW = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/"
UA = {"User-Agent": "Mozilla/5.0 (GOV RADAR site check; 73036396@naver.com)"}
MAX_AGE_HOURS = 30  # the daily run is at 06:10 KST; older than this means a missed run
BOARD_FIELDS = ["iso", "title", "buyer", "deadline", "url", "source", "slug", "n", "added", "sec", "pg"]

def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r: return r.status, r.read().decode("utf8", "replace")
    except urllib.error.HTTPError as ex: return ex.code, ""
    except Exception as ex: return type(ex).__name__, ""

def main(out):
    res = {"checked": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "pages": [], "feeds": {}, "local": {}}
    for path, needle in (("/ko/mdb/?stay=1", RAW + "tenders.json"), ("/ko/?stay=1", RAW + "tenders.json"),
                         ("/ko/ethiopia/?stay=1", RAW + "cty/"), ("/ko/about/?stay=1", RAW + "cty/_summary.json")):
        code, html = get(SITE + path)
        res["pages"].append({"page": path, "status": code, "reads_feed": needle in html})
    for f in ("tenders.json", "cty/_summary.json", "awards.json"):
        code, body = get(RAW + f)
        try: j = json.loads(body)
        except Exception: j = {}
        upd = j.get("updated", ""); age = None
        try: age = round((datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.strptime(upd, "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc)).total_seconds() / 3600, 1)
        except Exception: pass
        res["feeds"][f] = {"status": code, "updated": upd, "age_hours": age, "count": j.get("count") or (j.get("t") or {}).get("n")}
    lp = os.path.join(ROOT, "data_branch", "feeds", "tenders.json")
    try:
        items = json.load(open(lp, encoding="utf8"))["items"]
        missing = {k: sum(1 for x in items if k not in x) for k in BOARD_FIELDS}
        res["local"] = {"items": len(items), "missing_fields": {k: v for k, v in missing.items() if v}, "sources": sorted({x["source"] for x in items})}
    except Exception as ex:
        res["local"] = {"error": type(ex).__name__}
    # Do not accept future-dated feeds as fresh; they can be caused by a clock or timestamp bug.
    for v in res["feeds"].values():
        v["fresh"] = v["age_hours"] is not None and -0.1 <= v["age_hours"] <= MAX_AGE_HOURS
        v["issue"] = ("unreachable" if v["status"] != 200 else
                      "invalid_or_future_timestamp" if v["age_hours"] is None or v["age_hours"] < -0.1 else
                      "stale_publication" if not v["fresh"] else
                      "empty_feed" if (v["count"] or 0) <= 0 else "ok")
    if res["local"].get("missing_fields"):
        res["local"]["issue"] = "invalid_new_items"
    elif res["local"].get("error"):
        res["local"]["issue"] = "local_collection_unavailable"
    else:
        res["local"]["issue"] = "ok"
    res["failed_public_feeds"] = [name for name, item in res["feeds"].items() if item["issue"] != "ok"]
    ok = all(p["status"] == 200 and p["reads_feed"] for p in res["pages"]) and all(v["status"] == 200 and (v["count"] or 0) > 0 and v["fresh"] for v in res["feeds"].values()) \
         and not res["local"].get("missing_fields") and not res["local"].get("error")
    res["result"] = "PASS" if ok else "FAIL"
    os.makedirs(os.path.dirname(out), exist_ok=True); json.dump(res, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1)); return ok

if __name__ == "__main__":
    if not main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data_branch", "feeds", "site_check.json")):
        print("FAIL: a public page does not load the feeds, a feed is empty or older than", MAX_AGE_HOURS, "hours, or the new feed misses board fields"); sys.exit(1)
