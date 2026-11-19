#!/usr/bin/env node
// Non-destructive source-level comparison. This is not a live-browser or accessibility test.
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const base=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(base,p),'utf8');
const legacy=read('ko/prepare/index.html');
const next=read('ko/resilience/index.html');
const runtime=read('assets/wmm-resilience.js');
const oldKit=legacy.includes('가정 비축 키트');
const oldWater=legacy.includes('84L') && legacy.includes('3L');
const newGuide=runtime.includes('3.8L') && runtime.includes('rs-w');
const oldSafetyPhrase=legacy.includes('실외 또는 충분히 환기된 곳');
const readySourcePresent=fs.existsSync(path.join(base,'ko/ready/index.html'));
assert.ok(oldKit,'Main legacy prepare source must remain available');
assert.ok(next.includes('href="/ko/prepare/"'),'New page must link to existing kit page');
assert.ok(next.includes('href="/ko/ready/"'),'New page must preserve existing live ready link');
assert.ok(next.includes('noindex, nofollow'),'New review page must remain unindexed');
assert.ok(newGuide,'New household calculator must retain explicit water assumptions');
const report={legacy_prepare_present:true,legacy_ready_in_repo:readySourcePresent,
  duplicate_water_guidance_requires_editorial_review:oldWater&&newGuide,
  legacy_burner_safety_wording_requires_review:oldSafetyPhrase,
  review_only_new_route:'/ko/resilience/',
  production_site_tested:false,
  recommendation:'Do not merge or deploy. Check live builder, baseline differences and warnings first.'};
console.log(JSON.stringify(report,null,2));
