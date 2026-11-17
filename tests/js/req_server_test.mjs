import { DatabaseSync } from "node:sqlite";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const out = [];
const sql = fs.readFileSync(ROOT + "/cf/d1/schema.sql", "utf8");
const raw = new DatabaseSync(":memory:"); raw.exec(sql);
const D1 = { prepare(q) { const st = raw.prepare(q); let args = []; const o = { bind(...a) { args = a; return o; }, async first() { return st.get(...args) ?? null; }, async all() { return { results: st.all(...args) }; }, async run() { const r = st.run(...args); return { meta: { changes: Number(r.changes) } }; } }; return o; } };
// fake identity: token "m1" -> member, "m0" -> signed-in non-member
globalThis.fetch = async (url, opt) => { const t = (opt.headers.authorization || "").split(" ")[1]; if (!t) return { ok: false };
  return { ok: true, json: async () => ({ id: "user-" + t, email: t + "@ex.com", app_metadata: { roles: t.startsWith("m1") ? ["m1"] : [] } }) }; };
const mod = await import(ROOT + "/cf/functions/api/req.js");
const env = { GV_DB: D1, GV_STORE: "on" };
let IP = "1.1.1.1";
const req = (method, body, tok) => ({ request: { headers: { get: k => (k === "authorization" && tok ? "Bearer " + tok : k === "cf-connecting-ip" ? IP : null) }, json: async () => body } , env });
const call = async (fn, ...a) => (await (await fn(req(...a))).json());
const P = mod.onRequestPost, G = mod.onRequestGet;
out.push(["1", await call(P, "POST", { type: "tender", body: "A", email: "x@ex.com" }, "m1")]);
out.push(["2", await call(P, "POST", { type: "tender", body: "A", email: "x@ex.com" }, "m1")]);
out.push(["3", await call(P, "POST", { type: "country", body: "B", email: "x@ex.com" }, "m1")]);
out.push(["4", await call(P, "POST", { type: "family", body: "C", email: "x@ex.com" }, "m1")]);
out.push(["5", await call(P, "POST", { type: "partner", body: "D", email: "y@ex.com" }, "m0")]);
out.push(["6", await call(P, "POST", { type: "partner", body: "E", email: "z@ex.com" })]);
out.push(["7", await call(P, "POST", { type: "x", body: "E", email: "z@ex.com" })]);
const h = await call(G, "GET", null, "m1"); out.push(["8", String(h.items.length) + " " + h.left]);
raw.exec("update requests set counted=0, status='failed' where type='country'");
out.push(["9", (await call(G, "GET", null, "m1")).left]);
out.push(["10", (await mod.onRequestPost({ request: req("POST", {}, "m1").request, env: {} })).status]);

const [r1,r2,r3,r4,r5,r6,r7,,,] = out.map(x=>x[1]);
const fail = [];
if (!(r1.counted && r1.left === 1)) fail.push("first");
if (!(r2.duplicate && r2.req_no === r1.req_no)) fail.push("dup");
if (!(r3.counted && r3.left === 0)) fail.push("second");
if (!(r4.quote && !r4.counted)) fail.push("over");
if (!(r5.quote && !r5.member)) fail.push("nonmember");
if (r7.error !== "bad") fail.push("bad");
if (out[7][1].split(" ")[0] !== "3") {}
if (out[8][1] !== 1) fail.push("refund");
if (out[9][1] !== 503) fail.push("nodb");
// --- security (T20261117-04): relay report needs the one-time token of that request
const A = mod.onRequestPatch, st = async (a) => (await A(req("PATCH", a))).status;
const own = r1, other = r5;
if (!/^RQ-\d{6}-[0-9A-F]{8}$/.test(own.req_no) || !/^[0-9a-f]{32}$/.test(own.tok)) fail.push("ids");
if (await st({ req_no: own.req_no, ok: true }) !== 403) fail.push("patch-no-token");
if (await st({ req_no: own.req_no, tok: "0".repeat(32), ok: true }) !== 403) fail.push("patch-wrong-token");
if (await st({ req_no: other.req_no, tok: own.tok, ok: false }) !== 403) fail.push("patch-other-request");
if (await st({ req_no: own.req_no, tok: own.tok, ok: true }) !== 200) fail.push("patch-owner");
if (raw.prepare("select status, relay_key from requests where req_no=?").get(own.req_no).status !== "client_ok") fail.push("patch-status");
if (await st({ req_no: own.req_no, tok: own.tok, ok: false }) !== 403) fail.push("patch-replay");
raw.prepare("update requests set created_at='2020-01-01T00:00:00Z' where req_no=?").run(r3.req_no);
if (await st({ req_no: r3.req_no, tok: r3.tok, ok: true }) !== 403) fail.push("patch-expired");
if (raw.prepare("select status from requests where req_no=?").get(other.req_no).status !== "received") fail.push("other-untouched");
// monthly slot cannot be used twice by two requests at once
const trio = await Promise.all(["R1", "R2", "R3"].map(x => call(P, "POST", { type: "tender", body: x, email: "q@ex.com" }, "m1x")));
// rate limit per person (10 a day) and per network (20 a day)
IP = "2.2.2.2"; let last;
for (let i = 0; i < 11; i++) last = await mod.onRequestPost(req("POST", { type: "partner", body: "S" + i, email: "spam@ex.com" }));
if (last.status !== 429) fail.push("rate-person");
IP = "3.3.3.3";
for (let i = 0; i < 21; i++) last = await mod.onRequestPost(req("POST", { type: "partner", body: "N" + i, email: "n" + i + "@ex.com" }));
if (last.status !== 429) fail.push("rate-network");
const slot = raw.prepare("select sum(counted) c from requests where user_key='u:user-m1x'").get().c;
if (slot > 2) fail.push("race");
// --- retention, member standing, store switch (owner decision 2026-11-17)
const S = mod.standing, K = (iso) => new Date(Date.parse(iso) - 9 * 3600e3);   // Korea time -> Date
const chk = (name, got, want) => { if (JSON.stringify(got) !== JSON.stringify(want)) fail.push(name + ":" + JSON.stringify(got)); };
const mon = { plan: "monthly", paid_through: "2026-11", status: "active" }, late = { plan: "monthly", paid_through: "2026-10", status: "active" };
chk("paid", S("m1", mon, K("2026-11-20T10:00:00Z")).state, "ok");
chk("due-day1", S("m1", late, K("2026-11-01T23:00:00Z")).state, "ok");
chk("day2-block", [S("m1", late, K("2026-11-02T00:00:00Z")).state, S("m1", late, K("2026-11-02T00:00:00Z")).can_request], ["grace", false]);
chk("day7-last", S("m1", late, K("2026-11-07T23:59:00Z")).grade, "m1");
chk("day8-m0", S("m1", late, K("2026-11-08T00:00:00Z")).grade, "m0");
chk("suspended", S("m3", { plan: "monthly", paid_through: "2026-12", status: "suspended" }, K("2026-11-10T00:00:00Z")).paid, false);
chk("annual-in", S("m2", { plan: "annual", contract_end: "2027-03-31", status: "active" }, K("2026-11-10T00:00:00Z")).state, "ok");
chk("annual-after1", S("m2", { plan: "annual", contract_end: "2026-11-09", status: "active" }, K("2026-11-10T00:00:00Z")).state, "grace");
chk("annual-after7", S("m2", { plan: "annual", contract_end: "2026-11-02", status: "active" }, K("2026-11-09T00:00:00Z")).grade, "m0");
chk("no-row", S("m1", null).state, "no_billing_row");
chk("free", S("m0", null).paid, false);
// grace member: request is taken as a quote, not counted
raw.prepare("insert into members (user_id, plan, paid_through, status) values ('user-m1g','monthly','2000-01','active')").run();
IP = "4.4.4.4";
const g = await call(P, "POST", { type: "tender", body: "G1", email: "g@ex.com" }, "m1g");
if (!(g.quote && !g.counted && g.standing === "lapsed")) fail.push("lapsed-quote:" + JSON.stringify(g));
// retention: closing starts the clock; text blanked after 90 days, record deleted after 1 year; legal hold untouched
raw.prepare("update requests set status='done' where req_no=?").run(r1.req_no);
const c = raw.prepare("select completed_at, purge_body_at, purge_row_at from requests where req_no=?").get(r1.req_no);
if (!c.completed_at || Math.round((Date.parse(c.purge_body_at) - Date.parse(c.completed_at)) / 864e5) !== 90 || Math.round((Date.parse(c.purge_row_at) - Date.parse(c.completed_at)) / 864e5) !== 365) fail.push("clock:" + JSON.stringify(c));
const any = raw.prepare("select purge_body_at, purge_row_at from requests where req_no=?").get(r5.req_no);
if (!any.purge_body_at || !any.purge_row_at) fail.push("safety-clock");
raw.prepare("update requests set purge_body_at='2020-01-01T00:00:00Z' where req_no in (?,?)").run(r1.req_no, r3.req_no);
raw.prepare("update requests set legal_hold=1 where req_no=?").run(r3.req_no);
raw.prepare("update requests set purge_row_at='2020-01-01T00:00:00Z' where req_no=?").run(r5.req_no);
await call(G, "GET", null, "m1");
const a1 = raw.prepare("select body, email, type, status from requests where req_no=?").get(r1.req_no);
if (!(a1 && a1.body === "" && a1.email === "" && a1.type === "tender")) fail.push("purge-body:" + JSON.stringify(a1));
if (raw.prepare("select body from requests where req_no=?").get(r3.req_no).body !== "B") fail.push("legal-hold");
if (raw.prepare("select count(*) n from requests where req_no=?").get(r5.req_no).n !== 0) fail.push("purge-row");
// withdrawal: own rows deleted now except legal hold (blanked)
const del = await (await mod.onRequestDelete(req("DELETE", null, "m1"))).json();
const left = raw.prepare("select req_no, body, legal_hold from requests where user_key='u:user-m1'").all();
if (!(del.ok && left.length === 1 && left[0].legal_hold === 1 && left[0].body === "")) fail.push("withdraw:" + JSON.stringify(left));
// store switch: off -> 503 everywhere; test -> only @example addresses
const offEnv = { GV_DB: D1 }, tEnv = { GV_DB: D1, GV_STORE: "test" };
if ((await mod.onRequestPost({ request: req("POST", { type: "tender", body: "X", email: "a@example.com" }).request, env: offEnv })).status !== 503) fail.push("off");
if ((await mod.onRequestPost({ request: req("POST", { type: "tender", body: "X", email: "real@naver.com" }).request, env: tEnv })).status !== 503) fail.push("test-real");
IP = "9.9.9.9";
if ((await mod.onRequestPost({ request: req("POST", { type: "tender", body: "X", email: "a@example.com" }).request, env: tEnv })).status !== 200) fail.push("test-fake");
// network key: salted per day, not a plain hash; wiped after 48 h; duplicate answers carry no token
const crypto2 = await import("node:crypto");
const row1 = raw.prepare("select ip_hash from requests where ip_hash is not null limit 1").get();
const plain = crypto2.createHash("sha256").update("ip|1.1.1.1").digest("hex");
if (!row1 || row1.ip_hash === plain) fail.push("ip-plain-hash");
raw.prepare("update requests set created_at='2020-01-01T00:00:00Z' where req_no=?").run(r6.req_no);
IP = "5.5.5.5"; await call(P, "POST", { type: "tender", body: "W", email: "w@ex.com" });
if (raw.prepare("select ip_hash from requests where req_no=?").get(r6.req_no).ip_hash !== null) fail.push("ip-wipe-48h");
if (r2.tok) fail.push("dup-has-token");
if (fail.length) { console.error("FAIL", fail.join(",")); process.exit(1); } else console.log("req_server OK");
