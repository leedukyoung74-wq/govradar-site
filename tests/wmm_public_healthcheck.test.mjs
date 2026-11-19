import test from "node:test";
import assert from "node:assert/strict";
import {inspectPublicRoute, runPublicHealthcheck} from "../scripts/wmm_public_healthcheck.mjs";

const sample = {platform:"test",url:"https://example.org/path/"};
function mock({status=200,url=sample.url,contentType="text/html; charset=utf-8",html="<html><head><title>WMM</title></head><body><main>ok</main></body></html>"}) {
  return async () => new Response(html, {status,headers:{"content-type":contentType}});
}
function mockResponse({status=200,url=sample.url,contentType="text/html",html="<html><title>ok</title></html>"}) {
  return async () => ({ status, ok:status>=200 && status<300, url,
    headers:new Headers({"content-type":contentType}),
    body:new Response(html).body });
}

test("healthy HTML route has a limited HTTP-only pass", async () => {
  const result=await inspectPublicRoute(sample,mockResponse({}));
  assert.equal(result.available,true);
  assert.equal(result.classification,"HTTP_OK_HTML");
  assert.match(result.note,/NOT VERIFIED/);
});
test("HTTP 404 is not available", async () => {
  const result=await inspectPublicRoute(sample,mockResponse({status:404}));
  assert.equal(result.available,false);
  assert.equal(result.classification,"HTTP_ERROR");
});
test("login redirect is not a healthy public route", async () => {
  const result=await inspectPublicRoute(sample,mockResponse({url:"https://example.org/login/"}));
  assert.equal(result.available,false);
  assert.equal(result.classification,"LOGIN_REDIRECT");
});
test("cross-host redirect is not treated as success", async () => {
  const result=await inspectPublicRoute(sample,mockResponse({url:"https://different.example/login/"}));
  assert.equal(result.available,false);
  assert.equal(result.classification,"CROSS_HOST_REDIRECT");
});
test("unexpected content type is not healthy HTML", async () => {
  const result=await inspectPublicRoute(sample,mockResponse({contentType:"application/json",html:"{}"}));
  assert.equal(result.available,false);
  assert.equal(result.classification,"UNEXPECTED_CONTENT_TYPE");
});
test("empty server HTML is marked unavailable", async () => {
  const result=await inspectPublicRoute(sample,mockResponse({html:""}));
  assert.equal(result.available,false);
  assert.equal(result.classification,"EMPTY_HTML");
});
test("invalid URL rejected without network call", async () => {
  const result=await inspectPublicRoute({platform:"unsafe",url:"http://example.org/"},async()=>{throw new Error("should not fetch")});
  assert.equal(result.classification,"INVALID_URL");
});
test("result aggregation does not claim browser validation", async () => {
  const report=await runPublicHealthcheck([sample],mockResponse({}));
  assert.equal(report.kind,"PUBLIC_ONLY");
  assert.equal(report.results.length,1);
});
