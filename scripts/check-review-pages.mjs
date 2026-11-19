#!/usr/bin/env node
// Static safety checks: review page JavaScript compiles and required controls exist.
import { readFileSync } from 'node:fs';
import { Script } from 'node:vm';
import assert from 'node:assert/strict';
const pages = [
  ['quality/index.html',['status','cards','checks']],
  ['review/index.html',['search','scope','country','state','results','stats','prev','next','page']]
];
for (const [path,ids] of pages) {
  const text=readFileSync(new URL('../'+path,import.meta.url),'utf8');
  assert.match(text,/<meta name="robots" content="noindex,nofollow">/);
  for(const id of ids)assert.match(text,new RegExp('id="'+id+'"'));
  const scripts=[...text.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).filter(s=>s.trim());
  assert.ok(scripts.length,path+' must have an inline app script');
  for(const source of scripts)new Script(source,{filename:path});
  assert.ok(!/localStorage|document\.cookie|payment|checkout\.session/i.test(scripts.join('\n')),path+' review screen must not handle identity/billing');
  console.log('PASS',path,'inline scripts compile; required elements present');
}
