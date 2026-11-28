#!/usr/bin/env python3
"""Sanctions feed — no AI. Writes data_branch/feeds/sanctions.json: per country, how many listed people and
organisations are tied to it (nationality, citizenship or address) on four official public lists, and which
programmes / regimes they fall under.

Sources (all public, no key; attribution on the page):
- UN Security Council Consolidated List (XML)          https://scsanctions.un.org
- US Treasury OFAC SDN list (CSV, public domain)      https://sanctionslistservice.ofac.treas.gov
- EU Financial Sanctions Files (CSV, the public token the EU publishes for download; reuse with attribution)
- UK Sanctions List, FCDO (CSV, Open Government Licence v3.0)
A count is "entries tied to the country", NOT a statement that the country itself is sanctioned.
A source that fails keeps its last good numbers (ok=false), so one list being down never blanks the page.
"""
import collections, csv, datetime as dt, io, json, os, re, sys, time, unicodedata, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_branch", "feeds", "sanctions.json")
NAMES = json.load(open(os.path.join(ROOT, "tools", "country_names.json")))
UA = {"User-Agent": "GOV-RADAR-feed/1.0 (leedukyoung74@gmail.com)"}
URL = {"un": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
       "us": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV",
       "us_add": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADD.CSV",
       "eu": "https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw",
       "uk": "https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv"}
MIN = {"un": 500, "us": 5000, "eu": 1500, "uk": 2000}   # fewer distinct entries than this = broken download
NOW = dt.datetime.now(dt.timezone.utc)
csv.field_size_limit(10 ** 8)

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().replace("&", " and ")
    s = re.sub(r"\bst\.?\s", " saint ", " " + s)
    return re.sub(r"[^a-z]", "", s)

def iso(name):
    return NAMES.get(norm(name)) if name and name.strip() not in ("-0-", "na") else None

def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r: return r.read()
        except Exception as ex:
            if i == tries - 1: raise
            print(f"retry {i + 1}: {type(ex).__name__}"[:120]); time.sleep(5 if i == 0 else 15)

def tally(entries):
    """entries: {id: (set(iso2), set(programme))} -> (count per country, top programmes per country, unknown names)"""
    n, prog = collections.Counter(), collections.defaultdict(collections.Counter)
    for cs, ps in entries.values():
        for c in cs:
            n[c] += 1
            for p in ps: prog[c][p] += 1
    return n, {c: [p for p, _ in v.most_common(4)] for c, v in prog.items()}

def parse_un(raw):
    e, miss = {}, collections.Counter()
    for kind in ("INDIVIDUAL", "ENTITY"):
        for x in ET.fromstring(raw).iter(kind):
            cs = set()
            for v in [*x.findall("NATIONALITY/VALUE"), *x.findall(f"{kind}_ADDRESS/COUNTRY")]:
                c = iso(v.text or "")
                if c: cs.add(c)
                elif (v.text or "").strip(): miss[v.text.strip()] += 1
            e[x.findtext("REFERENCE_NUMBER") or x.findtext("DATAID")] = (cs, {(x.findtext("UN_LIST_TYPE") or "").strip()} - {""})
    return e, miss

def parse_us(sdn, add):
    e, miss = {}, collections.Counter()
    for r in csv.reader(io.StringIO(sdn.decode("latin-1"))):
        if len(r) > 3 and r[0].strip().isdigit():
            e[r[0].strip()] = (set(), {p.strip() for p in r[3].replace("[", "").split("]") if p.strip() and p.strip() != "-0-"})
    for r in csv.reader(io.StringIO(add.decode("latin-1"))):
        if len(r) > 4 and r[0].strip() in e:
            c = iso(r[4])
            if c: e[r[0].strip()][0].add(c)
            elif r[4].strip() not in ("", "-0-"): miss[r[4].strip()] += 1
    return e, miss

def parse_eu(raw):
    rd = csv.reader(io.StringIO(raw.decode("utf-8-sig", "replace")), delimiter=";")
    h = next(rd); ix = {k: h.index(k) for k in ("Entity_LogicalId", "Entity_Regulation_Programme", "Address_CountryIso2Code", "Citizenship_CountryIso2Code")}
    e = {}
    for r in rd:
        if len(r) <= max(ix.values()): continue
        cs, ps = e.setdefault(r[ix["Entity_LogicalId"]], (set(), set()))
        for k in ("Address_CountryIso2Code", "Citizenship_CountryIso2Code"):
            c = r[ix[k]].strip().upper()
            if len(c) == 2 and c.isalpha() and c not in ("00", "XX"): cs.add(c)
        if r[ix["Entity_Regulation_Programme"]].strip(): ps.add(r[ix["Entity_Regulation_Programme"]].strip())
    return e, collections.Counter()

def short_uk(n):
    """'The Russia (Sanctions) (EU Exit) Regulations 2019' -> 'Russia'"""
    n = re.sub(r"^The ", "", n.strip()); n = re.sub(r"\s*\((Sanctions|EU Exit)\)", "", n)
    return re.sub(r"\s*Regulations \d{4}$", "", n).replace(" Sanctions", "").strip()

def parse_uk(raw):
    rd = csv.reader(io.StringIO(raw.decode("utf-8-sig", "replace")))
    next(rd); h = next(rd)
    g, reg, ac, nat = h.index("OFSI Group ID"), h.index("Regime Name"), h.index("Address Country"), h.index("Nationality(/ies)")
    e, miss = {}, collections.Counter()
    for r in rd:
        if len(r) <= nat: continue
        cs, ps = e.setdefault(r[g], (set(), set()))
        for name in [r[ac], *re.split(r"\(\d+\)", r[nat])]:
            name = name.strip().strip(",").strip()
            c = iso(name)
            if c: cs.add(c)
            elif name: miss[name] += 1
        if r[reg].strip(): ps.add(short_uk(r[reg]))
    return e, miss

def build(old):
    src, per = dict(old.get("src") or {}), {}
    oldc = old.get("c") or {}
    jobs = {"un": lambda: parse_un(get(URL["un"])), "us": lambda: parse_us(get(URL["us"]), get(URL["us_add"])),
            "eu": lambda: parse_eu(get(URL["eu"])), "uk": lambda: parse_uk(get(URL["uk"]))}
    for k, job in jobs.items():
        try:
            e, miss = job()
            if len(e) < MIN[k]: raise ValueError(f"only {len(e)} entries (minimum {MIN[k]})")
            per[k] = tally(e)
            src[k] = {"ok": True, "entries": len(e), "tied": sum(1 for v in e.values() if v[0]), "at": NOW.strftime("%Y-%m-%dT%H:%MZ"),
                      "unmatched": [f"{n} ({c})" for n, c in miss.most_common(8)]}
        except Exception as ex:
            src[k] = {**(src.get(k) or {}), "ok": False, "err": f"{type(ex).__name__}: {ex}"[:160]}
    c = {}
    for k in jobs:
        if k in per:
            n, prog = per[k]
            for cc, v in n.items(): c.setdefault(cc, {})[k] = [v, prog.get(cc, [])]
        else:   # keep last good numbers for a list that failed today
            for cc, v in oldc.items():
                if k in v: c.setdefault(cc, {})[k] = v[k]
    return {"updated": NOW.strftime("%Y-%m-%dT%H:%MZ"), "src": src, "c": dict(sorted(c.items())),
            "credit": {"un": "UN Security Council Consolidated List", "us": "US Treasury OFAC SDN List",
                       "eu": "EU Financial Sanctions Files (European Commission)", "uk": "UK Sanctions List, FCDO (Open Government Licence v3.0)"}}

if __name__ == "__main__":
    try: old = json.load(open(OUT, encoding="utf8"))
    except Exception: old = {}
    d = build(old)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(d, open(OUT, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print(f"sanctions feed: {len(d['c'])} countries", {k: (v.get("ok"), v.get("entries"), v.get("tied")) for k, v in d["src"].items()})
    for k, v in d["src"].items():
        if v.get("unmatched"): print(f"  {k} names not matched:", v["unmatched"])
    sys.exit(0 if any(v.get("ok") for v in d["src"].values()) else 1)
