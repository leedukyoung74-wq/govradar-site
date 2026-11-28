#!/usr/bin/env python3
"""Read-only public HTML Cloudflare beacon audit. Never invokes JS or posts metrics."""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone
import os
import json
import ssl

URLS = (
    ("WMM", "https://www.wmm-hoa.com/"),
    ("WMM apex", "https://wmm-hoa.com/"),
    ("GCSME Korea", "https://www.gcsme.kr/"),
    ("GCSME apex", "https://gcsme.kr/"),
)
MARKER = "static.cloudflareinsights.com/beacon.min.js"

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.beacons = []
    def handle_starttag(self, tag, attrs):
        if tag != "script":
            return
        a = dict(attrs)
        src = a.get("src", "") or ""
        if MARKER in src:
            self.beacons.append({
                "has_beacon": True,
                "has_site_token": "token=" in src or "token" in (a.get("data-cf-beacon", "") or ""),
            })

def probe(label, url):
    result = {"site":label, "url":url, "http":None, "final":None,
              "html":False,"script":"UNKNOWN","csp":"UNKNOWN","cloudflare_edge":"UNKNOWN","server":"UNKNOWN","error":None}
    try:
        req = Request(url, headers={"User-Agent":"WMM-Analytics-ReadOnly-Check/1.0"})
        with urlopen(req, timeout=20, context=ssl.create_default_context()) as response:
            result["http"] = response.status
            result["final"] = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                result["error"] = "Non-HTML response"
                return result
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                result["error"] = "HTML exceeds 2MB inspection cap"
                return result
            result["cloudflare_edge"] = "CF_RAY_PRESENT" if response.headers.get("CF-Ray") else "NO_CF_RAY"
            result["server"] = (response.headers.get("Server") or "NOT_SET")[:60]
            result["html"] = True
            charset = response.headers.get_content_charset() or "utf-8"
            parser = Scripts()
            parser.feed(raw.decode(charset, errors="replace"))
            result["script"] = "PRESENT" if parser.beacons and any(b["has_site_token"] for b in parser.beacons) else ("MISSING_TOKEN" if parser.beacons else "NOT_IN_INITIAL_HTML")
            result["csp"] = "SET" if response.headers.get("Content-Security-Policy") else "NOT_SET"
    except HTTPError as e:
        result["http"] = e.code
        result["error"] = "HTTP response error"
    except (URLError, OSError, ValueError) as e:
        result["error"] = type(e).__name__
    return result

def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    data = [probe(name, url) for name, url in URLS]
    print(json.dumps({"checked":now,"results":data},ensure_ascii=False,indent=2))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as f:
            f.write("## WMM + GCSME Cloudflare beacon audit (READ ONLY)\n\n")
            f.write("Checked: "+now+"\n\n")
            f.write("| Site | HTTP | Final URL | Cloudflare edge | Server | Beacon in initial HTML | CSP header | Error |\n|---|---|---|---|---|---|---|---|\n")
            for r in data:
                f.write("| {site} | {http} | `{final}` | {cloudflare_edge} | {server} | {script} | {csp} | {error} |\n".format(**{k:(str(v).replace("|","/") if v is not None else "-") for k,v in r.items()}))
            f.write("\n**LIMIT:** HTML inspection cannot prove whether the beacon executes or delivers a request. 'NOT_IN_INITIAL_HTML' may still allow runtime injection by a client script. No browser script execution, metric POST, API credentials, DNS edits, or deployment performed. Manual Cloudflare dashboard/Network validation is still required.\n")
    # Diagnostic output is evidence, not operational success. No fake PASS/FAIL.
if __name__ == "__main__":
    main()
