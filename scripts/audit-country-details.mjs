#!/usr/bin/env node
/**
 * WMM country-profile source coverage; read-only diagnostic.
 * A valid URL is NOT independent verification or a license to republish.
 * node scripts/audit-country-details.mjs > audit-results/country-coverage.json
 */
import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { URL } from 'node:url';
const files = new URL('../data/c/', import.meta.url);
const countries = JSON.parse(readFileSync(new URL('../data/countries.json', import.meta.url),'utf8'));
const urlOK = raw => {
  try { const u=new URL(raw);return ['http:','https:'].includes(u.protocol)&&!!u.hostname; }
  catch { return false; }
};
const isDate=s=>{
 if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;
 const d=new Date(s+'T00:00:00Z');return !Number.isNaN(d.getTime())&&d.toISOString().slice(0,10)===s;
};
let withoutFile=0,withoutSources=0,stale=0,invalidDeadlines=0,deadlinePassed=0, totalTenders=0;
const now=new Date(); const today=now.toISOString().slice(0,10);
const records=[];
const missingProfiles=[];
const pastDeadlineTenders=[];
for(const c of countries){
 const path=new URL(c.iso+'.json',files);
 if(!existsSync(path)){withoutFile++;missingProfiles.push({iso:c.iso,slug:c.slug||null,name_ko:c.names?.ko||null,name_en:c.names?.en||null,required_path:'data/c/'+c.iso+'.json'});records.push({iso:c.iso,profile_exists:false,officially_verified:false,flags:['PROFILE_MISSING']});continue;}
 let doc;
 try{doc=JSON.parse(readFileSync(path,'utf8'));}
 catch{records.push({iso:c.iso,profile_exists:true,officially_verified:false,flags:['PROFILE_INVALID_JSON']});continue;}
 const sources=Array.isArray(doc.sources)?doc.sources:[];
 const links=sources.filter(s=>urlOK(s?.url));
 const tenders=Array.isArray(doc.tenders)?doc.tenders:[];
 const flags=[];
 if(!links.length){withoutSources++;flags.push('NO_SOURCE_LINKS');}
 if(!isDate(doc.updated)){flags.push('NO_VALID_PROFILE_DATE');} else{
   const age=(now.getTime()-Date.parse(doc.updated+'T00:00:00Z'))/86400000;
   if(age>30){stale++;flags.push('PROFILE_STALE_30D');}
 }
 for(const [tenderIndex,t] of tenders.entries()){
   totalTenders++;
   if(t.deadline&&!isDate(t.deadline)){invalidDeadlines++;flags.push('INVALID_TENDER_DATE');}
   if(isDate(t.deadline)&&t.deadline<today){deadlinePassed++;flags.push('PAST_DEADLINE_REQUIRES_REVIEW');pastDeadlineTenders.push({iso:c.iso,country:c.names?.ko||c.names?.en||c.iso,profile_path:'data/c/'+c.iso+'.json',source_index:tenderIndex,title:t.title||null,buyer:t.buyer||null,recorded_deadline:t.deadline,source_url:urlOK(t.url)?t.url:null,editorial_action:'VERIFY_EXTENSION_CANCELLATION_OR_ARCHIVE',verified:false});}
 }
 if(tenders.some(t=>!urlOK(t.url)))flags.push('TENDER_MISSING_DIRECT_SOURCE');
 records.push({
  iso:c.iso,profile_exists:true,
  legacy_done:c.done===true,
  profile_updated:doc.updated||null,
  source_link_count:links.length,tender_count:tenders.length,
  officially_verified:false, flags:[...new Set(flags)]
 });
}
const output={
 audit_at_utc:now.toISOString(), coverage_total:countries.length, profiles_missing:withoutFile,
 profiles_without_source_links:withoutSources, profiles_stale_over_30_days:stale,
 tenders_count:totalTenders,tenders_invalid_deadline:invalidDeadlines,
 tenders_past_deadline_requiring_review:deadlinePassed,
 verified_official_sources:0,
 verification_note:'Source URL and legacy done flags are NOT evidence of official confirmation. The verified count stays zero until independent, documented human review occurs.',
 missing_profile_work_queue:missingProfiles,
 past_deadline_tenders_work_queue:pastDeadlineTenders.sort((a,b)=>a.recorded_deadline.localeCompare(b.recorded_deadline)),
 countries:records
};
const serialized = JSON.stringify(output, null, 2) + '\n';
const outputArg = process.argv.indexOf('--output');
if (outputArg !== -1) {
  const requested = process.argv[outputArg + 1];
  if (!requested || requested.startsWith('--')) {
    console.error('Usage: node scripts/audit-country-details.mjs --output <existing-folder/report.json>');
    process.exitCode = 2;
  } else {
    const destination = resolve(requested);
    writeFileSync(destination, serialized, { encoding: 'utf8', flag: 'w' });
    const reread = JSON.parse(readFileSync(destination, 'utf8'));
    if (reread.coverage_total !== countries.length) throw new Error('Report round-trip validation failed');
    console.log('UTF-8 JSON report written and verified: ' + destination);
  }
} else {
  process.stdout.write(serialized);
}
