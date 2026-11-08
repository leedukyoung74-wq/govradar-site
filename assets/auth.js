/* GOV RADAR sign-in — Netlify Identity (GoTrue REST on the same origin).
   Email + password sign-up/sign-in, password reset, Google sign-in when enabled.
   Membership level comes from app_metadata.roles (m1…m5, edu, youth, uni, admin). */
(function () {
  const API = "/.netlify/identity", KEY = "wmm.auth.v1";
  const L = window.RADAR_LANG || "en", T = (window.RADAR_AT || {});
  const $ = s => document.querySelector(s);
  const tt = k => T[k] || k;
  let S = null, SETTINGS = null; const subs = [];

  function load() { try { S = JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { S = null; } }
  function save(v) { S = v; try { v ? localStorage.setItem(KEY, JSON.stringify(v)) : localStorage.removeItem(KEY); } catch (e) {} subs.forEach(f => { try { f(S); } catch (e) {} }); }
  async function j(path, opt) {
    const r = await fetch(API + path, opt);
    const txt = await r.text(); let d = null; try { d = txt ? JSON.parse(txt) : null; } catch (e) { d = { msg: txt }; }
    if (!r.ok) { const m = (d && (d.error_description || d.msg || d.error)) || ("HTTP " + r.status); const err = new Error(m); err.status = r.status; throw err; }
    return d;
  }
  async function settings() { if (SETTINGS) return SETTINGS; try { SETTINGS = await j("/settings"); } catch (e) { SETTINGS = { off: true, status: e.status }; } return SETTINGS; }
  async function withTokens(tok) {
    const user = await j("/user", { headers: { authorization: "Bearer " + tok.access_token } });
    save({ access_token: tok.access_token, refresh_token: tok.refresh_token, expires_at: Date.now() + (tok.expires_in || 3600) * 1000, user });
    return S;
  }
  async function refresh() {
    if (!S || !S.refresh_token) return null;
    try { const tok = await j("/token", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: "grant_type=refresh_token&refresh_token=" + encodeURIComponent(S.refresh_token) }); return await withTokens(tok); }
    catch (e) { save(null); return null; }
  }
  async function token() { if (!S) return null; if (Date.now() > S.expires_at - 60000) await refresh(); return S && S.access_token; }
  async function login(email, password) {
    const tok = await j("/token", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: "grant_type=password&username=" + encodeURIComponent(email) + "&password=" + encodeURIComponent(password) });
    return withTokens(tok);
  }
  async function signup(email, password, data) { return j("/signup", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email, password, data }) }); }
  async function recover(email) { return j("/recover", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email }) }); }
  async function update(attrs) { const t = await token(); const user = await j("/user", { method: "PUT", headers: { "content-type": "application/json", authorization: "Bearer " + t }, body: JSON.stringify(attrs) }); save({ ...S, user }); return user; }
  function logout() { const t = S && S.access_token; save(null); if (t) fetch(API + "/logout", { method: "POST", headers: { authorization: "Bearer " + t } }).catch(() => {}); }
  function roles() { return (S && S.user && S.user.app_metadata && S.user.app_metadata.roles) || []; }
  function tier() { const r = roles().map(x => String(x).toLowerCase()); for (const k of ["admin", "m5", "m4", "m3", "m2", "uni", "m1", "edu", "youth"]) if (r.includes(k)) return k; return S ? "free" : null; }
  function has(min) { const order = { free: 0, youth: 1, edu: 1, m1: 1, uni: 2, m2: 2, m3: 3, m4: 4, m5: 5, admin: 9 }; const t = tier(); return t ? (order[t] || 0) >= (order[min] || 0) : false; }

  /* handle links from emails: #confirmation_token / #recovery_token / #invite_token / #access_token (Google) */
  async function hash() {
    const h = new URLSearchParams((location.hash || "").replace(/^#/, ""));
    const clear = () => history.replaceState(null, "", location.pathname + location.search);
    try {
      if (h.get("confirmation_token")) { clear(); const tok = await j("/verify", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ token: h.get("confirmation_token"), type: "signup" }) }); await withTokens(tok); toast(tt("confirmed")); }
      else if (h.get("recovery_token")) { clear(); const tok = await j("/verify", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ token: h.get("recovery_token"), type: "recovery" }) }); await withTokens(tok); open("newpw"); }
      else if (h.get("invite_token")) { clear(); open("invite", h.get("invite_token")); }
      else if (h.get("access_token")) { const tok = { access_token: h.get("access_token"), refresh_token: h.get("refresh_token"), expires_in: +h.get("expires_in") || 3600 }; clear(); await withTokens(tok); toast(tt("welcome")); }
      else if (h.get("error_description")) { clear(); toast(h.get("error_description")); }
    } catch (e) { toast(e.message); }
  }

  /* ---------- modal UI ---------- */
  function toast(msg) { if (!msg) return; const n = document.createElement("div"); n.className = "toast"; n.textContent = msg; document.body.appendChild(n); setTimeout(() => n.remove(), 3600); }
  let MODE = "login", INVITE = null;
  async function open(mode, invite) {
    MODE = mode || "login"; INVITE = invite || null;
    const m = $("#authm"); if (!m) return; m.hidden = false;
    const st = await settings();
    const off = st.off;
    $("#authsoon").hidden = !off; $("#authf").hidden = !!off;
    if (off) { $("#authsoon").textContent = tt("not_enabled"); return; }
    const sign = MODE === "signup", reset = MODE === "reset", newpw = MODE === "newpw" || MODE === "invite";
    $("#auth-h").textContent = tt(sign ? "signup" : reset ? "reset" : newpw ? "newpw" : "login");
    $("#auth-name-w").hidden = !sign; $("#auth-age-w").hidden = !sign; $("#auth-terms-w").hidden = !sign;
    $("#auth-email-w").hidden = newpw; $("#auth-pw-w").hidden = reset;
    $("#auth-sub").textContent = tt(sign ? "signup" : reset ? "send_reset" : newpw ? "save_pw" : "login");
    $("#auth-sw").innerHTML = sign ? `<a href="#" data-am="login">${tt("have_acct")}</a>` : reset || newpw ? `<a href="#" data-am="login">${tt("back")}</a>` : `<a href="#" data-am="signup">${tt("no_acct")}</a> · <a href="#" data-am="reset">${tt("forgot")}</a>`;
    const g = $("#auth-google"); g.hidden = !(st.external && st.external.google) || reset || newpw;
    $("#authmsg").textContent = "";
    setTimeout(() => { const f = newpw ? $("#authp") : $("#authe"); f && f.focus(); }, 50);
  }
  function close() { const m = $("#authm"); if (m) m.hidden = true; }
  function wire() {
    const m = $("#authm"); if (!m) return;
    $("#authx").addEventListener("click", close);
    m.addEventListener("click", e => { if (e.target === m) close(); const a = e.target.closest("[data-am]"); if (a) { e.preventDefault(); open(a.dataset.am); } });
    $("#auth-google").addEventListener("click", () => { location.href = API + "/authorize?provider=google"; });
    $("#authf").addEventListener("submit", async e => {
      e.preventDefault(); const msg = $("#authmsg"), btn = $("#auth-sub"); btn.disabled = true; msg.textContent = "…";
      const em = ($("#authe").value || "").trim(), pw = $("#authp").value || "";
      try {
        if (MODE === "signup") {
          if (!$("#auth-terms").checked) throw new Error(tt("need_terms"));
          const age = $("#auth-age").value; if (age === "u14") throw new Error(tt("u14"));
          if (pw.length < 8) throw new Error(tt("pw_short"));
          const r = await signup(em, pw, { full_name: $("#authn").value.trim(), lang: L, age_band: age, terms_at: new Date().toISOString() });
          if (r && r.confirmed_at) { await login(em, pw); msg.textContent = tt("welcome"); setTimeout(close, 900); } else msg.textContent = tt("check_mail");
        } else if (MODE === "reset") { await recover(em); msg.textContent = tt("reset_sent"); }
        else if (MODE === "newpw") { if (pw.length < 8) throw new Error(tt("pw_short")); await update({ password: pw }); msg.textContent = tt("pw_saved"); setTimeout(close, 900); }
        else if (MODE === "invite") { if (pw.length < 8) throw new Error(tt("pw_short")); const tok = await j("/verify", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ token: INVITE, type: "signup", password: pw }) }); await withTokens(tok); msg.textContent = tt("welcome"); setTimeout(close, 900); }
        else { await login(em, pw); msg.textContent = tt("welcome"); setTimeout(close, 700); }
      } catch (err) {
        const s = String(err.message || "");
        msg.textContent = /invalid_grant|Invalid Login|No user found/i.test(s) ? tt("bad_login") : /not confirmed|Email not confirmed/i.test(s) ? tt("not_confirmed") : /already/i.test(s) ? tt("exists") : s;
      } finally { btn.disabled = false; }
    });
  }
  function paint() {
    const b = $("#loginbtn"); if (!b) return;
    b.textContent = S ? tt("account") : tt("login");
    b.classList.toggle("on", !!S);
    document.documentElement.dataset.tier = tier() || "";
    document.querySelectorAll("[data-tier-min]").forEach(x => { const ok = has(x.dataset.tierMin); x.classList.toggle("unlocked", ok); });
  }

  window.WMMAuth = { get session() { return S; }, user: () => S && S.user, token, login, signup, logout, update, tier, has, open, settings, onChange: f => subs.push(f) };
  load(); subs.push(paint);
  document.addEventListener("DOMContentLoaded", () => {
    wire(); paint(); hash();
    const b = $("#loginbtn"); if (b) b.addEventListener("click", () => { if (S) location.href = `/${L}/account/`; else open("login"); });
    document.addEventListener("click", e => { const a = e.target.closest("[data-auth]"); if (a) { e.preventDefault(); if (S && a.dataset.auth === "signup") location.href = `/${L}/account/`; else open(a.dataset.auth); } });
    if (S && Date.now() > S.expires_at - 60000) refresh().then(paint);
  });
})();
