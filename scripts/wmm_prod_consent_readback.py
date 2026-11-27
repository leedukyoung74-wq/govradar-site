#!/usr/bin/env python3
"""No-login, no-POST production acceptance check of Cloudflare D1 consent deployment."""
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from datetime import datetime,timezone
import json,time,os,sys
from urllib.parse import urlsplit

ROOT="https://radar.wmm-hoa.com"
UA="WMM-Privacy-Consent-ReadOnly-Acceptance/1.0"
def get(path):
    url=ROOT+path
    assert urlsplit(url).hostname=="radar.wmm-hoa.com"
    req=Request(url,headers={"User-Agent":UA,"Cache-Control":"no-cache"})
    try:
        with urlopen(req,timeout=18) as r:
            return r.status,r.read(240000).decode("utf-8","replace"),r.geturl()
    except HTTPError as e:
        return e.code,e.read(10000).decode("utf-8","replace"),url

def main():
    results=[]
    status,body,_=get("/api/req")
    results.append({"check":"anonymous GET /api/req","http":status,"ok":status==401 and '"login"' in body})
    request_heading={"ko":"회원 분석 의뢰","en":"Member analysis requests",
       "es":"Solicitudes de análisis","fr":"Demandes d’analyse","ar":"طلبات التحليل",
       "vi":"Yêu cầu phân tích","id":"Permintaan analisis"}
    for lang,heading in request_heading.items():
        path=f"/{lang}/request/"
        status,body,dest=get(path)
        good=(status==200 and heading in body and
              "privacy_consent:f.querySelector(" in body and
              'if(!ok||!f.querySelector(' in body and
              'name="privacy_agree" value="yes" required' in body and
              f'name="lang" value="{lang}"' in body and
              'name="form-name" value="order"' in body and
              '/nfform?next=' in body and
              'fetch("/api/req"' in body and
              'http-equiv="refresh"' not in body)
        results.append({"check":path+" local form","http":status,"ok":good,"heading":heading,"native_form":good})
    # Home presentation only: no checkout, account access, scripts executed or synthetic analytics.
    locale_price={"ko":("19,800원","VAT 포함"),"en":("₩19,800","VAT incl."),
       "es":("₩19.800","IVA incluido"),"fr":("19 800 ₩","TVA comprise"),
       "ar":("19,800 وون","شامل ضريبة"),"vi":("₩19.800","đã gồm VAT"),
       "id":("₩19.800","termasuk PPN")}
    for lang,(price,tax) in locale_price.items():
        status,body,_=get(f"/{lang}/")
        good=(status==200 and price in body and tax in body and
              'id="kp-t">—' in body and 'id="kp-u">—' in body and
              'Date.parse(String(d.updated||""))' in body and
              '.replace(/Z$/,":00Z")' not in body and
              not any(old in body for old in ("20,000원","₩20,000","₩20.000","20 000 ₩","20,000 وون")))
        results.append({"check":f"/{lang}/ home pricing + freshness","http":status,"ok":good})
    print(json.dumps({"checked_at":datetime.now(timezone.utc).isoformat(),"results":results,"all_pass":all(x["ok"] for x in results),
    "note":"No POST, login, or client event measurement; no real receipt/DB write tested."},indent=2))
    s=os.environ.get("GITHUB_STEP_SUMMARY")
    if s:
        with open(s,"a",encoding="utf8") as f:
            f.write("## GOV RADAR live consent post-deploy readback (NO POST)\n\n")
            f.write("| GET-only check | HTTP | Expected contract |\n|---|---:|---|\n")
            for r in results:f.write(f"| {r['check']} | {r['http']} | {'PASS' if r['ok'] else 'FAIL'} |\n")
            f.write("\nAnonymous 401 is auth guard evidence only; not successful D1 inserts or staff email delivery. Never use artificial customer requests for this audit.\n")
    if not all(x["ok"] for x in results):sys.exit(1)
if __name__=="__main__":main()
