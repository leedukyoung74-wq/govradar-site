// Shared helpers for www.wmm-hoa.com server functions (moved from chatgpt.site, 2026-11-22).
export const FIREBASE = {
  apiKey: "AIzaSyC6hgCCHyEmpVurQgiKwkygx8EmlTsUzIM",
  authDomain: "wmm-support-map.firebaseapp.com",
  projectId: "wmm-support-map",
  appId: "1:7025059622:web:ba3cb2c4ff09567d3083e7",
};
export const json = (data, status = 200, extra = {}) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra } });

const b64u = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
let JWKS = null, JWKS_AT = 0;
async function keys() {
  if (JWKS && Date.now() - JWKS_AT < 3600e3) return JWKS;
  const r = await fetch("https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com", { cf: { cacheTtl: 3600 } });
  JWKS = (await r.json()).keys || []; JWKS_AT = Date.now();
  return JWKS;
}
/** Verify a Firebase ID token (RS256) — returns the claims or null. */
export async function verify(request) {
  const h = request.headers.get("authorization") || "";
  const tok = h.startsWith("Bearer ") ? h.slice(7).trim() : "";
  const parts = tok.split(".");
  if (parts.length !== 3) return null;
  try {
    const head = JSON.parse(new TextDecoder().decode(b64u(parts[0])));
    const body = JSON.parse(new TextDecoder().decode(b64u(parts[1])));
    if (head.alg !== "RS256") return null;
    const now = Math.floor(Date.now() / 1000);
    if (body.aud !== FIREBASE.projectId || body.iss !== "https://securetoken.google.com/" + FIREBASE.projectId) return null;
    if (!body.sub || body.exp < now - 30 || body.iat > now + 300) return null;
    const jwk = (await keys()).find((k) => k.kid === head.kid);
    if (!jwk) return null;
    const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64u(parts[2]), new TextEncoder().encode(parts[0] + "." + parts[1]));
    return ok ? body : null;
  } catch { return null; }
}
