#!/usr/bin/env python3
"""Read-only public CERT-EU and Australian Cyber Security Centre RSS headlines.
An advisory is NOT a confirmed attack on any government agency or business.
Official host URL allowlisting, link attribution and NO public syndication.
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

CERT_URL="https://cert.europa.eu/publications/security-advisories-rss"
AUS_URL="https://www.cyber.gov.au/rss/alerts"
UTC=dt.timezone.utc
ATOM="{http://www.w3.org/2005/Atom}"
LIMIT=5_000_000


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def timeparse(s):
    if not isinstance(s,str) or not s.strip():return None
    try:
        t=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
        if t.tzinfo:return t.astimezone(UTC)
    except (ValueError,TypeError,OverflowError):pass
    try:
        t=parsedate_to_datetime(s)
        if t.tzinfo:return t.astimezone(UTC)
    except (ValueError,TypeError,OverflowError):pass
    return None


def allowed_source(url,provider):
    if not isinstance(url,str) or re.search(r"[\x00-\x20\\]",url):return False
    try:
        p=urllib.parse.urlsplit(url)
        if p.scheme!="https" or p.username or p.password or p.port is not None or p.fragment:return False
        if provider=="cert_eu":
            return p.hostname in ("cert.europa.eu","www.cert.europa.eu") and p.path=="/publications/security-advisories-rss" and not p.query
        if provider=="acsc_au":
            return p.hostname=="www.cyber.gov.au" and p.path=="/rss/alerts" and not p.query
    except (ValueError,TypeError):return False
    return False


def official_article(url,provider):
    if not isinstance(url,str) or re.search(r"[\x00-\x20\\]",url):return None
    try:
        p=urllib.parse.urlsplit(url)
        hosts=("cert.europa.eu","www.cert.europa.eu") if provider=="cert_eu" else ("www.cyber.gov.au","cyber.gov.au")
        if (p.scheme=="https" and p.hostname in hosts and p.port is None
            and not p.username and not p.password and p.path.startswith("/")
            and not p.fragment):return url
    except (ValueError,TypeError):pass
    return None


class RedirectSameOfficial(urllib.request.HTTPRedirectHandler):
    def __init__(self,provider):
        super().__init__()
        self.provider=provider
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed_source(newurl,self.provider):raise ValueError("nonofficial_redirect")
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def get(provider):
    url=CERT_URL if provider=="cert_eu" else AUS_URL
    if not allowed_source(url,provider):raise ValueError("invalid_official_url")
    req=urllib.request.Request(url,headers={
        "User-Agent":"WMM-GOV-RADAR/1.0 (official public cyber advisory sources only)",
        "Accept":"application/rss+xml,application/atom+xml,application/xml,text/xml"})
    with urllib.request.build_opener(RedirectSameOfficial(provider)).open(req,timeout=25) as resp:
        if resp.status!=200 or not allowed_source(resp.geturl(),provider):
            raise ValueError("source_response_not_ok")
        raw=resp.read(LIMIT+1)
    if len(raw)>LIMIT:raise ValueError("source_too_large")
    return raw


def parse_items(raw):
    if not isinstance(raw,bytes) or not raw or len(raw)>LIMIT:raise ValueError("bad_xml_size")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():raise ValueError("xml_entities_denied")
    try:r=ET.fromstring(raw)
    except ET.ParseError:raise ValueError("broken_xml") from None
    if r.tag=="rss":
        ch=r.find("channel")
        if ch is None or not ch.findtext("title"):raise ValueError("bad_rss")
        children=ch.findall("item")
        if len(children)>3000:raise ValueError("excessive_feed")
        return [(e.findtext("title") or "",e.findtext("link") or "",e.findtext("pubDate") or "") for e in children]
    if r.tag==ATOM+"feed":
        if not r.findtext(ATOM+"title"):raise ValueError("bad_atom")
        children=r.findall(ATOM+"entry")
        if len(children)>3000:raise ValueError("excessive_feed")
        result=[]
        for e in children:
            href=next((x.get("href","") for x in e.findall(ATOM+"link") if x.get("rel","alternate")=="alternate"),"")
            result.append((e.findtext(ATOM+"title") or "",href,e.findtext(ATOM+"updated") or e.findtext(ATOM+"published") or ""))
        return result
    raise ValueError("unexpected_feed_format")


def parse_official(raw,now,provider):
    if provider not in ("cert_eu","acsc_au"):raise ValueError("unknown_provider")
    seen,rows=set(),[]
    for title,link,published in parse_items(raw):
        name=title.strip()
        url=official_article(link,provider)
        date=timeparse(published)
        if not name or not url or date is None or date>now+dt.timedelta(minutes=5):
            continue
        if now-date>dt.timedelta(days=90):
            continue
        if url in seen:continue
        seen.add(url)
        rows.append({"title":name[:220],"url":url,"publication_utc":iso(date),
                     "advisory_type":"OFFICIAL_ADVISORY_NOT_VERIFIED_INCIDENT",
                     "confirmed_government_compromise":False,
                     "enterprise_impact_confirmed":False})
    rows.sort(key=lambda x:x["publication_utc"],reverse=True)
    return {
        "schema":"wmm.official-public-cyber-advisories.v1",
        "provider":provider,
        "geo_scope":"EU" if provider=="cert_eu" else "AU",
        "is_sovereign_country":provider=="acsc_au",
        "source_name":"CERT-EU" if provider=="cert_eu" else "Australian Cyber Security Centre",
        "source_url":CERT_URL if provider=="cert_eu" else AUS_URL,
        "count":len(rows), "items":rows[:100],
        "source_is_official":True,"government_site_attack_confirmed":False,
        "public_release_allowed":False,
        "message":"Only publisher's recent advisory headlines, not government breach confirmation; customer impact unknown."
    }


def safe_error(e):
    if isinstance(e,urllib.error.HTTPError):return "HTTP_"+str(e.code)
    if isinstance(e,TimeoutError):return "TIMEOUT"
    if isinstance(e,ValueError) and str(e) in {"nonofficial_redirect","invalid_official_url",
       "source_response_not_ok","source_too_large","xml_entities_denied","broken_xml",
       "bad_rss","bad_atom","unexpected_feed_format"}:return str(e)
    return "SOURCE_ERROR"


def collect(path,now,fetchers):
    p=Path(path).resolve()
    if {x.lower() for x in p.parts}&{"public","dist","live","data_branch"}:
        raise ValueError("public_output_forbidden")
    previous={}
    if p.exists():
        previous=json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(previous,dict) or not isinstance(previous.get("feeds"),dict):
            raise ValueError("invalid_previous_report")
    r={"schema":"wmm.official-cyber-internal.v1","checked_at":iso(now),
       "public_release_allowed":False,"customer_data_processed":False,
       "cyberattack_confirmed":False,"feeds":{},"health":{}}
    for provider in ("cert_eu","acsc_au"):
        before=previous.get("feeds",{}).get(provider)
        oldstate=previous.get("health",{}).get(provider,{})
        try:
            r["feeds"][provider]=parse_official(fetchers[provider](),now,provider)
            r["health"][provider]={"status":"OK","last_success_at":iso(now),"last_checked_at":iso(now),"error":None}
        except (OSError,ValueError,TypeError,ET.ParseError) as e:
            r["feeds"][provider]=before if isinstance(before,dict) else {"provider":provider,"count":None,"items":[]}
            r["health"][provider]={"status":"STALE" if isinstance(before,dict) else "ERROR",
                                   "last_success_at":oldstate.get("last_success_at"),
                                   "last_checked_at":iso(now),"error":safe_error(e)}
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent,prefix=".wmm-official-",suffix=".tmp")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(r,f,ensure_ascii=False,indent=2)
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return r


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    r=collect(args.out,dt.datetime.now(UTC),{
        "cert_eu":lambda:get("cert_eu"),"acsc_au":lambda:get("acsc_au")})
    print(json.dumps({"checked_at":r["checked_at"],
                      "status":{p:{"state":r["health"][p]["status"],
                                   "last_success_at":r["health"][p]["last_success_at"],
                                   "recent_advisories":r["feeds"][p].get("count"),
                                   "error":r["health"][p]["error"]}
                                for p in ("cert_eu","acsc_au")},
                      "public_release":False,"confirmed_breaches":False},ensure_ascii=False))
    return 0 if all(x["status"]=="OK" for x in r["health"].values()) else 1

if __name__=="__main__":raise SystemExit(main())
