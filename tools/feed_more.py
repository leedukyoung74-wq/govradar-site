"""Extra tender sources for feed_tenders.py — standard library only.
- EU TED (Tenders Electronic Daily) search API v3: EU/EEA notices of about EUR 2M+, and every notice from buyers
  outside the EU/EEA (EU-funded tenders abroad, candidate countries).
- UK Find a Tender Service OCDS API: open UK notices of about GBP 1M+.
- Korea DAPA overseas tender information (data.go.kr), only when the DAPA_KEY secret is set.
Each function returns items in the same shape as feed_tenders.worldbank()."""
import datetime, json, os, re, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISO3 = json.load(open(os.path.join(ROOT, "src", "iso3.json")))
TODAY = datetime.date.today(); MIN_DL = (TODAY + datetime.timedelta(days=3)).isoformat()
UA = {"User-Agent": "GOV RADAR tender collector (73036396@naver.com)"}
EEA = "AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE NOR ISL LIE CHE".split()
# rough EUR rates, only to rank and filter by size (labelled "approx." on the site)
EUR = {"EUR": 1, "SEK": .087, "NOK": .085, "DKK": .134, "PLN": .23, "CZK": .04, "RON": .2, "HUF": .0025, "BGN": .51, "CHF": 1.05,
       "ISK": .0066, "GBP": 1.17, "USD": .92, "MKD": .016, "MDL": .051, "RSD": .0085, "TRY": .027, "ALL": .0098, "UAH": .022}
PG = {"works": "CW", "supplies": "GO", "services": "NC"}

def _post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r: return json.loads(r.read().decode("utf8", "replace"))
def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r: return r.read().decode("utf8", "replace")
def _first(v):
    if isinstance(v, dict):
        for k in ("eng", "ENG", "en"):
            if v.get(k): return _first(v[k])
        return _first(next(iter(v.values()), ""))
    if isinstance(v, list): return _first(v[0]) if v else ""
    return str(v or "")

def ted():
    out = []; d = lambda n: (TODAY - datetime.timedelta(days=n)).strftime("%Y%m%d"); dl = (TODAY + datetime.timedelta(days=3)).strftime("%Y%m%d")
    base = f"notice-type IN (cn-standard cn-social) AND deadline-receipt-tender-date-lot>={dl}"
    queries = [(f"{base} AND publication-date>={d(30)} AND estimated-value-proc>=1000000", 2e6, 12),
               (f"{base} AND publication-date>={d(45)} AND NOT buyer-country IN ({' '.join(EEA)})", 0, 6)]
    fields = ["publication-number", "notice-title", "buyer-name", "buyer-country", "deadline-receipt-tender-date-lot",
              "contract-nature", "estimated-value-proc", "estimated-value-cur-proc"]
    for q, minv, pages in queries:
        for page in range(1, pages + 1):
            try: j = _post("https://api.ted.europa.eu/v3/notices/search", {"query": q, "fields": fields, "limit": 250, "page": page})
            except Exception as ex: print("ted", page, "failed:", ex); break
            ns = j.get("notices") or []
            for n in ns:
                c3 = (n.get("buyer-country") or [""])[0]; iso = ISO3.get(c3)
                if not iso: continue
                dls = sorted(str(x)[:10] for x in (n.get("deadline-receipt-tender-date-lot") or []) if re.match(r"\d{4}-\d\d-\d\d", str(x)))
                if not dls or dls[0] < MIN_DL: continue
                cur = str(n.get("estimated-value-cur-proc") or "");
                try: val = float(n.get("estimated-value-proc") or 0)
                except Exception: val = 0
                eur = val * EUR.get(cur, 0)
                if minv and eur < minv: continue
                title = _first(n.get("notice-title")); title = re.sub(r"^[^–]{2,60}–\s*", "", title, count=1)
                pn = n.get("publication-number", "")
                nat = (n.get("contract-nature") or [""])[0]
                out.append({"iso": iso, "title": title[:220], "buyer": _first(n.get("buyer-name"))[:160], "deadline": dls[0],
                            "url": f"https://ted.europa.eu/en/notice/-/detail/{pn}", "source": "EU TED", "type": "Contract notice", "project": "",
                            "pm": "", "pmn": "", "pg": PG.get(nat, ""), "ma": "", "est": str(round(val)) if val else "", "cur": cur, "eur": round(eur)})
            if len(ns) < 250: break
    # keep the biggest per country so one large market cannot flood the board
    by = {}
    for x in sorted(out, key=lambda x: -x["eur"]): by.setdefault(x["iso"], []).append(x)
    res = [x for v in by.values() for x in v[:25]]
    print("ted", len(out), "kept", len(res)); return res

def uk():
    out = []; url = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?" + urllib.parse.urlencode(
        {"stages": "tender", "limit": 100, "updatedFrom": (TODAY - datetime.timedelta(days=21)).isoformat() + "T00:00:00"})
    for _ in range(40):
        try: j = json.loads(_get(url))
        except Exception as ex: print("uk failed:", ex); break
        for r in j.get("releases") or []:
            t = r.get("tender") or {}
            if t.get("status") != "active": continue
            dl = str((t.get("tenderPeriod") or {}).get("endDate") or "")[:10]
            if not dl or dl < MIN_DL: continue
            v = t.get("value") or {}; amt = v.get("amount") or 0
            if amt * EUR.get(v.get("currency", "GBP"), 1.17) < 1.2e6: continue
            out.append({"iso": "GB", "title": str(t.get("title") or "")[:220], "buyer": str((r.get("buyer") or {}).get("name") or "")[:160], "deadline": dl,
                        "url": f"https://www.find-tender.service.gov.uk/Notice/{r.get('id')}", "source": "UK Find a Tender", "type": "Tender notice", "project": "",
                        "pm": "", "pmn": str(t.get("procurementMethodDetails") or "")[:60], "pg": PG.get(t.get("mainProcurementCategory"), ""),
                        "ma": "", "est": str(round(amt)) if amt else "", "cur": v.get("currency", "")})
        nxt = (j.get("links") or {}).get("next")
        if not nxt or not j.get("releases"): break
        url = nxt
    seen = {}
    for x in out: seen[x["url"]] = x
    res = sorted(seen.values(), key=lambda x: -float(x["est"] or 0))[:40]
    print("uk", len(seen), "kept", len(res)); return res

def dapa():
    key = os.environ.get("DAPA_KEY")
    if not key: print("dapa: no DAPA_KEY, skipped"); return []
    out = []
    q = {"serviceKey": key, "pageNo": 1, "numOfRows": 500,
         "inqryBgnDt": (TODAY - datetime.timedelta(days=60)).strftime("%Y%m%d"), "inqryEndDt": TODAY.strftime("%Y%m%d")}
    try: x = _get("https://apis.data.go.kr/1690000/DCAIBidInfoService/getDCAIBidInfoList?" + urllib.parse.urlencode(q, safe="%"))
    except Exception as ex: print("dapa failed:", ex); return []
    try: root = ET.fromstring(x)
    except Exception: print("dapa: not XML:", x[:300]); return []
    items = root.findall(".//item")
    if items: print("dapa fields:", [c.tag for c in items[0]])
    else: print("dapa: no items:", x[:300])
    for it in items:
        d = {c.tag: (c.text or "").strip() for c in it}
        g = lambda *ks: next((d[k] for k in d for kk in ks if kk.lower() in k.lower() and d[k]), "")
        dl = re.sub(r"\D", "", g("EndDt", "endDate", "clseDt", "Deadline"))[:8]
        dl = f"{dl[:4]}-{dl[4:6]}-{dl[6:8]}" if len(dl) == 8 else ""
        if not dl or dl < MIN_DL: continue
        cn = g("ntnNm", "cntry", "country", "nation")
        from feed_tenders import iso_of
        iso = iso_of(cn) or ISO3.get(cn.upper())
        if not iso: continue
        out.append({"iso": iso, "title": (g("EngNm", "engTitle", "Eng") or g("Nm", "title"))[:220], "buyer": g("ordrInst", "agency", "dmnd")[:160], "deadline": dl,
                    "url": g("url", "Url", "link") or "https://www.dapa.go.kr", "source": "DAPA (Korea)", "type": g("ntceType", "type", "Form") or "Bid notice",
                    "project": "", "pm": "", "pmn": "", "pg": "GO", "ma": "", "est": "", "cur": ""})
    print("dapa", len(out)); return out

def ukcf():
    """UK Contracts Finder OCDS search (below and above threshold, England). GBP 1M+ only."""
    out = []; url = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?" + urllib.parse.urlencode(
        {"publishedFrom": (TODAY - datetime.timedelta(days=21)).isoformat() + "T00:00:00", "stages": "tender", "limit": 100})
    for _ in range(40):
        try: j = json.loads(_get(url))
        except Exception as ex: print("ukcf failed:", ex); break
        for r in j.get("releases") or []:
            t = r.get("tender") or {}
            if t.get("status") != "active": continue
            dl = str((t.get("tenderPeriod") or {}).get("endDate") or "")[:10]
            if not dl or dl < MIN_DL: continue
            v = t.get("value") or {}; amt = v.get("amount") or 0
            if amt * EUR.get(v.get("currency", "GBP"), 1.17) < 1.2e6: continue
            nid = str(r.get("id") or "")[:36]
            out.append({"iso": "GB", "title": str(t.get("title") or "")[:220], "buyer": str((r.get("buyer") or {}).get("name") or "")[:160], "deadline": dl,
                        "url": f"https://www.contractsfinder.service.gov.uk/Notice/{nid}", "source": "UK Contracts Finder", "type": "Tender notice", "project": "",
                        "pm": "", "pmn": "", "pg": PG.get(t.get("mainProcurementCategory"), ""), "ma": "", "est": str(round(amt)), "cur": v.get("currency", "")})
        nxt = (j.get("links") or {}).get("next")
        if not nxt or not j.get("releases"): break
        url = nxt
    print("ukcf", len(out)); return out

def canada():
    """CanadaBuys open tender notices (open data CSV). Keeps notices open to foreign suppliers under WTO-GPA or the Canada-Korea FTA.
    Contact names, e-mails and phone numbers in the file are not stored."""
    import csv, io
    try: txt = _get("https://canadabuys.canada.ca/opendata/pub/openTenderNotice-ouvertAvisAppelOffres.csv")
    except Exception as ex: print("canada failed:", ex); return []
    out = []
    for r in csv.DictReader(io.StringIO(txt.lstrip("﻿"))):
        ta = r.get("tradeAgreements-accordsCommerciaux-eng") or ""
        if not re.search(r"World Trade Organization|WTO|Korea", ta): continue
        dl = (r.get("tenderClosingDate-appelOffresDateCloture") or "")[:10]
        if not dl or dl < MIN_DL: continue
        cat = (r.get("procurementCategory-categorieApprovisionnement") or "")
        out.append({"iso": "CA", "title": (r.get("title-titre-eng") or "")[:220], "buyer": (r.get("contractingEntityName-nomEntitContractante-eng") or "")[:160],
                    "deadline": dl, "url": r.get("noticeURL-URLavis-eng") or "https://canadabuys.canada.ca", "source": "CanadaBuys", "type": "Tender notice",
                    "project": "", "pm": "", "pmn": (r.get("procurementMethod-methodeApprovisionnement-eng") or "")[:60],
                    "pg": "CW" if "CNST" in cat else "GO" if "GD" in cat else "NC", "ma": "WTO-GPA" if "World Trade" in ta else "", "est": "", "cur": ""})
    out.sort(key=lambda x: x["deadline"])
    print("canada", len(out)); return out[:100]

def prozorro():
    """Ukraine Prozorro public API: open EU-procedure (international) tenders of about UAH 40M+ (roughly US$1M)."""
    cands, url = [], "https://public-api.prozorro.gov.ua/api/2.5/tenders?" + urllib.parse.urlencode(
        {"descending": 1, "limit": 1000, "opt_fields": "status,procurementMethodType,tenderPeriod,tenderID"})
    stop = (TODAY - datetime.timedelta(days=4)).isoformat()
    for _ in range(25):
        try: j = json.loads(_get(url))
        except Exception as ex: print("prozorro list failed:", ex); break
        d = j.get("data") or []
        for x in d:
            if x.get("status") == "active.tendering" and x.get("procurementMethodType") in ("aboveThreshold", "aboveThresholdEU", "competitiveDialogueEU", "requestForProposal"):
                dl = str((x.get("tenderPeriod") or {}).get("endDate") or "")[:10]
                if dl >= MIN_DL: cands.append(x)
        if not d or str(d[-1].get("dateModified", ""))[:10] < stop: break
        url = (j.get("next_page") or {}).get("uri")
        if not url: break
    import concurrent.futures as cf
    def one(x):
        try: return json.loads(_get("https://public-api.prozorro.gov.ua/api/2.5/tenders/" + x["id"]))["data"]
        except Exception: return None
    with cf.ThreadPoolExecutor(8) as ex: details = list(ex.map(one, cands[:400]))
    out = []
    for t in details:
        if not t: continue
        v = t.get("value") or {}; amt = v.get("amount") or 0
        if amt * EUR.get(v.get("currency", "UAH"), .022) < 1e6: continue
        out.append({"iso": "UA", "title": str(t.get("title_en") or t.get("title") or "")[:220], "buyer": str((t.get("procuringEntity") or {}).get("name") or "")[:160],
                    "deadline": str(t["tenderPeriod"]["endDate"])[:10], "url": f"https://prozorro.gov.ua/tender/{t.get('tenderID')}", "source": "Prozorro (Ukraine)",
                    "type": "Tender notice", "project": "", "pm": "", "pmn": str(t.get("procurementMethodType") or "")[:60],
                    "pg": {"works": "CW", "goods": "GO", "services": "NC"}.get(t.get("mainProcurementCategory"), ""), "ma": "International" if "EU" in str(t.get("procurementMethodType")) else "",
                    "est": str(round(amt)), "cur": v.get("currency", "")})
    out.sort(key=lambda x: -float(x["est"] or 0))
    print("prozorro candidates", len(cands), "kept", len(out[:60])); return out[:60]

def sam():
    """US SAM.gov Get Opportunities public API — runs only when the SAM_KEY secret is set."""
    key = os.environ.get("SAM_KEY")
    if not key: print("sam: no SAM_KEY, skipped"); return []
    f = lambda d: d.strftime("%m/%d/%Y")
    q = {"api_key": key, "postedFrom": f(TODAY - datetime.timedelta(days=30)), "postedTo": f(TODAY), "ptype": "o,k", "limit": 1000}
    try: j = json.loads(_get("https://api.sam.gov/opportunities/v2/search?" + urllib.parse.urlencode(q)))
    except Exception as ex: print("sam failed:", str(ex).replace(key, "***")); return []
    out = []
    for r in j.get("opportunitiesData") or []:
        dl = str(r.get("responseDeadLine") or "")[:10]
        if not dl or dl < MIN_DL: continue
        out.append({"iso": "US", "title": str(r.get("title") or "")[:220], "buyer": str(r.get("fullParentPathName") or "")[:160], "deadline": dl,
                    "url": r.get("uiLink") or "https://sam.gov", "source": "SAM.gov (US)", "type": str(r.get("type") or "")[:40], "project": "",
                    "pm": "", "pmn": "", "pg": "", "ma": "", "est": "", "cur": ""})
    print("sam", len(out)); return out[:80]
