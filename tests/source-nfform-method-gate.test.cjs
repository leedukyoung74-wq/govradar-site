"use strict";
// Offline, no network, no customer data; verifies only the GET/HEAD method guard.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const source = fs.readFileSync("cf/functions/nfform.js","utf8");
const load = () => import("data:text/javascript;base64,"+Buffer.from(source,"utf8").toString("base64"));

test("GET is explicit 405 POST-only and never forwards customer data", async () => {
  const mod = await load();
  assert.equal(typeof mod.onRequestPost,"function");
  const result = mod.onRequestGet();
  assert.equal(result.status,405);
  assert.equal(result.headers.get("Allow"),"POST");
  assert.equal(result.headers.get("Cache-Control"),"no-store");
  assert.match(await result.text(),/POST required/);
});

test("HEAD is explicit 405 with no response body", async () => {
  const mod = await load();
  const result = mod.onRequestHead();
  assert.equal(result.status,405);
  assert.equal(result.headers.get("Allow"),"POST");
  assert.equal(result.headers.get("Cache-Control"),"no-store");
  assert.equal(await result.text(),"");
});

test("original accepted form-name whitelist and POST sender remain untouched", async () => {
  const mod = await load();
  for (const name of ["consortium","contract-request","expert-apply","feedback",
                       "gcsme-member","order","partner-apply","unlock"])
    assert.equal(mod.REGISTERED_FORM_NAMES.has(name),true);
  assert.equal(mod.REGISTERED_FORM_NAMES.has("unknown"),false);
  assert.equal(mod.safeConfirmationPath("/ko/thanks/"),"/ko/thanks/");
  assert.equal(mod.safeConfirmationPath("https://bad.test/"),"/ko/thanks/");
});

function syntheticRequest(payload, next="/ko/thanks/") {
  const body = new URLSearchParams({ "form-name":"order",
    "email":"qa-synthetic@invalid.test", "privacy_agree":"yes", ...payload });
  return new Request("https://radar.wmm-hoa.com/nfform?next="+
    encodeURIComponent(next), { method:"POST",
    headers: {"content-type":"application/x-www-form-urlencoded"},
    body: body.toString() });
}

test("synthetic POST, mocked Netlify 200: only trusted upstream; safe 303", async () => {
  const mod = await load();
  const originalFetch = global.fetch;
  let calls = 0;
  global.fetch = async (url, options) => {
    calls++;
    assert.equal(url,"https://wmm-govradar.netlify.app/");
    assert.equal(options.method,"POST");
    assert.match(new TextDecoder().decode(options.body),/form-name=order/);
    return new Response("synthetic ok",{status:200});
  };
  try {
    const result = await mod.onRequestPost({
      request: syntheticRequest({}, "https://attacker.invalid/redirect") });
    assert.equal(result.status,303);
    assert.equal(result.headers.get("Location"),"https://radar.wmm-hoa.com/ko/thanks/");
    assert.equal(calls,1);
  } finally { global.fetch = originalFetch; }
});

test("synthetic invalid form and membership codes never reach upstream", async () => {
  const mod = await load();
  const originalFetch = global.fetch;
  let calls=0;
  global.fetch=async () => { calls++; return new Response("",{status:200}); };
  try {
    const bad = await mod.onRequestPost({ request: syntheticRequest({"form-name":"unknown"}) });
    assert.equal(bad.status,400);
    const leak = await mod.onRequestPost({
      request: syntheticRequest({need:"member code: INVALID-EXAMPLE"}) });
    assert.equal(leak.status,400);
    assert.equal(calls,0);
  } finally { global.fetch = originalFetch; }
});

test("synthetic Netlify upstream failure cannot show a success confirmation", async () => {
  const mod = await load();
  const originalFetch=global.fetch;
  let calls=0;
  global.fetch=async () => { calls++; return new Response("failed",{status:503}); };
  try {
    const result = await mod.onRequestPost({request: syntheticRequest({})});
    assert.equal(result.status,502);
    assert.equal(result.headers.has("Location"),false);
    assert.equal(calls,1);
  } finally { global.fetch=originalFetch; }
});

test("synthetic wrong content type cannot forward", async () => {
  const mod=await load();
  const result=await mod.onRequestPost({
    request: new Request("https://radar.wmm-hoa.com/nfform", {
      method:"POST",headers:{"content-type":"application/json"},
      body: JSON.stringify({"form-name":"order"}) })});
  assert.equal(result.status,415);
});

test("synthetic direct POST cannot bypass required privacy consent or honeypot", async () => {
  const mod = await load();
  const originalFetch = global.fetch;
  let calls=0;
  global.fetch=async () => { calls++; return new Response("",{status:200}); };
  try {
    const noConsent = new URLSearchParams({
      "form-name":"order","email":"qa-synthetic@invalid.test","hp":""
    });
    const missing = await mod.onRequestPost({
      request: new Request("https://radar.wmm-hoa.com/nfform",{
        method:"POST", headers:{"content-type":"application/x-www-form-urlencoded"},
        body:noConsent.toString()
      })
    });
    assert.equal(missing.status,400);
    assert.match(await missing.text(),/Privacy consent required/);
    const refused = await mod.onRequestPost({
      request: syntheticRequest({privacy_agree:"no"})
    });
    assert.equal(refused.status,400);
    const trap = await mod.onRequestPost({
      request: syntheticRequest({hp:"bot"})
    });
    assert.equal(trap.status,400);
    assert.equal(calls,0);
  } finally { global.fetch=originalFetch; }
});

test("feedback synthetic consent works and omission fails without upstream", async () => {
  const mod=await load();
  const originalFetch=global.fetch;
  let calls=0;
  global.fetch=async () => { calls++; return new Response("synthetic",{status:200}); };
  try {
    const result=await mod.onRequestPost({
      request: syntheticRequest({"form-name":"feedback"})
    });
    assert.equal(result.status,303);
    assert.equal(calls,1);
    const bad=new URLSearchParams({"form-name":"feedback","email":"qa-synthetic@invalid.test"});
    const refused=await mod.onRequestPost({
      request:new Request("https://radar.wmm-hoa.com/nfform",{
        method:"POST", headers:{"content-type":"application/x-www-form-urlencoded"},
        body:bad.toString()
      })
    });
    assert.equal(refused.status,400);
    assert.equal(calls,1);
  } finally { global.fetch=originalFetch; }
});
