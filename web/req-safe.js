/* GOV RADAR request UX: do not claim a request was received before an actual server response.
   This is a source-only, nonproduction change. No PII is written to localStorage. */
(function () {
  "use strict";
  var form = document.querySelector(".rq-form");
  if (!form) return;
  var K = window.WMM_REQUEST_TEXT || {};
  var msg = form.querySelector(".rq-msg");
  var button = form.querySelector('button[type="submit"]');
  var list = document.querySelector(".rq-mine");
  var key = "gv_rq";
  var langs = ["ko", "en", "es", "fr", "ar", "vi", "id"];
  var lang = langs.includes(document.documentElement.lang) ? document.documentElement.lang : "en";
  var busy = false;
  var strings = {
    ko: {
      sending: "접수 확인 중입니다. 아직 완료되지 않았습니다.",
      saved: "서버에 요청번호가 저장됐습니다. 담당자 확인 메일은 별도로 기다려 주세요.",
      relayFailed: "요청은 서버에 저장됐지만 담당자 알림 전달은 확인되지 않았습니다. 요청번호를 보관해 주세요.",
      forwarded: "양식 전달 서버에서 응답했습니다. 최종 접수는 담당자 확인 메일로 확인해 주세요.",
      failed: "접수를 확인하지 못했습니다. 다시 시도하거나 공식 문의 채널을 이용해 주세요.",
      unverified: "이전 브라우저 기록 — 실제 접수 여부 미확인",
      stored: "서버 저장 완료",
      duplicate: "최근 동일 요청이 서버에 저장됐습니다."
    },
    en: {
      sending: "Checking submission. Your request is not yet confirmed.",
      saved: "Request stored on our server. Please await a separate confirmation email.",
      relayFailed: "Request stored on our server, but delivery to the team could not be verified. Keep the request number.",
      forwarded: "The form relay responded. Please wait for a confirmation email to verify receipt.",
      failed: "Submission could not be confirmed. Please retry or use the official contact channel.",
      unverified: "Older browser-only record — receipt not verified",
      stored: "Stored on server",
      duplicate: "A matching request was already stored recently."
    }
  };
  var S = strings[lang] || strings.en;
  function field(name) { return form.elements.namedItem(name); }
  function current() {
    var chosen = document.querySelector('input[name="rqt"]:checked');
    return chosen ? chosen.value : "";
  }
  function setState(text) {
    msg.textContent = text;
    msg.setAttribute("role", "status");
    msg.setAttribute("aria-live", "polite");
  }
  function history() {
    try {
      var records = JSON.parse(localStorage.getItem(key) || "[]");
      return Array.isArray(records) ? records : [];
    } catch (_error) { return []; }
  }
  function store(record) {
    try {
      var records = history().filter(function (x) { return x && x.id !== record.id; });
      records.unshift(record);
      localStorage.setItem(key, JSON.stringify(records.slice(0, 30)));
    } catch (_error) { /* local history is optional; server receipt remains authoritative */ }
  }
  function paint(records) {
    if (!list) return;
    list.replaceChildren();
    if (!records.length) {
      var empty = document.createElement("li");
      empty.textContent = K.none || "No requests yet.";
      list.appendChild(empty);
      return;
    }
    records.forEach(function (r) {
      if (!r || typeof r !== "object") return;
      var li = document.createElement("li");
      var title = document.createElement("b");
      title.textContent = String(r.id || "");
      li.appendChild(title);
      var info = document.createElement("small");
      info.className = "note";
      var known = Boolean(r.verified);
      var label = known ? (S.stored + " · " + String(r.at || "")) : S.unverified;
      info.textContent = " · " + (K.names && K.names[r.t] || r.t || "") + " · " + label;
      li.appendChild(info);
      list.appendChild(li);
    });
  }
  function token() {
    try {
      var t = JSON.parse(localStorage.getItem("wmm.auth.v1") || "null");
      return t && t.access_token || null;
    } catch (_error) { return null; }
  }
  function authHeaders() {
    var headers = { "content-type": "application/json" };
    var value = token();
    if (value) headers.authorization = "Bearer " + value;
    return headers;
  }
  function relayForm() {
    var data = new URLSearchParams(new FormData(form)).toString();
    // Cloudflare relay must report a successful HTTP response. Do not treat opaque redirects as confirmed.
    return fetch(form.action, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded;charset=UTF-8" },
      body: data, redirect: "follow", credentials: "same-origin"
    }).then(function (r) {
      if (!r.ok || r.type === "opaque" || r.type === "opaqueredirect") throw new Error("form relay failed");
      return true;
    });
  }
  function details(type) {
    var box = form.querySelector('.rq-f[data-t="' + type + '"]');
    if (!box) return null;
    var lines = [], valid = true;
    box.querySelectorAll("[data-k]").forEach(function (input) {
      var value = String(input.value || "").trim();
      if (input.hasAttribute("data-req") && !value) valid = false;
      if (value) lines.push((input.closest("label").textContent || input.dataset.k).trim() + ": " + value);
    });
    var code = form.querySelector('[data-k="code"]');
    if (code && code.value.trim()) lines.push("member code: " + code.value.trim());
    return valid ? lines.join("\n") : null;
  }
  function updateFields(type, id, description) {
    field("product").value = "request:" + type + (id ? " " + id : "");
    field("field").value = type;
    field("need").value = (id ? "[" + id + "] " : "") +
      (K.names && K.names[type] || type) + "\n" + description;
  }
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (busy) return;
    if (!form.reportValidity()) return;
    var type = current();
    var body = details(type);
    if (!body) { setState(K.req || S.failed); return; }
    var email = String(field("email").value || "").trim();
    busy = true;
    button.disabled = true;
    setState(S.sending);
    updateFields(type, "", body);
    // We distinguish server storage from a form relay response and from complete failure.
    fetch("/api/req", {
      method: "POST", headers: authHeaders(),
      body: JSON.stringify({ type: type, body: body, email: email, lang: lang,
        privacy_consent: Boolean(field("privacy_agree") && field("privacy_agree").checked) }),
      credentials: "same-origin"
    }).then(function (response) {
      if (response.status === 503) return { fallback: true };
      if (!response.ok) throw new Error("request API rejected submission");
      return response.json().then(function (data) {
        if (!data || typeof data.req_no !== "string" || !/^RQ-[A-Z0-9-]+$/.test(data.req_no)) {
          throw new Error("missing authoritative server receipt");
        }
        return { data: data };
      });
    }).then(function (result) {
      if (result.fallback) {
        // No request number and no local "received" history: no false success.
        return relayForm().then(function () { setState(S.forwarded); });
      }
      var server = result.data;
      var id = server.req_no;
      store({ id: id, t: type, verified: true, at: new Date().toISOString().slice(0, 10) });
      paint(history());
      updateFields(type, id, body);
      setState((server.duplicate ? S.duplicate : S.saved) + " " + id);
      // Secondary owner alert is best-effort; failure must not erase a valid server receipt.
      return relayForm().catch(function () { setState(S.relayFailed + " " + id); });
    }).catch(function () {
      setState(S.failed);
    }).finally(function () {
      busy = false;
      button.disabled = false;
    });
  });
  document.querySelectorAll('input[name="rqt"]').forEach(function (radio) {
    radio.addEventListener("change", function () {
      var chosen = current();
      form.querySelectorAll(".rq-f").forEach(function (panel) {
        panel.hidden = panel.dataset.t !== chosen;
      });
    });
  });
  paint(history());
  if (token()) {
    fetch("/api/req", { headers: authHeaders(), credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error("no server records"); return r.json(); })
      .then(function (data) {
        if (!Array.isArray(data.items)) return;
        // Do not convert old browser-only pseudo receipts into confirmed records.
        paint(data.items.map(function (r) {
          return { id: r.req_no, t: r.type, at: String(r.created_at || "").slice(0, 10), verified: true };
        }));
      }).catch(function () { /* retain explicitly unverified local-only records */ });
  }
})();
