import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync, existsSync} from "node:fs";
import {resolve, dirname, join} from "node:path";
import {fileURLToPath} from "node:url";

const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const xml=readFileSync(join(root,"sitemap.xml"),"utf8");
const base="https://radar.wmm-hoa.com";
const locales=["ko","en","es","fr","ar","vi","id"];
const urls=[...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(x=>x[1]);

test("original generated sitemap preserved at full country-page scale",()=>{
  assert.match(xml,/^<\?xml version="1.0" encoding="UTF-8"\?>/);
  assert.match(xml,/<urlset\b/);
  assert.match(xml,/<\/urlset>\s*$/);
  assert.ok(urls.length>1000, "Must not shrink a full country sitemap to a minimal landing-page list");
  assert.equal(new Set(urls).size,urls.length);
  for(const locale of locales){
    assert.ok(urls.includes(base+"/"+locale+"/"),"Missing homepage for "+locale);
    assert.ok(urls.includes(base+"/"+locale+"/ghana/"),"Missing source-backed country for "+locale);
  }
});

test("known localized paths in the sitemap have existing source files",()=>{
  for(const locale of locales){
    for(const suffix of ["","prepare/","ghana/"]){
      const url=base+"/"+locale+"/"+suffix;
      assert.ok(urls.includes(url),"Missing canonical "+url);
      assert.equal(existsSync(join(root,locale,suffix,"index.html")),true,"Missing static source "+url);
    }
  }
});

test("public sitemap excludes unapproved resilience, thanks and private account paths",()=>{
  assert.ok(!urls.some(x=>/\/(?:resilience|thanks|account|member)\//.test(x)));
});

test("all locations use the verified official host",()=>{
  for(const url of urls){
    const parsed=new URL(url);
    assert.equal(parsed.protocol,"https:");
    assert.equal(parsed.hostname,"radar.wmm-hoa.com");
  }
});
