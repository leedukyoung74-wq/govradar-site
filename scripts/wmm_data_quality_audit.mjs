// WMM static opportunity data quality audit. Read-only, offline, no publication.
// Run: node scripts/wmm_data_quality_audit.mjs --json
import {readFileSync} from "node:fs";
import {dirname,resolve,join} from "node:path";
import {fileURLToPath,pathToFileURL} from "node:url";

const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const readJson=path=>JSON.parse(readFileSync(join(root,path),"utf8"));
const ISO_DAY=/^\d{4}-\d{2}-\d{2}$/;
const SOURCE_KEYS=["original_url","source_url","sourceUrl","url","source"];
const KIND_SET=new Set(["biz","oda","tenders"]);
const validDay=x=>typeof x==="string"&&ISO_DAY.test(x)&&!Number.isNaN(Date.parse(x))&&new Date(x+"T00:00:00Z").toISOString().slice(0,10)===x;
const validExternalUrl=value=>{
  if(typeof value!=="string"||!value.trim())return false;
  try {const u=new URL(value);return u.protocol==="https:"&&!!u.hostname;}catch{return false;}
};

export function auditOpportunityData({countries,regions,opps},asOf="2026-11-20"){
  if(!validDay(asOf))throw new TypeError("asOf must be a valid YYYY-MM-DD date");
  const errors=[], warnings=[];
  const countryCodes=new Set(),regionCodes=new Set();
  if(!Array.isArray(countries)||!Array.isArray(regions)||!Array.isArray(opps?.items)){
    return {asOf,errors:[{type:"INVALID_SCHEMA",message:"Expected countries[], regions[] and opps.items[]"}],warnings,counts:{}};
  }
  for(const [index,c] of countries.entries()){
    if(!c||typeof c.iso!=="string"||!/^[A-Z]{2}$/.test(c.iso))errors.push({type:"COUNTRY_ISO",index,iso:c?.iso});
    else if(countryCodes.has(c.iso))errors.push({type:"DUPLICATE_COUNTRY",index,iso:c.iso});
    else countryCodes.add(c.iso);
  }
  for(const [index,r] of regions.entries()){
    if(!r||typeof r.code!=="string"||!r.code.trim())errors.push({type:"REGION_CODE",index});
    else if(regionCodes.has(r.code))errors.push({type:"DUPLICATE_REGION",index,code:r.code});
    else regionCodes.add(r.code);
    if(!countryCodes.has(r?.parent))errors.push({type:"REGION_PARENT",index,parent:r?.parent});
  }
  const counts={countries:countries.length,specialRegions:regions.length,opportunities:opps.items.length,
    byKind:{biz:0,oda:0,tenders:0},regionLinked:0,missingOfficialSource:0,
    pastDeadlineTenders:0,deadlineTodayTenders:0,unknownDeadlineTenders:0,
    invalidDeadline:0};
  const identity=new Set();
  for(const [index,item] of opps.items.entries()){
    if(!item||typeof item!=="object"){errors.push({type:"INVALID_ITEM",index});continue}
    if(regionCodes.has(item.iso))counts.regionLinked++;
    else if(!countryCodes.has(item.iso))errors.push({type:"UNKNOWN_TERRITORY",index,iso:item.iso});
    if(!KIND_SET.has(item.kind))errors.push({type:"UNKNOWN_KIND",index,kind:item.kind});
    else counts.byKind[item.kind]++;
    if(!item.ko||!item.en)warnings.push({type:"MISSING_TITLE",index});
    const dedupe=[item.iso,item.kind,item.ko].join("|");
    if(identity.has(dedupe))warnings.push({type:"DUPLICATE_CANDIDATE",index});
    identity.add(dedupe);
    const urls=SOURCE_KEYS.map(key=>item[key]).filter(v=>typeof v==="string"&&v.trim());
    if(urls.length===0)counts.missingOfficialSource++;
    else if(!urls.some(validExternalUrl))warnings.push({type:"INVALID_SOURCE_URL",index});
    if(item.deadline){
      if(!validDay(item.deadline)){counts.invalidDeadline++;warnings.push({type:"INVALID_DEADLINE",index,deadline:item.deadline})}
      else if(item.kind==="tenders"){
        if(item.deadline<asOf)counts.pastDeadlineTenders++;
        else if(item.deadline===asOf)counts.deadlineTodayTenders++;
      }
    }else if(item.kind==="tenders")counts.unknownDeadlineTenders++;
  }
  if(countries.length!==193)warnings.push({type:"COUNTRY_COUNT_NOT_193",actual:countries.length});
  if(regions.length!==23)warnings.push({type:"SPECIAL_REGION_COUNT_NOT_23",actual:regions.length});
  if(counts.missingOfficialSource)warnings.push({type:"MISSING_OFFICIAL_URLS",count:counts.missingOfficialSource});
  if(counts.pastDeadlineTenders)warnings.push({type:"PAST_DEADLINE_TENDERS",count:counts.pastDeadlineTenders});
  return {asOf,dataUpdated:opps.updated??null,classification:"STATIC_SOURCE_AUDIT_ONLY",
    counts,errors,warnings,
    notice:"Source links missing means unverified; a date passing does NOT prove cancellation or current availability. No network or production data was modified."};
}

export function loadCurrentData(){
  return {countries:readJson("data/countries.json"),regions:readJson("data/regions.json"),opps:readJson("data/opps.json")};
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  const ix=process.argv.indexOf("--as-of");
  const asOf=ix>=0?process.argv[ix+1]:new Date().toISOString().slice(0,10);
  const report=auditOpportunityData(loadCurrentData(),asOf);
  if(process.argv.includes("--json"))console.log(JSON.stringify(report,null,2));
  else console.log(JSON.stringify({asOf:report.asOf,counts:report.counts,errors:report.errors.length,warnings:report.warnings},null,2));
  if(report.errors.length)process.exitCode=1;
}
