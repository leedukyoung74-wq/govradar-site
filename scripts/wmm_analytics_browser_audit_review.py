#!/usr/bin/env python3
"""Read-only Chromium verification of WMM and GCSME Cloudflare RUM, never submit synthetic metrics."""
from datetime import datetime,timezone
from urllib.parse import urlparse
from pathlib import Path
import json,os,shutil
from playwright.sync_api import sync_playwright, Error as PlaywrightError

URLS=[
  ("WMM", "https://www.wmm-hoa.com/"),
  ("GCSME Korea","https://www.gcsme.kr/"),
]
def inspect(browser,label,url):
  result={"site":label,"url":url,"status":None,"final":None,"beacon_loaded":False,
          "beacon_script_dom":False,"rum_post_attempted":False,"blocked_post_count":0,
          "error":None}
  ctx=browser.new_context(service_workers="block",ignore_https_errors=False,
      user_agent="WMM-ReadOnly-RUM-Validation/1.0 (No metric publication)")
  page=ctx.new_page()
  def track(req):
    u=req.url.lower()
    if "static.cloudflareinsights.com/beacon.min.js" in u:
      result["beacon_loaded"]=True
    if "/cdn-cgi/rum" in u and req.method.upper()=="POST":
      result["rum_post_attempted"]=True
  def abort_analytics(route):
    # Never transmit synthetic performance events from automated tests.
    req=route.request
    if req.method.upper()=="POST":
      result["blocked_post_count"]+=1
      route.abort("blockedbyclient")
    else:
      route.continue_()
  page.on("request",track)
  page.route("**/cdn-cgi/rum*",abort_analytics)
  try:
    response=page.goto(url,wait_until="domcontentloaded",timeout=30000)
    result["status"]=response.status if response else None
    result["final"]=page.url
    page.wait_for_timeout(6000)
    result["beacon_script_dom"]=page.locator('script[src*="static.cloudflareinsights.com/beacon.min.js"]').count()>0
  except Exception as e:
    result["error"]=type(e).__name__
  finally:
    ctx.close()
  return result

def main():
  chrome=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
  if not chrome:
    raise SystemExit("NO_CHROME_BIN: runner lacks preinstalled Chrome, audit inconclusive")
  with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=chrome,headless=True,args=["--no-sandbox","--disable-gpu"])
    results=[inspect(browser,label,url) for label,url in URLS]
    browser.close()
  now=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
  print(json.dumps({"checked_at":now,"note":"NO synthetic RUM data sent", "results":results},ensure_ascii=False,indent=2))
  path=os.environ.get("GITHUB_STEP_SUMMARY")
  if path:
    with open(path,"a",encoding="utf8") as f:
      f.write("\n### Real Chromium DOM/network RUM diagnostic (no RUM POST transmitted)\n\n")
      f.write("| Site | HTTP | Beacon script in DOM | Beacon JS requested | RUM POST attempted (blocked) | Error |\n")
      f.write("|---|---:|---|---|---|---|\n")
      for r in results:
        f.write(f"| {r['site']} | {r['status']} | {r['beacon_script_dom']} | {r['beacon_loaded']} | {r['rum_post_attempted']} | {r['error']} |\n")
      f.write("\nA failed/blocked POST is intentionally not a metric. DOM/script checks do not prove that Cloudflare Analytics dashboard has recorded real visits.\n")
if __name__=="__main__":
  main()
