// Offline-only regression: public price and GET-only form-route status.
// No real URL fetch, user account, Netlify form POST, API secret or checkout.
import test from "node:test";
import assert from "node:assert/strict";
import { PRODUCTS } from "../cf/functions/pay/_products.js";
import { onRequestGet as billingConfig } from "../cf/functions/pay/config.js";
import { onRequestPost as paymentConfirm } from "../cf/functions/pay/confirm.js";
import { onRequestGet as formProbe, onRequestPost as formSubmit } from "../cf/functions/nfform.js";

test("source products match previously agreed final customer price VAT included", () => {
  assert.deepEqual(Object.keys(PRODUCTS).sort(),
    ["analysis-month","analysis-year"]);
  assert.equal(PRODUCTS["analysis-month"].amount,20000);
  assert.equal(PRODUCTS["analysis-year"].amount,200000);
});

test("missing Toss keys keep real checkout disabled; GET config remains accurate", async () => {
  const response=await billingConfig({env:{}});
  assert.equal(response.status,200);
  const info=await response.json();
  assert.equal(info.enabled,false);
  assert.equal(info.clientKey,"");
  assert.equal(info.products["analysis-month"].amount,20000);
  assert.equal(info.products["analysis-year"].amount,200000);
  assert.equal(response.headers.get("cache-control"),"no-store");
});

test("real payment confirmation stays disabled with missing secret", async () => {
  const request=new Request("https://radar.wmm-hoa.com/pay/confirm",{
    method:"POST",headers:{"content-type":"application/json"},
    body:JSON.stringify({item:"analysis-month",amount:20000})
  });
  const response=await paymentConfirm({request,env:{}});
  assert.equal(response.status,503);
  const result=await response.json();
  assert.equal(result.ok,false);
  assert.equal(result.code,"NOT_READY");
});

test("the previous VAT-added amount fails the backend price equality check", async () => {
  const request=new Request("https://radar.wmm-hoa.com/pay/confirm",{
    method:"POST",headers:{"content-type":"application/json"},
    body:JSON.stringify({paymentKey:"TEST_ONLY",orderId:"analysis-month-fake",
                         item:"analysis-month",amount:22000,email:"no@invalid.test"})
  });
  const response=await paymentConfirm({request,env:{TOSS_SECRET_KEY:"DUMMY_TEST_ONLY"}});
  assert.equal(response.status,400);
  assert.equal((await response.json()).code,"AMOUNT_MISMATCH");
});

test("anonymous GET form relay reveals only method 405, not any customer data", async () => {
  const response=formProbe();
  assert.equal(response.status,405);
  assert.equal(response.headers.get("allow"),"POST");
  assert.equal(response.headers.get("cache-control"),"no-store");
  assert.equal(await response.text(),"Method Not Allowed");
});

test("invalid empty form cannot forward anything to Netlify", async () => {
  const request=new Request("https://radar.wmm-hoa.com/nfform",{
    method:"POST",headers:{"content-type":"application/x-www-form-urlencoded"},
    body:""
  });
  const response=await formSubmit({request});
  assert.equal(response.status,400);
  assert.equal(await response.text(),"Empty form submission");
});

test("invalid/non-registered form cannot be relayed externally", async () => {
  const request=new Request("https://radar.wmm-hoa.com/nfform",{
    method:"POST",headers:{"content-type":"application/x-www-form-urlencoded"},
    body:"form-name=unregistered-test&hello=world"
  });
  const response=await formSubmit({request});
  assert.equal(response.status,400);
  assert.equal(await response.text(),"Unknown or invalid form name");
});
