#!/usr/bin/env python3
"""True browser DOM readback of GOV RADAR open-tender KPI. GET only, POST blocked."""
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from playwright.sync_api import sync_playwright
import json,shutil,os,sys

ROOT="https://radar.wmm-hoa.com/"
DATA="https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/today.json"
LANGS=("ko",) # diagnostic mode; return to seven locales after pinpointing error
def main():
    with urlopen(Request(DATA,headers={"User-Agent":"WMM-Public-KPI-QA/1.0"}),timeout=20) as r:j=json.loads(r.read(300000))
    n=j.get("n",{}).get("open")
    updated=datetime.fromisoformat(str(j.get("updated","")).replace("Z","+00:00"))
    age=(datetime.now(timezone.utc)-updated).total_seconds()/3600
    assert type(n)==int and n>=0 and -1<=age<30,(n,age)
    chrome=shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    assert chrome,"No chrome on runner, cannot draw browser conclusion"
    rows=[]
    with sync_playwright() as p:
      browser=p.chromium.launch(executable_path=chrome,headless=True,args=["--no-sandbox","--disable-gpu"])
      for lang in LANGS:
        context=browser.new_context(viewport={"width":390,"height":844},service_workers="block",user_agent="WMM-ReadOnly-KPI-QA/1.0")
        page=context.new_page()
        issues=[];console_errors=[];feed_responses=[]
        page.on("pageerror",lambda e:issues.append("PAGEERROR "+str(e)[:300]))
        page.on("console",lambda m:console_errors.append("CONSOLE "+m.text[:300]) if m.type=="error" else None)
        page.on("requestfailed",lambda r:issues.append("REQUEST_FAILED "+r.method+" "+str(r.failure)+" "+r.url[:160]))
        page.on("response",lambda r:feed_responses.append((r.status,r.url[:180])) if "today.json" in r.url else None)
        page.route("**/cdn-cgi/rum*",lambda route: route.abort())
        page.route("**/cloudflareinsights.com/cdn-cgi/rum*",lambda route: route.abort())
        status=None; rendered="—"; expected=None; width=0; scroll=0; error=None;stamp=""
        try:
          resp=page.goto(ROOT+lang+"/",wait_until="domcontentloaded",timeout=30000)
          status=resp.status if resp else None
          page.wait_for_function("""() => {let el=document.querySelector('#kp-t'); return el && el.textContent.trim()!=='—'}""",timeout=12000)
          rendered=page.locator("#kp-t").inner_text().strip()
          expected=page.evaluate("n => new Intl.NumberFormat(document.documentElement.lang==='ar'?'ar-u-nu-latn':document.documentElement.lang).format(n)",n)
          stamp=page.locator("#kp-u").inner_text().strip()
          width=page.evaluate("window.innerWidth")
          scroll=page.evaluate("document.documentElement.scrollWidth")
        except Exception as e:
          error=type(e).__name__
          try:
            rendered=page.locator("#kp-t").inner_text().strip()
            width=page.evaluate("window.innerWidth");scroll=page.evaluate("document.documentElement.scrollWidth")
            expected=page.evaluate("n => new Intl.NumberFormat(document.documentElement.lang).format(n)",n)
          except Exception:pass
        ok=(status==200 and rendered==expected and stamp not in ("","—") and scroll<=width+6)
        rows.append({"lang":lang,"http":status,"open_feed":n,"rendered":rendered,"expected":expected,
            "updated_label":stamp,"viewport_width":width,"document_width":scroll,"ok":ok,"error":error,"issues":issues[:20],"console_errors":console_errors[:10],"feed_responses":feed_responses[:10]})
        context.close()
      browser.close()
    result={"tested_at":datetime.now(timezone.utc).isoformat(),"feed_updated":j.get("updated"),"age_hours":round(age,2),"results":rows,"all_pass":all(x["ok"] for x in rows)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    s=os.getenv("GITHUB_STEP_SUMMARY")
    if s:
      with open(s,"a",encoding="utf8") as f:
        f.write("## WMM GOV RADAR real Chromium 7-language home KPI/390px readback (GET-only)\n\n")
        f.write(f"Official prepared data feed: {n} open, updated {j.get('updated')}; age {age:.2f} hours. This is aggregator data, not individual tender verification.\n\n")
        f.write("| Language | HTTP | Rendered open | Feed expected | Mobile overflow | Result |\n|---|---|---|---|---|---|\n")
        for x in rows:
          f.write(f"| {x['lang']} | {x['http']} | {x['rendered']} | {x['expected']} | {x['document_width']}>{x['viewport_width']} | {'PASS' if x['ok'] else 'FAIL'} |\n")
        f.write("\nAll POSTs blocked. No synthetic metrics, customer data, payment, or deployment. Rendering does not verify individual official tender links.\n")
    if not result["all_pass"]: sys.exit(1)
if __name__=="__main__":main()
