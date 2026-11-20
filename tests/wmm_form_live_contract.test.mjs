import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync,existsSync} from "node:fs";
import {resolve,join} from "node:path";
import {auditForms} from "../scripts/wmm_form_routes_audit.mjs";

const root=resolve(process.env.WMM_LIVE_FORM_ROOT||"live-branch/public");
const handler=readFileSync(new URL("../cf/functions/nfform.js",import.meta.url),"utf8");
const {REGISTERED_FORM_NAMES}=await import("data:text/javascript;base64,"+Buffer.from(handler).toString("base64"));

test("every Netlify form generated for the live site is recognized by the relay",()=>{
  assert.equal(existsSync(join(root,"ko/index.html")),true,"Missing read-only live checkout");
  const audit=auditForms(root);
  assert.equal(audit.problems.length,0,JSON.stringify(audit.problems.slice(0,5)));
  assert.ok(audit.forms>=30,"Unexpectedly few forms in live build");
  for(const name of audit.names)
    assert.ok(REGISTERED_FORM_NAMES.has(name),"Relay missing deployed form: "+name);
  assert.ok(audit.names.includes("order"),"Core inquiry form missing");
  assert.equal(audit.productionSubmissionVerified,false);
});
