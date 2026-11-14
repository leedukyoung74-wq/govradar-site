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
  // NASA JPL blocks cross-site requests; asteroid list comes from the daily hazard data instead
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

/* ---- Live situation board (verified facts only) from the GitHub data branch: no Netlify deploy needed ---- */
(function () {
  var box = document.querySelectorAll(".liveboard"); if (!box.length) return;
  var L = (location.pathname.match(/^\/([a-z]{2})\//) || [, "en"])[1], ko = L === "ko";
  var T = {
    ko: { war: "전쟁", tension: "긴장", watch: "경계", high: "위험", medium: "주의", hot: "진행 중인 전쟁·분쟁", dis: "자연재해·감염병 (최근 7일)", ctry: "나라별 경보", asof: "기준", off: "공식 발표", more: "더 보기", ne: "지구 근접", fail: "상황판을 불러오지 못했습니다. 아래 상세 내용을 보세요.", k: { tsunami: "쓰나미", quake: "지진", storm: "태풍", flood: "홍수", volcano: "화산", weather: "폭우·이상기상", fire: "산불", epidemic: "감염병", asteroid: "소행성·혜성" }, c: { conflict: "분쟁", disaster: "재해", epidemic: "감염병" } },
    en: { war: "War", tension: "Tension", watch: "Watch", high: "High", medium: "Elevated", hot: "Active conflicts", dis: "Disasters & outbreaks (last 7 days)", ctry: "Country alerts", asof: "As of", off: "official", more: "More", ne: "Near Earth", fail: "Could not load the live board. See the details below.", k: { tsunami: "Tsunami", quake: "Earthquake", storm: "Typhoon", flood: "Flood", volcano: "Volcano", weather: "Extreme weather", fire: "Wildfire", epidemic: "Outbreak", asteroid: "Asteroid / comet" }, c: { conflict: "Conflict", disaster: "Disaster", epidemic: "Outbreak" } },
    es: { war: "Guerra", tension: "Tensión", watch: "Vigilancia", high: "Alto", medium: "Elevado", hot: "Conflictos activos", dis: "Desastres y brotes (últimos 7 días)", ctry: "Alertas por país", asof: "Al", off: "oficial", more: "Más" , ne: "Cerca de la Tierra", k: { tsunami: "Tsunami", quake: "Terremoto", storm: "Tifón", flood: "Inundación", volcano: "Volcán", weather: "Clima extremo", fire: "Incendio forestal", epidemic: "Brote", asteroid: "Asteroide / cometa" }, c: { conflict: "Conflicto", disaster: "Desastre", epidemic: "Brote" } },
    fr: { war: "Guerre", tension: "Tension", watch: "Vigilance", high: "Élevé", medium: "Modéré", hot: "Conflits en cours", dis: "Catastrophes et épidémies (7 derniers jours)", ctry: "Alertes par pays", asof: "Au", off: "officiel", more: "Plus" , ne: "Près de la Terre", k: { tsunami: "Tsunami", quake: "Séisme", storm: "Typhon", flood: "Inondation", volcano: "Volcan", weather: "Météo extrême", fire: "Feu de forêt", epidemic: "Épidémie", asteroid: "Astéroïde / comète" }, c: { conflict: "Conflit", disaster: "Catastrophe", epidemic: "Épidémie" } },
    ar: { war: "حرب", tension: "توتر", watch: "مراقبة", high: "مرتفع", medium: "متوسط", hot: "نزاعات جارية", dis: "كوارث وأوبئة (آخر 7 أيام)", ctry: "تنبيهات الدول", asof: "حتى", off: "رسمي", more: "المزيد" , ne: "قرب الأرض", k: { tsunami: "تسونامي", quake: "زلزال", storm: "إعصار", flood: "فيضان", volcano: "بركان", weather: "طقس متطرف", fire: "حريق غابات", epidemic: "تفشٍّ وبائي", asteroid: "كويكب / مذنب" }, c: { conflict: "نزاع", disaster: "كارثة", epidemic: "وباء" } },
    vi: { war: "Chiến tranh", tension: "Căng thẳng", watch: "Theo dõi", high: "Cao", medium: "Trung bình", hot: "Xung đột đang diễn ra", dis: "Thiên tai và dịch bệnh (7 ngày qua)", ctry: "Cảnh báo theo quốc gia", asof: "Tính đến", off: "chính thức", more: "Thêm" , ne: "Gần Trái Đất", k: { tsunami: "Sóng thần", quake: "Động đất", storm: "Bão", flood: "Lũ lụt", volcano: "Núi lửa", weather: "Thời tiết cực đoan", fire: "Cháy rừng", epidemic: "Dịch bệnh", asteroid: "Tiểu hành tinh / sao chổi" }, c: { conflict: "Xung đột", disaster: "Thiên tai", epidemic: "Dịch bệnh" } },
    id: { war: "Perang", tension: "Ketegangan", watch: "Pantauan", high: "Tinggi", medium: "Sedang", hot: "Konflik berlangsung", dis: "Bencana dan wabah (7 hari terakhir)", ctry: "Peringatan per negara", asof: "Per", off: "resmi", more: "Lainnya" , ne: "Dekat Bumi", k: { tsunami: "Tsunami", quake: "Gempa", storm: "Topan", flood: "Banjir", volcano: "Gunung api", weather: "Cuaca ekstrem", fire: "Kebakaran hutan", epidemic: "Wabah", asteroid: "Asteroid / komet" }, c: { conflict: "Konflik", disaster: "Bencana", epidemic: "Wabah" } }
  };
  var t = Object.assign({}, T.en, T[L] || {}); window.__gvT = t; t.k = (T[L] && T[L].k) || T.en.k; t.c = (T[L] && T[L].c) || T.en.c;
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }
  /* animated hazard overlays drawn over the radar map */
  var FX = {
    flood: '<svg viewBox="0 0 160 100" preserveAspectRatio="none"><g class="fl-rise"><path class="fl-w1" d="M-160 62 Q-140 54 -120 62 T-80 62 T-40 62 T0 62 T40 62 T80 62 T120 62 T160 62 T200 62 T240 62 T280 62 T320 62 V100 H-160Z"/><path class="fl-w2" d="M-160 70 Q-140 63 -120 70 T-80 70 T-40 70 T0 70 T40 70 T80 70 T120 70 T160 70 T200 70 T240 70 T280 70 T320 70 V100 H-160Z"/></g><g class="rain">' + Array.apply(null, Array(14)).map(function (_, i) { return '<line x1="' + (i * 12 + 4) + '" y1="-10" x2="' + (i * 12) + '" y2="6" style="animation-delay:' + (i % 5) * .17 + 's"/>'; }).join("") + '</g></svg>',
    storm: '<svg viewBox="-50 -50 100 100"><g class="ty-spin"><path d="M0 0 C 14 -2 22 -14 16 -28 C 30 -14 26 8 6 12" /><path d="M0 0 C -14 2 -22 14 -16 28 C -30 14 -26 -8 -6 -12" /><path class="ty-arm" d="M0 0 C 8 10 24 14 36 6"/><path class="ty-arm" d="M0 0 C -8 -10 -24 -14 -36 -6"/></g><circle class="ty-eye" r="4"/></svg>',
    tsunami: '<svg viewBox="0 0 160 100" preserveAspectRatio="none"><g class="ts-move"><path class="ts-body" d="M-90 100 L-90 70 C -60 66 -40 40 -14 30 C 6 22 26 30 30 46 C 22 40 10 42 8 52 C 6 62 22 70 40 72 L 60 74 L 60 100 Z"/><path class="ts-foam" d="M-14 30 C 6 22 26 30 30 46 C 22 40 10 42 8 52"/></g></svg>',
    quake: '<svg viewBox="0 0 160 100" preserveAspectRatio="none"><polyline class="qk-line" points="0,50 20,50 26,30 32,72 38,22 44,80 50,36 56,62 62,46 70,50 90,50 96,40 102,60 108,50 160,50"/></svg><i class="qk-r"></i><i class="qk-r r2"></i><i class="qk-r r3"></i>',
    fire: '<svg viewBox="0 0 160 100"><g class="fi-g">' + [40, 62, 84, 106, 128].map(function (x, i) { return '<path class="fi-f" style="animation-delay:' + i * .13 + 's" d="M' + x + ' 92 C ' + (x - 10) + ' 78 ' + (x - 6) + ' 64 ' + x + ' 52 C ' + (x + 2) + ' 64 ' + (x + 12) + ' 70 ' + (x + 8) + ' 92 Z"/>'; }).join("") + '</g>' + Array.apply(null, Array(8)).map(function (_, i) { return '<circle class="fi-e" r="1.4" cx="' + (36 + i * 13) + '" cy="60" style="animation-delay:' + i * .3 + 's"/>'; }).join("") + '</svg>',
    volcano: '<svg viewBox="0 0 160 100"><path class="vo-smoke" d="M80 40 C 70 30 74 18 86 16 C 90 6 106 8 106 18 C 118 18 118 32 106 34 Z"/><path class="vo-m" d="M40 100 L72 46 L88 46 L120 100 Z"/><path class="vo-lava" d="M74 46 L86 46 L92 60 L84 56 L80 70 L76 56 L68 62 Z"/>' + Array.apply(null, Array(7)).map(function (_, i) { return '<circle class="vo-p" r="2" cx="80" cy="46" style="--dx:' + ((i - 3) * 9) + 'px;animation-delay:' + i * .22 + 's"/>'; }).join("") + '</svg>',
    weather: '<svg viewBox="0 0 160 100" preserveAspectRatio="none"><g class="rain heavy">' + Array.apply(null, Array(22)).map(function (_, i) { return '<line x1="' + (i * 8) + '" y1="-10" x2="' + (i * 8 - 5) + '" y2="10" style="animation-delay:' + (i % 7) * .11 + 's"/>'; }).join("") + '</g></svg>',
    epidemic: '<svg viewBox="-50 -50 100 100">' + [[0, 0, 13], [-26, -14, 7], [24, 16, 8], [22, -20, 5], [-20, 20, 6]].map(function (v, i) { return '<g class="vi-g" style="animation-delay:' + i * .35 + 's" transform="translate(' + v[0] + " " + v[1] + ')"><circle r="' + v[2] + '"/>' + [0, 45, 90, 135, 180, 225, 270, 315].map(function (a) { return '<line x1="0" y1="' + -v[2] + '" x2="0" y2="' + -(v[2] + v[2] * .45) + '" transform="rotate(' + a + ')"/>'; }).join("") + '</g>'; }).join("") + '</svg>',
    asteroid: '<svg viewBox="0 0 160 100">' + Array.apply(null, Array(18)).map(function (_, i) { return '<circle class="st" r="' + (i % 3 ? .6 : 1) + '" cx="' + ((i * 37) % 160) + '" cy="' + ((i * 23) % 100) + '" style="animation-delay:' + (i % 6) * .4 + 's"/>'; }).join("") + '<g class="co-move"><path class="co-tail" d="M0 0 L-70 -26 L-66 -18 Z"/><circle class="co-head" r="4"/></g><circle class="earth" cx="128" cy="78" r="16"/></svg>'
  };
  FX.tsunami += ""; FX.war = '<i class="qk-r"></i><i class="qk-r r2"></i>';
  function hzCard(x, cn, label, home) {
    var k = x.kind, map = x.iso ? '<div class="hotmap hzmap" data-focus="' + esc(x.iso) + '" data-hl="' + esc(x.iso) + '" data-pts="[]"></div>' : '<div class="hzmap space"></div>';
    return '<div class="lb-hz hz-' + k + '"><div class="hz-vis">' + map + '<div class="hzfx">' + (FX[k] || FX.quake) + '</div><span class="hz-tag">' + esc(label) + '</span></div><div class="hz-txt"><p><b>' + (x.iso ? cn(x.iso) : "🌍 " + (window.__gvT && window.__gvT.ne || "Near Earth")) + '</b> <small class="note">' + esc(x.date || "") + '</small></p><p>' + esc(pick(x)) + (x.url && !home ? ' <a href="' + esc(x.url) + '" target="_blank" rel="noopener">↗</a>' : "") + '</p></div></div>';
  }
  var TR = {};
  function tr(s) { return (s && TR[s]) || s; }
  function pick(o) { return ko ? (o.ko || o.en) : tr(o.en || o.ko); }
  function flag(iso) { return iso && iso.length === 2 ? String.fromCodePoint.apply(null, iso.toUpperCase().split("").map(function (c) { return 127397 + c.charCodeAt(0); })) : "🌐"; }
  var RAW = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/hz/";
  var trP = (L === "ko" || L === "en") ? Promise.resolve({}) : fetch(RAW + "i18n/" + L + ".json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; });
  Promise.all([fetch(RAW + "hazards.json", { cache: "no-cache" }).then(function (r) { if (!r.ok) throw 0; return r.json(); }), trP])
    .then(function (a) { TR = a[1] || {}; return a[0]; })
    .then(function (d) {
      box.forEach(function (b) {
        var names = {}; try { names = JSON.parse(b.getAttribute("data-names")); } catch (e) {}
        var home = b.getAttribute("data-mode") === "home";
        function cn(iso) { var n = names[iso]; if (n && !n[1]) return flag(iso) + " " + esc(n[0]); return n ? '<a href="/' + L + "/" + n[1] + '/#risk">' + flag(iso) + " " + esc(n[0]) + "</a>" : flag(iso) + " " + esc(iso || ""); }
        var h = '<p class="lb-asof"><b>' + t.asof + " " + esc((d.checked || d.updated || "").replace("T", " ")) + "</b>" + (d.summary_ko ? " · " + esc(ko ? d.summary_ko : tr(d.summary_en || "")).slice(0, home ? 220 : 600) + (home ? "…" : "") : "") + "</p>";
        h += '<h3>' + t.hot + '</h3><div class="lb-grid">' + d.hotspots.map(function (x) {
          return '<div class="lb-card"><p><b>' + cn(x.iso) + "</b> <span class=\"lv " + esc(x.level) + '">' + (t[x.level] || "") + "</span></p><p><b>" + esc(pick(x)) + "</b></p>" +
            (home ? "" : "<ul>" + x.facts.map(function (f) { return "<li>" + esc(pick(f)) + (f.v === "official" ? ' <small class="note">(' + t.off + ")</small>" : "") + "</li>"; }).join("") + "</ul>") + "</div>";
        }).join("") + "</div>";
        var seen = {}, dis = home ? d.disasters.filter(function (x) { if (seen[x.kind]) return false; seen[x.kind] = 1; return true; }).slice(0, 6) : d.disasters.slice();
        if (!home) { var order = ["tsunami", "quake", "storm", "flood", "volcano", "fire", "weather", "epidemic", "asteroid"], first = [], rest = [], got = {};
          dis.forEach(function (x) { if (!got[x.kind]) { got[x.kind] = 1; first.push(x); } else rest.push(x); });
          first.sort(function (a, b) { return order.indexOf(a.kind) - order.indexOf(b.kind); }); dis = first.concat(rest); }
        var nCard = home ? dis.length : Math.min(12, dis.length);
        h += "<h3>" + t.dis + '</h3><div class="lb-hzgrid">' + dis.slice(0, nCard).map(function (x) { return hzCard(x, cn, t.k[x.kind] || x.kind, home); }).join("") + "</div>";
        if (dis.length > nCard) h += '<ul class="lb-list">' + dis.slice(nCard).map(function (x) {
          return "<li><span class=\"tag\">" + (t.k[x.kind] || x.kind) + "</span> " + (x.iso ? cn(x.iso) : "🌍") + " · " + esc(x.date || "") + " — " + esc(pick(x)) + (x.url ? ' <a href="' + esc(x.url) + '" target="_blank" rel="noopener">↗</a>' : "") + "</li>";
        }).join("") + "</ul>";
        var cs = home ? d.countries.filter(function (c) { return c.level === "high"; }) : d.countries;
        h += "<h3>" + t.ctry + ' <small class="note">' + t.high + " " + d.countries.filter(function (c) { return c.level === "high"; }).length + " · " + t.medium + " " + d.countries.filter(function (c) { return c.level === "medium"; }).length + "</small></h3>";
        h += home ? '<p class="lb-chips">' + cs.map(function (c) { return '<span class="lb-chip high">' + cn(c.iso) + "</span>"; }).join(" ") + "</p>"
          : '<div class="lb-grid">' + cs.map(function (c) {
            return '<div class="lb-card"><p><b>' + cn(c.iso) + '</b> <span class="lv ' + (c.level === "high" ? "war" : "tension") + '">' + t[c.level] + "</span></p><ul>" +
              ["conflict", "disaster", "epidemic"].filter(function (k) { return c[k]; }).map(function (k) { return (ko ? c[k].ko : (c[k].en.length ? c[k].en : c[k].ko)).map(function (s) { return "<li><small class=\"note\">" + t.c[k] + "</small> " + esc(ko ? s : tr(s)) + "</li>"; }).join(""); }).join("") + "</ul></div>";
          }).join("") + "</div>";
        b.querySelector(".lb-body").innerHTML = h;
        var draw = function () { b.querySelectorAll(".hzmap:not(.space)").forEach(function (m) { if (window.gvHotmap) window.gvHotmap(m); }); };
        if (window.jsVectorMap) draw(); else window.addEventListener("load", draw);
      });
    })
    .catch(function () { box.forEach(function (b) { b.querySelector(".lb-body").innerHTML = '<p class="note">' + (t.fail || T.en.fail) + "</p>"; }); });
})();

/* ---- Free sign-up gate: working details open once signed in (or as an analysis member) ---- */
(function () {
  var L = (location.pathname.match(/^\/([a-z]{2})\//) || [, "en"])[1], ko = L === "ko";
  var M = { ko: ["무료 가입하면 바로 보입니다", "이메일만으로 가입 · 관심 나라 저장 · 내 입찰 담기", "무료 가입", "이미 가입했어요"], en: ["Sign up free to see this", "Email only · save countries · keep your tender list", "Sign up free", "I already have an account"],
    es: ["Regístrese gratis para verlo", "Solo correo · guarde países y licitaciones", "Registro gratis", "Ya tengo cuenta"], fr: ["Inscrivez-vous gratuitement pour voir ceci", "E-mail uniquement · enregistrez pays et appels d'offres", "Inscription gratuite", "J'ai déjà un compte"],
    ar: ["سجّل مجانًا لرؤية هذا", "بالبريد الإلكتروني فقط · احفظ الدول والمناقصات", "سجّل مجانًا", "لدي حساب"], vi: ["Đăng ký miễn phí để xem", "Chỉ cần email · lưu quốc gia và gói thầu", "Đăng ký miễn phí", "Tôi đã có tài khoản"], id: ["Daftar gratis untuk melihat", "Cukup email · simpan negara dan tender", "Daftar gratis", "Saya sudah punya akun"] };
  var m = M[L] || M.en;
  function signed() { try { var s = JSON.parse(localStorage.getItem("wmm.auth.v1") || "null"); return !!(s && s.access_token) || !!localStorage.getItem("gv_code"); } catch (e) { return false; } }
  function apply() {
    var on = signed(); document.documentElement.classList.toggle("signed-in", on);
    document.querySelectorAll(".sgate").forEach(function (g) {
      var box = g.querySelector(".sgate-box");
      if (on) { if (box) box.remove(); return; }
      if (box) return;
      box = document.createElement("div"); box.className = "sgate-box";
      box.innerHTML = "<b>🔓 " + m[0] + "</b><p>" + m[1] + '</p><p><button class="btn pri" data-auth="signup">' + m[2] + '</button> <button class="btn" data-auth="login">' + m[3] + "</button></p>";
      g.appendChild(box);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply); else apply();
  window.addEventListener("storage", apply); setInterval(apply, 4000);
})();
/* owner shortcut: shown on every page only in a browser that opened the owner screen */
(function () {
  try { if (!localStorage.getItem("gv_owner") || location.pathname.indexOf("/owner/") === 0) return; } catch (e) { return; }
  var a = document.createElement("a"); a.href = "/owner/"; a.textContent = "운영자 화면";
  a.setAttribute("style", "position:fixed;right:14px;bottom:14px;z-index:9999;background:#1d2b4f;color:#fff;font-weight:700;font-size:13px;padding:9px 14px;border-radius:20px;box-shadow:0 2px 8px rgba(0,0,0,.25);text-decoration:none");
  document.body.appendChild(a);
})();
