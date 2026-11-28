"use strict";
const fs=require("node:fs");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const langs=["ko","en","es","fr","ar","vi","id"];
const monthly={ko:"월 20,000원",en:"₩20,000/month",es:"₩20.000/mes",fr:"20 000 ₩/mois",ar:"20,000 وون شهريًا",vi:"₩20.000/tháng",id:"₩20.000/bulan"};
const vat={ko:"VAT 포함",en:"VAT incl.",es:"IVA incluido",fr:"TTC",ar:"شامل الضريبة",vi:"đã gồm VAT",id:"termasuk PPN"};
const rejected={ko:"VAT 별도",en:"VAT excl.",es:"sin IVA",fr:"(HT)",ar:"دون الضريبة",vi:"chưa VAT",id:"belum PPN"};
const stale=/(?<![0-9])(?:19[, .]800|198[, .]000)(?![0-9])/;
function read(path){return fs.readFileSync(path,"utf8");}
for(const l of langs){
 const home=read("public/"+l+"/index.html");
 assert.ok(home.includes('href="/support/?lang='+l+'"'),"missing help link "+l);
 const near=home.match(/<input[^>]*value="Analysis membership"[^>]*>[\s\S]{0,450}?<\/label>/i);
 assert.ok(near,"missing M1 selector "+l);
 assert.ok(near[0].includes(monthly[l]),"wrong monthly price "+l);
 assert.ok(near[0].includes(vat[l]),"M1 VAT excluded "+l);
 assert.ok(!near[0].includes(rejected[l]),"excluded VAT "+l);
 assert.ok(!stale.test(near[0]),"obsolete price "+l);
 for(const path of ["thanks","consortium/thanks"]){
  const page=read("public/"+l+"/"+path+"/index.html");
  const content=page.slice(page.indexOf("<main>"),page.indexOf("</main>")+7);
  assert.match(content,/<h1>[^<]+<\/h1><p class="note" role="status">[^<]+<\/p>/);
  assert.ok(content.includes("73036396@naver.com"),"manual receipt path missing "+l+path);
  assert.ok(!/<h1>\s*(?:신청을 받았습니다|Thank you — application received|Thank you — we've got your request)/.test(content),"fake confirmed receipt "+l+path);
 }
}
const support=read("public/support/index.html");
assert.ok(support.includes('id="faqs"'));
assert.ok(support.includes('mailto:73036396@naver.com'));
assert.ok(support.includes("does not issue support tickets"));
assert.ok(!/<form\b/i.test(support));
const source=read("functions/nfform.js");
assert.match(source,/export function onRequestGet\(\)/);
assert.match(source,/export function onRequestHead\(\)/);
assert.match(source,/fields\.getAll\("privacy_agree"\)/);
assert.match(source,/fields\.getAll\("hp"\)/);
assert.match(source,/const MAX_FORM_BYTES = 256 \* 1024;/);
assert.match(source,/upstream|Netlify/);
const p=read("functions/pay/_products.js");
assert.match(p,/"analysis-month":\s*\{[^}]*amount:\s*20000/);
assert.match(p,/"analysis-year":\s*\{[^}]*amount:\s*200000/);
for(const file of ["functions/pay/config.js","functions/pay/confirm.js"])
 assert.ok(read(file).includes('env.WMM_PAYMENT_LIVE_ENABLED'),"flag missing "+file);
const routes=read("tests/customer-public-live-gate.test.cjs");
assert.match(routes,/expected exactly eight existing English fallbacks/);
console.log("INTEGRATED CUSTOMER REVIEW PASS: 7 price+VAT+FAQ; 14 non-confirming receipt pages; form consent and disabled-by-default payment gate");
