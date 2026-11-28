import test from "node:test";
import assert from "node:assert/strict";
import {auditRenderedMdb,auditCurrentMdb} from "../scripts/wmm_rendered_tenders_audit.mjs";
function fixture(date="2026-11-19",url="https://bidsfactory.com/listing/1") {
 return `<section><h2>Open tenders by deadline</h2><ul class="dl"><li data-s="energy" data-dl="${date}"><b>Project</b><a class="src" href="${url}">Notice</a></li></ul></section>`;
}
test("past date with aggregator link must not be declared official or open",()=>{
 const r=auditRenderedMdb(fixture(),{locale:"en",asOf:"2026-11-20"});
 assert.equal(r.counts.cards,1);
 assert.equal(r.counts.pastDeadline,1);
 assert.equal(r.counts.thirdPartyLinks,1);
 assert.equal(r.counts.officialStatusUnverified,1);
 assert.ok(r.issues.some(x=>x.type==="MISLEADING_OPEN_HEADING_WITH_PAST_DATES"));
});
test("same-day deadline is not automatically expired",()=>{
 const r=auditRenderedMdb(fixture("2026-11-20"),{asOf:"2026-11-20"});
 assert.equal(r.counts.deadlineToday,1);
 assert.equal(r.counts.pastDeadline,0);
});
test("invalid and absent links are reported",()=>{
 const r=auditRenderedMdb(fixture("2026-11-22","javascript:alert(1)"),{asOf:"2026-11-20"});
 assert.equal(r.counts.missingSourceLink,1);
});
test("invalid calendar dates are reported without false expiry",()=>{
 const r=auditRenderedMdb(fixture("2026-02-30"),{asOf:"2026-11-20"});
 assert.equal(r.counts.invalidDeadline,1);
 assert.equal(r.counts.pastDeadline,0);
});
test("all seven committed MDB pages are auditable and nonempty",()=>{
 const reports=auditCurrentMdb("2026-11-20");
 assert.equal(reports.length,7);
 for(const r of reports){
  assert.ok(r.counts.cards>0,`${r.locale}: no cards`);
  assert.equal(r.counts.invalidDeadline,0,`${r.locale}: malformed dates`);
  assert.equal(r.counts.missingSourceLink,0,`${r.locale}: missing href`);
  assert.equal(r.counts.cards,r.counts.officialStatusUnverified,`${r.locale}: wrong provenance state`);
 }
});
