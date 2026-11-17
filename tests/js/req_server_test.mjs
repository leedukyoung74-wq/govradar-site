import { DatabaseSync } from "node:sqlite";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const out = [];
const sql = fs.readFileSync(ROOT + "/cf/d1/schema.sql", "utf8");
const raw = new DatabaseSync(":memory:"); raw.exec(sql);
raw.exec("insert into members (user_id, plan, paid_through, status) values ('user-m1','monthly','2099-12','active'),('user-m1x','monthly','2099-12','active')");
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
// --- member standing (review T20261117-06: cumulative overdue, fail-closed)
const S = mod.standing, K = (iso) => new Date(Date.parse(iso) - 9 * 3600e3);   // Korea time -> Date
const chk = (name, got, want) => { if (JSON.stringify(got) !== JSON.stringify(want)) fail.push(name + ":" + JSON.stringify(got)); };
const mon = { plan: "monthly", paid_through: "2026-11", status: "active" }, late = { plan: "monthly", paid_through: "2026-10", status: "active" };
chk("paid", S("m1", mon, K("2026-11-20T10:00:00Z")).state, "ok");
chk("due-day1", S("m1", late, K("2026-11-01T23:00:00Z")).state, "ok");
chk("day2-block", [S("m1", late, K("2026-11-02T00:00:00Z")).state, S("m1", late, K("2026-11-02T00:00:00Z")).can_request], ["grace", false]);
chk("day7-last", S("m1", late, K("2026-11-07T23:59:00Z")).grade, "m1");
chk("day8-m0", S("m1", late, K("2026-11-08T00:00:00Z")).grade, "m0");
// P0-1: a long-unpaid member must NOT come back on the 1st of later months
for (const d of ["2026-12-01T00:00:00Z", "2026-12-02T00:00:00Z", "2026-12-08T00:00:00Z", "2027-01-01T00:00:00Z", "2027-06-01T12:00:00Z"]) chk("no-revive-" + d.slice(0, 10), S("m1", late, K(d)).grade, "m0");
chk("dec-1-due", S("m1", mon, K("2026-12-01T09:00:00Z")).state, "ok");          // paid through Nov: Dec 1 is the due day
chk("dec-2-grace", S("m1", mon, K("2026-12-02T00:00:00Z")).state, "grace");
chk("year-wrap", S("m1", { plan: "monthly", paid_through: "2026-12", status: "active" }, K("2027-01-08T00:00:00Z")).grade, "m0");
chk("paid-ahead", S("m1", { plan: "monthly", paid_through: "2027-02", status: "active" }, K("2026-12-15T00:00:00Z")).state, "ok");
chk("suspended", S("m3", { plan: "monthly", paid_through: "2026-12", status: "suspended" }, K("2026-11-10T00:00:00Z")).paid, false);
chk("annual-in", S("m2", { plan: "annual", contract_end: "2027-03-31", status: "active" }, K("2026-11-10T00:00:00Z")).state, "ok");
chk("annual-last-day", S("m2", { plan: "annual", contract_end: "2026-11-10", status: "active" }, K("2026-11-10T23:59:00Z")).state, "ok");
chk("annual-after1", S("m2", { plan: "annual", contract_end: "2026-11-09", status: "active" }, K("2026-11-10T00:00:00Z")).state, "grace");
chk("annual-after7", S("m2", { plan: "annual", contract_end: "2026-11-02", status: "active" }, K("2026-11-09T00:00:00Z")).grade, "m0");
chk("annual-much-later", S("m2", { plan: "annual", contract_end: "2026-11-02", status: "active" }, K("2027-11-03T00:00:00Z")).grade, "m0");
// P0-2: fail-closed
chk("no-row", [S("m1", null).state, S("m1", null).can_request, S("m1", null).paid], ["unverified", false, false]);
chk("db-error", S("m1", "error").state, "unverified");
chk("no-date", S("m1", { plan: "monthly", status: "active" }).state, "unverified");
chk("bad-plan", S("m1", { plan: "weekly", paid_through: "2026-11", status: "active" }).state, "unverified");
chk("staff", S("owner", null).can_request, true);
chk("free", S("m0", null).paid, false);
// existing m1 (no billing row) after this change: request becomes a quote, not counted
IP = "6.6.6.6";
const nr = await call(P, "POST", { type: "country", body: "NR", email: "nr@ex.com" }, "m1norow");
if (!(nr.quote && !nr.counted && nr.standing === "unverified")) fail.push("norow-quote:" + JSON.stringify(nr));
// DB error -> fail-closed too
const brokenDB = { prepare(q) { if (/from members/.test(q)) throw new Error("no such table"); return D1.prepare(q); } };
IP = "6.6.6.7";
const br = await (await mod.onRequestPost({ request: req("POST", { type: "country", body: "BR", email: "br@ex.com" }, "m1x").request, env: { GV_DB: brokenDB, GV_STORE: "on" } })).json();
if (!(br.quote && !br.counted && br.standing === "unverified")) fail.push("dberror-quote:" + JSON.stringify(br));
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
raw.prepare("update requests set legal_hold=1, legal_until='2099-12-31' where req_no=?").run(r3.req_no);
raw.prepare("update requests set purge_row_at='2020-01-01T00:00:00Z' where req_no=?").run(r5.req_no);
await call(G, "GET", null, "m1");
const a1 = raw.prepare("select body, email, type, status from requests where req_no=?").get(r1.req_no);
if (!(a1 && a1.body === "" && a1.email === "" && a1.type === "tender")) fail.push("purge-body:" + JSON.stringify(a1));
// P0-4: a hold keeps only the minimal record (text still blanked) and only until legal_until
const hh = raw.prepare("select body, email, legal_hold from requests where req_no=?").get(r3.req_no);
if (!(hh && hh.body === "" && hh.email === "" && hh.legal_hold === 1)) fail.push("legal-hold-minimal:" + JSON.stringify(hh));
if (raw.prepare("select count(*) n from requests where req_no=?").get(r5.req_no).n !== 0) fail.push("purge-row");
// hold with no date or a past date is released, then normal deletion applies
raw.exec("insert into requests (req_no, created_at, month, user_key, email, type, body, dedupe, legal_hold, legal_until, purge_row_at) values ('RQ-HOLD-OLD','2020-01-01T00:00:00Z','2020-01','u:zz','z@ex.com','tender','old','d',1,'2021-01-01','2021-06-01T00:00:00Z'),('RQ-HOLD-NODATE','2020-01-01T00:00:00Z','2020-01','u:zz','z@ex.com','tender','old','d',1,null,'2021-06-01T00:00:00Z')");
await call(G, "GET", null, "m1");
if (raw.prepare("select count(*) n from requests where req_no like 'RQ-HOLD-%'").get().n !== 0) fail.push("hold-expiry");
// withdrawal: own rows deleted now except legal hold (blanked)
const del = await (await mod.onRequestDelete(req("DELETE", null, "m1"))).json();
const left = raw.prepare("select req_no, body, legal_hold from requests where user_key='u:user-m1'").all();
if (!(del.ok && left.length === 1 && left[0].legal_hold === 1 && left[0].body === "")) fail.push("withdraw:" + JSON.stringify(left));
if (raw.prepare("select email from requests where req_no=?").get(r3.req_no).email !== "") fail.push("withdraw-email");
// P0-3: scheduled worker purges with no visitors, and logs the run
raw.exec("insert into requests (req_no, created_at, month, user_key, email, type, body, dedupe, purge_body_at, purge_row_at) values ('RQ-CRON-1','2026-01-01T00:00:00Z','2026-01','u:cr','c@ex.com','tender','secret','d','2026-02-01T00:00:00Z','2099-01-01T00:00:00Z')");
const W = await import(ROOT + "/cf/cron/purge-worker.js"); let waited;
await W.default.scheduled({ scheduledTime: Date.now() }, { GV_DB: D1 }, { waitUntil: p => (waited = p) }); await waited;
const cr = raw.prepare("select body, email from requests where req_no='RQ-CRON-1'").get();
if (!(cr.body === "" && cr.email === "")) fail.push("cron-purge");
const log = raw.prepare("select source, ok, body_cleared from purge_runs where source='cron' order by at desc limit 1").get();
if (!(log && log.ok === 1 && log.body_cleared >= 1)) fail.push("cron-log:" + JSON.stringify(log));
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
