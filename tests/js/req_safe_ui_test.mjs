import vm from "node:vm";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const source=fs.readFileSync(path.join(ROOT,"web/req-safe.js"),"utf8");

async function scenario(apiStatus, relayStatus) {
  let submit;
  const data=new Map();
  const localStorage={
    getItem:(k)=>data.get(k)||null,
    setItem:(k,v)=>data.set(k,v)
  };
  const status={textContent:"",setAttribute() {}};
  const button={disabled:false};
  const list={children:[],replaceChildren(){this.children=[];},appendChild(x){this.children.push(x);}};
  const inputIndustry={
    value:"Machinery",dataset:{k:"industry"},
    hasAttribute:(k)=>k==="data-req",
    closest:()=>({textContent:"Industry *"})
  };
  const panel={
    dataset:{t:"tender"},hidden:false,
    querySelectorAll:()=>[inputIndustry]
  };
  const fields={
    "email":{value:"buyer@example.com"},
    "product":{value:""},
    "field":{value:""},
    "need":{value:""}
  };
  const form={
    action:"https://radar.wmm-hoa.com/nfform?next=/en/thanks/",
    elements:{namedItem:(n)=>fields[n]},
    querySelector:(selector)=>{
      if(selector===".rq-msg")return status;
      if(selector==='button[type="submit"]')return button;
      if(selector==='.rq-f[data-t="tender"]')return panel;
      if(selector==='[data-k="code"]')return {value:""};
      throw Error("Unexpected form selector "+selector);
    },
    querySelectorAll:()=>[panel],
    addEventListener:(event,handler)=>{if(event==="submit")submit=handler;},
    reportValidity:()=>true
  };
  const radio={value:"tender",addEventListener() {}};
  const document={
    documentElement:{lang:"en"},
    querySelector:(s)=>{
      if(s===".rq-form")return form;
      if(s===".rq-mine")return list;
      if(s==='input[name="rqt"]:checked')return radio;
      return null;
    },
    querySelectorAll:()=>[radio],
    createElement:(tag)=>({tagName:tag,textContent:"",children:[],appendChild(n){this.children.push(n);}})
  };
  const calls=[];
  const fetch=async (url,options)=>{
    calls.push(url);
    if(url==="/api/req")return {
      status:apiStatus,ok:apiStatus===200,
      json:async()=>({req_no:"RQ-261120-TEST"})
    };
    if(url.includes("/nfform"))return {status:relayStatus,ok:relayStatus===200,type:"basic"};
    throw Error("Unexpected URL "+url);
  };
  class MockFormData {
    constructor(formData){this.fields=[["form-name","order"],["email",fields.email.value]];}
    *[Symbol.iterator](){yield* this.fields;}
  }
  const context={
    document,window:{WMM_REQUEST_TEXT:{names:{tender:"Tender suitability"},none:"No requests",req:"Required"}},
    fetch,localStorage,URLSearchParams,FormData:MockFormData,Date,JSON,Promise,console
  };
  vm.runInNewContext(source,context,{filename:"req-safe.js",timeout:1000});
  assert.equal(typeof submit,"function");
  let prevented=false;
  submit({preventDefault(){prevented=true;}});
  assert.equal(prevented,true);
  assert.match(status.textContent,/not yet confirmed/);
  await new Promise((resolve)=>setImmediate(resolve));
  await new Promise((resolve)=>setImmediate(resolve));
  assert.equal(button.disabled,false);
  return {status:status.textContent,history:data.get("gv_rq"),calls};
}

const a=await scenario(503,502);
assert.match(a.status,/could not be confirmed/i);
assert.equal(a.history,undefined,"failed requests must never become receipt history");

const b=await scenario(503,200);
assert.match(b.status,/wait for a confirmation email/i);
assert.equal(b.history,undefined,"relay response must not fabricate a server request number");

const c=await scenario(200,502);
assert.match(c.status,/stored on our server/i);
assert.match(c.status,/delivery to the team could not be verified/i);
assert.deepEqual(JSON.parse(c.history).map(x=>x.id),["RQ-261120-TEST"]);

console.log("req_safe_ui OK — failed, relayed-only, and server-confirmed states checked");
