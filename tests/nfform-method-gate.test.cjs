"use strict";
// Offline, no network, no customer data; verifies only the GET/HEAD method guard.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const source = fs.readFileSync("functions/nfform.js","utf8");
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
