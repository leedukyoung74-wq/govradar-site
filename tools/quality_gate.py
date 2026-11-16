"""Pre-publish data quality gate. Runs after collection and BEFORE anything is pushed to the data branch.
Compares the freshly built feeds with what the site is reading now (the data branch as checked out) and exits 1 —
which stops the publish step — when the new data looks broken. Nothing is published on failure, so the site keeps
yesterday's data. Usage: python tools/quality_gate.py [new_feeds_dir] [published_feeds_dir]"""
import datetime, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
BOARD_FIELDS = ["iso", "title", "buyer", "deadline", "url", "source", "slug", "n", "added", "sec", "pg"]

def load(p):
    try: return json.load(open(p, encoding="utf8"))
    except Exception: return None

def check(new, old, now=None):
    """new/old: dicts of feed name -> parsed JSON (old may be empty). Returns list of failure strings (empty = pass)."""
    import feed_tenders as FT
    now = now or datetime.datetime.now(datetime.timezone.utc); bad = []
    t = new.get("tenders.json")
    if not t or not isinstance(t.get("items"), list): return ["tenders.json missing or unreadable"]
    items = t["items"]; ot = (old.get("tenders.json") or {}).get("items") or []
    if len(items) < 100: bad.append(f"only {len(items)} notices (minimum 100)")
    if ot and len(items) < 0.6 * len(ot): bad.append(f"notices fell from {len(ot)} to {len(items)} (more than 40% drop)")
    oc = len({x.get("iso") for x in ot}); nc = len({x.get("iso") for x in items})
    if oc and nc < 0.7 * oc: bad.append(f"countries fell from {oc} to {nc} (more than 30% drop)")
    if t.get("count") != len(items): bad.append(f"count field {t.get('count')} != {len(items)} items")
    inval = {}
    for x in items:
        why = FT.valid(x, now)
        if why: inval[why] = inval.get(why, 0) + 1
        for k in BOARD_FIELDS:
            if k not in x: inval["missing:" + k] = inval.get("missing:" + k, 0) + 1
    if inval: bad.append(f"invalid notices {inval}")
    urls = [x.get("url") for x in items]
    if len(urls) != len(set(urls)): bad.append(f"{len(urls) - len(set(urls))} duplicate URLs")
    try:
        age = (now - datetime.datetime.strptime(t.get("updated", ""), "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc)).total_seconds() / 3600
        if age > 6: bad.append(f"tenders.json stamp is {age:.1f} h old (was it rebuilt?)")
    except Exception: bad.append("tenders.json has no valid 'updated' stamp")
    # a source that used to deliver must not silently vanish (an ERROR day carries yesterday's notices instead)
    old_src = {}; new_src = {}
    for x in ot: old_src[x["source"]] = old_src.get(x["source"], 0) + 1
    for x in items: new_src[x["source"]] = new_src.get(x["source"], 0) + 1
    for s_, n_ in old_src.items():
        if n_ >= 20 and new_src.get(s_, 0) == 0: bad.append(f"source '{s_}' went from {n_} notices to 0")
    for f, minimum in (("awards.json", 100), ("pipeline.json", 100), ("active.json", 1000)):
        j = new.get(f)
        if j is None: continue
        n_ = len(j.get("items") or [])
        if n_ < minimum: bad.append(f"{f} has only {n_} items (minimum {minimum})")
    s = new.get("cty/_summary.json")
    if s is not None and ((s.get("t") or {}).get("n") or 0) < 0.9 * len([x for x in items if x.get("deadline", "") >= now.date().isoformat()]):
        bad.append("cty/_summary.json open-tender count does not match tenders.json")
    o = new.get("hz/official.json")
    if o is not None:
        srcs = o.get("sources") or {}
        if not srcs or not isinstance(o.get("items"), dict): bad.append("hz/official.json unreadable")
        elif sum(1 for v in srcs.values() if v.get("ok")) == 0: bad.append("hz/official.json: no agency answered (all 6 failed)")
    ec = new.get("econ.json")
    if ec is not None:
        cc = ec.get("c") if isinstance(ec, dict) else None
        if not isinstance(cc, dict): bad.append("econ.json unreadable")
        else:
            n_gdp = sum(1 for v in cc.values() if v.get("gdp")); n_fx = sum(1 for v in cc.values() if v.get("usd"))
            if n_gdp < 150: bad.append(f"econ.json: only {n_gdp} countries with GDP (minimum 150)")
            if n_fx < 120: bad.append(f"econ.json: only {n_fx} countries with an exchange rate (minimum 120)")
            if not any((v or {}).get("ok") for v in (ec.get("src") or {}).values()): bad.append("econ.json: no source answered")
            kr = (cc.get("KR") or {}).get("usd") or 0
            if kr and not 500 < kr < 5000: bad.append(f"econ.json: USD/KRW {kr} looks wrong")
    sx = new.get("sanctions.json")
    if sx is not None:
        cc = sx.get("c") if isinstance(sx, dict) else None
        if not isinstance(cc, dict): bad.append("sanctions.json unreadable")
        else:
            if len(cc) < 100: bad.append(f"sanctions.json: only {len(cc)} countries (minimum 100)")
            if not any((v or {}).get("ok") for v in (sx.get("src") or {}).values()): bad.append("sanctions.json: no list answered")
            if not ((cc.get("KP") or {}).get("un") or [0])[0]: bad.append("sanctions.json: North Korea has no UN entries — parsing is broken")
    return bad

def published(path, d):
    """Read a file as it is in the last data-branch commit (what the site serves), not the working copy."""
    try: return json.loads(subprocess.run(["git", "-C", d, "show", "HEAD:feeds/" + path], capture_output=True, text=True, check=True).stdout)
    except Exception: return None

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data_branch")
    names = ["tenders.json", "awards.json", "pipeline.json", "cty/_summary.json"]
    new = {k: load(os.path.join(d, "feeds", k)) for k in names}
    old = {k: published(k, d) for k in names}
    if os.path.exists(os.path.join(d, "feeds", "active.json")): new["active.json"] = load(os.path.join(d, "feeds", "active.json"))
    if os.path.exists(os.path.join(d, "feeds", "sanctions.json")): new["sanctions.json"] = load(os.path.join(d, "feeds", "sanctions.json"))
    if os.path.exists(os.path.join(d, "feeds", "econ.json")): new["econ.json"] = load(os.path.join(d, "feeds", "econ.json"))
    if os.path.exists(os.path.join(d, "hz", "official.json")): new["hz/official.json"] = load(os.path.join(d, "hz", "official.json"))
    bad = check(new, old)
    print(json.dumps({"result": "FAIL" if bad else "PASS", "problems": bad,
                      "notices": len((new.get("tenders.json") or {}).get("items") or []),
                      "published_notices": len((old.get("tenders.json") or {}).get("items") or [])}, ensure_ascii=False, indent=1))
    if bad: print("BLOCKED: not publishing; the site keeps the current data."); sys.exit(1)
