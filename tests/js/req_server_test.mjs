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
const env = { GV_DB: D1 };
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
