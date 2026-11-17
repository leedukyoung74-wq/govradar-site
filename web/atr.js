/* GOV RADAR — official alerts in the reader's language, by fixed templates (no AI, no machine translation).
   Only patterns we know exactly are rewritten; anything else stays in the original English.
   ATR.t(alert, L, countryMap) -> text ; ATR.sec(code, L) -> sector label.  2026-11-17 */
(function () {
  var C = {}; // English country name (lower case) -> {ko:..,en:..}
  var ALIAS = { "democratic republic of congo": "congo - kinshasa", "democratic republic of the congo": "congo - kinshasa", "dr congo": "congo - kinshasa", "drc": "congo - kinshasa",
    "republic of congo": "congo - brazzaville", "republic of the congo": "congo - brazzaville", "congo": "congo - brazzaville",
    "bosnia and herzegovina": "bosnia & herzegovina", "czech republic": "czechia", "usa": "united states", "united states of america": "united states", "uk": "united kingdom",
    "ivory coast": "côte d’ivoire", "cote d'ivoire": "côte d’ivoire", "côte d'ivoire": "côte d’ivoire", "turkey": "türkiye", "east timor": "timor-leste", "swaziland": "eswatini",
    "burma": "myanmar", "cape verde": "cabo verde", "macedonia": "north macedonia", "the bahamas": "bahamas", "the gambia": "gambia", "kingdom of saudi arabia": "saudi arabia",
    "lao pdr": "laos", "lao people's democratic republic": "laos", "viet nam": "vietnam", "syrian arab republic": "syria", "iran (islamic republic of)": "iran",
    "republic of korea": "south korea", "korea": "south korea", "russian federation": "russia", "united republic of tanzania": "tanzania", "republic of moldova": "moldova",
    "brunei darussalam": "brunei", "bolivia (plurinational state of)": "bolivia", "venezuela (bolivarian republic of)": "venezuela", "micronesia (federated states of)": "micronesia" };
  function cn(name, L) { var k = String(name || "").trim().toLowerCase(); k = ALIAS[k] || k; var c = C[k]; return c ? (c[L] || c.en) : name; }
  var W = {
    ko: { q: "규모 {m} 지진 · {p} {dir}쪽 {d}km", qn: "규모 {m} 지진 · {p}", wf: "산불 · {r}", rx: "계획된 산불 관리(통제된 불) · {r}", tc: "열대성 저기압 {n}", ts: "열대폭풍 {n}", ast: "소행성 {n} 지구 근접 · 지구-달 거리의 {x}배",
          dr: "가뭄 진행 중: {c}", more: " 외 {n}개국", gd: "{col} 경보 · 열대성 저기압 {n}", col: { red: "적색", orange: "주황색", green: "녹색" }, who: "{dz} · {c}", sep: "·" },
    en: null,
    es: { q: "Sismo de magnitud {m} · a {d} km al {dir} de {p}", qn: "Sismo de magnitud {m} · {p}", wf: "Incendio forestal · {r}", rx: "Quema prescrita · {r}", tc: "Ciclón tropical {n}", ts: "Tormenta tropical {n}", ast: "Asteroide {n} cerca de la Tierra · {x} veces la distancia Tierra-Luna",
          dr: "Sequía en curso: {c}", more: " y {n} países más", gd: "Alerta {col} · ciclón tropical {n}", col: { red: "roja", orange: "naranja", green: "verde" }, who: "{dz} · {c}", sep: "," },
    fr: { q: "Séisme de magnitude {m} · à {d} km au {dir} de {p}", qn: "Séisme de magnitude {m} · {p}", wf: "Feu de forêt · {r}", rx: "Brûlage dirigé · {r}", tc: "Cyclone tropical {n}", ts: "Tempête tropicale {n}", ast: "Astéroïde {n} près de la Terre · {x} fois la distance Terre-Lune",
          dr: "Sécheresse en cours : {c}", more: " et {n} autres pays", gd: "Alerte {col} · cyclone tropical {n}", col: { red: "rouge", orange: "orange", green: "verte" }, who: "{dz} · {c}", sep: "," },
    ar: { q: "زلزال بقوة {m} · على بعد {d} كم من {p}", qn: "زلزال بقوة {m} · {p}", wf: "حريق غابات · {r}", rx: "حرق مخطط ومراقب · {r}", tc: "إعصار مداري {n}", ts: "عاصفة مدارية {n}", ast: "الكويكب {n} يقترب من الأرض · {x} ضعف المسافة بين الأرض والقمر",
          dr: "جفاف مستمر: {c}", more: " و{n} دول أخرى", gd: "تنبيه {col} · إعصار مداري {n}", col: { red: "أحمر", orange: "برتقالي", green: "أخضر" }, who: "{dz} · {c}", sep: "،" },
    vi: { q: "Động đất {m} độ · cách {p} {d} km", qn: "Động đất {m} độ · {p}", wf: "Cháy rừng · {r}", rx: "Đốt có kiểm soát · {r}", tc: "Xoáy thuận nhiệt đới {n}", ts: "Bão nhiệt đới {n}", ast: "Tiểu hành tinh {n} đến gần Trái Đất · gấp {x} lần khoảng cách Trái Đất–Mặt Trăng",
          dr: "Hạn hán đang diễn ra: {c}", more: " và {n} nước khác", gd: "Cảnh báo {col} · xoáy thuận nhiệt đới {n}", col: { red: "đỏ", orange: "cam", green: "xanh" }, who: "{dz} · {c}", sep: "," },
    id: { q: "Gempa magnitudo {m} · {d} km dari {p}", qn: "Gempa magnitudo {m} · {p}", wf: "Kebakaran hutan · {r}", rx: "Pembakaran terkendali · {r}", tc: "Siklon tropis {n}", ts: "Badai tropis {n}", ast: "Asteroid {n} mendekati Bumi · {x} kali jarak Bumi–Bulan",
          dr: "Kekeringan berlangsung: {c}", more: " dan {n} negara lain", gd: "Peringatan {col} · siklon tropis {n}", col: { red: "merah", orange: "oranye", green: "hijau" }, who: "{dz} · {c}", sep: "," }
  };
  var DIR = { ko: { N: "북", E: "동", S: "남", W: "서" }, es: { N: "N", E: "E", S: "S", W: "O" }, fr: { N: "N", E: "E", S: "S", W: "O" } };
  // WHO disease names (only common ones; others stay in English)
  var DZ = [
    [/middle east respiratory syndrome|\bMERS\b/i, { ko: "중동호흡기증후군(MERS)", es: "Síndrome respiratorio de Oriente Medio (MERS)", fr: "Syndrome respiratoire du Moyen-Orient (MERS)", ar: "متلازمة الشرق الأوسط التنفسية (ميرس)", vi: "Hội chứng hô hấp Trung Đông (MERS)", id: "Sindrom pernapasan Timur Tengah (MERS)" }],
    [/ebola/i, { ko: "에볼라", es: "Ébola", fr: "Ebola", ar: "إيبولا", vi: "Ebola", id: "Ebola" }],
    [/marburg/i, { ko: "마버그열", es: "Marburgo", fr: "Marburg", ar: "ماربورغ", vi: "Marburg", id: "Marburg" }],
    [/yellow fever/i, { ko: "황열", es: "Fiebre amarilla", fr: "Fièvre jaune", ar: "الحمى الصفراء", vi: "Sốt vàng", id: "Demam kuning" }],
    [/cholera/i, { ko: "콜레라", es: "Cólera", fr: "Choléra", ar: "الكوليرا", vi: "Dịch tả", id: "Kolera" }],
    [/mpox|monkeypox/i, { ko: "엠폭스", es: "Mpox", fr: "Mpox", ar: "جدري القردة", vi: "Mpox", id: "Mpox" }],
    [/dengue/i, { ko: "뎅기열", es: "Dengue", fr: "Dengue", ar: "حمى الضنك", vi: "Sốt xuất huyết", id: "Demam berdarah" }],
    [/avian influenza|bird flu|influenza a\(h5/i, { ko: "조류인플루엔자", es: "Influenza aviar", fr: "Grippe aviaire", ar: "إنفلونزا الطيور", vi: "Cúm gia cầm", id: "Flu burung" }],
    [/polio/i, { ko: "소아마비(폴리오)", es: "Poliomielitis", fr: "Poliomyélite", ar: "شلل الأطفال", vi: "Bại liệt", id: "Polio" }],
    [/measles/i, { ko: "홍역", es: "Sarampión", fr: "Rougeole", ar: "الحصبة", vi: "Sởi", id: "Campak" }],
    [/nipah/i, { ko: "니파바이러스", es: "Nipah", fr: "Nipah", ar: "نيباه", vi: "Nipah", id: "Nipah" }],
    [/plague/i, { ko: "페스트", es: "Peste", fr: "Peste", ar: "الطاعون", vi: "Dịch hạch", id: "Pes" }],
    [/lassa/i, { ko: "라싸열", es: "Fiebre de Lassa", fr: "Fièvre de Lassa", ar: "حمى لاسا", vi: "Sốt Lassa", id: "Demam Lassa" }],
    [/chikungunya/i, { ko: "치쿤구니야", es: "Chikungunya", fr: "Chikungunya", ar: "شيكونغونيا", vi: "Chikungunya", id: "Chikungunya" }],
    [/meningitis|meningococcal/i, { ko: "수막구균 감염증", es: "Meningitis", fr: "Méningite", ar: "التهاب السحايا", vi: "Viêm màng não", id: "Meningitis" }]
  ];
  var REG = { "who african region": { ko: "WHO 아프리카 지역", es: "Región de África de la OMS", fr: "Région africaine de l'OMS", ar: "إقليم أفريقيا لمنظمة الصحة العالمية", vi: "Khu vực châu Phi của WHO", id: "Kawasan Afrika WHO" },
    "global": { ko: "전 세계", es: "Mundial", fr: "Mondial", ar: "عالميًا", vi: "Toàn cầu", id: "Global" } };
  function f(s, o) { return s.replace(/\{(\w+)\}/g, function (m, k) { return o[k] == null ? "" : o[k]; }); }
  function place(p, L) { var i = p.lastIndexOf(", "); if (i < 0) return cn(p, L); var c = cn(p.slice(i + 2), L), q = p.slice(0, i); return L === "ko" ? c + " " + q : q + ", " + c; }
  function list(s, L, T) { var a = s.replace(/,\s*$/, "").split(/,\s*/).filter(Boolean), sep = T.sep === "·" ? "·" : T.sep + " "; var shown = a.slice(0, 6).map(function (x) { return cn(x, L); }).join(sep);
    return shown + (a.length > 6 ? f(T.more, { n: a.length - 6 }) : ""); }
  function t(a, L) {
    var s = String(a && a.t || "").replace(/&amp;/g, "&"), T = W[L]; if (!T) return s; var m;
    if ((m = s.match(/^M\s?([\d.]+)\s+(\d+)\s?km\s+([NSEW]{1,3})\s+of\s+(.+)$/))) {
      var dir = DIR[L] ? m[3].split("").map(function (c) { return DIR[L][c]; }).join("") : m[3];
      return f(T.q, { m: m[1], d: m[2], dir: dir, p: place(m[4], L) }); }
    if ((m = s.match(/^M\s?([\d.]+)\s+-?\s*(.+)$/))) return f(T.qn, { m: m[1], p: place(m[2], L) });
    if ((m = s.match(/^Wildfires?\s+(.+)$/i))) return f(T.wf, { r: m[1] });
    if ((m = s.match(/^Prescribed Fire\s+(.+)$/i))) return f(T.rx, { r: m[1] });
    if ((m = s.match(/^Tropical Cyclone\s+(.+)$/i))) return f(T.tc, { n: m[1] });
    if ((m = s.match(/^Tropical Storm\s+(.+)$/i))) return f(T.ts, { n: m[1] });
    if ((m = s.match(/^(\S+(?:\s\S+)?)\s+[—-]\s+([\d.]+)\s*LD$/))) return f(T.ast, { n: m[1], x: m[2] });
    if ((m = s.match(/^Drought is on ?going in\s+(.+)$/i))) return f(T.dr, { c: list(m[1], L, T) });
    if ((m = s.match(/^(Red|Orange|Green) (?:notification|alert) for tropical cyclone\s+([A-Z0-9-]+)/i))) return f(T.gd, { col: T.col[m[1].toLowerCase()], n: m[2] });
    if (a.k === "epidemic" || a.src === "WHO") {
      var dz = null; for (var i = 0; i < DZ.length; i++) if (DZ[i][0].test(s)) { dz = DZ[i][1][L]; break; }
      var mm = s.match(/^(.*?)\s*(?:–|-|,)\s*(.+)$/); if (dz && mm) { var rest = mm[2].trim(), r = REG[rest.toLowerCase()];
        return f(T.who, { dz: dz, c: r ? r[L] : list(rest.replace(/\s+and\s+/g, ", "), L, T) }); }
    }
    return s; }
  var SEC = { infra: { ko: "인프라·건설", en: "Infrastructure", es: "Infraestructura", fr: "Infrastructures", ar: "البنية التحتية", vi: "Hạ tầng", id: "Infrastruktur" },
    digital: { ko: "디지털·IT", en: "Digital and IT", es: "Digital y TI", fr: "Numérique et IT", ar: "الرقمنة وتقنية المعلومات", vi: "Số hóa, CNTT", id: "Digital dan TI" },
    energy: { ko: "에너지", en: "Energy", es: "Energía", fr: "Énergie", ar: "الطاقة", vi: "Năng lượng", id: "Energi" },
    health: { ko: "보건·의료", en: "Health", es: "Salud", fr: "Santé", ar: "الصحة", vi: "Y tế", id: "Kesehatan" },
    edu: { ko: "교육", en: "Education", es: "Educación", fr: "Éducation", ar: "التعليم", vi: "Giáo dục", id: "Pendidikan" },
    water: { ko: "물·환경", en: "Water and environment", es: "Agua y medio ambiente", fr: "Eau et environnement", ar: "المياه والبيئة", vi: "Nước, môi trường", id: "Air dan lingkungan" },
    trade: { ko: "무역·물류", en: "Trade and logistics", es: "Comercio y logística", fr: "Commerce et logistique", ar: "التجارة والخدمات اللوجستية", vi: "Thương mại, logistics", id: "Perdagangan dan logistik" } };
  function sec(c, L) { var x = SEC[c]; return x ? (x[L] || x.en) : ""; }
  function load(cb) { if (Object.keys(C).length) return cb();
    fetch("/data/countries.json").then(function (r) { return r.json(); }).then(function (d) { d.forEach(function (x) { if (x.names && x.names.en) C[x.names.en.toLowerCase()] = x.names; }); cb(); }).catch(function () { cb(); }); }
  window.ATR = { t: t, sec: sec, load: load, cn: cn };
})();
