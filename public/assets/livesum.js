/* GOV RADAR 최신 상황 상자 (2026-11-23) — <div data-livesum></div>
   매일 자동 수집·해설 갱신되는 data 브랜치의 hz/hazards.json 을 열 때마다 직접 읽어, 사이트를 다시 게시하지 않아도 최신 상황을 보여 준다. */
(function () {
  var RAW = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/hz/hazards.json";
  var L = (document.documentElement.lang || "ko").slice(0, 2), KO = L === "ko";
  var T = KO ? { h: "지금 상황 — 자동 갱신", upd: "해설 갱신", chk: "공식 자료 확인", more: "실시간 상황판에서 전체 보기 →", dis: "최근 재난·감염병 (공식 기관)", lv: { war: "전쟁", tension: "긴장", watch: "관찰", high: "높음" } }
    : { h: "Situation now — updated automatically", upd: "Briefing updated", chk: "Official data checked", more: "See everything on the live board →", dis: "Latest disasters and outbreaks (official agencies)", lv: { war: "War", tension: "Tension", watch: "Watch", high: "High" } };
  var LIVE = KO ? "/live/" : "/live/" + L + "/";
  function e(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function fl(c) { return c && c.length === 2 ? String.fromCodePoint.apply(null, c.split("").map(function (x) { return 127397 + x.charCodeAt(0); })) : "🌐"; }
  function pick(o, k) { return KO ? (o[k + "_ko"] || o.ko || o[k + "_en"] || o.en) : (o[k + "_en"] || o.en || o[k + "_ko"] || o.ko); }
  var css = ".lsm{max-width:1180px;margin:0 auto 34px;padding:0 max(16px,env(safe-area-inset-left));box-sizing:border-box}.lsm .in{background:#fff;border:1px solid #E3E7ED;border-left:5px solid #FF3B4E;border-radius:14px;padding:22px 24px;color:#0B1526}" +
    ".lsm h3{margin:0 0 4px;font-size:20px;display:flex;align-items:center;gap:8px}.lsm h3 i{width:9px;height:9px;border-radius:50%;background:#FF3B4E;box-shadow:0 0 9px #FF3B4E;animation:lsb 1.2s infinite}@keyframes lsb{50%{opacity:.3}}" +
    ".lsm .m{font-size:13px;color:#5A6577;margin:0 0 12px}.lsm .s{font-size:16px;line-height:1.7;margin:0 0 14px}.lsm ul{margin:0 0 12px;padding:0;list-style:none}.lsm li{padding:8px 0;border-top:1px solid #EEF1F5;font-size:15px;line-height:1.55}" +
    ".lsm li b{margin-inline-end:6px}.lsm .lv{display:inline-block;font-size:12px;font-weight:700;color:#fff;background:#FF3B4E;border-radius:999px;padding:1px 8px;margin-inline-end:6px}.lsm .lv.t{background:#FF8A3D}.lsm h4{margin:14px 0 4px;font-size:15px}.lsm a.go{font-weight:700;color:#0B1526;border-bottom:2px solid #B7800F;text-decoration:none}";
  function draw(el, H) {
    var hot = (H.hotspots || []).map(function (h) { return '<li><span class="lv' + (h.level === "war" ? "" : " t") + '">' + e(T.lv[h.level] || h.level) + '</span><b>' + fl(h.iso) + " " + e(pick(h, "")) + '</b>' + e(pick(h, "status")) + '</li>'; }).join("");
    var dis = (H.disasters || []).filter(function (d) { return d.kind !== "asteroid"; }).slice(0, 6).map(function (d) { return '<li>' + e(d.date) + " · " + fl(d.iso) + " " + (d.url ? '<a href="' + e(d.url) + '" target="_blank" rel="noopener">' + e(pick(d, "")) + '</a>' : e(pick(d, ""))) + '</li>'; }).join("");
    el.innerHTML = '<div class="in"><h3><i></i>' + e(T.h) + '</h3><p class="m">' + e(T.upd) + " " + e((H.editorial_updated || H.updated || "").replace("T", " ")) + " · " + e(T.chk) + " " + e((H.checked || "").replace("T", " ")) + " KST</p>" +
      '<p class="s">' + e(KO ? H.summary_ko : H.summary_en) + '</p><ul>' + hot + '</ul>' + (dis ? '<h4>' + e(T.dis) + '</h4><ul>' + dis + '</ul>' : "") + '<a class="go" href="' + LIVE + '">' + e(T.more) + '</a></div>';
  }
  function go() {
    var els = document.querySelectorAll("[data-livesum]"); if (!els.length) return;
    var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
    fetch(RAW, { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (H) { els.forEach(function (el) { el.classList.add("lsm"); draw(el, H); }); }).catch(function () { });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
})();
