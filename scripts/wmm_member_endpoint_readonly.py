#!/usr/bin/env python3
"""Read-only authentication endpoint connectivity audit. GET only; never login/signup or collect user data."""
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from datetime import datetime,timezone
from html.parser import HTMLParser
from hashlib import sha256
import json,os,ssl

TARGETS=(
 ("Netlify Identity settings","https://radar.wmm-hoa.com/.netlify/identity/settings"),
 ("GOV RADAR AI ask endpoint GET","https://radar.wmm-hoa.com/api/ask"),
 ("GOV RADAR member page","https://radar.wmm-hoa.com/ko/member/"),
 ("GOV RADAR account page","https://radar.wmm-hoa.com/ko/account/"),
 ("GOV RADAR business request page","https://radar.wmm-hoa.com/ko/request/"),
 ("GOV RADAR English business request","https://radar.wmm-hoa.com/en/request/"),
 ("GOV RADAR control missing route","https://radar.wmm-hoa.com/ko/route-audit-missing-20261127/"),
)
def probe(name,url):
    result={"service":name,"url":url,"http":None,"content_type":None,
            "redirect":None,"json_object":False,"identity_settings_keys":[],"html_hash":None,"html_has_form":None,"error":None}
    try:
      request=Request(url,headers={"Accept":"application/json,text/html","User-Agent":"WMM-ReadOnly-EndpointAudit/1.0"})
      with urlopen(request,timeout=15,context=ssl.create_default_context()) as r:
        result["http"]=r.status
        result["content_type"]=(r.headers.get("content-type") or "")[:90]
        result["redirect"]=r.geturl() if r.geturl()!=url else None
        if "text/html" in result["content_type"].lower():
          body=r.read(1000000)
          # Compare public rendered HTML with an intentionally nonexistent route; do not store body.
          result["html_hash"]=sha256(body).hexdigest()[:16]
          result["html_has_form"]=b"<form" in body.lower()
        if name=="Netlify Identity settings" and "application/json" in result["content_type"].lower():
          b=r.read(8192)
          try:
            j=json.loads(b)
            if isinstance(j,dict):
              result["json_object"]=True
              result["identity_settings_keys"]=[k for k in ("external","autoconfirm","disable_signup") if k in j]
          except (ValueError,UnicodeDecodeError): pass
    except HTTPError as e:
      result["http"]=e.code
      result["content_type"]=(e.headers.get("content-type") or "")[:90]
    except (URLError,OSError,ValueError) as e:
      result["error"]=type(e).__name__
    return result

def main():
    results=[probe(*t) for t in TARGETS]
    print(json.dumps({"checked_at":datetime.now(timezone.utc).isoformat(),"results":results},ensure_ascii=False,indent=2))
    path=os.getenv("GITHUB_STEP_SUMMARY")
    if path:
      with open(path,"a",encoding="utf8") as f:
        f.write("## WMM GOV RADAR endpoints: read-only audit\n\n")
        f.write("| Endpoint | HTTP | Type | JSON settings? | Error |\n|---|---:|---|---|---|\n")
        for r in results: f.write(f"| {r['service']} | {r['http']} | {r['content_type']} | {r['json_object']} | {r['error']} |\n")
        f.write("\nHTTP 200 on page does not mean identity backend is enabled. GET 404/405 on POST-only endpoint does not prove absence: verify hosting route/backend separately. No personal data, tokens or writes.\n")
if __name__=="__main__": main()
