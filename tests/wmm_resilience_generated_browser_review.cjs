#!/usr/bin/env node
/** WMM isolated PR55 Chromium visual and runtime checks: no login, payments or deployment. */
const { chromium } = require('playwright');
const { mkdirSync, writeFileSync } = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const base = 'http://127.0.0.1:8765';
const output = path.join(process.cwd(), 'browser-review');
mkdirSync(output,{recursive:true});
const langs=['ko','en','es','fr','ar','vi','id'];
const sizes=[
  {id:'desktop',width:1440,height:900},
  {id:'mobile',width:390,height:844},
  {id:'smallphone',width:320,height:720}
];
let browser, failures=[], results=[];
async function check(page, name, fn) {
  try { await fn(); return true; }
  catch(e){ failures.push({name,error:String(e.stack||e)}); return false; }
}
(async()=>{
try {
  browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  for(const lang of langs)for(const viewport of sizes){
    const name=lang+'-'+viewport.id;
    const page=await browser.newPage({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1});
    const errors=[];
    page.on('pageerror',e=>errors.push('pageerror: '+e.message));
    page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))errors.push(r.status()+' '+r.url());});
    const row={name,lang,viewport:viewport.id,width:viewport.width,height:viewport.height,checks:{}};
    row.checks.navigation=await check(page,name+' navigation',async()=>{
      const r=await page.goto(base+'/'+lang+'/resilience/',{waitUntil:'networkidle',timeout:25000});
      assert.equal(r.status(),200);
      await page.waitForFunction(()=>document.querySelectorAll('#rs-country option').length===193,{timeout:10000});
      assert.equal(await page.locator('main h1').count(),1);
      assert.equal(await page.locator('#rs-country option').count(),193);
      assert.equal(await page.locator('#rs-lang').inputValue(),lang);
      assert.equal(await page.locator('main').getAttribute('dir'),lang==='ar'?'rtl':'ltr');
    });
    row.checks.horizontalOverflow=await check(page,name+' overflow',async()=>{
      const sizes=await page.evaluate(()=>({viewport:innerWidth,page:document.documentElement.scrollWidth,body:document.body.scrollWidth}));
      assert.ok(sizes.page<=sizes.viewport+2,JSON.stringify(sizes));
    });
    row.checks.calculation=await check(page,name+' calculation',async()=>{
      const metric=await page.locator('#rs-out').innerText();
      assert.ok(metric.length>10);
      await page.locator('#rs-p').fill('4');
      await page.locator('#rs-d').selectOption('30');
      const after=await page.locator('#rs-out').innerText();
      assert.notEqual(after,metric);
      const waterNumber=await page.evaluate(()=>document.querySelector('#rs-out strong').textContent);
      // Localized digits are acceptable, but unit must remain liters.
      assert.ok(waterNumber.includes('L'),waterNumber);
    });
    row.checks.country=await check(page,name+' country',async()=>{
      await page.locator('#rs-country').selectOption('NZ');
      const rendered=await page.locator('#rs-foodcountry').innerText();
      assert.ok(rendered.includes('NZ'),rendered);
      assert.ok(rendered.length>30);
    });
    row.checks.checklist=await check(page,name+' checklist',async()=>{
      await page.locator('[data-check="water"]').check();
      assert.ok((await page.locator('#rs-progress').innerText()).includes('1/16'));
      await page.reload({waitUntil:'networkidle'});
      await page.waitForFunction(()=>document.querySelectorAll('#rs-country option').length===193);
      assert.ok(await page.locator('[data-check="water"]').isChecked());
      await page.locator('#rs-reset').click();
      assert.equal(await page.locator('[data-check="water"]').isChecked(),false);
    });
    row.checks.links=await check(page,name+' legacy links',async()=>{
      assert.equal(await page.locator('a[href="/'+lang+'/prepare/"]').count(),1);
    });
    row.checks.runtime=await check(page,name+' console/runtime',async()=>{
      assert.deepEqual(errors,[]);
    });
    const file=path.join(output,name+'.png');
    row.checks.screenshot=await check(page,name+' screenshot',async()=>{
      await page.screenshot({path:file,fullPage:true,animations:'disabled'});
    });
    results.push(row);
    console.log(name+' '+Object.entries(row.checks).filter(([_,v])=>!v).map(([k])=>k).join(','));
    await page.close();
  }
  const page=await browser.newPage();
  await page.goto(base+'/ko/resilience/?country=NZ',{waitUntil:'networkidle'});
  await page.waitForFunction(()=>document.querySelectorAll('#rs-country option').length===193);
  await page.locator('#rs-lang').selectOption('ar');
  await check(page,'language retention',async()=>{
    await page.waitForURL('**/ar/resilience/?country=NZ');
    await page.waitForFunction(()=>document.querySelectorAll('#rs-country option').length===193);
    assert.equal(await page.locator('#rs-country').inputValue(),'NZ');
    assert.equal(await page.locator('main').getAttribute('dir'),'rtl');
  });
  await page.close();
} catch(e){failures.push({name:'harness',error:String(e.stack||e)});}
finally {
  if(browser)await browser.close();
  const summary={date:new Date().toISOString(),branch:'wmm/prepare-upstream-review-20261119 (generated dist)',
    note:'Chromium emulation (not physical devices), no production deployment',
    screenshots:results.length,tests:results,failures};
  writeFileSync(path.join(output,'review-results.json'),JSON.stringify(summary,null,2)+'\n');
  console.log('Browser cases: '+results.length+', failures: '+failures.length);
  if(failures.length)for(const f of failures)console.error('FAIL '+f.name+': '+f.error);
  process.exitCode=failures.length?1:0;
}
})();
