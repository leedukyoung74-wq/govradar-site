// Validates the static sitemap against paths actually present in this repository.
// Intentionally does NOT claim that production has deployed these paths.
import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync, existsSync} from "node:fs";
import {fileURLToPath} from "node:url";
import {resolve,dirname,join} from "node:path";

const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const xml=readFileSync(join(root,"sitemap.xml"),"utf8");
const locales=["ko","en","es","fr","ar","vi","id"];
const expected=new Set(locales.flatMap(lang=>[
  `https://radar.wmm-hoa.com/${lang}/`,
  `https://radar.wmm-hoa.com/${lang}/prepare/`
]));
const entries=[...xml.matchAll(/<url>\s*([\s\S]*?)\s*<\/url>/g)].map(m=>m[1]);

test("sitemap contains 14 distinct source-verified canonical URLs",()=>{
  assert.match(xml,/^<\?xml version="1.0" encoding="UTF-8"\?>/);
  assert.match(xml,/<urlset\b/);
  const urls=entries.map(e=>e.match(/<loc>([^<]+)<\/loc>/)?.[1]);
  assert.equal(urls.length,expected.size);
  assert.deepEqual(new Set(urls),expected);
});

test("every listed URL resolves to a committed static index file",()=>{
  for(const url of expected){
    const p=new URL(url);
    assert.equal(p.hostname,"radar.wmm-hoa.com");
    assert.equal(p.protocol,"https:");
    const local=join(root,p.pathname.slice(1),"index.html");
    assert.equal(existsSync(local),true,`Missing source: ${local}`);
  }
});

test("each canonical URL has seven valid hreflang equivalents plus x-default",()=>{
  for(const entry of entries){
    const canonical=entry.match(/<loc>([^<]+)<\/loc>/)?.[1];
    assert.ok(canonical);
    const url=new URL(canonical);
    const segments=url.pathname.split("/").filter(Boolean);
    const route=segments.length>1?"prepare/":"";
    const alternates=[...entry.matchAll(/<xhtml:link rel="alternate" hreflang="([^"]+)" href="([^"]+)"\s*\/>/g)]
      .map(m=>({lang:m[1],url:m[2]}));
    assert.equal(alternates.length,8);
    for(const lang of locales){
      assert.equal(alternates.find(x=>x.lang===lang)?.url,`https://radar.wmm-hoa.com/${lang}/${route}`);
    }
    assert.equal(alternates.find(x=>x.lang==="x-default")?.url,`https://radar.wmm-hoa.com/en/${route}`);
  }
});

test("sitemap never claims unverified ready or resilience routes",()=>{
  assert.doesNotMatch(xml,/\/ready\/|\/resilience\//);
});
