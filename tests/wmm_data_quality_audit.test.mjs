import test from "node:test";
import assert from "node:assert/strict";
import {auditOpportunityData,loadCurrentData} from "../scripts/wmm_data_quality_audit.mjs";

const mk=()=>({
 countries:[{iso:"KR"},{iso:"PH"}],
 regions:[{code:"PH-BARMM",parent:"PH"}],
 opps:{updated:"2026-11-09",items:[
  {iso:"KR",kind:"tenders",ko:"테스트 조달",en:"Test tender",deadline:"2026-11-15"},
  {iso:"PH-BARMM",kind:"biz",ko:"지역 사업",en:"Regional opportunity",deadline:""},
  {iso:"PH",kind:"tenders",ko:"미래 공고",en:"Future tender",deadline:"2026-11-30",
   original_url:"https://example.org/official"}
 ]}
});
test("recognizes regional ISO references separately from sovereign countries",()=>{
 const r=auditOpportunityData(mk(),"2026-11-20");
 assert.equal(r.errors.length,0);
 assert.equal(r.counts.regionLinked,1);
 assert.equal(r.counts.pastDeadlineTenders,1);
 assert.equal(r.counts.missingOfficialSource,2);
});
test("unknown country and orphaned region are validation errors",()=>{
 const d=mk(); d.regions.push({code:"XX-REGION",parent:"XX"});d.opps.items.push({iso:"XX",kind:"biz",ko:"X",en:"X"});
 const r=auditOpportunityData(d,"2026-11-20");
 assert.ok(r.errors.some(x=>x.type==="REGION_PARENT"));
 assert.ok(r.errors.some(x=>x.type==="UNKNOWN_TERRITORY"));
});
test("today deadline is not labeled expired and malformed dates are warnings",()=>{
 const d=mk();d.opps.items[0].deadline="2026-11-20";d.opps.items[2].deadline="2026-02-30";
 const r=auditOpportunityData(d,"2026-11-20");
 assert.equal(r.counts.deadlineTodayTenders,1);
 assert.equal(r.counts.pastDeadlineTenders,0);
 assert.equal(r.counts.invalidDeadline,1);
});
test("current tracked datasets maintain expected country and region references",()=>{
 const r=auditOpportunityData(loadCurrentData(),"2026-11-20");
 assert.equal(r.errors.length,0,JSON.stringify(r.errors.slice(0,10)));
 assert.equal(r.counts.countries,193);
 assert.equal(r.counts.specialRegions,23);
 assert.equal(r.counts.opportunities,620);
 assert.equal(r.counts.regionLinked,6);
 assert.equal(r.counts.missingOfficialSource,620);
 assert.equal(r.counts.pastDeadlineTenders,78);
 assert.equal(r.classification,"STATIC_SOURCE_AUDIT_ONLY");
});
test("schema failures are reported without crashing",()=>{
 const r=auditOpportunityData({countries:null,regions:[],opps:{items:[]}},"2026-11-20");
 assert.equal(r.errors[0].type,"INVALID_SCHEMA");
});
