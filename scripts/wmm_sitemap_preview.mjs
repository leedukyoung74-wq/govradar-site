// Builds a review-only sitemap proposal from verified static source pages.
// Does not modify sitemap.xml, run external requests, or trigger deployments.
// Example: node scripts/wmm_sitemap_preview.mjs --output /tmp/wmm-sitemap-preview.xml --json
import {readdirSync, readFileSync, writeFileSync} from "node:fs";
import {resolve, join, relative, dirname} from "node:path";
import {fileURLToPath, pathToFileURL} from "node:url";

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const ORIGIN="https://radar.wmm-hoa.com";
export const LOCALES=["ko","en","es","fr","ar","vi","id"];
const xmlEscape=s=>s.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&apos;");

function* indexes(dir) {
  for (const ent of readdirSync(dir,{withFileTypes:true})) {
    if (ent.name.startsWith(".") || ent.isSymbolicLink()) continue;
    const abs=join(dir,ent.name);
    if (ent.isDirectory()) {
      if (["node_modules","widget","_next","dist","build"].includes(ent.name)) continue;
      yield* indexes(abs);
    } else if (ent.isFile() && ent.name==="index.html") yield abs;
  }
}

function canonicalFromHead(html) {
  const head=html.split(/<\/head>/i)[0];
  const el=head.match(/<link\b(?=[^>]*\brel\s*=\s*["']canonical["'])[^>]*>/i)?.[0]||"";
  return el.match(/\bhref\s*=\s*["']([^"']+)["']/i)?.[1]||null;
}
function noIndex(html) {
  const head=html.split(/<\/head>/i)[0];
  return [...head.matchAll(/<meta\b[^>]*>/gi)].some(([tag]) =>
    /\bname\s*=\s*["'](?:robots|googlebot)["']/i.test(tag) &&
    /\bcontent\s*=\s*["'][^"']*\bnoindex\b/i.test(tag)
  );
}

export function inventory(root=ROOT) {
  const groups=new Map(), excluded=[];
  for (const lang of LOCALES) {
    const localeDir=join(root,lang);
    try {readdirSync(localeDir);} catch {continue;}
    for (const abs of indexes(localeDir)) {
      const rel=relative(localeDir,abs).replaceAll("\\","/");
      const suffix=rel==="index.html" ? "" : rel.replace(/\/index\.html$/,"")+"/";
      const url=ORIGIN+"/"+lang+"/"+suffix;
      const html=readFileSync(abs,"utf8");
      const canonical=canonicalFromHead(html);
      const reject=noIndex(html)?"NOINDEX":canonical!==url?"CANONICAL_MISMATCH":null;
      if (reject) {excluded.push({path:relative(root,abs).replaceAll("\\","/"),reason:reject,canonical});continue;}
      if (!groups.has(suffix)) groups.set(suffix,new Map());
      groups.get(suffix).set(lang,url);
    }
  }
  const ordered=[...groups].sort((a,b)=>a[0].localeCompare(b[0],"en"));
  return {groups:ordered,excluded,sourceCount:ordered.reduce((n,[,m])=>n+m.size,0)};
}

export function renderSitemap(sets) {
  const lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'];
  for (const [suffix,byLang] of sets) {
    const langs=LOCALES.filter(l=>byLang.has(l));
    for (const lang of langs) {
      lines.push("  <url>",'    <loc>'+xmlEscape(byLang.get(lang))+'</loc>');
      for (const l of langs) lines.push('    <xhtml:link rel="alternate" hreflang="'+l+'" href="'+xmlEscape(byLang.get(l))+'"/>');
      if (byLang.has("en")) lines.push('    <xhtml:link rel="alternate" hreflang="x-default" href="'+xmlEscape(byLang.get("en"))+'"/>');
      lines.push("  </url>");
    }
  }
  return lines.concat("</urlset>","").join("\n");
}

if (process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href) {
  const data=inventory();
  const outputIndex=process.argv.indexOf("--output");
  if (outputIndex>=0) {
    const target=process.argv[outputIndex+1];
    if (!target || target==="--json" || target==="--stdout") throw Error("Explicit --output path required");
    // Do not allow overwriting the production sitemap or any source file.
    const absolute=resolve(target);
    if (absolute.startsWith(ROOT+"/") || absolute===join(ROOT,"sitemap.xml")) throw Error("Output must be outside the checked-out repository");
    writeFileSync(absolute,renderSitemap(data.groups),"utf8");
  }
  const summary={source:"STATIC_REPOSITORY_ONLY",localeCount:LOCALES.length,urls:data.sourceCount,groups:data.groups.length,excludedCount:data.excluded.length,excludedExamples:data.excluded.slice(0,15),productionDeployed:false};
  if (process.argv.includes("--json")) console.log(JSON.stringify(summary,null,2));
  else if (process.argv.includes("--stdout")) process.stdout.write(renderSitemap(data.groups));
  else console.log("Sitemap preview (NOT DEPLOYED)",summary);
}
