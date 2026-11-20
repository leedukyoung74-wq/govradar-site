// Cloudflare Pages POST /nfform -> existing Netlify Forms endpoint.
// Handles only known in-site confirmation destinations. No outbound link redirects.
const NETLIFY_FORMS_ENDPOINT = "https://wmm-govradar.netlify.app/";
const FALLBACK = "/ko/thanks/";
const SAFE_CONFIRMATION = /^\/(?:ko|en|es|fr|ar|vi|id)\/(?:thanks|consortium\/thanks)\/$/;
const MAX_FORM_BYTES = 256 * 1024;

export function safeConfirmationPath(candidate) {
  if (typeof candidate !== "string" || !SAFE_CONFIRMATION.test(candidate)) return FALLBACK;
  return candidate;
}

async function readBoundedBody(request) {
  const length = Number(request.headers.get("content-length"));
  if (Number.isFinite(length) && length > MAX_FORM_BYTES) return null;
  if (!request.body) return new Uint8Array();
  const reader = request.body.getReader(), chunks = [];
  let size = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_FORM_BYTES) return null;
      chunks.push(value);
    }
    const combined = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { combined.set(chunk, offset); offset += chunk.byteLength; }
    return combined;
  } finally {
    try { await reader.cancel(); } catch {}
  }
}

export async function onRequestPost({request}) {
  const requestUrl = new URL(request.url);
  const next = safeConfirmationPath(requestUrl.searchParams.get("next"));
  const type = request.headers.get("content-type") || "";
  if (!/^application\/x-www-form-urlencoded(?:\s*;|\s*$)|^multipart\/form-data\s*;/i.test(type)) {
    return new Response("Unsupported form encoding", {status: 415});
  }
  let body;
  try { body = await readBoundedBody(request); }
  catch { return new Response("Cannot read form submission", {status: 400}); }
  if (body === null) return new Response("Form submission exceeds size limit", {status: 413});
  if (body.byteLength === 0) return new Response("Empty form submission", {status: 400});

  let response;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    response = await fetch(NETLIFY_FORMS_ENDPOINT, {
      method: "POST", headers: {
        "content-type": type,
        "user-agent": "GOV RADAR form relay"
      },
      body, redirect: "manual", signal: controller.signal
    });
  } catch {
    return new Response("Submission gateway unavailable. Please retry.", {status: 502});
  } finally { clearTimeout(timeout); }

  const acceptedDirect = response.status >= 200 && response.status < 300;
  const redirect = response.headers.get("location");
  let acceptedRedirect = false;
  if ((response.status === 302 || response.status === 303) && redirect) {
    try {
      const target = new URL(redirect, NETLIFY_FORMS_ENDPOINT);
      acceptedRedirect = target.origin === new URL(NETLIFY_FORMS_ENDPOINT).origin
        && target.protocol === "https:";
    } catch {}
  }
  if (!acceptedDirect && !acceptedRedirect) {
    return new Response("Submission not accepted by gateway. Please retry.", {status: 502});
  }

  // A transport-level success is not proof that a submission reached the
  // dashboard or CRM. That requires separate live provider confirmation.
  return Response.redirect(new URL(next, requestUrl.origin).href, 303);
}
