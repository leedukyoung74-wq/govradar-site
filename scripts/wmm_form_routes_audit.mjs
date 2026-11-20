// Read-only check that built localized Netlify forms still target the GOV RADAR relay.
// Never submits a form or changes a file.
// Usage: node scripts/wmm_form_routes_audit.mjs live-branch/public
import {readdirSync,readFileSync,existsSync} from "node:fs";
import {join,relative,resolve,dirname} from "node:path";
import {pathToFileURL} from "node:url";

const LANGUAGES = ["ko","en","es","fr","ar","vi","id"];
const BASE = "https://radar.wmm-hoa.com";
const SAFE_NEXT = /^\/(?:ko|en|es|fr|ar|vi|id)\/(?:thanks|consortium\/thanks)\/$/;

function attr(tag,name) {
  const match=tag.match(new RegExp("(?:^|\\s)"+name.replace(/[-/\\^$*+?.()|[\]{}]/g,"\\$&")+"\\s*=\\s*([\"'])(.*?)\\1","i"));
  return match?.[2]??null;
}
function* htmlFiles(root) {
  for(const item of readdirSync(root,{withFileTypes:true})) {
    if(item.isSymbolicLink()) continue;
    const p=join(root,item.name);
    if(item.isDirectory()) yield* htmlFiles(p);
    else if(item.isFile() && item.name.endsWith(".html")) yield p;
  }
}
export function auditForms(root) {
  const problems=[],seen=[];
  for(const language of LANGUAGES) {
    const locale=join(root,language);
    if(!existsSync(join(locale,"index.html"))) {
      problems.push({path:language,issue:"LANGUAGE_HOME_MISSING"});
      continue;
    }
    for(const path of htmlFiles(locale)) {
      const html=readFileSync(path,"utf8");
      const forms=[...html.matchAll(/<form\b[^>]*\bdata-netlify\s*=\s*["']true["'][^>]*>/gi)];
      for(const match of forms) {
        const tag=match[0], end=html.indexOf("</form>",match.index+tag.length);
        const body=end>=0?html.slice(match.index+tag.length,end):"";
        const name=attr(tag,"name"),method=attr(tag,"method"),action=attr(tag,"action");
        const label=relative(root,path).replaceAll("\\","/");
        const field=[...body.matchAll(/<input\b[^>]*>/gi)].map(x=>x[0])
          .find(x=>attr(x,"name")==="form-name");
        const safeName=attr(field||"","value");
        if(end<0) problems.push({path:label,issue:"FORM_NOT_CLOSED"});
        if(method?.toUpperCase()!=="POST") problems.push({path:label,issue:"FORM_NOT_POST"});
        if(!name || name!==safeName) problems.push({path:label,issue:"FORM_NAME_HIDDEN_MISMATCH",name,hidden:safeName});
        let next=null;
        try{
          const url=new URL(action,BASE);
          if(url.origin===BASE && url.pathname==="/nfform" && url.searchParams.size===1)
            next=url.searchParams.get("next");
        }catch{}
        if(!next || !SAFE_NEXT.test(next) || !next.startsWith("/"+language+"/"))
          problems.push({path:label,issue:"UNSAFE_OR_INCORRECT_NEXT",action});
        else if(!existsSync(join(root,next.slice(1),"index.html")))
          problems.push({path:label,issue:"CONFIRMATION_MISSING",target:next});
        seen.push({page:label,name,action});
      }
    }
  }
  if(!seen.length) problems.push({path:"all",issue:"NO_FORMS_DISCOVERED"});
  return {kind:"STATIC_REPO_ONLY",languages:LANGUAGES.length,forms:seen.length,
    names:[...new Set(seen.map(f=>f.name))].sort(),problems,productionSubmissionVerified:false};
}
if(process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href) {
  const root=resolve(process.argv[2]||"live-branch/public");
  const result=auditForms(root);
  console.log(JSON.stringify(result,null,2));
  if(result.problems.length)process.exitCode=1;
}
