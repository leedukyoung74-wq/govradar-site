const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const authSource = fs.readFileSync(path.join(__dirname, "../web/auth.js"), "utf8");

async function signupCase(marketingChecked) {
  const nodes = new Map();
  for (const id of ["#authm", "#authx", "#auth-google", "#authf", "#auth-sub", "#authmsg",
    "#authe", "#authp", "#auth-terms", "#auth-age", "#authn", "#auth-mkt",
    "#authsoon", "#auth-h", "#auth-name-w", "#auth-age-w", "#auth-terms-w",
    "#auth-mkt-w", "#auth-email-w", "#auth-pw-w", "#auth-sw", "#loginbtn"]) {
    nodes.set(id, {
      hidden: false, checked: false, disabled: false, value: "",
      handlers: {},
      classList: {toggle(){}},
      addEventListener(name,fn){ this.handlers[name] = fn; },
      focus(){}
    });
  }
  const n = id => nodes.get(id);
  n("#authe").value = "example@example.org";
  n("#authp").value = "safe-password-123";
  n("#auth-terms").checked = true;
  n("#auth-age").value = "adult";
  n("#authn").value = "Test User";
  n("#auth-mkt").checked = marketingChecked;
  const captured = [];
  const handlers = {};
  const doc = {
    querySelector: n, querySelectorAll: () => [],
    getElementById: () => null,
    documentElement: {dataset:{}},
    addEventListener(name,fn){ handlers[name] = fn; },
    body: {appendChild(){}}
  };
  const win = {RADAR_LANG:"en", RADAR_AT:{}};
  const fetchFn = async (url,opt={}) => {
    if (url.endsWith("/settings")) return {ok:true,text:async()=>JSON.stringify({external:{google:false}})};
    if (url.endsWith("/signup")) {
      captured.push(JSON.parse(opt.body));
      return {ok:true,text:async()=>JSON.stringify({})};
    }
    throw new Error("Unexpected network call " + url);
  };
  const storage = {getItem:()=>null,setItem(){},removeItem(){}};
  vm.runInNewContext(authSource, {
    window:win,document:doc,localStorage:storage,sessionStorage:storage,
    fetch:fetchFn,setTimeout(){return 1;},
    location:{origin:"https://radar.wmm-hoa.com",hostname:"radar.wmm-hoa.com",hash:"",pathname:"/en/",search:""},history:{replaceState(){}},
    Date, URLSearchParams, Error, JSON, String, encodeURIComponent
  },{timeout:1000,filename:"auth.js"});
  handlers.DOMContentLoaded();
  await win.WMMAuth.open("signup");
  await n("#authf").handlers.submit({preventDefault(){}});
  assert.equal(captured.length,1,"Expected exactly one signup request");
  return captured[0].data;
}

test("unchecked marketing checkbox never records a consent-granted timestamp",async()=>{
  const data = await signupCase(false);
  assert.equal(data.marketing,false);
  assert.equal(data.marketing_at,null);
  assert.match(data.marketing_decision_at,/^\d{4}-\d{2}-\d{2}T/);
  assert.equal(data.terms_at,data.marketing_decision_at);
});

test("checked marketing checkbox records an actual consent timestamp",async()=>{
  const data = await signupCase(true);
  assert.equal(data.marketing,true);
  assert.match(data.marketing_at,/^\d{4}-\d{2}-\d{2}T/);
  assert.equal(data.marketing_at,data.marketing_decision_at);
});

test("existing member choosing No sends marketing:false with cleared consent timestamp",async()=>{
  const nodes = new Map();
  for (const id of ["#authm","#authx","#auth-google","#authf","#loginbtn"]) {
    nodes.set(id,{hidden:false,handlers:{},classList:{toggle(){}},
      addEventListener(name,fn){this.handlers[name]=fn}});
  }
  let modal, openConsentDialog;
  const documentHandlers = {};
  const created = tag=>({
    tag,children:[],style:{},id:"",textContent:"",
    setAttribute(){},remove(){},
    appendChild(el){this.children.push(el);}
  });
  const doc = {
    querySelector:id=>nodes.get(id),querySelectorAll:()=>[],
    getElementById:()=>null,documentElement:{dataset:{}},
    addEventListener:(name,fn)=>documentHandlers[name]=fn,
    createElement:created,body:{appendChild(el){if(el.id==="mktask")modal=el;}}
  };
  const session={access_token:"mock-session-token",refresh_token:"mock-refresh",
    expires_at:Date.now()+600000,user:{id:"test-user",user_metadata:{}}};
  const storage={getItem:()=>JSON.stringify(session),setItem(){},removeItem(){}};
  const requests=[];
  const fetchFn=async (url,options={})=>{
    if (!url.endsWith("/user")) throw Error("Unexpected network call");
    if (!options.method) return {ok:true,text:async()=>JSON.stringify({id:"test-user",user_metadata:{}})};
    if (options.method!=="PUT") throw Error("Unexpected method");
    requests.push(JSON.parse(options.body));
    return {ok:true,text:async()=>JSON.stringify({id:"test-user",user_metadata:{marketing:false}})};
  };
  const win={RADAR_LANG:"en",RADAR_AT:{}};
  vm.runInNewContext(authSource,{
    window:win,document:doc,localStorage:storage,sessionStorage:storage,
    fetch:fetchFn,setTimeout(fn,ms){if(ms===1200)openConsentDialog=fn;return 1;},
    location:{origin:"https://radar.wmm-hoa.com",hostname:"radar.wmm-hoa.com",hash:"",pathname:"/en/",search:""},history:{replaceState(){}},
    Date,URLSearchParams,Error,JSON,String,encodeURIComponent
  },{timeout:1000,filename:"auth.js"});
  documentHandlers.DOMContentLoaded();
  await new Promise(resolve=>setImmediate(resolve)); // allow Identity /user verification
  assert.equal(typeof openConsentDialog,"function");
  openConsentDialog();
  assert.ok(modal,"Marketing choice dialog must appear");
  const buttons=modal.children.find(el=>el.tag==="div").children;
  assert.equal(buttons.length,2);
  await buttons[1].onclick();
  assert.equal(requests.length,1);
  assert.equal(requests[0].data.marketing,false);
  assert.equal(requests[0].data.marketing_at,null);
  assert.match(requests[0].data.marketing_decision_at,/^\d{4}-\d{2}-\d{2}T/);
});

test("explicit marketing refusal path clears granted-at marker",()=>{
  assert.match(authSource,/marketing_at:\s*v\s*\?\s*decisionAt\s*:\s*null/);
  assert.match(authSource,/marketing_decision_at:\s*decisionAt/);
});
