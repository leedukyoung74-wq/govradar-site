// Read-only release QA: seven public entry links point to the same local-only FAQ.
const fs=require('node:fs'),assert=require('node:assert/strict'),vm=require('node:vm');
const locales=['ko','en','es','fr','ar','vi','id'];
const html=fs.readFileSync('public/support/index.html','utf8');
const js=html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(js,'FAQ script present');
assert.doesNotThrow(()=>new vm.Script(js[1]));
for(const code of locales){
 const home=fs.readFileSync('public/'+code+'/index.html','utf8');
 assert.ok(home.includes('href="/support/?lang='+code+'"'),code+': discoverability missing');
 assert.ok(html.includes('<option value="'+code+'">'),code+': FAQ option missing');
 assert.ok(new RegExp('(?:^|\\n)'+code+':\\{').test(js[1]),code+': FAQ copy missing');
}
assert.ok(js[1].includes("cards.replaceChildren()"));
assert.ok(js[1].includes("h.textContent=q;p.textContent=a"));
assert.ok(!/\b(?:fetch|XMLHttpRequest|sendBeacon|WebSocket)\s*\(/.test(js[1]));
assert.ok(!/<form\b/i.test(html));
assert.ok(html.includes("default-src 'none'"));
assert.ok(html.includes('73036396@naver.com') && html.includes('info@gcsme.club'));
assert.ok(html.includes('KRW 20,000/month or KRW 200,000/year, VAT included'));
console.log('PASS seven language entry links + local-only FAQ; no form, no customer POST, no tracking or payment');
