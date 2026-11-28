// Read-only public health checks. Does not verify authentication, UI, CRM, or transactions.
// Run: node scripts/wmm_public_healthcheck.mjs --json
import { pathToFileURL } from "node:url";

export const DEFAULT_SITES = Object.freeze([
  { platform: "WMM", url: "https://www.wmm-hoa.com/" },
  { platform: "WMM membership", url: "https://www.wmm-hoa.com/membership/" },
  { platform: "WMM support", url: "https://www.wmm-hoa.com/support-map/" },
  { platform: "GOV RADAR KO", url: "https://radar.wmm-hoa.com/ko/" },
  { platform: "GOV RADAR EN", url: "https://radar.wmm-hoa.com/en/" },
  { platform: "GOV RADAR ready", url: "https://radar.wmm-hoa.com/ko/ready/" },
  { platform: "GOV RADAR prepare", url: "https://radar.wmm-hoa.com/ko/prepare/" }
]);
// Unverified PLAYGROUND and MIRACLE MAKERS domains must not be guessed.
const TIMEOUT_MS = 12000;
const MAX_HTML_BYTES = 256_000;

function titleFromHtml(html) {
  return html.match(/<title\b[^>]*>([\s\S]*?)<\/title\s*>/i)?.[1]?.replace(/\s+/g, " ").trim() || null;
}

export async function inspectPublicRoute(item, fetchFn = fetch) {
  const checkedAt = new Date().toISOString();
  let parsed;
  try {
    parsed = new URL(item.url);
    if (parsed.protocol !== "https:" || !parsed.hostname) throw new Error("HTTPS URL required");
  } catch {
    return { ...item, checkedAt, available: false, classification: "INVALID_URL", error: "Invalid HTTPS URL" };
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetchFn(item.url, {
      method: "GET", redirect: "follow", signal: controller.signal,
      headers: { "User-Agent": "WMM-PublicHealthcheck/1.1" }
    });
    let finalUrl;
    try { finalUrl = new URL(res.url || item.url); } catch { finalUrl = parsed; }
    const redirectedToDifferentHost = finalUrl.hostname !== parsed.hostname;
    const insecureRedirect = finalUrl.protocol !== "https:";
    const contentType = res.headers.get("content-type") || "";
    const isHtml = /text\/html|application\/xhtml\+xml/i.test(contentType);
    let html = "";
    let htmlBytesRead = 0;
    let htmlTruncated = false;
    if (isHtml && res.body) {
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      try {
        while (true) {
          const {value, done} = await reader.read();
          if (done) { html += decoder.decode(); break; }
          const remaining = MAX_HTML_BYTES - htmlBytesRead;
          if (remaining <= 0) { htmlTruncated = true; break; }
          const bytes = value.subarray(0, remaining);
          html += decoder.decode(bytes, {stream: true});
          htmlBytesRead += bytes.length;
          if (bytes.length < value.length) { htmlTruncated = true; break; }
        }
      } finally { await reader.cancel().catch(() => {}); }
    }
    const title = titleFromHtml(html);
    const suspectedLoginRedirect = /\b(login|signin|sign-in|auth)\b/i.test(finalUrl.pathname)
      && !/\b(login|signin|sign-in|auth)\b/i.test(parsed.pathname);
    const available = res.ok && isHtml && !insecureRedirect && !redirectedToDifferentHost
      && !suspectedLoginRedirect && !!html.trim();
    const classification = !res.ok ? "HTTP_ERROR" :
      insecureRedirect ? "INSECURE_REDIRECT" :
      redirectedToDifferentHost ? "CROSS_HOST_REDIRECT" :
      suspectedLoginRedirect ? "LOGIN_REDIRECT" :
      !isHtml ? "UNEXPECTED_CONTENT_TYPE" :
      !html.trim() ? "EMPTY_HTML" : "HTTP_OK_HTML";
    return {
      ...item, checkedAt, status: res.status, finalUrl: finalUrl.href,
      contentType, classification, available, title,
      hasFormInInitialHtml: /<form(?:\s|>)/i.test(html),
      htmlInspected: !!html, htmlBytesRead, htmlTruncated,
      note: "Public HTTP only: client rendering, soft 404, login, CRM, payment, accuracy and UX NOT VERIFIED"
    };
  } catch (err) {
    return { ...item, checkedAt, available:false, classification: "FETCH_ERROR",
      error: err?.name === "AbortError" ? "Timeout" : String(err?.message || err) };
  } finally { clearTimeout(timeout); }
}

export async function runPublicHealthcheck(sites = DEFAULT_SITES, fetchFn = fetch) {
  const results = [];
  for (const item of sites) results.push(await inspectPublicRoute(item, fetchFn));
  return {checkedAt: new Date().toISOString(), kind:"PUBLIC_ONLY", results};
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const report = await runPublicHealthcheck();
  if (process.argv.includes("--json")) console.log(JSON.stringify(report, null, 2));
  else for (const r of report.results)
    console.log(`${r.available ? "PASS" : "FAIL"} ${r.platform}: ${r.classification} ${r.status || r.error || ""} ${r.finalUrl || r.url}`);
  if (report.results.some(r => !r.available)) process.exitCode = 1;
}
