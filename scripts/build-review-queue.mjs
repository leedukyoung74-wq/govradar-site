#!/usr/bin/env node
/**
 * WMM review queue: creates local JSON evidence only, never mutates the site's datasets.
 * Run: node scripts/build-review-queue.mjs > audit-results/review-queue.json
 */
import { readFileSync } from 'node:fs';
const root = new URL('../data/', import.meta.url);
const load = filename => JSON.parse(readFileSync(new URL(filename, root), 'utf8'));
const countries = load('countries.json'), regions = load('regions.json'), data = load('opps.json');
const countryIds = new Set(countries.map(x=>x.iso));
const regionIds = new Set(regions.map(x=>x.code));
const validDate=s=>{
 if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;
 const d=new Date(s+'T00:00:00Z');
 return !Number.isNaN(d.getTime())&&d.toISOString().slice(0,10)===s;
};
const rows=data.items.map((item,index)=>{
 const source=item.source_url||item.sourceUrl||item.url||item.source||null;
 let sourceUrl=null;try{if(source){const url=new URL(source);if(['http:','https:'].includes(url.protocol))sourceUrl=url.href;}}catch{}
 const place_type=regionIds.has(item.iso)?'selected_special_region':countryIds.has(item.iso)?'country':'unknown';
 const flags=[];
 if(!sourceUrl)flags.push('MISSING_PRIMARY_SOURCE');
 if(!item.deadline)flags.push('DEADLINE_UNKNOWN');else if(!validDate(item.deadline))flags.push('DEADLINE_FORMAT_OR_DATE_INVALID');
 if(place_type==='unknown')flags.push('UNKNOWN_LOCATION');
 if(!item.ko&&!item.en)flags.push('TITLE_MISSING');
 return {
  source_row:index+1, location_code:item.iso||null, place_type, kind:item.kind||null,
  title_ko:item.ko||null,title_en:item.en||null, recorded_update:item.u||null,
  deadline:item.deadline||null, source_url:sourceUrl,flags,
  editorial_status:'UNVERIFIED',opportunity_stage:'WMM_HYPOTHESIS_UNTIL_VERIFIED'
 };
});
const prioritized=[...rows].sort((a,b)=>{
 const score=x=>x.flags.includes('UNKNOWN_LOCATION')?0:x.deadline&&validDate(x.deadline)?1:2;
 return score(a)-score(b)||String(a.deadline||'9999').localeCompare(String(b.deadline||'9999'))||a.source_row-b.source_row;
});
const byFlag={};
for(const row of rows)for(const flag of row.flags)byFlag[flag]=(byFlag[flag]||0)+1;
console.log(JSON.stringify({
 generated_at_utc:new Date().toISOString(),
 source_snapshot_updated:data.updated||null,
 total_records:rows.length,
 flagged_counts:byFlag,
 human_review_first_20:prioritized.slice(0,20),
 explanation:'This is a 20-record human review queue, not proof of actual tenders, procurement or independent confirmation. Never auto-publish or auto-attribute from this report.'
},null,2));
