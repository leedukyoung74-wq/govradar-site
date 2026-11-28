// Offline checks for the local-only customer help center (NO DEPLOY, NO POST).
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync('src/customer-support.html','utf8');
const builder=fs.readFileSync('build.py','utf8');
const languages=['ko','en','es','fr','ar','vi','id'];
assert.match(html,/<html lang="ko" dir="ltr">/);
assert.match(html,/id="search"[\s\S]*?placeholder=/);
assert.match(html,/id="faqs" class="faq-grid"/);
assert.match(html,/id="count" role="status" aria-live="polite"/);
assert.match(html,/id="language"/);
assert.match(html,/document\.documentElement\.dir=lang==='ar'\?'rtl':'ltr'/);
assert.match(html,/history\.replaceState/);
for (const lang of languages) {
  assert.match(html,new RegExp('<option value="'+lang+'">'));
  assert.match(html,new RegExp('(?:^|\\n)'+lang+':\\{'));
  assert.ok(builder.includes('"/support/?lang={L}"'),'generated footer link required');
}
const body=html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(body,'local script exists');
assert.doesNotThrow(()=>new vm.Script(body[1]),'script parses');
assert.ok(body[1].includes('cards.replaceChildren()'));
assert.ok(body[1].includes('h.textContent=q;p.textContent=a'),'FAQ never interprets customer-provided HTML');
assert.doesNotMatch(body[1],/\b(?:fetch|XMLHttpRequest|sendBeacon|WebSocket)\s*\(/);
assert.doesNotMatch(html,/<form\b/i);
assert.doesNotMatch(html,/(?:data-cf-beacon|googletagmanager|analytics\.js|tossPayments)/i);
assert.match(html,/content="default-src 'none';/);
assert.match(html,/KRW 20,000\/month or KRW 200,000\/year, VAT included/);
assert.match(html,/월 20,000원 또는 연 200,000원이며 부가세 포함/);
assert.match(html,/https:\/\/gcsme\.club/);
assert.match(html,/https:\/\/www\.gcsme\.kr/);
assert.match(html,/https:\/\/www\.wmm-hoa\.com/);
assert.match(html,/mailto:73036396@naver\.com/);
assert.match(builder,/W\("\/support\/index\.html", _support\.read\(\)\)/);
assert.match(builder,/src[^\n]*customer-support\.html|customer-support\.html/);
assert.ok(builder.includes('href="/support/?lang={L}"'));
assert.match(html,/This page does not issue support tickets/);
assert.match(html,/لا يتم إنشاء تذكرة تلقائيًا/);
const extraMatch=html.match(/const EXTRA_FAQ=(\{[\s\S]*\});\nfor\(const lang of valid\)/);
assert.ok(extraMatch,"eight extra localized customer questions are present");
const extra=JSON.parse(extraMatch[1]);
assert.deepEqual(Object.keys(extra).sort(),languages.slice().sort());
for (const lang of languages) {
  assert.equal(extra[lang].length,8,lang+": expected 8 new customer solutions");
  for (const [question,answer] of extra[lang]) {
    assert.ok(question.length>=8 && answer.length>=30,"not actionable enough "+lang);
  }
}
console.log('PASS: seven locale customer help, safe client search, explicit non-ticket status, source build and shared footer link (READ ONLY)');
