// Member analysis requests, recorded on the server (Cloudflare D1 binding GV_DB).
// POST: record a request (login optional), count it against the monthly allowance (analysis members: 2 a month),
//       block the same request sent twice within 10 minutes, return the request number. The page then also sends
//       the Netlify form as before (owner inbox + Gmail draft alert); if that fails, the record stays here.
// GET:  signed-in users get their own requests from any device, plus how many are left this month.
// No GV_DB binding yet -> 503 not_configured, and the page keeps working the old way (browser-only list).
const IDENTITY = "https://wmm-govradar.netlify.app/.netlify/identity/user";
const MEMBER = ["m1", "m2", "m3", "m4", "m5", "admin", "owner"], LIMIT = 2, TYPES = ["tender", "country", "family", "partner"];
const json = (o, s) => new Response(JSON.stringify(o), { status: s || 200, headers: { "content-type": "application/json", "cache-control": "no-store" } });
async function sha(s) { const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join(""); }
async function who(request) {
  const auth = request.headers.get("authorization") || "";
  if (!/^Bearer\s+\S+/.test(auth)) return null;
  const r = await fetch(IDENTITY, { headers: { authorization: auth } }); if (!r.ok) return null;
  const u = await r.json(), roles = ((u.app_metadata || {}).roles || []).map(x => String(x).toLowerCase());
  return { id: u.id, email: String(u.email || "").toLowerCase(), grade: MEMBER.find(g => roles.includes(g)) || "m0" };
}
const kstMonth = d => new Date(d.getTime() + 9 * 3600e3).toISOString().slice(0, 7);
async function used(db, key, month) { const r = await db.prepare("select count(*) n from requests where user_key=? and month=? and counted=1").bind(key, month).first(); return (r && r.n) || 0; }
export async function onRequestGet({ request, env }) {
  if (!env.GV_DB) return json({ error: "not_configured" }, 503);
  const u = await who(request); if (!u) return json({ error: "login" }, 401);
  const key = "u:" + u.id, month = kstMonth(new Date());
  const rows = await env.GV_DB.prepare("select req_no, created_at, type, status, counted from requests where user_key=? order by created_at desc limit 30").bind(key).all();
  const n = await used(env.GV_DB, key, month), member = u.grade !== "m0";
  return json({ items: rows.results || [], member, limit: member ? LIMIT : 0, left: member ? Math.max(0, LIMIT - n) : 0 });
}
export async function onRequestPost({ request, env }) {
  if (!env.GV_DB) return json({ error: "not_configured" }, 503);
  let b; try { b = await request.json(); } catch (e) { return json({ error: "bad" }, 400); }
  // Explicit consent must be verified server-side, not just by the HTML checkbox.
  // Reject oversized inputs rather than silently truncating a customer's request.
  if (!b || typeof b !== "object" || Array.isArray(b) || b.privacy_consent !== true) {
    return json({ error: "privacy_consent_required" }, 400);
  }
  const type = typeof b.type === "string" ? b.type : "";
  const body = typeof b.body === "string" ? b.body.trim() : "";
  const lang = typeof b.lang === "string" ? b.lang : "en";
  let email = typeof b.email === "string" ? b.email.trim().toLowerCase() : "";
  if (!TYPES.includes(type) || !body || body.length > 4000 ||
      !["ko", "en", "es", "fr", "ar", "vi", "id"].includes(lang) ||
      email.length > 254 || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return json({ error: "bad" }, 400);
  }
  const u = await who(request); if (u) email = u.email || email;
  const key = u ? "u:" + u.id : "e:" + (await sha(email)), now = new Date(), month = kstMonth(now), db = env.GV_DB;
  const dedupe = await sha(type + "|" + body + "|" + email);
  const prev = await db.prepare("select req_no, counted from requests where user_key=? and dedupe=? and created_at>? order by created_at desc limit 1")
    .bind(key, dedupe, new Date(now.getTime() - 6e5).toISOString()).first();
  const member = !!u && u.grade !== "m0";
  if (prev) { const n = await used(db, key, month); return json({ req_no: prev.req_no, duplicate: true, counted: !!prev.counted, member, left: member ? Math.max(0, LIMIT - n) : 0 }); }
  const n = await used(db, key, month), counted = member && n < LIMIT ? 1 : 0;   // over the limit or not a member -> quote first, not counted
  const d = new Date(now.getTime() + 9 * 3600e3), req = "RQ-" + d.toISOString().slice(2, 10).replace(/-/g, "") + "-" + (await sha(dedupe + now.toISOString())).slice(0, 4).toUpperCase();
  await db.prepare("insert into requests (req_no, created_at, month, user_key, email, grade, type, lang, body, dedupe, counted) values (?,?,?,?,?,?,?,?,?,?,?)")
    .bind(req, now.toISOString(), month, key, email, u ? u.grade : null, type, lang, body, dedupe, counted).run();
  return json({ req_no: req, duplicate: false, counted: !!counted, member, quote: !counted, left: member ? Math.max(0, LIMIT - n - counted) : 0 });
}
// PATCH previously trusted an unauthenticated browser-supplied "ok" status.
// That allowed anyone with a request number to forge owner-delivery status. Until
// a server-to-server authenticated relay receipt is implemented, do not accept
// status changes from browser clients. POST and authenticated GET are unaffected.
export async function onRequestPatch() {
  return json({ error: "unverified_relay_status_not_supported" }, 403);
}
