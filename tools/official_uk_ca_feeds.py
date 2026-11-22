#!/usr/bin/env python3
"""Read-only official UK Met Office severe-weather summary and ECCC Toronto Atom.
UK national coverage; Canada CA-ON-TORONTO only. RSS/Atom summaries are NOT
validated current emergency notifications; human confirmation before alert.
No customer data, no public redistributions, no paid API credentials.
"""
import argparse
import datetime as dt
from email.utils import parsedate_to_datetime
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UTC=dt.timezone.utc
MET_URL="https://www.metoffice.gov.uk/public/data/PWSCache/WarningsRSS/Region/UK"
CA_URL="https://weather.gc.ca/rss/battleboard/on61_e.xml"
CAP=8_000_000
ATOM="{http://www.w3.org/2005/Atom}"


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_dt(s):
    if not isinstance(s,str) or not s: return None
    try:
        t=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
        return t.astimezone(UTC) if t.tzinfo else None
    except (TypeError,ValueError,OverflowError):
        try:
            t=parsedate_to_datetime(s)
            return t.astimezone(UTC) if t.tzinfo else None
        except (TypeError,ValueError,OverflowError):
            return None


def allowed(url,provider):
    if not isinstance(url,str) or re.search(r"[\x00-\x20\\]",url):
        return False
    try:
        p=urllib.parse.urlsplit(url)
        if p.scheme!="https" or p.username or p.password or p.port is not None or p.fragment:
            return False
        if provider=="uk":
            return p.hostname in {"www.metoffice.gov.uk","weather.metoffice.gov.uk"} and p.path=="/public/data/PWSCache/WarningsRSS/Region/UK" and not p.query
        if provider=="ca":
            return p.hostname in {"weather.gc.ca","www.weather.gc.ca"} and p.path=="/rss/battleboard/on61_e.xml" and not p.query
    except (ValueError,TypeError):pass
    return False


def official_article_url(url,provider):
    try:
        p=urllib.parse.urlsplit(url)
        goodhosts=({"weather.metoffice.gov.uk","www.metoffice.gov.uk"} if provider=="uk" else
                   {"weather.gc.ca","www.weather.gc.ca"})
        if (p.scheme=="https" and p.hostname in goodhosts and p.port is None
            and not p.username and not p.password and p.path.startswith("/")
            and not p.fragment and not re.search(r"[\x00-\x20\\]",url)):
            return url
    except (ValueError,TypeError):pass
    return None


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self,provider):
        super().__init__()
        self.provider=provider
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed(newurl,self.provider):
            raise ValueError("cross_provider_redirect")
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def fetch(provider):
    url=MET_URL if provider=="uk" else CA_URL
    if not allowed(url,provider):raise ValueError("nonofficial_source")
    req=urllib.request.Request(url,headers={
        "User-Agent":"WMM-GOV-RADAR/1.0 (official public source read-only internal monitoring)",
        "Accept":"application/rss+xml,application/atom+xml,application/xml,text/xml"
    })
    with urllib.request.build_opener(OfficialRedirect(provider)).open(req,timeout=25) as r:
        if r.status!=200 or not allowed(r.geturl(),provider):
            raise ValueError("unexpected_source_response")
        b=r.read(CAP+1)
    if len(b)>CAP:raise ValueError("source_too_large")
    return b


def entries(raw):
    if not isinstance(raw,bytes) or not raw or len(raw)>CAP:raise ValueError("invalid_xml_payload")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("xml_entities_forbidden")
    try:root=ET.fromstring(raw)
    except ET.ParseError:raise ValueError("broken_xml") from None
    if root.tag=="rss":
        channel=root.find("channel")
        if channel is None or not channel.findtext("title"):
            raise ValueError("invalid_rss_channel")
        items=channel.findall("item")
        if len(items)>1000:raise ValueError("too_many_items")
        return [(it.findtext("title") or "",
                 it.findtext("link") or "",
                 it.findtext("pubDate") or "",
                 it.findtext("description") or "") for it in items]
    if root.tag==ATOM+"feed":
        if not root.findtext(ATOM+"title"):
            raise ValueError("invalid_atom_channel")
        items=root.findall(ATOM+"entry")
        if len(items)>1000:raise ValueError("too_many_items")
        data=[]
        for it in items:
            link=next((s.attrib.get("href") or "" for s in it.findall(ATOM+"link")
                       if s.attrib.get("rel","alternate") in ("alternate","")), "")
            data.append((it.findtext(ATOM+"title") or "", link,
                         it.findtext(ATOM+"updated") or it.findtext(ATOM+"published") or "",
                         it.findtext(ATOM+"summary") or ""))
        return data
    raise ValueError("unsupported_official_feed_format")


def parse(raw,now,provider):
    if provider not in ("uk","ca"):raise ValueError("unknown_provider")
    data=entries(raw)
    rows,seen=[],set()
    for title,link,stamp,desc in data:
        title=title.strip()
        if not title or re.search(r"(?i)no (?:severe )?(?:weather )?(?:warnings?|watches?) (?:are )?in (?:force|effect)",title):
            continue
        dated=parse_dt(stamp)
        if dated is None or dated>now+dt.timedelta(minutes=5) or now-dated>dt.timedelta(days=7):
            continue
        src=official_article_url(link,provider)
        if not src:continue # Met RSS terms require direct link to an official article.
        key=(title.casefold(),src)
        if key in seen:continue
        seen.add(key)
        rows.append({"title":title[:200], "observed_source_update":iso(dated),
                     "source_url":src,"confirmed_active":False,
                     "customer_impact_confirmed":False,
                     "scope_note":"RSS/ATOM update; currently active warning not confirmed"})
    rows.sort(key=lambda r:r["observed_source_update"],reverse=True)
    return {
        "schema":"wmm.official-uk-ca.v1",
        "provider":provider,
        "geo_scope":"GB" if provider=="uk" else "CA-ON-TORONTO",
        "sovereign_iso":"GB" if provider=="uk" else "CA",
        "source":"UK Met Office" if provider=="uk" else "Environment and Climate Change Canada",
        "source_url":MET_URL if provider=="uk" else CA_URL,
        "requires_link_to_source":provider=="uk",
        "feed_type":"uk_rss_warning_summaries" if provider=="uk" else "toronto_city_region_weather_atom",
        "count":len(rows), "items":rows[:100],
        "government_website_attack_confirmed":False,
        "source_is_official":True,
        "rights_note":"Met Office RSS requires linked official articles and attribution" if provider=="uk"
            else "Canada ECCC official weather information; review reuse and regional accuracy",
        "no_auto_critical_alert":True,
    }


def parse_uk_metoffice(raw,now):return parse(raw,now,"uk")
def parse_canada_eccc(raw,now):return parse(raw,now,"ca")


def safe_error(exc):
    if isinstance(exc,urllib.error.HTTPError):return "HTTP_"+str(exc.code)
    if isinstance(exc,TimeoutError):return "TIMEOUT"
    if isinstance(exc,ValueError) and str(exc) in ("nonofficial_source","cross_provider_redirect",
        "unexpected_source_response","source_too_large","broken_xml","invalid_rss_channel",
        "invalid_atom_channel","unsupported_official_feed_format","xml_entities_forbidden"):
        return str(exc)
    return "SOURCE_ERROR"


def collect(outpath,now,fetchers):
    p=Path(outpath).resolve()
    if {x.lower() for x in p.parts}&{"public","dist","live","data_branch"}:
        raise ValueError("refuse_deployment_output")
    old={}
    if p.exists():
        old=json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(old,dict) or not isinstance(old.get("feeds"),dict):raise ValueError("bad_previous_report")
    obj={
        "schema":"wmm.internal-uk-ca.v1","checked_at":iso(now),
        "public_publish_allowed":False,"customer_data_processed":False,
        "cyberattack_confirmed":False,"feeds":{},"health":{}
    }
    for provider,parser in (("uk",parse_uk_metoffice),("ca",parse_canada_eccc)):
        before=old.get("feeds",{}).get(provider)
        before_status=old.get("health",{}).get(provider,{})
        try:
            obj["feeds"][provider]=parser(fetchers[provider](),now)
            obj["health"][provider]={"status":"OK","checked_at":iso(now),
                                      "last_success_at":iso(now),"stale":False,"error":None}
        except (OSError,ValueError,TypeError,ET.ParseError) as e:
            obj["feeds"][provider]=before if isinstance(before,dict) else {"provider":provider,"count":None,"items":[]}
            obj["health"][provider]={
                "status":"STALE" if isinstance(before,dict) else "ERROR",
                "checked_at":iso(now),"last_success_at":before_status.get("last_success_at"),
                "stale":True,"error":safe_error(e)
            }
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent,prefix=".wmm-source-",suffix=".tmp")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(obj,f,ensure_ascii=False,indent=2)
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return obj


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    result=collect(args.out,dt.datetime.now(UTC),{
        "uk":lambda:fetch("uk"),"ca":lambda:fetch("ca"),
    })
    print(json.dumps({"checked_at":result["checked_at"],
        "all_ok":all(x["status"]=="OK" for x in result["health"].values()),
        "providers":{k:{"status":result["health"][k]["status"],
                        "count":result["feeds"][k].get("count"),
                        "last_success_at":result["health"][k]["last_success_at"],
                        "error_category":result["health"][k]["error"]}for k in ("uk","ca")},
        "customer_data":False,"public_deployment":False},ensure_ascii=False))
    return 0 if all(x["status"]=="OK" for x in result["health"].values()) else 1


if __name__=="__main__": raise SystemExit(main())
