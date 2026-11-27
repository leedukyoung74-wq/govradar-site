"use strict";
// Never sends a customer request. Verifies that every published form using
// /nfform requires an actual user-checked privacy_agree=yes field.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const LANGS = ["ko","en","es","fr","ar","vi","id"];
const VALID = new Set(["consortium","contract-request","expert-apply","feedback",
  "gcsme-member","order","partner-apply","unlock"]);

function allHtml(root) {
  const files=[];
  function walk(d) {
    for(const item of fs.readdirSync(d,{withFileTypes:true})) {
      const p=path.join(d,item.name);
      if(item.isDirectory()) walk(p);
      else if(item.isFile() && p.endsWith(".html")) files.push(p);
    }
  }
  walk(root);
  return files;
}

test("all published /nfform customer forms contain required explicit privacy agreement",()=>{
  const root="public";
  assert.equal(fs.existsSync(root),true);
  const found=new Map();
  let htmlScanned=0, relayForms=0;
  for(const file of allHtml(root)) {
    htmlScanned++;
    const html=fs.readFileSync(file,"utf8");
    for(const m of html.matchAll(/<form\b[\s\S]*?<\/form>/gi)) {
      const f=m[0];
      if(!/\baction=["']\/nfform(?:\?|["'])/i.test(f)) continue;
      relayForms++;
      const n=f.match(/name=["']form-name["']\s+value=["']([^"']+)["']/);
      assert.ok(n,"form-name missing: "+file);
      assert.ok(VALID.has(n[1]),"unknown form-name "+n[1]+" at "+file);
      const privacy=[...f.matchAll(/<input\b[^>]*\bname=["']privacy_agree["'][^>]*>/gi)].map(x=>x[0]);
      assert.equal(privacy.length,1,"privacy field count wrong: "+file);
      const tag=privacy[0];
      assert.match(tag,/\bvalue=["']yes["']/i,"consent must be yes: "+file);
      assert.match(tag,/\btype=["']checkbox["']/i,"consent must be explicit checkbox: "+file);
      assert.match(tag,/\brequired(?:\s|>|=)/i,"consent must be required: "+file);
      found.set(n[1],(found.get(n[1])||0)+1);
    }
  }
  assert.ok(htmlScanned>1500,"unexpected public HTML tree size");
  assert.ok(relayForms>=50,"expected all seven locales of known forms");
  for(const name of ["order","consortium","contract-request","expert-apply",
                      "gcsme-member","partner-apply","unlock"]) {
    assert.ok(found.has(name),"missing registered form "+name);
  }
  console.log("PUBLISHED_FORM_CONSENT_AUDIT", JSON.stringify({
    htmlScanned,relayForms,byName:Object.fromEntries([...found].sort())
  }));
});
