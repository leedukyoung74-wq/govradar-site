// Browser test of the request page (Playwright).
// 1) only an explicit 503 not_configured may fall back to the Netlify form; 429/400/500/network/503 busy/test_only send nothing
// 2) once the server has saved the request, an alert (Netlify) or PATCH failure never erases it or says "nothing was sent",
//    and never shows "staff notified". Run: node tests/js/req_page_fallback.mjs
import { createRequire } from "node:module"; const { chromium } = createRequire(import.meta.url)("playwright");
import { execFileSync } from "node:child_process";
import path from "node:path"; import { fileURLToPath } from "node:url";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const html = execFileSync("python3", ["-c", `import sys;sys.path.insert(0,'.');import pages_req as P;print(P.request_page('ko',lambda *a,**k:'<!doctype html><html lang=ko><body>',lambda L:'</body></html>',['ko','en']))`], { cwd: ROOT }).toString();
const OK = { status: 200, body: '{"req_no":"RQ-261117-ABCDEF12","tok":"' + "a".repeat(32) + '","member":false,"counted":false}' };
const CASES = [ // name, api answer, netlify behaviour, patch behaviour, expected {form posts, saved locally, message must include, must not include}
  ["429", { status: 429, body: '{"error":"too_many"}' }, "ok", "ok", { form: 0, kept: false, has: "아무것도 전송되지 않았습니다" }],
  ["400", { status: 400, body: '{"error":"bad"}' }, "ok", "ok", { form: 0, kept: false }],
  ["500", { status: 500, body: "oops" }, "ok", "ok", { form: 0, kept: false }],
  ["network", null, "ok", "ok", { form: 0, kept: false }],
  ["503-busy", { status: 503, body: '{"error":"busy"}' }, "ok", "ok", { form: 0, kept: false }],
  ["test_only", { status: 503, body: '{"error":"test_only"}' }, "ok", "ok", { form: 0, kept: false, has: "비공개 시험" }],
  ["503-not_configured", { status: 503, body: '{"error":"not_configured"}' }, "ok", "ok", { form: 1 }],
  ["200-alert-ok", OK, "ok", "ok", { form: 1, kept: true, has: "알림 보냄", patch: 1 }],
  ["200-alert-500", OK, "500", "ok", { form: 1, kept: true, has: "알림 전송 실패", not: ["아무것도 전송되지", "알림 보냄"], patch: 1 }],
  ["200-alert-network", OK, "abort", "ok", { form: 1, kept: true, has: "알림 전송 실패", not: ["아무것도 전송되지", "알림 보냄"], patch: 1 }],
  ["200-patch-fails", OK, "ok", "abort", { form: 1, kept: true, has: "알림 보냄", not: ["아무것도 전송되지"] }],
];
const b = await chromium.launch(), fail = [];
for (const [name, api, nf, pt, want] of CASES) {
  const p = await b.newPage(); let form = 0, patch = 0;
  await p.route("http://t.test/ko/request/", r => r.fulfill({ contentType: "text/html; charset=utf-8", body: html }));
  await p.route("**/api/req", r => { const m = r.request().method();
    if (m === "PATCH") { patch++; return pt === "abort" ? r.abort() : r.fulfill({ status: 200, body: "{}" }); }
    if (m === "GET") return r.fulfill({ status: 503, body: '{"error":"not_configured"}' });
    return api ? r.fulfill({ status: api.status, contentType: "application/json", body: api.body }) : r.abort(); });
  await p.route("**/ko/thanks/**", r => { form++; return nf === "abort" ? r.abort() : nf === "500" ? r.fulfill({ status: 500, body: "x" }) : r.fulfill({ status: 200, contentType: "text/html", body: "ok" }); });
  await p.goto("http://t.test/ko/request/");
  const ok = await p.evaluate(() => { const f = document.querySelector("form.rq-form"); if (!f) return "noform";
    const pick = f.querySelector("input[type=radio]"); if (pick) { pick.checked = true; pick.dispatchEvent(new Event("change", { bubbles: true })); }
    for (const el of f.querySelectorAll("input,textarea,select")) { if (el.type === "radio" || el.type === "hidden" || el.name === "hp") continue;
      if (el.type === "checkbox") { el.checked = true; continue; } if (el.type === "email" || el.name === "email") el.value = "t@example.com"; else if (el.tagName === "SELECT") { if (el.options.length > 1) el.selectedIndex = 1; } else if (!el.value) el.value = "test"; }
    return "ok"; });
  if (ok !== "ok") { fail.push(name + ":" + ok); continue; }
  await p.evaluate(() => document.querySelector("form.rq-form button[type=submit],form.rq-form button").click());
  await p.waitForTimeout(1500);
  const st = await p.evaluate(() => { let a = []; try { a = JSON.parse(localStorage.getItem("gv_rq") || "[]") } catch (e) {}
    const m = [...document.querySelectorAll(".rq-msg")].map(e => e.textContent).join(" | ");
    return { kept: a.some(x => x.id === "RQ-261117-ABCDEF12"), n: a.length, msg: m }; });
  const errs = [];
  if ((form > 0 ? 1 : 0) !== want.form) errs.push("form posts=" + form);
  if (want.kept !== undefined && (want.kept ? !st.kept : st.n > 0)) errs.push("kept=" + st.kept + " n=" + st.n);
  if (want.has && !st.msg.includes(want.has)) errs.push("missing '" + want.has + "'");
  for (const x of want.not || []) if (st.msg.includes(x)) errs.push("shows '" + x + "'");
  if (want.patch !== undefined && patch !== want.patch) errs.push("patch=" + patch);
  console.log(name.padEnd(20), "form", form, "patch", patch, "kept", st.kept, errs.length ? "FAIL " + errs.join("; ") : "ok");
  if (errs.length) fail.push(name + ": " + errs.join("; "));
  await p.close();
}
await b.close();
if (fail.length) { console.error("FAIL", fail.join(" | ")); process.exit(1); } else console.log("req_page_fallback OK");
