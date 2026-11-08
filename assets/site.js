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
