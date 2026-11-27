"use strict";
// All payment tests are in-memory. No real payment approval or Form POST.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");

function load(name) {
  const products=fs.readFileSync("functions/pay/_products.js","utf8");
  const file=fs.readFileSync("functions/pay/"+name+".js","utf8");
  const merged=products+"\n"+file.replace(
    /^\s*import\s+\{\s*PRODUCTS\s*\}\s+from\s+["']\.\/_products\.js["'];?\s*/m,"");
  return import("data:text/javascript;base64,"+Buffer.from(merged).toString("base64"));
}
function paymentRequest(item,amount) {
  return new Request("https://radar.wmm-hoa.com/pay/confirm", {
    method:"POST",headers:{"content-type":"application/json"},
    body:JSON.stringify({item,amount,paymentKey:"test-non-real-payment",
      orderId:item+"-SYNTHETIC-NEVER-SENT",email:"qa@invalid.test"})
  });
}

test("fixed M1 total charge is monthly 20000 annual 200000 VAT included", async()=>{
  const {PRODUCTS}=await load("config");
  assert.equal(PRODUCTS["analysis-month"].amount,20000);
  assert.equal(PRODUCTS["analysis-year"].amount,200000);
  assert.ok(!Object.values(PRODUCTS).some(p=>p.amount===22000||p.amount===220000));
});
test("GET /pay/config with no keys cannot enable payments and shows correct price", async()=>{
  const {onRequestGet}=await load("config");
  const r=await onRequestGet({env:{}});
  assert.equal(r.status,200);
  const body=await r.json();
  assert.equal(body.enabled,false);
  assert.equal(body.clientKey,"");
  assert.equal(body.products["analysis-month"].amount,20000);
  assert.equal(body.products["analysis-year"].amount,200000);
});
test("live secret absent: confirmation returns 503 without any external action",async()=>{
  const {onRequestPost}=await load("confirm");
  const old=global.fetch;
  let calls=0;
  global.fetch=async()=>{calls++;throw Error("MUST NOT CALL");};
  try{
    const r=await onRequestPost({request:paymentRequest("analysis-month",20000),env:{}});
    assert.equal(r.status,503);
    assert.equal(calls,0);
  } finally{global.fetch=old;}
});
test("old 22000/220000 and mismatched amounts fail before any Toss API call",async()=>{
  const {onRequestPost}=await load("confirm");
  const old=global.fetch;
  let calls=0;global.fetch=async()=>{calls++;throw Error("MUST NOT CALL");};
  try{
    for (const [item,amt] of [["analysis-month",22000],["analysis-year",220000],
                             ["analysis-month",19999],["analysis-year",200001]]) {
      const r=await onRequestPost({request:paymentRequest(item,amt),
        env:{TOSS_SECRET_KEY:"TEST-SECRET-NOT-REAL"}});
      assert.equal(r.status,400);
      assert.equal((await r.json()).code,"AMOUNT_MISMATCH");
    }
    assert.equal(calls,0);
  } finally{global.fetch=old;}
});
test("synthetic valid amounts use ONLY mocked processor and mocked form gateway",async()=>{
  const {onRequestPost}=await load("confirm");
  const old=global.fetch;const calls=[];
  global.fetch=async(url,options)=>{
    calls.push({url,method:options.method,body:options.body});
    if (url==="https://api.tosspayments.com/v1/payments/confirm")
      return Response.json({method:"virtual",approvedAt:"2026-11-27"});
    if (url==="https://wmm-govradar.netlify.app/")
      return new Response("mocked",{status:200});
    throw Error("unexpected service called");
  };
  try{
    for (const [item,amt] of [["analysis-month",20000],["analysis-year",200000]]) {
      const r=await onRequestPost({request:paymentRequest(item,amt),
        env:{TOSS_SECRET_KEY:"TEST-SECRET-NOT-REAL"}});
      assert.equal(r.status,200);
      const result=await r.json();
      assert.equal(result.ok,true);
      assert.equal(result.amount,amt);
    }
    assert.equal(calls.length,4);
    for(const c of calls)assert.equal(c.method,"POST");
    assert.equal(JSON.parse(calls[0].body).amount,20000);
    assert.equal(JSON.parse(calls[2].body).amount,200000);
  } finally{global.fetch=old;}
});
