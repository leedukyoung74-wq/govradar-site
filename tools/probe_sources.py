"""Check every source in tools/sources/registry.json: does the URL answer, and does robots.txt forbid crawling?
Writes url_status, robots and checked back into the registry. This is reachability only — an open page is NOT
proof that tenders can be collected; the "collect" field changes only when a collector actually succeeds."""
import json, os, sys, datetime, urllib.request, urllib.parse, urllib.robotparser, concurrent.futures as cf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "tools", "sources", "registry.json")
UA = "GOV RADAR source check (73036396@naver.com)"

def head(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return str(r.status)
    except urllib.error.HTTPError as ex: return str(ex.code)
    except Exception as ex: return type(ex).__name__

def robots(url):
    p = urllib.parse.urlparse(url); rp = urllib.robotparser.RobotFileParser()
    try:
        req = urllib.request.Request(f"{p.scheme}://{p.netloc}/robots.txt", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r: rp.parse(r.read().decode("utf8", "replace").splitlines())
    except urllib.error.HTTPError as ex:
        return "no-robots-file" if ex.code == 404 else "unknown"  # an unreadable robots.txt is NOT permission
    except Exception: return "unknown"
    return "allowed" if rp.can_fetch(UA, url) else "disallowed"

def check(s):
    if not s.get("url"): return s | {"url_status": "no-url", "robots": "", "checked": TODAY}
    return s | {"url_status": head(s["url"]), "robots": robots(s["url"]), "checked": TODAY}

TODAY = datetime.date.today().isoformat()
if __name__ == "__main__":
    reg = json.load(open(REG, encoding="utf8"))
    with cf.ThreadPoolExecutor(16) as ex: reg = list(ex.map(check, reg))
    out = sys.argv[1] if len(sys.argv) > 1 else REG
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(reg, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    ok = sum(1 for s in reg if s["url_status"].startswith(("2", "3")))
    print("sources", len(reg), "answering", ok, "robots-disallowed", sum(1 for s in reg if s["robots"] == "disallowed"),
          "collecting (PASS)", sum(1 for s in reg if s["collect"] == "PASS"))
