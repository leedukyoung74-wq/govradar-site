"""Read-only browser verification of public GOV RADAR pages; no form POST or login."""
import asyncio,json
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
BASE="https://radar.wmm-hoa.com"
LANGS=("ko","en","es","fr","ar","vi","id")
CASES=[(f"{l} home mobile",f"/{l}/?stay=1",390,844) for l in LANGS]
CASES += [(f"{l} request mobile",f"/{l}/request/?stay=1",390,844) for l in LANGS]
CASES += [("ko member mobile","/ko/member/?stay=1",390,844),
          ("en member mobile","/en/member/?stay=1",390,844),
          ("ko tenders desktop","/ko/mdb/?stay=1",1366,768),
          ("en tenders desktop","/en/mdb/?stay=1",1366,768)]

async def main():
    output=Path("public-browser-evidence");output.mkdir(exist_ok=True)
    rows=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        for name,path,width,height in CASES:
            ctx=await browser.new_context(viewport={"width":width,"height":height},device_scale_factor=1)
            page=await ctx.new_page()
            issues=[];status=None;actual=None;state={}
            try:
                response=await page.goto(BASE+path,wait_until="domcontentloaded",timeout=30000)
                actual=page.url;status=response.status if response else None
                if status!=200:issues.append("not_http_200")
                if urlparse(actual).hostname!="radar.wmm-hoa.com":issues.append("redirected_off_domain")
                await page.wait_for_timeout(400)
                state=await page.evaluate("""() => ({
                  width:innerWidth,scroll:document.documentElement.scrollWidth,
                  bodyScroll:document.body?document.body.scrollWidth:0,
                  documentLang:document.documentElement.lang,
                  heading:!!document.querySelector('h1'),
                  form:!!document.querySelector('.rq-form'),
                  title:document.title.slice(0,100)
                })""")
                if max(state["scroll"],state["bodyScroll"])>width+20:issues.append("horizontal_overflow")
                if not state["heading"]:issues.append("missing_heading")
                if state["documentLang"]!=path.split("/")[1]:issues.append("unexpected_document_language")
                if "/request/" in path and not state["form"]:issues.append("request_form_missing")
                if name in ("ko home mobile","en home mobile","ko tenders desktop","en tenders desktop"):
                    await page.screenshot(path=str(output/(name.replace(" ","_")+".png")),full_page=False)
            except Exception as err:
                issues.append("browser_exception_"+type(err).__name__)
                state["exception_excerpt"]=str(err)[:200]
            row={"case":name,"path":path,"status":status,"final_url":actual,
                 "metrics":state,"issues":issues}
            rows.append(row)
            print(json.dumps(row,ensure_ascii=False),flush=True)
            await ctx.close()
        await browser.close()
    passed=sum(not r["issues"] for r in rows)
    report={"result":"PASS" if passed==len(rows) else "FAIL",
            "passed":passed,"total":len(rows),"checks":rows,
            "notice":"Existing public-site smoke only; does not prove review-source deployment"}
    (output/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({k:report[k] for k in ("result","passed","total","notice")},ensure_ascii=False))
    if passed!=len(rows):raise SystemExit(1)
if __name__=="__main__":
    asyncio.run(main())
