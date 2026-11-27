import test from "node:test";
import assert from "node:assert/strict";
import {classify,inspect} from "./worker.mjs";

const NOW=Date.parse("2026-11-28T02:00:00Z");
const health={
  official:{"usgs_fast_checked":"2026-11-28T10:10","sources":{"usgs":{"ok":true}}},
  nws:{"source_health":{"ok":true,"stale":false,"last_ok":"2026-11-28T01:10:00Z"}},
  cisa:{"source_health":{"ok":true,"stale":false,"last_ok":"2026-11-28T01:40:00Z"}}
};
function mockFetch(override={}) {
  const calls=[];
  async function fetcher(url,options) {
    calls.push({url,method:options.method,options});
    const base=url.split("/").pop();
    if(options.method==="POST") return {status:override.dispatchStatus||204};
    const key=base==="official.json"?"official":base==="nws_active.json"?"nws":"cisa";
    return {status:200,text:async()=>JSON.stringify(override[key]||health[key])};
  }
  return {fetcher,calls};
}
function environment(enabled=false) {
  const values=new Map();
  return {
    DISPATCH_ENABLED:enabled?"true":"false",
    GH_DISPATCH_TOKEN:"SYNTHETIC_PRIVATE_DO_NOT_PRINT",
    WMM_CRON_STATE:{
      get:async k=>values.get(k)||null,
      put:async(k,v)=>values.set(k,v)
    }
  };
}

test("KST 01:10 is UTC 16:10 on previous day; source age correct",()=>{
  const status=classify(health.official,health.nws,health.cisa,NOW);
  assert.equal(status.failClosed,false);
  assert.equal(status.usgs,true);
  assert.equal(status.nws_cisa,true);
});
test("default disabled mode allows only 3 bounded GETs and zero POSTs",async()=>{
  const o=mockFetch();
  const result=await inspect(environment(false),NOW,o.fetcher);
  assert.equal(result.enabled,false);
  assert.equal(result.usgs,"DISABLED");
  assert.equal(result.nws_cisa,"DISABLED");
  assert.equal(o.calls.length,3);
  assert.equal(o.calls.filter(x=>x.method==="POST").length,0);
  assert.equal(result.published_items,0);
  assert.equal(result.customer_data_accessed,false);
});
test("explicit enable sends at most 2 approved workflow dispatches",async()=>{
  const o=mockFetch();
  const env=environment(true);
  const result=await inspect(env,NOW,o.fetcher);
  assert.equal(result.usgs,"DISPATCH_ACCEPTED");
  assert.equal(result.nws_cisa,"DISPATCH_ACCEPTED");
  assert.equal(o.calls.length,5);
  const posts=o.calls.filter(x=>x.method==="POST");
  assert.equal(posts.length,2);
  assert(posts.every(x=>x.url.startsWith("https://api.github.com/repos/leedukyoung74-wq/govradar-site/actions/workflows/")));
  assert(posts.every(x=>JSON.parse(x.options.body).inputs.dry_run==="false"));
  assert(!JSON.stringify(result).includes(env.GH_DISPATCH_TOKEN));
});
test("KV cooldown prevents repeated GitHub dispatch if data still stale",async()=>{
  const env=environment(true);
  const a=mockFetch();
  await inspect(env,NOW,a.fetcher);
  const b=mockFetch();
  const second=await inspect(env,NOW+5*60_000,b.fetcher);
  assert.equal(second.usgs,"COOLDOWN_ACTIVE");
  assert.equal(second.nws_cisa,"COOLDOWN_ACTIVE");
  assert.equal(b.calls.filter(x=>x.method==="POST").length,0);
});
test("no token or KV blocks dispatch, but may check public source data",async()=>{
  const env={DISPATCH_ENABLED:"true"};
  const o=mockFetch();
  const s=await inspect(env,NOW,o.fetcher);
  assert.equal(s.usgs,"MISSING_PRIVATE_AUTH_OR_KV");
  assert.equal(o.calls.length,3);
});
test("missing source timestamps fail closed without external dispatch",async()=>{
  const o=mockFetch({official:{sources:{usgs:{ok:true}}}});
  const r=await inspect(environment(true),NOW,o.fetcher);
  assert.equal(r.usgs,"SOURCE_STATUS_INVALID");
  assert.equal(r.nws_cisa,"SOURCE_STATUS_INVALID");
  assert.equal(o.calls.filter(x=>x.method==="POST").length,0);
});
test("GH endpoint denial must not persist cooldown as success",async()=>{
  const env=environment(true),o=mockFetch({dispatchStatus:403});
  const r=await inspect(env,NOW,o.fetcher);
  assert.equal(r.usgs,"DISPATCH_DENIED");
  assert.equal(r.nws_cisa,"DISPATCH_DENIED");
  assert.equal(await env.WMM_CRON_STATE.get("cooldown_usgs"),null);
});
test("fresh sources make exactly 3 GET requests, no dispatch",async()=>{
  const o=mockFetch({
    official:{sources:{usgs:{ok:true}},usgs_fast_checked:"2026-11-28T10:59"},
    nws:{source_health:{ok:true,stale:false,last_ok:"2026-11-28T01:59:00Z"}},
    cisa:{source_health:{ok:true,stale:false,last_ok:"2026-11-28T01:59:00Z"}}
  });
  const r=await inspect(environment(true),NOW,o.fetcher);
  assert.equal(r.usgs,"NOT_DUE");
  assert.equal(r.nws_cisa,"NOT_DUE");
  assert.equal(o.calls.length,3);
});
