/* GOV RADAR public site: map, search, member actions (sign-in lives in auth.js).
   Visitors can read everything; saving and the AI analyst need a free account. */
(function () {
  const L = window.RADAR_LANG || "en", T = window.RADAR_T || {}, CFG = window.RADAR_CONFIG || {};
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

  /* ---------- country grid filter ---------- */
  let region = "ALL";
  function filter() {
    const q = ($("#q") && $("#q").value || "").trim().toLowerCase();
    $$("#grid .flag").forEach(a => { a.hidden = !((region === "ALL" || a.dataset.r === region) && (!q || a.dataset.n.includes(q))); });
  }
  $$(".filters .chip").forEach(b => b.addEventListener("click", () => { region = b.dataset.r; $$(".filters .chip").forEach(x => x.classList.toggle("on", x === b)); filter(); }));
  if ($("#q")) $("#q").addEventListener("input", filter);

  /* ---------- mobile menu ---------- */
  const bg = $("#burger"), nl = $("#navlinks");
  if (bg && nl) { bg.addEventListener("click", () => { const o = nl.classList.toggle("open"); bg.setAttribute("aria-expanded", o); }); nl.addEventListener("click", e => { if (e.target.closest("a")) { nl.classList.remove("open"); bg.setAttribute("aria-expanded", false); } }); }

  /* ---------- map ---------- */
  function initMap() {
    const el = $("#wmap"); if (!el || typeof jsVectorMap === "undefined") return;
    fetch("/data/countries.json").then(r => r.json()).then(cs => {
      const by = Object.fromEntries(cs.map(c => [c.iso, c])), vals = {};
      cs.forEach(c => vals[c.iso] = c.risk === "high" ? "high" : c.done ? "y" : "n");
      new jsVectorMap({
        selector: "#wmap", map: "world", zoomButtons: true, zoomOnScroll: false, backgroundColor: "transparent",
        regionStyle: { initial: { fill: css("--m-land"), stroke: css("--m-sea"), strokeWidth: .4 }, hover: { fill: css("--m-hover") } },
        series: { regions: [{ attribute: "fill", scale: { y: css("--m-done"), n: css("--m-land"), high: css("--m-high") }, values: vals }] },
        onRegionTooltipShow(e, tip, code) { const c = by[code]; if (c) tip.text(c.names[L] || c.names.en); },
        onRegionClick(e, code) { const c = by[code]; if (c) location.href = `/${L}/${c.slug}/`; }
      });
    }).catch(() => {});
  }
  if (document.readyState === "complete") initMap(); else window.addEventListener("load", initMap);

  /* ---------- member actions (Netlify Identity via auth.js) ---------- */
  const A = () => window.WMMAuth;
  document.addEventListener("click", async e => {
    const b = e.target.closest("[data-act]"); if (!b) return;
    const act = b.dataset.act, au = A();
    if (act === "join") { au && au.open(au.session ? "login" : "signup"); return; }
    if (!au || !au.session) { alert1(T.members_only); au && au.open("signup"); return; }
    const md = (au.user().user_metadata) || {};
    if (act === "watch") {
      const w = (md.watch || []).filter(x => !(x.iso === b.dataset.iso && x.title === b.dataset.title));
      w.unshift({ iso: b.dataset.iso, title: b.dataset.title, deadline: b.dataset.deadline || null, at: new Date().toISOString().slice(0, 10) });
      try { await au.update({ data: { watch: w.slice(0, 100) } }); b.textContent = "✓"; } catch (err) { b.textContent = "!"; }
    } else if (act === "follow") {
      const f = new Set(md.follows || []); f.add(b.dataset.iso);
      try { await au.update({ data: { follows: [...f].slice(0, 60) } }); b.textContent = "✓"; } catch (err) { b.textContent = "!"; }
    } else if (act === "ask") {
      const q = ($("#askq").value || "").trim(); if (!q) return; const out = $("#askout"); out.textContent = "…"; b.disabled = true;
      try {
        const r = await fetch(CFG.askEndpoint || "/api/ask", { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + (await au.token()) }, body: JSON.stringify({ iso: b.dataset.iso, q, lang: L }) });
        if (!r.ok) throw 0; const j = await r.json(); out.textContent = j.answer || j.error || "—";
      } catch (err) { out.textContent = T.ask_soon || "—"; } finally { b.disabled = false; }
    }
  });
  function alert1(msg) { if (!msg) return; const n = document.createElement("div"); n.className = "note"; n.style.cssText = "position:fixed;left:50%;bottom:20px;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:10px 16px;border-radius:8px;z-index:60"; n.textContent = msg; document.body.appendChild(n); setTimeout(() => n.remove(), 2600); }
})();

/* ---------- prep bar ---------- */
(function () {
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  let cur = null;
  function show(id) {
    cur = cur === id ? null : id;
    $$(".pchips button").forEach(b => b.classList.toggle("on", b.dataset.pp === cur));
    $$(".pp").forEach(p => p.hidden = p.dataset.pp !== cur);
    const pn = $("#preppanel"); if (pn) pn.hidden = !cur;
  }
  $$(".pchips button").forEach(b => b.addEventListener("click", () => show(b.dataset.pp)));
  const x = $("#pp-x"); if (x) x.addEventListener("click", () => { cur = null; show(null); });
})();

/* ---------- Earth & space (live where the source allows browser access) ---------- */
(function () {
  const $ = s => document.querySelector(s);
  const g = $("#earthg"), lh = $("#localhaz"); if (!g && !lh) return;
  const none = g ? g.dataset.none : "—", LD = g ? g.dataset.ld : "LD", KP = g ? g.dataset.kp : "Kp";
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
  const card = k => g && g.querySelector(`.ecard[data-k="${k}"] .eb`);
  const list = (k, arr, f) => { const c = card(k); if (!c) return; c.innerHTML = arr && arr.length ? "<ul>" + arr.slice(0, 8).map(f).join("") + "</ul>" : `<p class="note">${esc(none)}</p>`; };
  const L = window.RADAR_LANG || "en", isKo = L === "ko";
  const item = x => `<li>${x.iso ? `<span class="fi fi-${String(x.iso).toLowerCase()}"></span> ` : ""}${esc(x.text || x.name || "")}${x.date ? ` <span class="note">${esc(x.date)}</span>` : ""}${/^https:\/\//.test(x.url || "") ? ` <a href="${esc(x.url)}" target="_blank" rel="noopener">↗</a>` : ""}</li>`;
  let HZ = {};
  fetch("/data/hazards.json").then(r => r.json()).then(h => {
    HZ = !isKo && h.en ? { ...h, ...h.en } : h || {};
    if (h.checked && $("#eh-at")) $("#eh-at").textContent = "· " + h.checked.replace("T", " ");
    ["tsunami", "volcano", "storm", "weather", "fire", "epidemic"].forEach(k => list(k, HZ[k], item));
    if (!window.__liveQuake) list("quake", HZ.quake, q => `<li><b>M${esc(q.mag)}</b> ${esc(q.place || "")} <span class="note">${esc(q.date || "")}</span></li>`);
    if (!window.__liveSpace) space(HZ.space || {});
    if (!window.__liveNeo) list("asteroid", HZ.asteroid, a => `<li><b>${esc(a.name)}</b> · ${esc(a.date || "")} · ${esc(a.ld)} ${esc(LD)}${a.size ? " · " + esc(a.size) : ""}</li>`);
    tick(); local();
  }).catch(() => {});
  function space(sp) {
    const c = card("space"); if (!c) return;
    const sc = (k, v) => `<span class="${v && String(v).slice(1) !== "0" ? "on" : ""}">${k}${esc(String(v || "0").replace(/^[RSG]/, ""))}</span>`;
    c.innerHTML = `<div class="scale">${sc("R", sp.r)}${sc("S", sp.s)}${sc("G", sp.g)}</div>${sp.kp != null ? `<p>${esc(KP)} <b>${esc(sp.kp)}</b></p>` : ""}${sp.text ? `<p class="note">${esc(sp.text)}</p>` : ""}`;
  }
  // USGS live earthquakes (M4.5+, past 7 days)
  fetch("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson").then(r => r.json()).then(j => {
    window.__liveQuake = true;
    const q = j.features.sort((a, b) => b.properties.mag - a.properties.mag).slice(0, 8);
    list("quake", q, f => { const p = f.properties, d = new Date(p.time); return `<li><b>M${p.mag.toFixed(1)}</b> ${esc(p.place || "")} <span class="note">${d.toISOString().slice(5, 10)}</span>${p.tsunami ? " 🌊" : ""} <a href="${esc(p.url)}" target="_blank" rel="noopener">↗</a></li>`; });
    tick(q);
  }).catch(() => {});
  // NOAA SWPC scales + Kp
  Promise.all([fetch("https://services.swpc.noaa.gov/products/noaa-scales.json").then(r => r.json()), fetch("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json").then(r => r.json()).catch(() => null)]).then(([sc, kp]) => {
    window.__liveSpace = true; const n = sc["0"] || {};
    space({ r: "R" + (n.R && n.R.Scale || 0), s: "S" + (n.S && n.S.Scale || 0), g: "G" + (n.G && n.G.Scale || 0), kp: kp && kp.length > 1 ? kp[kp.length - 1][1] : null });
  }).catch(() => {});
  // NASA JPL close approaches (next 60 days, within 0.05 au)
  fetch("https://ssd-api.jpl.nasa.gov/cad.api?dist-max=0.05&date-min=now&date-max=%2B60&sort=dist").then(r => r.json()).then(j => {
    window.__liveNeo = true; const f = j.fields, idx = k => f.indexOf(k);
    list("asteroid", j.data.slice(0, 6), r => `<li><b>${esc(r[idx("des")])}</b> · ${esc(String(r[idx("cd")]).slice(0, 11))} · ${(parseFloat(r[idx("dist")]) / 0.00257).toFixed(1)} ${esc(LD)} · H ${esc(r[idx("h")])}</li>`);
  }).catch(() => {});
  function tick(q) {
    const t = $("#htick"); if (!t) return; const p = [];
    (q || []).slice(0, 2).forEach(f => p.push("M" + f.properties.mag.toFixed(1) + " " + (f.properties.place || "")));
    if (!q) (HZ.quake || []).slice(0, 2).forEach(x => p.push("M" + x.mag + " " + (x.place || "")));
    if (HZ.space && HZ.space.g && HZ.space.g !== "G0") p.push(HZ.space.g);
    (HZ.storm || []).slice(0, 1).forEach(x => p.push(x.text || ""));
    if (p.length) t.textContent = p.join(" · ");
  }
  function local() {
    if (!lh) return; const iso = lh.dataset.iso, out = [];
    ["quake", "tsunami", "volcano", "storm", "weather", "fire", "epidemic"].forEach(k => (HZ[k] || []).forEach(x => { if (x && x.iso === iso) out.push(k === "quake" ? `<li><b>M${esc(x.mag)}</b> ${esc(x.place || "")} <span class="note">${esc(x.date || "")}</span></li>` : item(x)); }));
    if (out.length) { lh.querySelector("ul").innerHTML = out.join(""); lh.hidden = false; }
  }
})();

/* ---------- account page (profile stored on the member's own Identity record) ---------- */
(function () {
  const f = document.getElementById("acct"); if (!f) return;
  const st = document.getElementById("acct-st"), msg = document.getElementById("acct-msg"), tierEl = document.getElementById("acct-tier");
  function paint() {
    const au = window.WMMAuth; if (!au) return;
    if (!au.session) { f.hidden = true; document.getElementById("acct-out").hidden = false; document.getElementById("acct-in").hidden = true; return; }
    document.getElementById("acct-out").hidden = true; document.getElementById("acct-in").hidden = false;
    const u = au.user(), p = u.user_metadata || {}; st.textContent = u.email; f.hidden = false;
    if (tierEl) tierEl.textContent = (window.RADAR_AT && window.RADAR_AT.tiers && window.RADAR_AT.tiers[au.tier()]) || au.tier();
    for (const el of f.elements) { if (!el.name) continue; if (el.name === "ind") el.checked = (p.industries || []).includes(el.value); else if (el.type === "checkbox") el.checked = !!p[el.name]; else if (el.name === "certs") el.value = (p.certs || []).join(", "); else if (p[el.name] != null) el.value = p[el.name]; }
    const wl = document.getElementById("acct-watch"); if (wl) wl.innerHTML = (p.watch || []).map(w => `<li>${String(w.title).replace(/[<>&]/g, "")} <span class="note">${w.iso} ${w.deadline || ""}</span></li>`).join("") || "<li class=note>—</li>";
  }
  document.addEventListener("DOMContentLoaded", () => { paint(); window.WMMAuth && window.WMMAuth.onChange(paint); });
  const lo = document.getElementById("acct-logout"); if (lo) lo.addEventListener("click", () => { window.WMMAuth.logout(); location.href = "/" + (window.RADAR_LANG || "en") + "/"; });
  f.addEventListener("submit", async e => {
    e.preventDefault(); const v = n => f.elements[n];
    const data = { company: v("company").value.trim(), industries: [...f.querySelectorAll('input[name=ind]:checked')].map(x => x.value),
      revenue_100m: +v("revenue_100m").value || null, years: +v("years").value || null, projects: +v("projects").value || null, employees: +v("employees").value || null,
      certs: v("certs").value.split(/[,，]/).map(x => x.trim()).filter(Boolean), alert_email: v("alert_email") ? v("alert_email").checked : true,
      marketing_consent: v("marketing_consent").checked, consent_at: v("marketing_consent").checked ? new Date().toISOString() : null, updated_at: new Date().toISOString() };
    try { await window.WMMAuth.update({ data }); msg.textContent = "✓"; } catch (err) { msg.textContent = err.message; }
  });
})();

/* Language switch: stay on the same page in the new language (fall back to that language's page from the menu). */
window.gvLang = function (sel) {
  var o = sel.options[sel.selectedIndex], l = o.getAttribute("data-l"), fb = o.value;
  var path = location.pathname, m = path.match(/^\/([a-z]{2})(\/.*)?$/);
  if (!l || !m) { location.href = fb; return; }
  var target = "/" + l + (m[2] || "/") + location.search + location.hash;
  fetch("/" + l + (m[2] || "/"), { method: "HEAD" }).then(function (r) {
    location.href = r.ok ? target : fb;
  }).catch(function () { location.href = target; });
};

/* ---- Analysis-member access: decrypt member-only analysis in the browser (keys and files on the GitHub data branch) ---- */
(function () {
  var BASE = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/m/";
  var L = (location.pathname.match(/^\/([a-z]{2})\//) || [, "en"])[1], ko = L === "ko";
  function ls(k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { return null; } }
  function ss(k, v) { try { if (v === undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k, v); } catch (e) { return null; } }
  var b64d = function (s) { return Uint8Array.from(atob(s), function (c) { return c.charCodeAt(0); }); };
  var b64e = function (b) { return btoa(String.fromCharCode.apply(null, new Uint8Array(b))); };
  function norm(c) { return (c || "").toUpperCase().replace(/[^0-9A-F]/g, "").replace(/(.{4})(?=.)/g, "$1-"); }
  async function sha(t) { var h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t)); return Array.from(new Uint8Array(h)).map(function (x) { return x.toString(16).padStart(2, "0"); }).join(""); }
  async function getK(code) {
    var cached = ss("gv_k");
    if (cached) return crypto.subtle.importKey("raw", b64d(cached), "AES-GCM", false, ["decrypt"]);
    var kj = await fetch(BASE + "keys.json", { cache: "no-store" }).then(function (r) { if (!r.ok) throw 0; return r.json(); });
    var ent = kj.keys[(await sha("govradar:" + code)).slice(0, 20)];
    if (!ent) throw new Error("nokey");
    if (ent.exp < new Date().toISOString().slice(0, 10)) throw new Error("expired");
    var base = await crypto.subtle.importKey("raw", new TextEncoder().encode(code), "PBKDF2", false, ["deriveKey"]);
    var kek = await crypto.subtle.deriveKey({ name: "PBKDF2", salt: b64d(ent.s), iterations: kj.iter || 150000, hash: "SHA-256" }, base, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
    var raw = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64d(ent.iv) }, kek, b64d(ent.w));
    ss("gv_k", b64e(raw)); ls("gv_exp", ent.exp);
    return crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["decrypt"]);
  }
  async function dec(K, path) {
    var j = await fetch(BASE + path).then(function (r) { if (!r.ok) throw 0; return r.json(); });
    var pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64d(j.iv) }, K, b64d(j.c));
    return JSON.parse(new TextDecoder().decode(pt));
  }
  function esc(s) { var d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }
  async function unlockCountry(K) {
    var cards = document.querySelectorAll("a.card.locked[data-mi]");
    if (!cards.length) return;
    var data = await dec(K, L + "/" + cards[0].getAttribute("data-iso") + ".json");
    cards.forEach(function (a) {
      var b = data.biz[+a.getAttribute("data-mi")]; if (!b) return;
      var div = document.createElement("div"); div.className = "card";
      div.innerHTML = '<p class="note">' + (ko ? "분석 회원" : "Member") + "</p><h3>" + esc(b.title) + "</h3>" + (b.why ? "<p>" + esc(b.why) + "</p>" : "") + (b.target ? '<p class="note">' + esc(b.target) + "</p>" : "") + (b.basis ? '<p class="note">' + esc(b.basis) + "</p>" : "");
      a.replaceWith(div);
    });
    document.querySelectorAll(".lockbox").forEach(function (x) { x.innerHTML = "<b>" + (ko ? "분석 회원으로 모든 분석을 보고 있습니다" : "You are viewing all analysis as a member") + "</b>"; });
  }
  async function run() {
    var page = /\/member\/$/.test(location.pathname), st = document.getElementById("mstate");
    var code = norm(page && location.hash.length > 5 ? decodeURIComponent(location.hash.slice(1)) : ls("gv_code"));
    function say(t) { if (st) st.textContent = t; }
    if (page) {
      var inp = document.getElementById("mcode");
      document.getElementById("mgo").onclick = function () { ss("gv_k", ""); try { sessionStorage.removeItem("gv_k"); } catch (e) {} ls("gv_code", norm(inp.value)); location.hash = ""; run(); };
      document.getElementById("mout").onclick = function () { ls("gv_code", null); ls("gv_exp", null); try { sessionStorage.removeItem("gv_k"); } catch (e) {} say(ko ? "이 브라우저에서 해제했습니다." : "Signed out on this browser."); };
      if (code && inp) inp.value = code;
    }
    if (!code) { if (page) say(ko ? "열람 코드를 넣어 주세요." : "Enter your access code."); return; }
    try {
      var K = await getK(code); ls("gv_code", code);
      if (page) { history.replaceState(null, "", location.pathname); say((ko ? "열람이 켜졌습니다. 이용 기간: " : "Access is on. Valid until ") + (ls("gv_exp") || "")); }
      document.documentElement.classList.add("is-member");
      await unlockCountry(K);
    } catch (e) {
      var m = e && e.message;
      if (m === "nokey" || m === "expired") { ls("gv_code", null); try { sessionStorage.removeItem("gv_k"); } catch (x) {} }
      if (page) say(m === "expired" ? (ko ? "이용 기간이 끝났습니다. 연장은 73036396@naver.com으로 연락 주세요." : "Your access has expired. Write to 73036396@naver.com to renew.")
        : m === "nokey" ? (ko ? "코드를 찾을 수 없습니다. 다시 확인해 주세요." : "Code not found. Please check it.")
        : (ko ? "잠시 연결이 안 됩니다. 잠시 후 다시 시도해 주세요." : "Could not connect. Please try again shortly."));
    }
  }
  if (window.crypto && crypto.subtle) { if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run(); }
})();
