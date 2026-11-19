#!/usr/bin/env node
// Read-only DOM simulation of the real browser script. Does not deploy or use the network.
// This checks calculations, async country loading, localization, persistence, and navigation.
// It does NOT replace real Chrome/Edge, mobile, assistive technology, or RTL visual review.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const rootDir = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(rootDir, 'assets/wmm-resilience.js'), 'utf8');
const countries = JSON.parse(fs.readFileSync(path.join(rootDir,'data/countries.json'),'utf8'));
const foods = JSON.parse(fs.readFileSync(path.join(rootDir,'data/wmm-food-country-profiles.json'),'utf8'));
const optionPattern = /<option value="([^"]+)">([^<]*)<\/option>/g;

function makePage(lang, search = '?country=KR', store = new Map()) {
  const elements = new Map();
  const newEl = () => ({
    value: '', textContent: '', innerHTML: '', listeners: {}, dataset: {}, checked: false,
    get options() {
      return [...this.innerHTML.matchAll(optionPattern)].map(m=>({value:m[1],textContent:m[2]}));
    },
    get selectedIndex() {
      return this.options.findIndex(x=>x.value===this.value);
    },
    addEventListener(type, cb) { this.listeners[type] = cb; },
    setAttribute() {}
  });
  const el = id => {
    if(!elements.has(id)) elements.set(id,newEl());
    return elements.get(id);
  };
  const defaults = {'#rs-p':'2','#rs-d':'14','#rs-w':'3.8','#rs-b':'500',
    '#rs-use':'150','#rs-panel':'100','#rs-sun':'3'};
  for(const [id,value] of Object.entries(defaults)) el(id).value=value;
  const root = newEl();
  root.querySelector=el;
  root.querySelectorAll=()=>[];
  const location={pathname:'/'+lang+'/resilience/',search,href:''};
  const calls=[];
  const doc={
    getElementById:id=>id==='wmm-resilience'?root:null,
    createElement:()=>({click() {}})
  };
  const localStorage={
    getItem:key=>store.has(key)?store.get(key):null,
    setItem:(key,val)=>store.set(key,String(val)),
    removeItem:key=>store.delete(key)
  };
  const sandbox={
    document:doc, location, localStorage, URL, URLSearchParams,
    Blob, Promise, setTimeout:()=>0,
    fetch(url) {
      calls.push(url);
      const data=url==='/data/countries.json'?countries:
        url==='/data/wmm-food-country-profiles.json'?foods:null;
      return Promise.resolve({ok:!!data,json:()=>Promise.resolve(structuredClone(data))});
    }
  };
  vm.runInNewContext(script,sandbox,{filename:'wmm-resilience.js',timeout:4000});
  return {root,el,store,location,calls};
}

async function settle() {
  // Drain the Promise.all/json()/then() continuations without timers.
  for(let i=0;i<8;i++) await Promise.resolve();
}
(async()=>{
  const ko=makePage('ko');
  await settle();
  assert.equal(ko.root.dir,'ltr');
  assert.match(ko.root.innerHTML,/<h1>개인·가족별 재난 자립 대비<\/h1>/);
  assert.match(ko.el('#rs-out').innerHTML,/106\.4 L/);
  assert.match(ko.el('#rs-out').innerHTML,/84/);
  assert.match(ko.el('#rs-out').innerHTML,/56,000 kcal/);
  assert.match(ko.el('#rs-out').innerHTML,/400 Wh/);
  assert.match(ko.el('#rs-pout').innerHTML,/210 Wh/);
  assert.equal(ko.calls.length,2);
  assert.equal(ko.el('#rs-country').options.length,193);
  assert.equal(ko.el('#rs-country').value,'KR');
  assert.match(ko.el('#rs-foodcountry').innerHTML,/검토 예시 · 미검증|미검증/);
  assert.match(ko.root.innerHTML,/최소 약 6m/);
  ko.el('#rs-lang').listeners.change({target:{value:'en'}});
  assert.equal(ko.location.href,'/en/resilience/?country=KR');

  // Changing input recomputes values, without a reload or external request.
  ko.el('#rs-p').value='4';
  ko.el('#rs-d').value='30';
  ko.el('#rs-p').listeners.input();
  assert.match(ko.el('#rs-out').innerHTML,/456 L/);
  assert.match(ko.el('#rs-out').innerHTML,/360/);
  assert.equal(ko.calls.length,2);

  // Browser-only storage, progress, and clearing.
  assert.match(ko.el('#rs-progress').textContent,/0\/16/);
  ko.el('#rs-checks').listeners.change({target:{dataset:{check:'water'},checked:true}});
  assert.match(ko.el('#rs-progress').textContent,/1\/16/);
  assert.ok(ko.store.has('WMM_RESILIENCE_CHECK_V1'));
  ko.el('#rs-reset').listeners.click();
  assert.match(ko.el('#rs-progress').textContent,/0\/16/);
  assert.ok(!ko.store.has('WMM_RESILIENCE_CHECK_V1'));

  // Arabic direction and all-language selection path.
  const ar=makePage('ar','?country=NZ');
  await settle();
  assert.equal(ar.root.dir,'rtl');
  assert.equal(ar.el('#rs-country').options.length,193);
  assert.equal(ar.el('#rs-country').value,'NZ');
  ar.el('#rs-lang').listeners.change({target:{value:'vi'}});
  assert.equal(ar.location.href,'/vi/resilience/?country=NZ');

  for(const lang of ['en','es','fr','vi','id']){
    const page=makePage(lang);
    await settle();
    assert.equal(page.el('#rs-country').options.length,193,lang);
    assert.match(page.root.innerHTML,/<h1>[^<]+<\/h1>/,lang);
    assert.match(page.el('#rs-out').innerHTML,/106.4 L/,lang);
  }
  assert.equal(foods.filter(x=>x.status==='illustrative').length,42);
  assert.equal(foods.filter(x=>x.status==='pending').length,151);
  assert.ok(foods.every(x=>!x.local_official_guidance_verified && x.sources.length===0));
  console.log('PASS: calculations, 7 language routes, Arabic direction, 193 country loads, local checklist');
})().catch(err=>{console.error(err);process.exitCode=1});
