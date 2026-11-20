const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const script = fs.readFileSync(path.join(__dirname, "../web/auth.js"), "utf8");
function storage(initial={}) {
  const m = new Map(Object.entries(initial));
  return {getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,String(v)),
    removeItem:k=>m.delete(k),data:m};
}
function browser({pathname="/ko/",search="",hash="",sess=storage(),fetchUser=true}) {
  const elements=new Map();
  for (const id of ["#authm","#authx","#auth-google","#authf","#loginbtn"]) {
    elements.set(id,{hidden:false,classList:{toggle(){}},
      handlers:{},addEventListener(name,fn){this.handlers[name]=fn;}});
  }
  const handlers={};const requests=[];const redirects=[];
  const doc={
    querySelector:id=>elements.get(id),querySelectorAll:()=>[],
    getElementById:()=>null,documentElement:{dataset:{}},
    createElement:()=>({className:"",textContent:"",remove(){}}),
    body:{appendChild(){}},
    addEventListener(name,fn){handlers[name]=fn;}
  };
  const location={origin:"https://radar.wmm-hoa.com",pathname,search,hash,href:"",
    replace(url){redirects.push(url);}};
  const local=storage();
  const window={RADAR_LANG:"ko",RADAR_AT:{}};
  const fetchFn=async(url,options={})=>{
    requests.push({url,options});
    if(url.endsWith("/user") && fetchUser) return {ok:true,text:async()=>JSON.stringify({id:"test-user",app_metadata:{roles:["m1"]}})};
    throw new Error("Unexpected request "+url);
  };
  vm.runInNewContext(script, {window,document:doc,localStorage:local,
    sessionStorage:sess,fetch:fetchFn,Date,JSON,Error,String,
    URL,URLSearchParams,encodeURIComponent,setTimeout(){return 1;},
    location,history:{replaceState(){}}}, {filename:"auth.js",timeout:1000});
  handlers.DOMContentLoaded();
  return {elements,handlers,location,local,sess,requests,redirects,window};
}

const KEY="wmm.auth.return.v1";
test("Google OAuth remembers the actual local route and query, not third-party URL",()=>{
  const sess=storage();
  const b=browser({pathname:"/ko/ghana/",search:"?sector=energy",sess});
  b.elements.get("#auth-google").handlers.click();
  assert.equal(sess.getItem(KEY),"/ko/ghana/?sector=energy");
  assert.equal(b.location.href,"/.netlify/identity/authorize?provider=google");
});

test("post-OAuth callback returns to exact in-site route after validating user token",async()=>{
  const sess=storage({[KEY]:"/ko/ghana/?sector=energy"});
  const b=browser({pathname:"/ko/",hash:"#access_token=fake&refresh_token=fake-refresh&expires_in=3600",sess});
  await new Promise(r=>setImmediate(r));
  assert.deepEqual(b.redirects,["/ko/ghana/?sector=energy"]);
  assert.equal(sess.getItem(KEY),null);
  assert.equal(b.window.WMMAuth.user()?.id,"test-user");
  assert.equal(b.requests.some(r=>r.url.endsWith("/user")),true);
});

test("external redirect injection cannot hijack OAuth callback",async()=>{
  const sess=storage({[KEY]:"//malicious.example/hijack"});
  const b=browser({pathname:"/ko/",hash:"#access_token=fake&refresh_token=fake",sess});
  await new Promise(r=>setImmediate(r));
  assert.deepEqual(b.redirects,[]);
  assert.equal(sess.getItem(KEY),null);
});

test("malformed stored locale or fragment cannot be used to redirect",async()=>{
  for(const bad of ["/outside/", "/en/route/#access_token=steal","https://malicious.example/","/ko/\\malicious.example/"]) {
    const sess=storage({[KEY]:bad});
    const b=browser({pathname:"/ko/",hash:"#access_token=fake",sess});
    await new Promise(r=>setImmediate(r));
    assert.deepEqual(b.redirects,[], "Bad target "+bad);
  }
});

test("same page does not trigger another redirect after OAuth",async()=>{
  const sess=storage({[KEY]:"/ko/"});
  const b=browser({pathname:"/ko/",hash:"#access_token=fake",sess});
  await new Promise(r=>setImmediate(r));
  assert.deepEqual(b.redirects,[]);
  assert.equal(sess.getItem(KEY),null);
});
