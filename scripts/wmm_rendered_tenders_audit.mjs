// Offline audit of rendered GOV RADAR MDB cards, separate from data/opps.json.
// The existence of an href does NOT prove it is an official notice or currently open.
// Run: node scripts/wmm_rendered_tenders_audit.mjs --json --as-of 2026-11-20
import {readFileSync} from "node:fs";
import {dirname,resolve,join} from "node:path";
import {fileURLToPath,pathToFileURL} from "node:url";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const LOCALES=["ko","en","es","fr","ar","vi","id"];
const dayPattern=/^\d{4}-\d{2}-\d{2}$/;
function validDate(s) {
 return typeof s==="string"&&dayPattern.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s+"T00:00:00Z").toISOString().slice(0,10)===s;
}
function safeHref(s) {
 try {const u=new URL(s);return u.protocol==="https:"&&u.hostname.length>0}
 catch {return false}
}
// Match only MDB list items with both category and deadline attributes; this is not a full HTML parser.
export function auditRenderedMdb(html,{locale="ko",asOf="2026-11-20"}={}) {
 if(!validDate(asOf))throw new TypeError("Invalid asOf date");
 const cards=[...html.matchAll(/<li\s+data-s="([^"]+)"\s+data-dl="([^"]*)"[^>]*>([\s\S]*?)<\/li>/gi)];
 const counts={cards:cards.length,pastDeadline:0,deadlineToday:0,futureDeadline:0,unknownDeadline:0,invalidDeadline:0,missingSourceLink:0,externalSourceLinks:0,thirdPartyLinks:0,officialStatusUnverified:0};
 const issues=[];
 for(const [index,match] of cards.entries()){
  const deadline=match[2],body=match[3];
  const url=body.match(/<a\s+class="src"\s+href="([^"]+)"/i)?.[1]||null;
  if(!url||!safeHref(url)){counts.missingSourceLink++;issues.push({type:"MISSING_OR_INVALID_LINK",index});}
  else {counts.externalSourceLinks++;const host=new URL(url).hostname.toLowerCase();if(/bidsfactory\.com$/.test(host))counts.thirdPartyLinks++;}
  // Source links may be aggregators; never automatically classify them as official.
  counts.officialStatusUnverified++;
  if(!deadline){counts.unknownDeadline++;continue}
  if(!validDate(deadline)){counts.invalidDeadline++;issues.push({type:"INVALID_DATE",index,deadline});continue}
  if(deadline<asOf)counts.pastDeadline++;
  else if(deadline===asOf)counts.deadlineToday++;
  else counts.futureDeadline++;
 }
 const headingClaimsOpen=/<h2[^>]*>[^<]*(?:열린 입찰|Open tenders)/i.test(html);
 if(headingClaimsOpen&&counts.pastDeadline>0)issues.push({type:"MISLEADING_OPEN_HEADING_WITH_PAST_DATES",count:counts.pastDeadline});
 return {locale,asOf,classification:"RENDERED_STATIC_HTML_AUDIT_ONLY",counts,issues,
  caveat:"The file may differ from live site. Deadlines are date-only; extensions/timezones/status and validity of third-party links require original notice verification."};
}
export function auditCurrentMdb(asOf="2026-11-20") {
 return LOCALES.map(locale=>{
  const path=join(root,locale,"mdb","index.html");
  return auditRenderedMdb(readFileSync(path,"utf8"),{locale,asOf});
 });
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const ix=process.argv.indexOf("--as-of");
 const asOf=ix>=0?process.argv[ix+1]:new Date().toISOString().slice(0,10);
 const results=auditCurrentMdb(asOf);
 if(process.argv.includes("--json"))console.log(JSON.stringify(results,null,2));
 else for(const r of results)console.log(`${r.locale}: ${r.counts.cards} cards, ${r.counts.pastDeadline} past dates, ${r.counts.missingSourceLink} missing links`);
 if(results.some(r=>r.counts.missingSourceLink||r.counts.invalidDeadline))process.exitCode=1;
}
