const test=require("node:test");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");
const path=require("node:path");
const source=fs.readFileSync(path.join(__dirname,"../web/auth.js"),"utf8");

async function caseFor({storedRoles=["admin"],serverRoles=["m1"],failure=null,expired=false}={}){
  const saved=JSON.stringify({access_token:"test-token",refresh_token:"test-refresh",
    expires_at:Date.now()+(expired?-100000:3600000),user:{id:"old",app_metadata:{roles:storedRoles}}});
  const map=new Map([["wmm.auth.v1",saved]]);
  const local={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,v),removeItem:k=>map.delete(k)};
  const requests=[], listeners={}, tierUI={dataset:{tierMin:"m5"},unlocked:false,classList:{toggle(k,v){if(k==="unlocked")tierUI.unlocked=!!v;}}};
  const button={textContent:"",classList:{toggle(){}},addEventListener(){}};
  const doc={querySelector:id=>id==="#loginbtn"?button:null,
    querySelectorAll:()=>[tierUI],getElementById:()=>null,
    documentElement:{dataset:{}},addEventListener:(name,fn)=>listeners[name]=fn};
  const win={RADAR_LANG:"ko",RADAR_AT:{account:"account",login:"login"}};
  const fetchFn=async(url,init={})=>{
    requests.push({url,method:init.method||"GET"});
    if(url.endsWith("/token"))return {ok:true,text:async()=>JSON.stringify({access_token:"new-token",refresh_token:"new-refresh",expires_in:3600})};
    if(url.endsWith("/user")){
      if(failure)return {ok:false,status:failure,text:async()=>JSON.stringify({error:"token rejected"})};
      return {ok:true,text:async()=>JSON.stringify({id:"server",app_metadata:{roles:serverRoles}})};
    }
    throw Error("Unexpected fetch "+url);
  };
  vm.runInNewContext(source,{window:win,document:doc,localStorage:local,sessionStorage:{removeItem(){}},
    fetch:fetchFn,Date,URL,URLSearchParams,JSON,Error,String,
    encodeURIComponent,setTimeout(){return 1;},location:{origin:"https://radar.wmm-hoa.com",hostname:"radar.wmm-hoa.com",pathname:"/ko/",search:"",hash:""},
    history:{replaceState(){}},
  },{filename:"auth.js",timeout:1000});
  const auth=win.WMMAuth;
  const before={tier:auth.tier(),admin:auth.has("admin"),m5:auth.has("m5"),label:button.textContent,unlocked:tierUI.unlocked};
  listeners.DOMContentLoaded();
  await new Promise(resolve=>setImmediate(resolve));
  const after={tier:auth.tier(),admin:auth.has("admin"),m5:auth.has("m5"),m1:auth.has("m1"),
    unknown:auth.has("unknown-premium"),label:button.textContent,unlocked:tierUI.unlocked};
  return {before,after,auth,requests,map};
}

test("cached forged admin role unlocks nothing until server verifies",async()=>{
  const x=await caseFor();
  assert.equal(x.before.tier,null);
  assert.equal(x.before.admin,false);
  assert.equal(x.after.tier,"m1");
  assert.equal(x.after.admin,false);
  assert.equal(x.after.m5,false);
  assert.equal(x.after.m1,true);
  assert.equal(x.after.unlocked,false);
  assert.equal(x.after.unknown,false);
  assert.equal(x.after.label,"account");
});

test("stale cached premium role is never trusted on server failure",async()=>{
  const x=await caseFor({serverRoles:["admin"],failure:503});
  assert.equal(x.after.tier,null);
  assert.equal(x.after.m5,false);
  assert.equal(x.after.admin,false);
  assert.ok(x.map.has("wmm.auth.v1"),"Temporary outage need not destroy session for retry");
});

test("rejected stored token clears cached membership and shows no premium UI",async()=>{
  const x=await caseFor({failure:401});
  assert.equal(x.after.tier,null);
  assert.equal(x.after.admin,false);
  assert.ok(!x.map.has("wmm.auth.v1"));
});

test("malformed roles property is harmless and unknown tiers deny by default",async()=>{
  const x=await caseFor({serverRoles:"admin"});
  assert.equal(x.after.tier,"free");
  assert.equal(x.after.admin,false);
  assert.equal(x.after.unknown,false);
});

test("expired cached sessions refresh and revalidate against Identity",async()=>{
  const x=await caseFor({expired:true,storedRoles:["admin"],serverRoles:["m2"]});
  assert.equal(x.after.tier,"m2");
  assert.equal(x.after.admin,false);
  assert.ok(x.requests.some(r=>r.url.endsWith("/token")));
  assert.ok(x.requests.some(r=>r.url.endsWith("/user")));
});
