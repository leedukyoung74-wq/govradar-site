#!/usr/bin/env node
// Read-only review gate for emergency water and combustion warnings on legacy kit routes.
// All changes are kept inside the unmerged PR55 branch.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const langs=['ko','en','es','fr','ar','vi','id'];
const unsafe=[
 'ventilate indoors','with strong ventilation only',
 'ventile en interiores','avec une forte ventilation',
 'مع التهوية داخل المباني','مع تهوية جيدة فقط',
 'thông gió khi dùng trong nhà','pastikan ventilasi jika di dalam ruangan',
 '실외 또는 충분히 환기된 곳에서만 사용'
];
for(const lang of langs) {
 const content=fs.readFileSync(path.join(root,lang,'prepare','index.html'),'utf8');
 assert.match(content,/106\.4L/,lang+': 2-person 14-day quantity should follow 3.8 L baseline');
 assert.ok(!content.includes('84L'),lang+': obsolete quantity must not be present');
 const h=content.match(/<h2>(?:꼭 지킬 것|Safety first|La seguridad primero|La sécurité d'abord|السلامة أولًا|An toàn là trên hết|Keselamatan nomor satu)<\/h2><ul><li>([^<]+)<\/li>/);
 assert.ok(h,lang+': an accessible water explanatory list item is required');
 assert.ok(/(?:3\.8|3,8|3\.8)/.test(h[1]),lang+': baseline must be spelled out');
 assert.ok(h[1].includes(lang==='ko'?'106.4':lang==='en'?'106.4':lang==='ar'?'106.4':lang==='fr'?'106,4':lang==='es'?'106,4':lang==='vi'?'106,4':'106,4'),lang+': displayed quantity should agree with language note');
 for(const phrase of unsafe) assert.ok(!content.includes(phrase),lang+': hazardous indoor stove wording still present: '+phrase);
 assert.ok(content.includes('/'+lang+'/prepare/') || content.includes('prepare/'),lang+': existing page path must persist');
}
console.log('PASS: 7 legacy prepare routes harmonize 106.4 L and avoid ambiguous indoor stove directions');
