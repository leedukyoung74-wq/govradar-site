import test from "node:test";
import assert from "node:assert/strict";
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from "node:fs";
import {tmpdir} from "node:os";
import {join,dirname} from "node:path";
import {fileURLToPath} from "node:url";
import {inventory,renderSitemap,LOCALES} from "../scripts/wmm_sitemap_preview.mjs";

const BASE="https://radar.wmm-hoa.com";
const page=(canonical,extra="")=>'<!doctype html><html><head><link rel="canonical" href="'+canonical+'">'+extra+'</head><body>Content</body></html>';

test("preview includes only canonical files that exist and excludes noindex/aliases",()=> {
  const root=mkdtempSync(join(tmpdir(),"wmm-sitemap-"));
  const put=(relative,html)=>{
    const file=join(root,relative);mkdirSync(dirname(file),{recursive:true});writeFileSync(file,html);
  };
  try {
    put("ko/index.html",page(BASE+"/ko/"));
    put("en/index.html",page(BASE+"/en/"));
    put("ko/ghana/index.html",page(BASE+"/ko/ghana/"));
    put("ko/draft/index.html",page(BASE+"/ko/draft/",'<meta name="robots" content="noindex, nofollow">'));
    put("ko/redirect/index.html",page(BASE+"/ko/"));
    put("en/teaser/index.html","<html><head></head><body>Unverified</body></html>");
    const {groups,sourceCount,excluded}=inventory(root);
    assert.equal(sourceCount,3);
    assert.equal(excluded.length,3);
    assert.ok(excluded.some(x=>x.reason==="NOINDEX"));
    assert.ok(excluded.some(x=>x.reason==="CANONICAL_MISMATCH"));
    const sitemap=renderSitemap(groups);
    const urls=[...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(x=>x[1]);
    assert.deepEqual(new Set(urls),new Set([BASE+"/ko/",BASE+"/en/",BASE+"/ko/ghana/"]));
    assert.match(sitemap,/hreflang="x-default" href="https:\/\/radar.wmm-hoa.com\/en\/"/);
    assert.doesNotMatch(sitemap,/\/draft\/|\/redirect\/|\/teaser\//);
    // Ghana has no EN counterpart: never claim an invented translation.
    assert.doesNotMatch(sitemap,/<xhtml:link[^>]+href="https:\/\/radar.wmm-hoa.com\/en\/ghana\/"/);
  } finally {rmSync(root,{recursive:true,force:true});}
});

test("repository preview discovers verifiable country pages beyond 14 existing entries",()=>{
  const data=inventory();
  assert.ok(data.sourceCount>14,"Repo should have at least one source-backed country page beyond base sitemap");
  const ghana=data.groups.find(([suffix])=>suffix==="ghana/");
  assert.ok(ghana);
  assert.equal(ghana[1].get("ko"),BASE+"/ko/ghana/");
  const sitemap=renderSitemap(data.groups);
  assert.equal((sitemap.match(/<url>/g)||[]).length,data.sourceCount);
  assert.doesNotMatch(sitemap,/<lastmod>/); // no invented update timestamps
  assert.ok(LOCALES.every(l=>data.groups.find(([suffix])=>suffix==="")[1].has(l)));
});
