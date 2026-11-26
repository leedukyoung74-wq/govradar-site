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
  const type = String(b.type || ""), body = String(b.body || "").slice(0, 4000), lang = String(b.lang || "").slice(0, 5);
  let email = String(b.email || "").trim().toLowerCase();
  if (!TYPES.includes(type) || !body || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "bad" }, 400);
  // Never persist or relay membership access credentials supplied by older cached forms.
  if (/^\s*(?:member\s+code|رمز\s+العضوية)\s*:/im.test(body)) return json({ error: "secret_in_request" }, 400);
  const u = await who(request); if (u) email = u.email || email;
  const key = u ? "u:" + u.id : "e:" + (await sha(email)), now = new Date(), month = kstMonth(now), db = env.GV_DB;
  const dedupe = await sha(type + "|" + body + "|" + email);
  const prev = await db.prepare("select req_no, counted from requests where user_key=? and dedupe=? and created_at>? order by created_at desc limit 1")
    .bind(key, dedupe, new Date(now.getTime() - 6e5).toISOString()).first();
  const member = !!u && u.grade !== "m0";
  if (prev) { const n = await used(db, key, month); return json({ req_no: prev.req_no, duplicate: true, counted: !!prev.counted, member, left: member ? Math.max(0, LIMIT - n) : 0 }); }
  const d = new Date(now.getTime() + 9 * 3600e3), req = "RQ-" + d.toISOString().slice(2, 10).replace(/-/g, "") + "-" + crypto.randomUUID().replace(/-/g, "").slice(0, 4).toUpperCase();
  // Quota decision and insert MUST happen in the same D1/SQLite write statement.
  // A separate used() read followed by a regular INSERT can over-allocate the
  // two monthly included analyses when multiple requests arrive together.
  const quotaSql = "insert into requests (req_no, created_at, month, user_key, email, grade, type, lang, body, dedupe, counted) "
    + "select ?,?,?,?,?,?,?,?,?,?, case when ?=1 and "
    + "(select count(*) from requests where user_key=? and month=? and counted=1) < ? then 1 else 0 end";
  await db.prepare(quotaSql)
    .bind(req, now.toISOString(), month, key, email, u ? u.grade : null, type, lang, body, dedupe,
      member ? 1 : 0, key, month, LIMIT).run();
  const inserted = await db.prepare("select counted from requests where req_no=? and user_key=?").bind(req, key).first();
  const counted = !!(inserted && inserted.counted === 1);
  const totalUsed = await used(db, key, month);
  return json({ req_no: req, duplicate: false, counted, member, quote: !counted,
    left: member ? Math.max(0, LIMIT - totalUsed) : 0 });
}
// The page reports whether the Netlify form went through, so a failed alert is visible to the owner.
export async function onRequestPatch({ request, env }) {
  if (!env.GV_DB) return json({ error: "not_configured" }, 503);
  // A request number is not proof of ownership. Anonymous/other-user callers
  // must never alter the relay status of a stored customer request.
  const u = await who(request);
  if (!u || !u.id) return json({ error: "login" }, 401);
  let b; try { b = await request.json(); } catch (e) { return json({ error: "bad" }, 400); }
  const reqNo = typeof b.req_no === "string" ? b.req_no : "";
  if (!/^RQ-[0-9]{6}-[A-F0-9]{4}$/.test(reqNo) || typeof b.ok !== "boolean")
    return json({ error: "bad" }, 400);
  const key = "u:" + u.id;
  const owned = await env.GV_DB.prepare("select req_no from requests where req_no=? and user_key=?").bind(reqNo, key).first();
  if (!owned) return json({ error: "not_found" }, 404);
  const st = b.ok ? "relayed" : "relay_failed";
  await env.GV_DB.prepare("update requests set status=? where req_no=? and user_key=? and status in ('received','relay_failed')")
    .bind(st, reqNo, key).run();
  return json({ ok: true });
}
