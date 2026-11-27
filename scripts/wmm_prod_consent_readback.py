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
    for lang in ("ko","en","ar"):
        path=f"/{lang}/request/"
        status,body,dest=get(path)
        good=(status==200 and "privacy_consent:f.querySelector(" in body and
              'if(!ok||!f.querySelector(' in body and 'name="privacy_agree" value="yes" required' in body)
        results.append({"check":path,"http":status,"ok":good,"specific_consent":good})
    for lang in ("es","fr","vi","id"):
        path=f"/{lang}/request/"
        status,body,dest=get(path)
        good=status==200 and "http-equiv=\"refresh\"" in body and "/en/request/" in body
        results.append({"check":path,"http":status,"ok":good,"expected_lang_redirect":good})
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
