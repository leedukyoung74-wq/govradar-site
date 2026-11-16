/* GOV RADAR deadline helper — one rule for every tender list on the site.
   deadline_at with a time and offset (e.g. 2026-11-27T17:00:00Z, 2026-11-23T09:00:00+02:00) is compared with the
   real current time; a notice disappears the minute it closes. A date with no time is kept until that date has ended
   everywhere (23:59:59 at UTC-12) and is labelled "time not given — check the notice", never "open for bids".
   Tested by tests/test_deadline.py (node). */
var GRDL = window.GRDL || (function () {
  var T = {
    ko: ["마감", "시각 미확인 · 원문 확인", "내 시간", "마감됨", "시간 남음", "분 남음"],
    en: ["closes", "time not given · check the notice", "your time", "closed", "h left", "min left"],
    es: ["cierre", "hora no indicada · ver el aviso", "su hora", "cerrado", "h restantes", "min restantes"],
    fr: ["clôture", "heure non indiquée · voir l'avis", "votre heure", "clos", "h restantes", "min restantes"],
    ar: ["الإغلاق", "الوقت غير محدد · راجع الإعلان", "توقيتك", "مغلق", "ساعة متبقية", "دقيقة متبقية"],
    vi: ["đóng", "chưa rõ giờ · xem thông báo", "giờ của bạn", "đã đóng", "giờ còn lại", "phút còn lại"],
    id: ["tutup", "jam tidak disebut · cek pengumuman", "waktu Anda", "ditutup", "jam lagi", "menit lagi"]
  };
  var RX = /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$/;
  function info(at, d, now) {
    now = now == null ? Date.now() : now;
    var m = RX.exec(String(at || ""));
    if (m) {
      var ms = Date.parse(at); if (isNaN(ms)) return { timed: false, ms: null, open: true, date: "", src: "", left: null };
      var off = m[4] === "Z" ? "+00:00" : (m[4].length === 5 ? m[4].slice(0, 3) + ":" + m[4].slice(3) : m[4]);
      return { timed: true, ms: ms, open: now < ms, date: m[1], src: m[1] + " " + m[2] + ":" + m[3] + " (UTC" + off + ")", left: ms - now };
    }
    var dd = /^\d{4}-\d{2}-\d{2}/.exec(String(at || d || ""));
    if (dd) { var e = Date.parse(dd[0] + "T23:59:59-12:00"); if (isNaN(e) || new Date(Date.parse(dd[0] + "T12:00:00Z")).toISOString().slice(0, 10) !== dd[0]) return { timed: false, ms: null, open: true, date: "", src: "", left: null }; return { timed: false, ms: e, open: now < e, date: dd[0], src: dd[0], left: e - now }; }
    return { timed: false, ms: null, open: true, date: "", src: "", left: null };
  }
  function days(i) { return i.left == null ? null : Math.floor(i.left / 864e5); }
  function mine(i, L) {
    if (!i.timed) return "";
    try { return new Intl.DateTimeFormat(L === "ar" ? "ar-u-nu-latn" : L, { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false, timeZoneName: "short" }).format(i.ms); }
    catch (e) { return ""; }
  }
  function label(i, L) {
    var t = T[L] || T.en;
    if (!i.date) return "";
    if (!i.open) return t[3];
    var s = t[0] + " " + i.src;
    if (!i.timed) return s + " · " + t[1];
    var m = mine(i, L); if (m) s += " · " + t[2] + " " + m;
    if (i.left < 864e5) s += " · " + (i.left < 36e5 ? Math.max(1, Math.round(i.left / 6e4)) + t[5] : Math.floor(i.left / 36e5) + t[4]);
    return s;
  }
  return { info: info, days: days, label: label, mine: mine, T: T };
})();
if (typeof window !== "undefined") window.GRDL = GRDL;
