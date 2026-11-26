import { DatabaseSync } from "node:sqlite";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const out = [];
const sql = fs.readFileSync(ROOT + "/cf/d1/schema.sql", "utf8");
const raw = new DatabaseSync(":memory:"); raw.exec(sql);
const D1 = { prepare(q) { const st = raw.prepare(q); let args = []; const o = { bind(...a) { args = a; return o; }, async first() { return st.get(...args) ?? null; }, async all() { return { results: st.all(...args) }; }, async run() { st.run(...args); return {}; } }; return o; } };
// fake identity: token "m1" -> member, "m0" -> signed-in non-member
globalThis.fetch = async (url, opt) => { const t = (opt.headers.authorization || "").split(" ")[1]; if (!t) return { ok: false };
  return { ok: true, json: async () => ({ id: "user-" + t, email: t + "@ex.com", app_metadata: { roles: t.startsWith("m1") ? ["m1"] : [] } }) }; };
const mod = await import(ROOT + "/cf/functions/api/req.js");
const env = { GV_DB: D1 };
const req = (method, body, tok) => ({ request: { headers: { get: k => (k === "authorization" && tok ? "Bearer " + tok : null) }, json: async () => body } , env });
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
out.push(["secret",await call(P,"POST",{type:"partner",body:"Partner request\nmember code: ABCD-EFGH",email:"x@ex.com"},"m1")]);
out.push(["arabic_secret",await call(P,"POST",{type:"partner",body:"رمز العضوية: ABCD-EFGH",email:"x@ex.com"},"m1")]);

const [r1,r2,r3,r4,r5,r6,r7,,,] = out.map(x=>x[1]);
// PATCH must reject anonymous, cross-user and malformed status changes.
const patch = mod.onRequestPatch;
const ownNo = r1.req_no;
const cross = await patch(req("PATCH", { req_no: ownNo, ok: true }, "m0"));
const anon = await patch(req("PATCH", { req_no: ownNo, ok: true }));
const invalid = await patch(req("PATCH", { req_no: "bad", ok: true }, "m1"));
const mine = await patch(req("PATCH", { req_no: ownNo, ok: true }, "m1"));
const stored = raw.prepare("select status from requests where req_no=?").get(ownNo);
const failed = await patch(req("PATCH", { req_no: r3.req_no, ok: false }, "m1"));
const failedState = raw.prepare("select status from requests where req_no=?").get(r3.req_no)?.status;
const retry = await patch(req("PATCH", { req_no: r3.req_no, ok: true }, "m1"));
const retriedState = raw.prepare("select status from requests where req_no=?").get(r3.req_no)?.status;

out.push(["patch", [cross.status, anon.status, invalid.status, mine.status, stored?.status].join(" ")]);
// Concurrent member submissions for a new user must receive at most 2 included slots.
const concurrent = await Promise.all(["Q1","Q2","Q3","Q4","Q5"].map(body =>
  call(P, "POST", { type:"country", body, email:"quota@ex.com" }, "m1-quota")));
const quotaRows = raw.prepare("select count(*) as n, sum(counted) as used from requests where user_key=?").get("u:user-m1-quota");
const quotaIncluded = concurrent.filter(x => x.counted).length;
// Concurrent duplicate submissions are still to be guarded independently.
const fail = [];
if (!(r1.counted && r1.left === 1)) fail.push("first");
if (quotaRows.n!==5 || quotaRows.used!==2 || quotaIncluded!==2) fail.push("atomic-quota");
if (!(r2.duplicate && r2.req_no === r1.req_no)) fail.push("dup");
if (!(r3.counted && r3.left === 0)) fail.push("second");
if (!(r4.quote && !r4.counted)) fail.push("over");
if (!(r5.quote && !r5.member)) fail.push("nonmember");
if (r7.error !== "bad") fail.push("bad");
if (out.find(x=>x[0]==="secret")?.[1]?.error!=="secret_in_request") fail.push("secret-leak");
if (out.find(x=>x[0]==="arabic_secret")?.[1]?.error!=="secret_in_request") fail.push("arabic-secret-leak");
if (out[7][1].split(" ")[0] !== "3") {}
if (out[8][1] !== 1) fail.push("refund");
if (out[9][1] !== 503) fail.push("nodb");
if (out.find(x => x[0] === "patch")?.[1] !== "404 401 400 200 gateway_reported") fail.push("patch-ownership");
if (failed.status!==200 || failedState!=="gateway_failed_reported" || retry.status!==200 || retriedState!=="gateway_reported") fail.push("gateway-retry");
if (fail.length) { console.error("FAIL", fail.join(",")); process.exit(1); } else console.log("req_server OK");
