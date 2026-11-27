/**
 * STAGED Cloudflare Cron watchdog. Dispatch disabled by default, no deploy.
 * No paid API, customer records, checkout, DNS changes, or source publication.
 * Source freshness verification is independent of GitHub scheduled triggers.
 */
const REPO="leedukyoung74-wq/govradar-site";
const ROOT="https://raw.githubusercontent.com/"+REPO+"/data/hz/";
const API="https://api.github.com/repos/"+REPO+"/actions/workflows/";
const TARGETS={
  usgs: { workflow:"wmm_fast_timer.yml", maxAge:20*60_000, cooldown:15*60_000 },
  nws_cisa: { workflow:"wmm_nws_cisa_timer.yml", maxAge:45*60_000, cooldown:30*60_000 }
};
function timestamp(value,kst=false) {
  if (typeof value!=="string" || value.length>45) return null;
  const x=kst && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?$/.test(value)
    ? value+"+09:00":value;
  const t=Date.parse(x);
  return Number.isFinite(t)?t:null;
}
export function classify(official,nws,kev,now) {
  const us=timestamp(official?.usgs_fast_checked,true);
  const nw=timestamp(nws?.source_health?.last_ok);
  const ke=timestamp(kev?.source_health?.last_ok);
  const ok=(t,limit,healthy)=>t!==null && healthy && now>=t && now-t>limit;
  const hasUS=official?.sources?.usgs?.ok===true;
  const hasNWS=nws?.source_health?.ok===true && nws.source_health.stale===false;
  const hasKEV=kev?.source_health?.ok===true && kev.source_health.stale===false;
  return {
    usgs:ok(us,TARGETS.usgs.maxAge,hasUS),
    nws_cisa:ok(nw,45*60_000,hasNWS)||ok(ke,6*3600_000,hasKEV),
    failClosed:us===null || nw===null || ke===null ||
      !hasUS || !hasNWS || !hasKEV
  };
}
async function jsonGet(name,fetcher) {
  if (!["official.json","nws_active.json","cisa_kev.json"].includes(name))
    throw Error("UNAPPROVED_FILE");
  const res=await fetcher(ROOT+name,{
    method:"GET",redirect:"error",headers:{Accept:"application/json"}
  });
  if (res.status!==200) throw Error("UPSTREAM_NOT_200");
  const body=await res.text();
  if (body.length>450_000) throw Error("UPSTREAM_TOO_LARGE");
  return JSON.parse(body);
}
async function attempt(key,env,fetcher,now) {
  if (env.DISPATCH_ENABLED!=="true") return "DISABLED";
  if (!env.GH_DISPATCH_TOKEN || !env.WMM_CRON_STATE ||
      typeof env.WMM_CRON_STATE.get!=="function" ||
      typeof env.WMM_CRON_STATE.put!=="function")
    return "MISSING_PRIVATE_AUTH_OR_KV";
  const target=TARGETS[key];
  if (!target) return "UNAPPROVED_SOURCE";
  const slot="cooldown_"+key;
  let prev;
  try { prev=Number(await env.WMM_CRON_STATE.get(slot)); }
  catch (_e) {return "KV_READ_ERROR";}
  if (Number.isFinite(prev) && prev>0 && now-prev<target.cooldown)
    return "COOLDOWN_ACTIVE";
  const res=await fetcher(API+target.workflow+"/dispatches",{
    method:"POST",redirect:"error",
    headers:{
      Authorization:"Bearer "+env.GH_DISPATCH_TOKEN,
      Accept:"application/vnd.github+json",
      "X-GitHub-Api-Version":"2022-11-28",
      "Content-Type":"application/json",
      "User-Agent":"WMM-GOVRADAR-free-cron-guard/1.0"
    },
    body:JSON.stringify({ref:"main",inputs:{dry_run:"false"}})
  });
  if (res.status!==204) return "DISPATCH_DENIED";
  try {await env.WMM_CRON_STATE.put(slot,String(now));}
  catch (_e) {return "DISPATCH_ACCEPTED_KV_WRITE_FAILED";}
  return "DISPATCH_ACCEPTED";
}
export async function inspect(env,now=Date.now(),fetcher=fetch) {
  const result={
    scope:"WMM_FREE_CRON_WATCHDOG_STAGED",enabled:env?.DISPATCH_ENABLED==="true",
    usgs:"NOT_CHECKED",nws_cisa:"NOT_CHECKED",
    maximum_dispatches_per_cron:2,published_items:0,
    customer_data_accessed:false,real_time_sla_proven:false
  };
  let a,b,c;
  try {
    [a,b,c]=await Promise.all([
      jsonGet("official.json",fetcher),
      jsonGet("nws_active.json",fetcher),
      jsonGet("cisa_kev.json",fetcher)
    ]);
  } catch (_e) {
    result.usgs="SOURCE_READ_ERROR";result.nws_cisa="SOURCE_READ_ERROR";
    return result;
  }
  const status=classify(a,b,c,now);
  if (status.failClosed) {
    result.usgs="SOURCE_STATUS_INVALID";
    result.nws_cisa="SOURCE_STATUS_INVALID";
    return result;
  }
  for (const name of ["usgs","nws_cisa"]) {
    if (!status[name]) {result[name]="NOT_DUE";continue;}
    try {result[name]=await attempt(name,env,fetcher,now);}
    catch (_e) {result[name]="DISPATCH_REQUEST_FAILED";}
  }
  return result;
}
export default {
  async scheduled(_event,env,ctx) {
    ctx.waitUntil(inspect(env).then(result=>{
      // Whitelisted result only; no token, raw source, URL or personal data.
      console.log(JSON.stringify(result));
    }));
  }
};
