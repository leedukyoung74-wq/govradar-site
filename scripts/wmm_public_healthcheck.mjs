// WMM public-only health check (non-deploying, no secrets, no user data)
// Run: node scripts/wmm_public_healthcheck.mjs
// Optional: node scripts/wmm_public_healthcheck.mjs --json
// Exits nonzero if a configured public route is unavailable.
const sites = [
  { platform: "WMM", url: "https://www.wmm-hoa.com/" },
  { platform: "WMM membership", url: "https://www.wmm-hoa.com/membership/" },
  { platform: "WMM support", url: "https://www.wmm-hoa.com/support-map/" },
  { platform: "GOV RADAR KO", url: "https://radar.wmm-hoa.com/ko/" },
  { platform: "GOV RADAR EN", url: "https://radar.wmm-hoa.com/en/" },
  { platform: "GOV RADAR ready", url: "https://radar.wmm-hoa.com/ko/ready/" },
  { platform: "GOV RADAR prepare", url: "https://radar.wmm-hoa.com/ko/prepare/" }
];
// PLAYGROUND / MIRACLE MAKERS intentionally excluded until official production URLs verified.
const timeoutMs = 12000;
async function inspect(item) {
  const checkedAt = new Date().toISOString();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(item.url, {
      method: "GET", redirect: "follow", signal: controller.signal,
      headers: { "User-Agent": "WMM-PublicHealthcheck/1.0" }
    });
    const type = res.headers.get("content-type") || "";
    let body = "";
    if (type.includes("text/html") && res.body) {
      const reader = res.body.getReader();
      let size = 0;
      try {
        while (size < 256_000) {
          const {value, done} = await reader.read();
          if (done) break;
          size += value.byteLength;
          body += new TextDecoder().decode(value);
        }
      } finally { await reader.cancel().catch(() => {}); }
    }
    const title = body.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]?.replace(/\s+/g," ").trim() || null;
    const hasForm = /<form(?:\s|>)/i.test(body);
    return { ...item, checkedAt, status: res.status, finalUrl: res.url, title,
      hasFormInInitialHtml: hasForm, htmlInspected: !!body, available: res.ok,
      note: "Public HTTP check only; login, JavaScript, CRM, payment, accuracy and browser UX not verified" };
  } catch (error) {
    return {...item, checkedAt, available:false, error:String(error?.message||error)};
  } finally { clearTimeout(timer); }
}
const results = [];
for (const item of sites) results.push(await inspect(item));
const report = { checkedAt: new Date().toISOString(), kind:"PUBLIC_ONLY", results };
if (process.argv.includes("--json")) console.log(JSON.stringify(report,null,2));
else for(const r of results) console.log(`${r.available?"PASS":"FAIL"} ${r.platform}: ${r.status||r.error} ${r.finalUrl||r.url}`);
if(results.some(r=>!r.available)) process.exitCode=1;
