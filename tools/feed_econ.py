#!/usr/bin/env python3
"""Country economy feed — no AI. Writes data_branch/feeds/econ.json for the "at a glance" card on country pages.

Sources (both free, no key):
- World Bank Indicators API (CC BY 4.0): population, GDP, GDP per capita, real GDP growth, CPI inflation —
  the latest non-empty year for each country (mrnev=1). Regional aggregates are skipped.
- ExchangeRate-API open access (open.er-api.com, daily; attribution required: https://www.exchangerate-api.com).
  Country -> currency comes from tools/currency.json (a fixed table, CLDR via Babel).
A source that fails keeps its last good values from the current file and is marked ok=false, so the page
can show the date the values are from instead of pretending they are new.
"""
import datetime as dt, json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_branch", "feeds", "econ.json")
ISO3 = json.load(open(os.path.join(ROOT, "tools", "iso3.json")))
CUR = json.load(open(os.path.join(ROOT, "tools", "currency.json")))
UA = {"User-Agent": "GOV-RADAR-feed/1.0 (leedukyoung74@gmail.com)"}
IND = {"pop": "SP.POP.TOTL", "gdp": "NY.GDP.MKTP.CD", "pc": "NY.GDP.PCAP.CD", "gr": "NY.GDP.MKTP.KD.ZG", "cpi": "FP.CPI.TOTL.ZG"}
NOW = dt.datetime.now(dt.timezone.utc)

def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read().decode("utf8", "replace"))
        except Exception as ex:
            if i == tries - 1: raise
            print(f"retry {i + 1}: {type(ex).__name__}: {ex}"[:160]); time.sleep(5 if i == 0 else 15)

def parse_wb(j):
    """World Bank JSON page -> {ISO2: [value, year]} for real countries only."""
    out = {}
    for x in (j[1] if isinstance(j, list) and len(j) > 1 and j[1] else []):
        a2 = ISO3.get(x.get("countryiso3code") or "")
        if a2 and x.get("value") is not None: out[a2] = [round(x["value"], 4 if abs(x["value"]) < 1000 else 0), x.get("date")]
    return out

def parse_fx(j):
    if j.get("result") != "success" or not isinstance(j.get("rates"), dict): raise ValueError("fx: bad answer")
    return j["rates"], j.get("time_last_update_utc", "")

def build(old):
    valid = set(ISO3.values()) | set(CUR)
    c = {k: dict(v) for k, v in (old.get("c") or {}).items() if k in valid}   # drops retired codes (FX, UK, YU, DY, HV)
    src = dict(old.get("src") or {})
    for k, code in IND.items():
        try:
            vals = parse_wb(get(f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&mrnev=1&per_page=400"))
            if len(vals) < 150: raise ValueError(f"only {len(vals)} countries")
            for a2, v in vals.items(): c.setdefault(a2, {})[k] = v
            src[k] = {"ok": True, "n": len(vals), "at": NOW.strftime("%Y-%m-%dT%H:%MZ")}
        except Exception as ex:
            src[k] = {**(src.get(k) or {}), "ok": False, "err": f"{type(ex).__name__}: {ex}"[:160]}
    try:
        rates, upd = parse_fx(get("https://open.er-api.com/v6/latest/USD"))
        krw = rates.get("KRW")
        for a2, cur in CUR.items():
            r = rates.get(cur)
            if not r: continue
            e = c.setdefault(a2, {}); e["cur"] = cur; e["usd"] = round(r, 6 if r < 1 else 4)
            if krw: e["krw"] = round(krw / r, 6 if krw / r < 1 else 4)
        src["fx"] = {"ok": True, "n": len(rates), "at": NOW.strftime("%Y-%m-%dT%H:%MZ"), "rates_at": upd}
    except Exception as ex:
        src["fx"] = {**(src.get("fx") or {}), "ok": False, "err": f"{type(ex).__name__}: {ex}"[:160]}
    return {"updated": NOW.strftime("%Y-%m-%dT%H:%MZ"), "src": src, "c": dict(sorted(c.items())),
            "credit": {"wb": "World Bank Open Data (CC BY 4.0)", "fx": "Rates By Exchange Rate API (https://www.exchangerate-api.com)"}}

if __name__ == "__main__":
    try: old = json.load(open(OUT, encoding="utf8"))
    except Exception: old = {}
    d = build(old)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(d, open(OUT, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    ok = [k for k, v in d["src"].items() if v.get("ok")]
    print(f"econ feed: {len(d['c'])} countries, sources ok {len(ok)}/{len(d['src'])}", {k: v.get("n") for k, v in d["src"].items()})
    sys.exit(0 if ok else 1)
