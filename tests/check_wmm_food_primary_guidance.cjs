#!/usr/bin/env node
// Read-only evidence gate: official preparedness guidance is NOT product verification.
const fs=require('node:fs');
const path=require('node:path');
const dir=path.resolve(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(dir,p),'utf8'));
const master=read('data/countries.json');
const food=read('data/wmm-food-country-profiles.json');
const official=read('data/wmm-food-primary-guidance-reviewed.json');
const ids=new Set(master.map(c=>c.iso));
if(official.countries.length!==3)throw Error('Expected exactly three initial source-reviewed countries');
const documented=new Set();
for(const item of official.countries){
 if(!ids.has(item.iso)||documented.has(item.iso))throw Error('Invalid or duplicated official source country');
 documented.add(item.iso);
 if(item.source_review_status!=='official_primary_guidance_checked'||item.product_review_status!=='not_checked')
  throw Error('Source status must not claim product verification');
 if(!Array.isArray(item.evidence)||item.evidence.length<2)throw Error('Primary source evidence missing');
 for(const itemSource of item.evidence) {
   const url=new URL(itemSource.url);
   if(url.protocol!=='https:'||!['safekorea.go.kr','www.youtube.com','www.maff.go.jp','ask.fsis.usda.gov','www.cdc.gov'].includes(url.hostname))throw Error('Unreviewed source host');
   if(!itemSource.verified_claim_ko||!itemSource.scope_limit)throw Error('Source scope must be documented');
 }
}
for(const foodRecord of food){
 if(foodRecord.local_official_guidance_verified!==false || foodRecord.retail_availability_verified!==false ||
 foodRecord.shelf_life_verified!==false)throw Error('Evidence of official guidance does not imply retail or shelf life verification');
}
console.log('PASS: 3 countries have primary-source guidance notes; 193 country-food product profiles remain unverified');
