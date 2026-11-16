"""Daily intelligence feed — no AI, Python standard library only (runs on GitHub Actions after feed_tenders.py).
Writes two files the site loads in the browser:
  data_branch/feeds/awards.json   — recent World Bank contract awards: who won, from which country, for how much
  data_branch/feeds/pipeline.json — World Bank projects still in the pipeline (not yet approved), i.e. tenders 6-18 months ahead
Sources: search.worldbank.org/api/v2/procnotices (notice_type = Contract Award) and /api/v2/projects (status = Pipeline).
Prices are shown in the currency of the signed contract; a rough USD figure is added only for currencies in the FX table."""
import datetime, json, os, re, sys, html, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tools"))
from feed_tenders import get, iso_of, NAMES, SLUG, TODAY
try:
    from pages3 import classify
except Exception:
    classify = lambda s: []
FEEDS = os.path.join(ROOT, "data_branch", "feeds")
# approximate USD per unit, for sorting and "about US$" labels only (shown as approximate on the site)
FX = {"USD": 1, "EUR": 1.08, "GBP": 1.27, "JPY": .0067, "INR": .012, "CNY": .14, "IDR": .000063, "VND": .00004, "PHP": .017, "BDT": .0083, "PKR": .0036,
      "NGN": .00065, "KES": .0077, "ETB": .0072, "TZS": .00037, "UGX": .00027, "GHS": .065, "XOF": .0016, "XAF": .0016, "EGP": .02, "MAD": .1, "TRY": .029,
      "BRL": .18, "MXN": .055, "COP": .00025, "PEN": .27, "ARS": .001, "CLP": .00105, "UAH": .024, "KZT": .002, "UZS": .00008, "NPR": .0075, "LKR": .0033,
      "KRW": .00072, "THB": .029, "MYR": .23, "ZAR": .055, "ZMW": .037, "MWK": .00058, "RWF": .00072, "MZN": .0156, "TJS": .094, "KGS": .0115, "MNT": .00029,
      "GEL": .37, "AMD": .0026, "AZN": .59, "JOD": 1.41, "TND": .32, "DZD": .0074, "HNL": .04, "GTQ": .13, "DOP": .016, "BOB": .145, "PYG": .00013, "XCD": .37, "CDF": .00035, "NAD": .055, "SZL": .055, "BWP": .074, "LSL": .055, "AOA": .0011, "SLE": .044, "LRD": .0052, "GMD": .014, "HTG": .0076, "NIO": .027, "JMD": .0064}
def num(s):
    try: return float(re.sub(r"[^\d.]", "", s))
    except Exception: return None
def text(h): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "\n", h or ""))).strip()

def awards():
    out = []
    for os_ in range(0, 2000, 500):
        q = urllib.parse.urlencode({"format": "json", "rows": 500, "os": os_, "notice_type_exact": "Contract Award", "srt": "noticedate", "order": "desc", "fl": "*"})
        try: j = get("https://search.worldbank.org/api/v2/procnotices?" + q)
        except Exception as ex: print("awards page", os_, "failed:", ex); break
        rows = j.get("procnotices") or []
        if not rows: break
        for r in rows:
            h = str(r.get("notice_text") or "")
            m = re.search(r"Awarded Bidder\(s\):(.*?)(?:Evaluated Bidder|Rejected Bidder|<u><b>(?!Awarded)|$)", h, re.S)
            if not m: continue
            blk = m.group(1)
            names = [text(x) for x in re.findall(r"<b>([^<]{3,160})</b>", blk)]
            names = [re.sub(r"\s*\(\d+\)$", "", n) for n in names if not re.match(r"(Evaluation|Bid Price|Signed|Country)", n)]
            ctry = re.findall(r"Country:\s*([^<]+)<", blk)
            pr = re.search(r"Signed Contract price<br/>\s*([A-Z]{3})\s*([\d,\.]+)", blk)
            if not names: continue
            cur, amt = (pr.group(1), num(pr.group(2))) if pr else ("", None)
            usd = round(amt * FX[cur]) if amt and cur in FX else None
            iso = iso_of(r.get("project_ctry_name"), r.get("bid_description"))
            d = str(r.get("noticedate") or "")
            try: d = datetime.datetime.strptime(d, "%d-%b-%Y").date().isoformat()
            except Exception: d = d[:10]
            desc = re.sub(r"\s+", " ", str(r.get("bid_description") or r.get("project_name") or "")).strip()[:200]
            out.append({"date": d, "iso": iso or "", "ctry": str(r.get("project_ctry_name") or "")[:40], "title": desc, "project": str(r.get("project_name") or "")[:140],
                        "winner": names[0][:120], "wctry": ctry[0].strip()[:40] if ctry else "", "jv": len(names) > 1, "cur": cur, "amt": amt, "usd": usd,
                        "pg": str(r.get("procurement_group") or ""), "pm": str(r.get("procurement_method_code") or ""),
                        "url": "https://projects.worldbank.org/en/projects-operations/procurement-detail/" + str(r.get("id")),
                        "sec": classify(desc + " " + str(r.get("project_name") or ""))})
    return out

def us_date(v):
    """World Bank closing dates come as 12/31/2025 or 2025-12-31T00:00:00Z -> 2025-12-31"""
    v = str(v or "").strip(); m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", v)
    return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}" if m else v[:10]

def pipeline(status="Pipeline", pages=3):
    """World Bank projects by status: "Pipeline" (not yet approved, tenders 6-18 months ahead) or "Active" (approved,
    being carried out — procurement under way). Active rows use the total commitment (totalcommamt)."""
    out = []
    for os_ in range(0, pages * 500, 500):
        q = urllib.parse.urlencode({"format": "json", "rows": 500, "os": os_, "status_exact": status,
                                    "fl": "id,project_name,countryshortname,totalamt,totalcommamt,boardapprovaldate,sector1,sector,status,regionname,closingdate,url,mjtheme_namecode,lendinginstr"})
        try: j = get("https://search.worldbank.org/api/v2/projects?" + q)
        except Exception as ex: print("pipeline page", os_, "failed:", ex); break
        rows = list((j.get("projects") or {}).values())
        if not rows: break
        for r in rows:
            amt = num(str(r.get("totalamt") or "")) or 0
            if status == "Active": amt = num(str(r.get("totalcommamt") or "")) or amt
            iso = iso_of(r.get("countryshortname"), "")
            nm = re.sub(r"\s+", " ", str(r.get("project_name") or "")).strip()
            secs = [x.get("Name") for x in (r.get("sector") or []) if isinstance(x, dict) and x.get("Name")]
            out.append({"id": r.get("id"), "iso": iso or "", "ctry": str(r.get("countryshortname") or "")[:40], "title": nm[:200], "usd": amt,
                        "board": str(r.get("boardapprovaldate") or "")[:10], "close": us_date(r.get("closingdate")), "region": str(r.get("regionname") or "")[:40], "instr": str(r.get("lendinginstr") or "")[:40],
                        "wbsec": secs[:3], "url": r.get("url") or f"https://projects.worldbank.org/en/projects-operations/project-detail/{r.get('id')}",
                        "sec": classify(nm + " " + " ".join(secs))})
        if len(rows) < 500: break
    return out

def main():
    os.makedirs(FEEDS, exist_ok=True); now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    a = awards()
    if a:
        a.sort(key=lambda x: x["date"], reverse=True)
        by = {}
        for x in a: by[x["wctry"]] = by.get(x["wctry"], 0) + 1
        kr = [x for x in a if x["wctry"].lower() in ("korea, republic of", "korea", "south korea", "republic of korea", "korea, rep.")]
        json.dump({"updated": now, "count": len(a), "by_country": sorted(by.items(), key=lambda kv: -kv[1])[:40], "korea": kr[:60], "items": a[:1500]},
                  open(os.path.join(FEEDS, "awards.json"), "w", encoding="utf8"), ensure_ascii=False)
    p = pipeline()
    if p:
        p.sort(key=lambda x: -x["usd"])
        for x in p: x["n"] = NAMES.get(x["iso"]) or {}; x["slug"] = SLUG.get(x["iso"], "")
        json.dump({"updated": now, "count": len(p), "total_usd": sum(x["usd"] for x in p), "items": p},
                  open(os.path.join(FEEDS, "pipeline.json"), "w", encoding="utf8"), ensure_ascii=False)
    v = pipeline("Active", pages=8)
    if len(v) >= 1000:   # a short answer means the API failed part-way: keep yesterday's file
        v.sort(key=lambda x: -x["usd"])
        json.dump({"updated": now, "count": len(v), "total_usd": sum(x["usd"] for x in v), "items": v},
                  open(os.path.join(FEEDS, "active.json"), "w", encoding="utf8"), ensure_ascii=False)
    print("awards", len(a), "pipeline", len(p), "active", len(v))
if __name__ == "__main__": main()
