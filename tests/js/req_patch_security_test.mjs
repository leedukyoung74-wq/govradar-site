// No network and no actual customer data: owner-only status reporting regression.
import assert from "node:assert/strict";
import { DatabaseSync } from "node:sqlite";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const db=new DatabaseSync(":memory:");
db.exec(fs.readFileSync(root+"/cf/d1/schema.sql","utf8"));
const D1={prepare(sql){
  const stmt=db.prepare(sql); let params=[];
  const proxy={bind(...args){params=args;return proxy;},
    async first(){return stmt.get(...params)??null;},
    async all(){return {results:stmt.all(...params)};},
    async run(){stmt.run(...params);return {}}};
  return proxy;
}};
globalThis.fetch=async (_url,init)=>{
  const auth=init?.headers?.authorization || "";
  const token=auth.split(" ")[1];
  return token?{ok:true,json:async()=>({
    id:"user-"+token,email:token+"@example.org",
    app_metadata:{roles:token==="m1"?["m1"]:[]}
  })}:{ok:false};
};
const api=await import(root+"/cf/functions/api/req.js");
const invoke=async(fn,{body,token}={})=>{
  const request={
    headers:{get:k=>k==="authorization"&&token?"Bearer "+token:null},
    json:async()=>body
  };
  const response=await fn({request,env:{GV_DB:D1}});
  return {code:response.status,data:await response.json()};
};
const post=async(type,token,email)=>invoke(api.onRequestPost,{
  body:{type,body:"Evidence-only test",email,lang:"ko"},token
});
const mine=await post("partner","m1","m1@example.org");
assert.equal(mine.code,200);
assert.match(mine.data.req_no,/^RQ-[0-9]{6}-[A-F0-9]{4,16}$/);
const guest=await post("tender",null,"guest@example.org");
assert.equal(guest.code,200);

const anonymous=await invoke(api.onRequestPatch,{body:{req_no:mine.data.req_no,ok:true}});
assert.equal(anonymous.code,401,"Unauthenticated PATCH must not edit anyone's request");
const other=await invoke(api.onRequestPatch,{body:{req_no:mine.data.req_no,ok:true},token:"m0"});
assert.equal(other.code,404,"Other users cannot mark the request as delivered");
const guestPatch=await invoke(api.onRequestPatch,{body:{req_no:guest.data.req_no,ok:true}});
assert.equal(guestPatch.code,401,"Guest may submit a request but cannot claim delivery");
assert.equal(db.prepare("select status from requests where req_no=?").get(mine.data.req_no).status,"received");

const me=await invoke(api.onRequestPatch,{body:{req_no:mine.data.req_no,ok:true},token:"m1"});
assert.equal(me.code,200);
assert.equal(me.data.status,"relay_unverified");
assert.equal(me.data.delivery_verified,false);
assert.equal(db.prepare("select status from requests where req_no=?").get(mine.data.req_no).status,"relay_unverified");
const bad=await invoke(api.onRequestPatch,{body:{req_no:mine.data.req_no,ok:"true"},token:"m1"});
assert.equal(bad.code,400,"Client may only report boolean outcomes");

db.prepare("update requests set status='done' where req_no=?").run(mine.data.req_no);
const locked=await invoke(api.onRequestPatch,{body:{req_no:mine.data.req_no,ok:false},token:"m1"});
assert.equal(locked.code,409,"Completed staff status is immutable to the browser");
assert.equal(db.prepare("select status from requests where req_no=?").get(mine.data.req_no).status,"done");

const list=await invoke(api.onRequestGet,{token:"m1"});
assert.equal(list.code,200);
assert.equal(list.data.items.length,1);
assert.equal(list.data.items[0].status,"done");
console.log("PASS request PATCH owner-only and unverified-delivery contract");
