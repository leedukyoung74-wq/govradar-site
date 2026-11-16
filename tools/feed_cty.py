"""Per-country tender intel: feeds/cty/{ISO}.json built from tenders/pipeline/awards feeds.
Small files so each country page fetches only its own numbers."""
import json, os, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data_branch", "feeds")
CAP = 20e9  # drop implausible project totals (data-entry outliers)

def load(n):
    try: return json.load(open(os.path.join(FEEDS, n), encoding="utf8"))
    except Exception: return {}

def main():
    t, p, a = load("tenders.json"), load("pipeline.json"), load("awards.json")
    out = {}
    def slot(iso):
        return out.setdefault(iso, {"t": [], "p": [], "a": []})
    today = datetime.date.today().isoformat()
    for x in t.get("items", []):
        if x.get("iso") and (x.get("deadline") or "9") >= today: slot(x["iso"])["t"].append(x)
    for x in p.get("items", []):
        if x.get("iso") and 0 < (x.get("usd") or 0) < CAP: slot(x["iso"])["p"].append(x)
    for x in a.get("items", []):
        if x.get("iso"): slot(x["iso"])["a"].append(x)
    d = os.path.join(FEEDS, "cty"); os.makedirs(d, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    for iso, s in out.items():
        T = sorted(s["t"], key=lambda x: x.get("deadline") or "9")
        P = sorted(s["p"], key=lambda x: -x["usd"])
        A = sorted(s["a"], key=lambda x: x.get("date") or "", reverse=True)
        ctry = (A[0]["ctry"] if A else (P[0]["ctry"] if P else "")).lower()
        loc = sum(1 for x in A if (x.get("wctry") or "").lower() == ctry) if ctry else 0
        by = {}
        for x in A: by[x.get("wctry") or "?"] = by.get(x.get("wctry") or "?", 0) + 1
        kr = sum(1 for x in A if "korea" in (x.get("wctry") or "").lower())
        rec = {"updated": now,
               "t": {"n": len(T), "items": [{k: x.get(k, "") for k in ("title", "buyer", "deadline", "url", "pg", "source")} for x in T[:5]]},
               "p": {"n": len(P), "usd": round(sum(x["usd"] for x in P)),
                     "items": [{"title": x["title"], "usd": x["usd"], "url": x["url"], "sec": x.get("wbsec", [])[:2]} for x in P[:6]]},
               "a": {"n": len(A), "local": loc, "kr": kr, "usd": round(sum(x.get("usd") or 0 for x in A)),
                     "by": sorted(by.items(), key=lambda kv: -kv[1])[:5],
                     "items": [{k: x.get(k, "") for k in ("date", "title", "winner", "wctry", "usd", "url", "pg")} for x in A[:6]]}}
        json.dump(rec, open(os.path.join(d, f"{iso}.json"), "w", encoding="utf8"), ensure_ascii=False)
    # site-wide summary for the about page radar and counters
    gaps = []
    for x in t.get("items", []):
        if x.get("source") != "World Bank": continue  # only WB has a long first-seen history
        try: gaps.append((datetime.date.fromisoformat(x["deadline"]) - datetime.date.fromisoformat(x["added"])).days)
        except Exception: pass
    gaps.sort()
    A = a.get("items", []); P = [x for x in p.get("items", []) if 0 < (x.get("usd") or 0) < CAP]
    T = [x for x in t.get("items", []) if (x.get("deadline") or "9") >= today]
    blips = {}
    for x in T:
        if x.get("iso"): blips[x["iso"]] = blips.get(x["iso"], 0) + 1
    dates = sorted(x.get("date") for x in A if x.get("date"))
    summ = {"updated": now, "t": {"n": len(T), "c": len(blips)}, "p": {"n": len(p.get("items", [])), "usd": round(sum(x["usd"] for x in P))},
            "a": {"n": len(A), "kr": sum(1 for x in A if "korea" in (x.get("wctry") or "").lower()), "from": dates[0] if dates else "", "to": dates[-1] if dates else ""},
            "gap": gaps[len(gaps) // 2] if gaps else None, "blips": blips}
    json.dump(summ, open(os.path.join(d, "_summary.json"), "w", encoding="utf8"), ensure_ascii=False)
    print("cty files", len(out))

if __name__ == "__main__": main()
