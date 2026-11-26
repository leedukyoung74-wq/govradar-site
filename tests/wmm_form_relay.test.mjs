import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {fileURLToPath} from "node:url";
import {dirname,join} from "node:path";

const dir = dirname(fileURLToPath(import.meta.url));
const code = readFileSync(join(dir,"../cf/functions/nfform.js"),"utf8");
const {onRequestPost,safeConfirmationPath} =
  await import("data:text/javascript;base64,"+Buffer.from(code).toString("base64"));
const origin = "https://radar.wmm-hoa.com";
const provider = "https://wmm-govradar.netlify.app/";

function post(next="/ko/thanks/", body="form-name=order&email=test%40example.org",contentType="application/x-www-form-urlencoded") {
  return new Request(origin+"/nfform?next="+encodeURIComponent(next),{
    method:"POST",headers:{"content-type":contentType},body
  });
}
async function run(request, responder) {
  const previous=globalThis.fetch;
  const calls=[];
  globalThis.fetch=async (...args)=>{calls.push(args);return responder(...args);};
  try {return {response:await onRequestPost({request}),calls};}
  finally {globalThis.fetch=previous;}
}

test("allows exactly the existing localized completion routes",()=>{
  for(const lang of ["ko","en","es","fr","ar","vi","id"]){
    assert.equal(safeConfirmationPath("/"+lang+"/thanks/"),"/"+lang+"/thanks/");
    assert.equal(safeConfirmationPath("/"+lang+"/consortium/thanks/"),"/"+lang+"/consortium/thanks/");
  }
});

test("rejects arbitrary, protocol-relative and backslash completion destinations",()=>{
  for(const x of ["//phish.example/x","/\\phish.example","https://phish.example",
    "/ko/thanks/../admin/","/en/thanks/?next=evil", "/en/membership/", "/en/thanks#e",
    "/KO/thanks/","",null]) {
    assert.equal(safeConfirmationPath(x),"/ko/thanks/",String(x));
  }
});

test("normal Netlify Forms 303 returns local 303 and preserves original form bytes",async()=>{
  const request=post("/en/consortium/thanks/","form-name=consortium&contact=Lee");
  const {response,calls}=await run(request,async()=>new Response(null,{
    status:303,headers:{location:"/"}
  }));
  assert.equal(response.status,303);
  assert.equal(response.headers.get("location"),origin+"/en/consortium/thanks/");
  assert.equal(calls.length,1);
  assert.equal(calls[0][0],provider);
  assert.equal(calls[0][1].method,"POST");
  assert.equal(calls[0][1].redirect,"manual");
  assert.equal(new TextDecoder().decode(calls[0][1].body),"form-name=consortium&contact=Lee");
});

test("successful 200 response is a valid transport acceptance only",async()=>{
  const {response}=await run(post(),async()=>new Response("ok",{status:200}));
  assert.equal(response.status,303);
  assert.equal(response.headers.get("location"),origin+"/ko/thanks/");
});

test("malicious completion target cannot redirect users off-site",async()=>{
  const {response}=await run(post("/\\phish.example"),async()=>new Response("ok",{status:200}));
  assert.equal(response.headers.get("location"),origin+"/ko/thanks/");
});

test("form POST rejected by Netlify is never shown as successful",async()=>{
  for(const status of [400,401,404,429,500,503]){
    const {response}=await run(post(),async()=>new Response("fail",{status}));
    assert.equal(response.status,502,String(status));
    assert.equal(response.headers.get("location"),null);
  }
});

test("invalid upstream 3xx redirect is never accepted as a form submission",async()=>{
  for(const target of ["https://different.example/something","//different.example/","http://wmm-govradar.netlify.app/"]){
    const {response}=await run(post(),async()=>new Response(null,{status:302,headers:{location:target}}));
    assert.equal(response.status,502,target);
  }
});

test("upstream 302 or 303 without location is treated as failure",async()=>{
  for(const status of [302,303]){
    const {response}=await run(post(),async()=>new Response(null,{status}));
    assert.equal(response.status,502);
  }
});

test("gateway network failures do not falsely claim submission success",async()=>{
  const {response}=await run(post(),async()=>{throw new Error("provider down");});
  assert.equal(response.status,502);
});

test("unsupported content types fail without invoking gateway",async()=>{
  const {response,calls}=await run(post("/ko/thanks/","{}", "application/json"),
    async()=>{throw new Error("should not fetch");});
  assert.equal(response.status,415);
  assert.equal(calls.length,0);
});

test("empty forms fail without invoking gateway",async()=>{
  const {response,calls}=await run(post("/ko/thanks/",""),
    async()=>{throw new Error("should not fetch");});
  assert.equal(response.status,400);
  assert.equal(calls.length,0);
});

test("oversized form payloads are rejected before reaching provider",async()=>{
  const {response,calls}=await run(post("/ko/thanks/","x".repeat(300000)),
    async()=>{throw new Error("should not fetch");});
  assert.equal(response.status,413);
  assert.equal(calls.length,0);
});

test("multipart form data is forwarded byte-for-byte",async()=>{
  const body="--test-boundary\r\ncontent-disposition: form-data; name=\"form-name\"\r\n\r\norder\r\n--test-boundary--\r\n";
  const {response,calls}=await run(post("/ko/thanks/",body,"multipart/form-data; boundary=test-boundary"),
    async()=>new Response(null,{status:303,headers:{location:"/"}}));
  assert.equal(response.status,303);
  assert.equal(new TextDecoder().decode(calls[0][1].body),body);
});

test("missing, unknown and duplicate form-name values are never relayed",async()=>{
  for(const body of ["email=x%40example.org","form-name=unknown&email=x%40example.org",
    "form-name=order&form-name=feedback&email=x%40example.org"]) {
    const {response,calls}=await run(post("/ko/thanks/",body),
      async()=>{throw new Error("should not reach Netlify");});
    assert.equal(response.status,400,body);
    assert.equal(calls.length,0,body);
  }
});

test("each registered live form name is accepted by the relay",async()=>{
  for(const name of ["consortium","contract-request","expert-apply","feedback",
    "gcsme-member","order","partner-apply","unlock"]) {
    const body="form-name="+encodeURIComponent(name)+"&email=a%40example.org";
    const {response,calls}=await run(post("/ko/thanks/",body),
      async()=>new Response(null,{status:303,headers:{location:"/"}}));
    assert.equal(response.status,303,name);
    assert.equal(calls.length,1,name);
  }
});

test("broken multipart form-name cannot masquerade as a valid submission",async()=>{
  const {response,calls}=await run(post("/ko/thanks/","broken","multipart/form-data; boundary=test"),
    async()=>{throw new Error("should not reach Netlify");});
  assert.equal(response.status,400);
  assert.equal(calls.length,0);
});

test("member access codes are rejected before Netlify transport",async()=>{
  for(const payload of [
    "form-name=order&need="+encodeURIComponent("member code: ABCD-EFGH"),
    "form-name=order&need="+encodeURIComponent("Project\n member code: ABCD-EFGH")
  ]){
    const {response,calls}=await run(post("/ko/thanks/",payload),
      async()=>{throw new Error("must never reach provider");});
    assert.equal(response.status,400);
    assert.equal(calls.length,0);
  }
});
