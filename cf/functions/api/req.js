// Member analysis requests, recorded on the server (Cloudflare D1 binding GV_DB).
// POST: record a request (login optional), count it against the monthly allowance (analysis members: 2 a month),
//       block the same request sent twice within 10 minutes, return the request number. The page then also sends
//       the Netlify form as before (owner inbox + Gmail draft alert); if that fails, the record stays here.
// GET:  signed-in users get their own requests from any device, plus how many are left this month.
// No GV_DB binding yet -> 503 not_configured, and the page keeps working the old way (browser-only list).
// Real customer data is stored only when the owner switches GV_STORE=on (after the privacy notice and legal basis are final).
// Without it the server answers 503 like before; GV_STORE=test accepts test addresses only (@example.com / @example.org).
// Retention (owner decision 2026-11-17): request text 90 days after completion, minimal record up to 1 year after completion,
// contract/payment/dispute records kept apart in legal_records for the period the law sets; purged on every call (no cron).
// Member standing (owner decision 2026-11-17): see standing() below; the members table holds billing dates only.
import { purgeLogged } from "./_purge.js";
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
const rnd = n => [...crypto.getRandomValues(new Uint8Array(n))].map(x => x.toString(16).padStart(2, "0")).join("");
const DAY_KEY = 10, DAY_IP = 20, RELAY_WINDOW = 30 * 60e3;   // per person / per network per 24h; relay report accepted for 30 min
// Network address for the daily limit: keyed with a random salt that changes every day (UTC) and is deleted after 2 days,
// so stored values cannot be matched to an address or across days once the salt is gone. Values are wiped after 48 hours.
async function ipKey(db, ip, now) {
  const day = now.toISOString().slice(0, 10), old = new Date(now.getTime() - 2 * 864e5).toISOString().slice(0, 10);
  await db.prepare("insert or ignore into salts (day, salt) values (?, ?)").bind(day, rnd(32)).run();
  await db.prepare("delete from salts where day<?").bind(old).run();
  await db.prepare("update requests set ip_hash=null where ip_hash is not null and created_at<?").bind(new Date(now.getTime() - 2 * 864e5).toISOString()).run();
  const yday = new Date(now.getTime() - 864e5).toISOString().slice(0, 10);
  const r = await db.prepare("select salt from salts where day=?").bind(day).first(), y = await db.prepare("select salt from salts where day=?").bind(yday).first();
  const cur = await sha((r ? r.salt : rnd(32)) + "|" + ip);
  return { cur, prev: y ? await sha(y.salt + "|" + ip) : cur };   // prev lets the 24-hour limit span the UTC midnight salt change
}
const kstMonth = d => new Date(d.getTime() + 9 * 3600e3).toISOString().slice(0, 7);
async function used(db, key, month) { const r = await db.prepare("select count(*) n from requests where user_key=? and month=? and counted=1").bind(key, month).first(); return (r && r.n) || 0; }
const DAY = 864e5, KST = 9 * 3600e3;
const kstDate = d => new Date(d.getTime() + KST);                  // shift so getUTC* reads Korea time
// Member standing (owner decision 2026-11-17, fixed after ChatGPT review T20261117-06). Fail-closed: a paid role is honoured
// only when a billing row confirms it. No row, unreadable table or missing dates -> "unverified": the member keeps reading
// as before but new paid requests are taken as quotes (not counted) until the owner records the payment.
// monthly: paid_through = last paid month (YYYY-MM). The next fee is due on the 1st of the following month (KST).
//          Overdue days count from that due date and keep growing month after month until a payment is recorded:
//          due day = normal; 1-6 days overdue = new paid requests blocked; 7+ days (the 8th 00:00 KST on) = M0.
// quarterly / annual: contract_end = last day; day after = blocked, 7 days after = M0.  suspended: M0 at once.
export function standing(role, m, now) {
  now = now || new Date();
  if (!role || role === "m0") return { grade: "m0", paid: false, can_request: false, state: "free" };
  if (role === "admin" || role === "owner") return { grade: role, paid: true, can_request: true, state: "staff" };
  const unverified = { grade: "m0", paid: false, can_request: false, state: "unverified" };
  if (!m || m === "error") return unverified;
  if (m.status === "suspended") return { grade: "m0", paid: false, can_request: false, state: "suspended" };
  if (m.status !== "active") return unverified;
  const today = kstDate(now).toISOString().slice(0, 10), plan = m.plan || "monthly";
  let due;                                                           // first day NOT covered by a payment (KST date)
  if (plan === "monthly") {
    const pt = String(m.paid_through || ""); if (!/^\d{4}-\d{2}$/.test(pt)) return unverified;
    let y = +pt.slice(0, 4), mo = +pt.slice(5, 7) + 1; if (mo > 12) { mo = 1; y++; }
    due = `${y}-${String(mo).padStart(2, "0")}-01`;
  } else if (plan === "quarterly" || plan === "annual") {
    const end = String(m.contract_end || ""); if (!/^\d{4}-\d{2}-\d{2}$/.test(end)) return unverified;
    due = new Date(Date.parse(end) + DAY).toISOString().slice(0, 10);
    if (today < due) return { grade: role, paid: true, can_request: true, state: "ok" };
    const late = Math.round((Date.parse(today) - Date.parse(end)) / DAY);
    return late >= 7 ? { grade: "m0", paid: false, can_request: false, state: "lapsed" } : { grade: role, paid: true, can_request: false, state: "grace" };
  } else return unverified;
  const overdue = Math.round((Date.parse(today) - Date.parse(due)) / DAY);   // monthly: <=0 paid ahead or due today
  if (overdue >= 7) return { grade: "m0", paid: false, can_request: false, state: "lapsed" };
  if (overdue >= 1) return { grade: role, paid: true, can_request: false, state: "grace" };
  return { grade: role, paid: true, can_request: true, state: "ok" };
}
async function memberRow(db, id) { try { return await db.prepare("select * from members where user_id=?").bind(id).first(); } catch (e) { return "error"; } }   // error -> unverified (fail-closed)
// Retention runs on every call AND daily from the scheduled worker (cf/cron/purge-worker.js): see _purge.js.
async function purge(db, now) { await purgeLogged(db, now, "request"); }
const db0 = env => env.GV_DB;
function storeMode(env) { const v = String(env.GV_STORE || "").toLowerCase(); return v === "on" ? "on" : v === "test" ? "test" : "off"; }
export async function onRequestGet({ request, env }) {
  if (!env.GV_DB || storeMode(env) === "off") return json({ error: "not_configured" }, 503);
  const u = await who(request); if (!u) return json({ error: "login" }, 401);
  const now = new Date(); await purge(env.GV_DB, now);
  const key = "u:" + u.id, month = kstMonth(now), st = standing(u.grade, await memberRow(env.GV_DB, u.id), now);
  const rows = await env.GV_DB.prepare("select req_no, created_at, type, status, counted from requests where user_key=? order by created_at desc limit 30").bind(key).all();
  const n = await used(env.GV_DB, key, month), member = st.paid;
  return json({ items: rows.results || [], member, standing: st.state, can_request: st.can_request, limit: member ? LIMIT : 0, left: st.can_request ? Math.max(0, LIMIT - n) : 0 });
}
export async function onRequestPost({ request, env }) {
  const mode = storeMode(env);
  if (!env.GV_DB || mode === "off") return json({ error: "not_configured" }, 503);
  let b; try { b = await request.json(); } catch (e) { return json({ error: "bad" }, 400); }
  const type = String(b.type || ""), body = String(b.body || "").slice(0, 4000), lang = String(b.lang || "").slice(0, 5);
  let email = String(b.email || "").trim().toLowerCase();
  if (!TYPES.includes(type) || !body || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "bad" }, 400);
  const u = await who(request); if (u) email = u.email || email;
  if (mode === "test" && !/@example\.(com|org)$/.test(email)) return json({ error: "test_only" }, 503);   // test mode: real addresses refused; the page must NOT fall back to the old form
  await purge(db0(env), new Date());
  const key = u ? "u:" + u.id : "e:" + (await sha(email)), now = new Date(), month = kstMonth(now), db = env.GV_DB;
  const dedupe = await sha(type + "|" + body + "|" + email);
  const prev = await db.prepare("select req_no, counted from requests where user_key=? and dedupe=? and created_at>? order by created_at desc limit 1")
    .bind(key, dedupe, new Date(now.getTime() - 6e5).toISOString()).first();
  const st = u ? standing(u.grade, await memberRow(db, u.id), now) : { paid: false, can_request: false, state: "guest" };
  const member = st.paid, canCount = st.can_request;
  if (prev) { const n = await used(db, key, month); return json({ req_no: prev.req_no, duplicate: true, counted: !!prev.counted, member, left: member ? Math.max(0, LIMIT - n) : 0 }); }
  const ip = await ipKey(db, request.headers.get("cf-connecting-ip") || "none", now), since = new Date(now.getTime() - 864e5).toISOString();
  const rk = await db.prepare("select count(*) n from requests where user_key=? and created_at>?").bind(key, since).first();
  const ri = await db.prepare("select count(*) n from requests where ip_hash in (?,?) and created_at>?").bind(ip.cur, ip.prev, since).first();
  if ((rk && rk.n) >= DAY_KEY || (ri && ri.n) >= DAY_IP) return json({ error: "too_many" }, 429);
  const tok = rnd(16), d = new Date(now.getTime() + 9 * 3600e3), day = d.toISOString().slice(2, 10).replace(/-/g, "");
  let req = "", res = null;
  for (let i = 0; i < 3 && !res; i++) {          // 32-bit random suffix; primary key rejects a clash, then retry
    req = "RQ-" + day + "-" + rnd(4).toUpperCase();
    try {   // one statement: the monthly count and the insert happen together, so two requests at once cannot both use the last slot
      res = await db.prepare("insert into requests (req_no, created_at, month, user_key, email, grade, type, lang, body, dedupe, counted, relay_key, ip_hash) " +
        "select ?,?,?,?,?,?,?,?,?,?, case when ?=1 and (select count(*) from requests where user_key=? and month=? and counted=1) < ? then 1 else 0 end, ?, ?")
        .bind(req, now.toISOString(), month, key, email, u ? st.grade || u.grade : null, type, lang, body, dedupe, canCount ? 1 : 0, key, month, LIMIT, await sha(tok), ip.cur).run();
    } catch (e) { if (!/UNIQUE|constraint/i.test(String(e && e.message))) throw e; }
  }
  if (!res) return json({ error: "busy" }, 503);
  const row = await db.prepare("select counted from requests where req_no=?").bind(req).first(), counted = row ? row.counted : 0, n = await used(db, key, month);
  return json({ req_no: req, tok, duplicate: false, counted: !!counted, member, standing: st.state, quote: !counted, left: canCount ? Math.max(0, LIMIT - n) : 0 });
}
// The page reports whether ITS OWN post of the Netlify form looked successful. The server cannot see Netlify, so this is
// recorded as client_ok / client_fail (what the browser said), never as a confirmed delivery. Only the browser that made the request can report it: POST hands it a one-time random token (only its hash is stored),
// the report must come within 30 minutes, and it can only move received -> client_ok / client_fail. Knowing a request number is not enough.
// A relay failure keeps the request and its count: the record is still here for the owner to handle (owner gives the count back if it is cancelled).
export async function onRequestPatch({ request, env }) {
  if (!env.GV_DB || storeMode(env) === "off") return json({ error: "not_configured" }, 503);
  let b; try { b = await request.json(); } catch (e) { return json({ error: "bad" }, 400); }
  const no = String(b.req_no || ""), tok = String(b.tok || "");
  if (!/^RQ-\d{6}-[0-9A-F]{8}$/.test(no) || !/^[0-9a-f]{32}$/.test(tok)) return json({ error: "forbidden" }, 403);
  const st = b.ok ? "client_ok" : "client_fail", after = new Date(Date.now() - RELAY_WINDOW).toISOString();
  const r = await env.GV_DB.prepare("update requests set status=?, relay_key=null where req_no=? and relay_key=? and status='received' and created_at>?")
    .bind(st, no, await sha(tok), after).run();
  const changed = r && r.meta ? r.meta.changes : (r && r.changes);
  return changed ? json({ ok: true }) : json({ error: "forbidden" }, 403);
}

// Deletion request / withdrawal by the signed-in member: everything of theirs that has no legal reason to stay is deleted now.
// Rows under legal_hold (contract, payment, dispute) stay; their legal_records copy keeps only what the law needs.
export async function onRequestDelete({ request, env }) {
  if (!env.GV_DB || storeMode(env) === "off") return json({ error: "not_configured" }, 503);
  const u = await who(request); if (!u) return json({ error: "login" }, 401);
  const key = "u:" + u.id, db = env.GV_DB, e = "e:" + (await sha(u.email || ""));
  const r = await db.prepare("delete from requests where user_key in (?,?) and legal_hold=0").bind(key, e).run();
  await db.prepare("update requests set body='', email='', note=null, dedupe='', ip_hash=null, relay_key=null, body_purged_at=? where user_key in (?,?) and legal_hold=1").bind(new Date().toISOString(), key, e).run();
  return json({ ok: true, deleted: r && r.meta ? r.meta.changes : 0, kept_for_law: true });
}
