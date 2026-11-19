#!/usr/bin/env node
/**
 * WMM food-country verification queue. Inventory only; not official source verification.
 * Usage:
 *   node scripts/build_wmm_food_review_queue.mjs --check
 *   node scripts/build_wmm_food_review_queue.mjs --output <path/to/report.json>
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(readFileSync(new URL(p,root),'utf8'));
const countries=read('data/countries.json');
const regions=read('data/regions.json');
const foods=read('data/wmm-food-country-profiles.json');
const byCountry=new Map(countries.map(c=>[c.iso,c]));
if(countries.length!==193 || byCountry.size!==193 || foods.length!==193 ||
   regions.length!==23 || new Set(foods.map(x=>x.iso)).size!==193 ||
   foods.some(x=>!byCountry.has(x.iso)))throw Error('Country/region coverage mismatch');
const queue=foods.map(f=>{
 const c=byCountry.get(f.iso);
 const entries=Array.isArray(f.sources)?f.sources:[];
 const sourceCandidates=entries.filter(s=>typeof s?.url==='string' && /^https?:\/\//.test(s.url));
 return {
   iso:f.iso,
   country_ko:c.names?.ko||null,
   country_en:c.names?.en||null,
   status:f.status,
   illustrative_examples_count:Array.isArray(f.examples)?f.examples.length:0,
   official_source_candidates_count:sourceCandidates.length,
   official_source_independently_verified:f.local_official_guidance_verified===true,
   retail_verified:f.retail_availability_verified===true,
   shelf_life_verified:f.shelf_life_verified===true,
   reviewed_at:f.reviewed_at||null,
   review_tasks:[
     'Confirm country food-safety agency primary guidance and source URL',
     'Verify marketed products with manufacturer label and actual local retailers',
     'Check packaging and storage temperature/humidity/cold-chain limits',
     'Check allergens, dietary restrictions, infants and medical conditions',
     'Local-language review and evidence date'
   ]
 };
}).sort((a,b)=>(a.status==='illustrative'?0:1)-(b.status==='illustrative'?0:1)||
 a.iso.localeCompare(b.iso));
const illustrative=queue.filter(x=>x.status==='illustrative').length;
const pending=queue.filter(x=>x.status==='pending').length;
if(illustrative!==42||pending!==151)throw Error('Unexpected status distribution');
if(queue.some(x=>x.official_source_independently_verified||x.retail_verified||x.shelf_life_verified))
  throw Error('A verification flag changed: require independent review of evidence before publishing');
const result={
 generated_at_utc:new Date().toISOString(),
 total_countries:193,
 illustrative_drafts:illustrative,
 not_yet_drafted:pending,
 separately_tracked_special_regions:regions.length,
 country_food_officially_verified:0,
 verified_products:0,
 verification_notice:'Illustrative and pending records are not verified facts; URLs alone do not prove accuracy.',
 queue
};
const outputIndex=process.argv.indexOf('--output');
if(outputIndex!==-1){
 const destination=process.argv[outputIndex+1];
 if(!destination||destination.startsWith('--'))throw Error('Missing output filename');
 const p=resolve(destination);
 writeFileSync(p,JSON.stringify(result,null,2)+'\n',{encoding:'utf8'});
 const parsed=JSON.parse(readFileSync(p,'utf8'));
 if(parsed.queue.length!==193)throw Error('Output JSON round-trip failed');
 console.log('UTF-8 review queue written: '+p);
}else if(process.argv.includes('--check')){
 console.log('PASS: 193 country review queue; 42 illustrative; 151 pending; 23 separate special regions; zero verified');
}else process.stdout.write(JSON.stringify(result,null,2)+'\n');
