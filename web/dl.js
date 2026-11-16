/* GOV RADAR deadline helper — one rule for every tender list on the site.
   deadline_at with a time and offset (e.g. 2026-11-27T17:00:00Z, 2026-11-23T09:00:00+02:00) is compared with the
   real current time; a notice disappears the minute it closes. A date with no time is kept until that date has ended
   everywhere (23:59:59 at UTC-12) and is labelled "time not given — check the notice", never "open for bids".
   Tested by tests/test_deadline.py (node). */
var GRDL = window.GRDL || (function () {
  var T = {
    ko: ["마감", "시각 미확인 · 원문 확인", "내 시간", "마감됨", "시간 남음", "분 남음", "마감일 미확인 · 원문 확인", "검증 지연 · 마지막 확인", "원문 확인"],
    en: ["closes", "time not given · check the notice", "your time", "closed", "h left", "min left", "deadline unknown · check the notice", "verification delayed · last checked", "check the notice"],
    es: ["cierre", "hora no indicada · ver el aviso", "su hora", "cerrado", "h restantes", "min restantes", "fecha de cierre desconocida · ver el aviso", "verificación pendiente · última comprobación", "ver el aviso"],
    fr: ["clôture", "heure non indiquée · voir l'avis", "votre heure", "clos", "h restantes", "min restantes", "date limite inconnue · voir l'avis", "vérification en attente · dernier contrôle", "voir l'avis"],
    ar: ["الإغلاق", "الوقت غير محدد · راجع الإعلان", "توقيتك", "مغلق", "ساعة متبقية", "دقيقة متبقية", "موعد الإغلاق غير معروف · راجع الإعلان", "التحقق متأخر · آخر تحقق", "راجع الإعلان"],
    vi: ["đóng", "chưa rõ giờ · xem thông báo", "giờ của bạn", "đã đóng", "giờ còn lại", "phút còn lại", "chưa rõ hạn chót · xem thông báo", "xác minh bị chậm · kiểm tra lần cuối", "xem thông báo"],
    id: ["tutup", "jam tidak disebut · cek pengumuman", "waktu Anda", "ditutup", "jam lagi", "menit lagi", "batas waktu tidak diketahui · cek pengumuman", "verifikasi tertunda · terakhir dicek", "cek pengumuman"]
  };
  var RX = /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$/;
  // state: "open" (exact time, still open) | "date_only" (date without time, kept until the day ends at UTC-12)
  //        "closed" | "unknown" (no or impossible deadline). Only open and date_only count as open; unknown never does.
  var UNK = { state: "unknown", timed: false, ms: null, open: false, date: "", src: "", left: null };
  function info(at, d, now) {
    now = now == null ? Date.now() : now;
    var m = RX.exec(String(at || ""));
    if (m) {
      var ms = Date.parse(at); if (isNaN(ms)) return UNK;
      var off = m[4] === "Z" ? "+00:00" : (m[4].length === 5 ? m[4].slice(0, 3) + ":" + m[4].slice(3) : m[4]);
      return { state: now < ms ? "open" : "closed", timed: true, ms: ms, open: now < ms, date: m[1], src: m[1] + " " + m[2] + ":" + m[3] + " (UTC" + off + ")", left: ms - now };
    }
    var dd = /^\d{4}-\d{2}-\d{2}/.exec(String(at || d || ""));
    if (dd) { var e = Date.parse(dd[0] + "T23:59:59-12:00"); if (isNaN(e) || new Date(Date.parse(dd[0] + "T12:00:00Z")).toISOString().slice(0, 10) !== dd[0]) return UNK; return { state: now < e ? "date_only" : "closed", timed: false, ms: e, open: now < e, date: dd[0], src: dd[0], left: e - now }; }
    return UNK;
  }
  function days(i) { return i.left == null ? null : Math.floor(i.left / 864e5); }
  function mine(i, L) {
    if (!i.timed) return "";
    try { return new Intl.DateTimeFormat(L === "ar" ? "ar-u-nu-latn" : L, { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false, timeZoneName: "short" }).format(i.ms); }
    catch (e) { return ""; }
  }
  function label(i, L, stale) {
    var t = T[L] || T.en;
    if (i.state === "unknown") return t[6];
    if (stale) return /^\d{4}-\d\d-\d\dT\d\d:\d\d/.test(String(stale))
      ? t[7] + " " + String(stale).replace("T", " ").slice(0, 16) + " UTC · " + t[8]
      : t[7].split(" · ")[0] + " · " + t[8];   // never checked since it went stale: no time shown, no first-seen date
    if (!i.open) return t[3];
    var s = t[0] + " " + i.src;
    if (!i.timed) return s + " · " + t[1];
    var m = mine(i, L); if (m) s += " · " + t[2] + " " + m;
    if (i.left < 864e5) s += " · " + (i.left < 36e5 ? Math.max(1, Math.round(i.left / 6e4)) + t[5] : Math.floor(i.left / 36e5) + t[4]);
    return s;
  }
  // Re-check every row on the page every 30 s (and when the tab comes back): a row whose deadline has passed is
  // removed while the page stays open; labels (hours/minutes left) refresh. Rows carry data-at / data-dl / data-stale.
  function sweep(root, L) {
    (root || document).querySelectorAll("[data-gr]").forEach(function (li) {
      var i = info(li.dataset.at, li.dataset.dl);
      if (i.state === "closed") { li.remove(); return; }
      var g = li.querySelector(".grl"); if (g) g.textContent = label(i, L, li.dataset.stale);
    });
  }
  var started = false;
  function watch(L) {
    sweep(document, L); if (started) return; started = true;
    setInterval(function () { sweep(document, L); }, 30000);
    document.addEventListener("visibilitychange", function () { if (!document.hidden) sweep(document, L); });
  }
  return { info: info, days: days, label: label, mine: mine, sweep: sweep, watch: watch, T: T };
})();
if (typeof window !== "undefined") window.GRDL = GRDL;
