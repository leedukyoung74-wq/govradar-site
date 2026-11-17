// Browser test of the request page: only an explicit 503 not_configured may fall back to the Netlify form.
// 429 / 400 / 500 / network error -> nothing is posted anywhere. Run: node tests/js/req_page_fallback.mjs
import { createRequire } from "node:module"; const { chromium } = createRequire(import.meta.url)("playwright");
import { execFileSync } from "node:child_process";
import path from "node:path"; import { fileURLToPath } from "node:url";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const html = execFileSync("python3", ["-c", `import sys;sys.path.insert(0,'.');import pages_req as P;print(P.request_page('ko',lambda *a,**k:'<!doctype html><html lang=ko><body>',lambda L:'</body></html>',['ko','en']))`], { cwd: ROOT }).toString();
const b = await chromium.launch(), fail = [];
for (const [name, api, wantForm] of [["429", { status: 429, body: '{"error":"too_many"}' }, 0], ["400", { status: 400, body: '{"error":"bad"}' }, 0],
  ["500", { status: 500, body: "oops" }, 0], ["network", null, 0], ["503-other", { status: 503, body: '{"error":"busy"}' }, 0],
  ["503-not_configured", { status: 503, body: '{"error":"not_configured"}' }, 1], ["200", { status: 200, body: '{"req_no":"RQ-261117-ABCDEF12","tok":"' + "a".repeat(32) + '","member":false,"counted":false}' }, 1]]) {
  const p = await b.newPage(); let form = 0, patch = 0;
  await p.route("http://t.test/ko/request/", r => r.fulfill({ contentType: "text/html", body: html }));
  await p.route("**/api/req", r => { const m = r.request().method(); if (m === "PATCH") { patch++; return r.fulfill({ status: 200, body: "{}" }); }
    if (m === "GET") return r.fulfill({ status: 503, body: '{"error":"not_configured"}' });
    return api ? r.fulfill({ status: api.status, contentType: "application/json", body: api.body }) : r.abort(); });
  await p.route("**/ko/thanks/**", r => { form++; r.fulfill({ status: 200, contentType: "text/html", body: "ok" }); });
  await p.goto("http://t.test/ko/request/");
  const ok = await p.evaluate(() => { const f = document.querySelector("form.rq-form"); if (!f) return "noform";
    const pick = f.querySelector("input[type=radio]"); if (pick) { pick.checked = true; pick.dispatchEvent(new Event("change", { bubbles: true })); }
    for (const el of f.querySelectorAll("input,textarea,select")) { if (el.type === "radio" || el.type === "hidden" || el.name === "hp") continue;
      if (el.type === "checkbox") { el.checked = true; continue; } if (el.type === "email" || el.name === "email") el.value = "t@example.com"; else if (el.tagName === "SELECT") { if (el.options.length > 1) el.selectedIndex = 1; } else if (!el.value) el.value = "test"; }
    return "ok"; });
  if (ok !== "ok") { fail.push(name + ":" + ok); continue; }
  await p.evaluate(() => document.querySelector("form.rq-form button[type=submit],form.rq-form button").click());
  await p.waitForTimeout(1500);
  const msg = await p.evaluate(() => (document.querySelector(".rq-msg,[role=status],.note.rq") || {}).textContent || "");
  if ((form > 0 ? 1 : 0) !== wantForm) fail.push(`${name}: form posts=${form}`);
  console.log(name, "form posts", form, "patch", patch);
  await p.close();
}
await b.close();
if (fail.length) { console.error("FAIL", fail.join(" | ")); process.exit(1); } else console.log("req_page_fallback OK");
