/* GOV RADAR 실시간 뉴스 상자 (2026-11-23) — <div data-newsbox="t:cyber"> / "c:VN" / "tabs:war,cyber,disaster,epidemic,prep">
   /api/news 에서 구글 뉴스 검색 결과의 제목·언론사·시각·링크만 받아 보여 주고 15분마다 새로 받는다. */
(function () {
  var L = (document.documentElement.lang || "ko").slice(0, 2);
  var TX = {
    ko: { war: "전쟁·분쟁", cyber: "사이버 공격", disaster: "자연재해", epidemic: "감염병", prep: "정부 대비 권고", c: "이 나라 최신 뉴스", note: "자동 수집 · 뉴스 검색(구글·빙) 결과의 기사 제목만 보여 줍니다. 내용은 각 언론사 원문을 확인하세요.", at: "마지막 수집", none: "지금 새 기사가 없거나 연결되지 않습니다.", m: "분 전", h: "시간 전", d: "일 전", live: "실시간 뉴스" },
    en: { war: "War & conflict", cyber: "Cyberattacks", disaster: "Natural disasters", epidemic: "Epidemics", prep: "Government advice", c: "Latest news on this country", note: "Collected automatically from news search (Google, Bing) — headlines only. Read the original article for details.", at: "Last fetched", none: "No new articles right now, or the source is unreachable.", m: " min ago", h: " h ago", d: " d ago", live: "Live news" },
    es: { war: "Guerra y conflicto", cyber: "Ciberataques", disaster: "Desastres naturales", epidemic: "Epidemias", prep: "Consejos del gobierno", c: "Últimas noticias del país", note: "Recogido automáticamente de Google Noticias — solo titulares.", at: "Actualizado", none: "Sin artículos nuevos ahora.", m: " min", h: " h", d: " d", live: "Noticias en vivo" },
    fr: { war: "Guerre et conflits", cyber: "Cyberattaques", disaster: "Catastrophes", epidemic: "Épidémies", prep: "Conseils des États", c: "Dernières nouvelles du pays", note: "Collecté automatiquement depuis Google Actualités — titres seulement.", at: "Mis à jour", none: "Aucun nouvel article pour l'instant.", m: " min", h: " h", d: " j", live: "Actualités en direct" },
    ar: { war: "الحرب والنزاعات", cyber: "الهجمات السيبرانية", disaster: "الكوارث الطبيعية", epidemic: "الأوبئة", prep: "إرشادات الحكومات", c: "آخر أخبار هذا البلد", note: "تُجمع تلقائيًا من أخبار Google — العناوين فقط.", at: "آخر تحديث", none: "لا توجد مقالات جديدة الآن.", m: " د", h: " س", d: " ي", live: "أخبار مباشرة" },
    vi: { war: "Chiến tranh", cyber: "Tấn công mạng", disaster: "Thiên tai", epidemic: "Dịch bệnh", prep: "Khuyến cáo chính phủ", c: "Tin mới về quốc gia này", note: "Tự động thu thập từ Google News — chỉ tiêu đề.", at: "Cập nhật", none: "Chưa có bài mới.", m: " phút", h: " giờ", d: " ngày", live: "Tin trực tiếp" },
    id: { war: "Perang & konflik", cyber: "Serangan siber", disaster: "Bencana alam", epidemic: "Wabah", prep: "Imbauan pemerintah", c: "Berita terbaru negara ini", note: "Dikumpulkan otomatis dari Google Berita — judul saja.", at: "Diperbarui", none: "Belum ada artikel baru.", m: " mnt", h: " jam", d: " hr", live: "Berita langsung" }
  };
  var T = TX[L] || TX.en;
  function e(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function ago(d) { var m = Math.max(1, Math.round((Date.now() - d) / 60000)); return m < 60 ? m + T.m : m < 2880 ? Math.round(m / 60) + T.h : Math.round(m / 1440) + T.d; }
  var css = ".nbx{font-size:15px}.nbx .nbt{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}.nbx .nbt button{font:inherit;font-size:14px;font-weight:700;border:1px solid currentColor;background:transparent;color:inherit;opacity:.6;border-radius:999px;padding:6px 13px;cursor:pointer}.nbx .nbt button[aria-pressed=true]{opacity:1;background:#0B1526;color:#fff;border-color:#0B1526}.nbx.dark .nbt button[aria-pressed=true]{background:#fff;color:#0B1526;border-color:#fff}" +
    ".nbx ul{list-style:none;margin:0;padding:0;border-top:1px solid rgba(127,140,160,.3)}.nbx li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 14px;padding:11px 2px;border-bottom:1px solid rgba(127,140,160,.25)}.nbx li a{color:inherit;text-decoration:none;font-weight:700;line-height:1.45}.nbx li a:hover{text-decoration:underline}.nbx li span{font-size:13px;opacity:.65;white-space:nowrap}.nbx li small{grid-column:1/-1;font-size:13px;opacity:.65;margin-top:-2px}.nbx .nbn{font-size:12.5px;opacity:.65;margin:10px 0 0}.nbx .nbh{display:flex;align-items:center;gap:8px;font-weight:700;font-size:17px;margin:0 0 10px}.nbx .nbh i{width:8px;height:8px;border-radius:50%;background:#FF3B4E;box-shadow:0 0 8px #FF3B4E;animation:nbb 1.2s infinite}@keyframes nbb{50%{opacity:.3}}" +
    "@media(max-width:600px){.nbx li{grid-template-columns:1fr}.nbx li span{white-space:normal}}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  function box(el) {
    if (el.getAttribute("data-nbok")) return; el.setAttribute("data-nbok", "1");
    var spec = el.getAttribute("data-newsbox") || "", dark = el.hasAttribute("data-dark"), tabs = null, cur;
    el.classList.add("nbx"); if (dark) el.classList.add("dark");
    if (spec.indexOf("tabs:") === 0) { tabs = spec.slice(5).split(","); cur = "t:" + tabs[0]; } else cur = spec;
    var head = el.getAttribute("data-title") || (cur.indexOf("c:") === 0 ? T.c : tabs ? T.live : T[cur.slice(2)] || T.live);
    el.innerHTML = (el.hasAttribute("data-nohead") ? "" : '<p class="nbh"><i></i>' + e(head) + '</p>') + (tabs ? '<div class="nbt">' + tabs.map(function (k, i) { return '<button type="button" data-k="' + k + '" aria-pressed="' + (i === 0) + '">' + e(T[k] || k) + '</button>'; }).join("") + '</div>' : "") + '<ul></ul><p class="nbn"></p>';
    var ul = el.querySelector("ul"), nb = el.querySelector(".nbn");
    function load() {
      var q = cur.indexOf("c:") === 0 ? "c=" + cur.slice(2) : "t=" + cur.slice(2);
      fetch("/api/news?" + q + "&l=" + L).then(function (r) { return r.json(); }).then(function (j) {
        var it = (j.items || []).slice(0, +(el.getAttribute("data-n") || 12));
        ul.innerHTML = it.length ? it.map(function (x) { return '<li><a href="' + e(x.u) + '" target="_blank" rel="noopener">' + e(x.t) + '</a><span>' + e(x.s) + (x.d ? " · " + ago(x.d) : "") + '</span></li>'; }).join("") : '<li><small>' + e(T.none) + '</small></li>';
        nb.textContent = T.note + " " + T.at + " " + new Date(Date.parse(j.at) || Date.now()).toLocaleTimeString(L, { hour: "2-digit", minute: "2-digit" });
      }).catch(function () { ul.innerHTML = '<li><small>' + e(T.none) + '</small></li>'; });
    }
    if (tabs) el.querySelector(".nbt").addEventListener("click", function (ev) { var b = ev.target.closest("button"); if (!b) return; cur = "t:" + b.dataset.k; el.querySelectorAll(".nbt button").forEach(function (x) { x.setAttribute("aria-pressed", x === b); }); load(); });
    load(); setInterval(load, 900000);
  }
  function go() { document.querySelectorAll("[data-newsbox]").forEach(box); }
  window.NEWSBOX = box; addEventListener("load", go);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
})();
