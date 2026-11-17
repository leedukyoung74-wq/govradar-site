/* GOV RADAR cinematic hazard clips v2 (2026-11-15)
   Canvas motion graphics in a dark satellite-monitor style: light, particles, depth and a HUD.
   Overrides HZFX.card and adds "cyber". Animates only visible cards; half speed for reduced motion. */
(function () {
  var X = window.HZFX; if (!X) return;
  var NMC = { ko: "사이버 공격", en: "Cyberattack", es: "Ciberataque", fr: "Cyberattaque", ar: "هجوم سيبراني", vi: "Tấn công mạng", id: "Serangan siber" };
  for (var l in X.NM) X.NM[l].cyber = NMC[l] || NMC.en;
  // 2026-11-17: heat wave, cold wave and snow, long power outage (gallery), radioactive fallout (preparedness centre only)
  var NMX = { ko: { heat: "폭염", cold: "한파·대설", outage: "장기 정전", radiation: "핵·방사성 낙진", water: "물 오염" },
    en: { heat: "Heatwave", cold: "Cold wave · heavy snow", outage: "Long power outage", radiation: "Nuclear · radioactive fallout", water: "Water contamination" },
    es: { heat: "Ola de calor", cold: "Ola de frío · nevada", outage: "Apagón prolongado", radiation: "Nuclear · lluvia radiactiva", water: "Contaminación del agua" },
    fr: { heat: "Canicule", cold: "Vague de froid · neige", outage: "Panne de courant prolongée", radiation: "Nucléaire · retombées radioactives", water: "Pollution de l'eau" },
    ar: { heat: "موجة حر", cold: "موجة برد · ثلوج كثيفة", outage: "انقطاع طويل للكهرباء", radiation: "نووي · غبار مشع", water: "تلوث المياه" },
    vi: { heat: "Nắng nóng", cold: "Rét đậm · tuyết lớn", outage: "Mất điện kéo dài", radiation: "Hạt nhân · bụi phóng xạ", water: "Ô nhiễm nguồn nước" },
    id: { heat: "Gelombang panas", cold: "Gelombang dingin · salju lebat", outage: "Pemadaman listrik panjang", radiation: "Nuklir · debu radioaktif", water: "Pencemaran air" } };
  for (l in X.NM) { var nx = NMX[l] || NMX.en; for (var kk in nx) X.NM[l][kk] = nx[kk]; }
  X.G = X.K.concat(["cyber", "heat", "cold", "outage", "water"]);   // gallery list (these have no disaster dataset, so they stay off the data map)
  var CODE = { flood: "FLD", storm: "STM", quake: "EQK", tsunami: "TSU", landslide: "LSD", wildfire: "WLF", fire: "FIR", drought: "DRT", temp: "TMP", volcano: "VOL", impact: "IMP", war: "WAR", ethnic: "ETH", protest: "PRT", riot: "RIO", epidemic: "EPI", cyber: "CYB", heat: "HEA", cold: "CLD", outage: "PWR", radiation: "RAD", water: "WTR" };

  var css = ".hzc-v canvas.hzcv{position:absolute;inset:0;width:100%;height:100%;z-index:4;display:block}" +
    ".hzc-v.v2 .hzc-sw{opacity:.35}.hzc-v.v2 .hzc-rg{opacity:.45}.hzc-v.v2::after{opacity:.5}" +
    ".hzc-v.v2{box-shadow:0 0 0 1px rgba(140,200,255,.12) inset;background:#05090f}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  X.card = function (k, bgId, label, title, meta, now, nowLbl) {
    var map = (bgId && bgId !== "none") ? '<svg class="hzc-bg" viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice"><use href="#' + bgId + '"/></svg>' : "";
    return '<figure class="hzc hz-' + k + '"><div class="hzc-v v2">' + map + '<i class="hzc-sw"></i><i class="hzc-rg"></i><canvas class="hzcv" data-k="' + k + '" aria-hidden="true"></canvas><span class="hzc-tag">' + esc(label) + '</span>' +
      (now ? '<span class="hzc-now">' + esc(nowLbl) + '</span>' : "") + '</div>' +
      ((title || meta) ? '<figcaption>' + (title ? '<b>' + esc(title) + '</b>' : "") + (meta ? '<span>' + esc(meta) + '</span>' : "") + '</figcaption>' : "") + '</figure>';
  };

  /* ---------- helpers ---------- */
  var TAU = Math.PI * 2;
  function R(seed) { var s = seed >>> 0 || 1; return function () { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return ((s >>> 0) % 100000) / 100000; }; }
  function n1(x) { return Math.sin(x) * .5 + Math.sin(x * 2.13 + 1.7) * .3 + Math.sin(x * 4.71 + .3) * .2; }
  function rgba(c, a) { return "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a + ")"; }
  var LOW = 0; function glow(g, c, b) { if (LOW) { g.shadowBlur = 0; return; } g.shadowColor = c; g.shadowBlur = b; }
  function noGlow(g) { g.shadowBlur = 0; }
  function sky(g, w, h, top, bot, a) { var gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, top); gr.addColorStop(1, bot); g.globalAlpha = a == null ? 1 : a; g.fillStyle = gr; g.fillRect(0, 0, w, h); g.globalAlpha = 1; }
  function radial(g, x, y, r, c, a) { var gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, rgba(c, a)); gr.addColorStop(1, rgba(c, 0)); g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2); }
  function skyline(rnd, w, base, n, hmin, hmax) { var b = [], x = 0; while (x < w) { var bw = 10 + rnd() * 18, bh = hmin + rnd() * (hmax - hmin); b.push([x, base - bh, bw - 2, bh, rnd()]); x += bw; } return b; }
  function drawSky(g, B, col, win, t, flick) {
    B.forEach(function (b) { g.fillStyle = col; g.fillRect(b[0], b[1], b[2], b[3]);
      for (var yy = b[1] + 4; yy < b[1] + b[3] - 3; yy += 5) for (var xx = b[0] + 2; xx < b[0] + b[2] - 2; xx += 4) {
        var on = ((xx * 7 + yy * 13 + (b[4] * 100 | 0)) % 5) < 2; if (!on) continue;
        var a = flick ? .55 + .45 * Math.sin(t * 6 + xx + yy) : .7; g.fillStyle = rgba(win, a * .8); g.fillRect(xx, yy, 1.6, 2); } });
  }
  function hud(g, w, h, k, t, accent) {
    g.save(); g.strokeStyle = "rgba(200,230,255,.55)"; g.lineWidth = 1; var L = 10, m = 6;
    [[m, m, 1, 1], [w - m, m, -1, 1], [m, h - m, 1, -1], [w - m, h - m, -1, -1]].forEach(function (c) { g.beginPath(); g.moveTo(c[0], c[1] + L * c[3]); g.lineTo(c[0], c[1]); g.lineTo(c[0] + L * c[2], c[1]); g.stroke(); });
    var s = Math.floor(t) % 3600, tc = "T+" + ("0" + Math.floor(s / 60)).slice(-2) + ":" + ("0" + s % 60).slice(-2) + ":" + ("0" + Math.floor((t % 1) * 30)).slice(-2);
    var sm = w < 240; g.fillStyle = "rgba(0,0,0,.5)"; g.fillRect(8, h - 20, sm ? 48 : 64, 13); if (!sm) g.fillRect(w - 76, h - 20, 68, 13); g.font = "600 " + (sm ? 8 : 9) + "px ui-monospace,Menlo,Consolas,monospace"; g.fillStyle = "rgba(210,235,255,.8)"; g.textAlign = "right"; if (!sm) g.fillText(tc, w - 12, h - 11);
    g.textAlign = "left"; g.fillStyle = accent || "rgba(120,255,200,.85)"; g.fillText("● " + CODE[k] + "-" + (X.G.indexOf(k) + 1 < 10 ? "0" : "") + (X.G.indexOf(k) + 1), 12, h - 11);
    var sy = (t * 40) % (h + 40) - 20; var gr = g.createLinearGradient(0, sy - 18, 0, sy + 2); gr.addColorStop(0, "rgba(140,220,255,0)"); gr.addColorStop(1, "rgba(140,220,255,.06)"); g.fillStyle = gr; g.fillRect(0, sy - 18, w, 20);
    g.restore();
  }
  function flame(g, x, y, s, life, c) { // life 0..1
    var a = (1 - life); var col = life < .25 ? [255, 244, 200] : life < .5 ? [255, 190, 70] : life < .75 ? [255, 110, 30] : [200, 50, 20];
    var gr = g.createRadialGradient(x, y, 0, x, y, s); gr.addColorStop(0, rgba(col, .9 * a)); gr.addColorStop(1, rgba(col, 0)); g.fillStyle = gr; g.beginPath(); g.arc(x, y, s, 0, TAU); g.fill();
  }

  /* ---------- scenes: init(S) once per size, draw(g,S,t,dt) ---------- */
  var SC = {};
  SC.flood = { init: function (S) { var r = S.r; S.B = skyline(r, S.w, S.h * .72, 0, S.h * .12, S.h * .42); S.rain = []; for (var i = 0; i < 140; i++) S.rain.push([r() * S.w, r() * S.h, .6 + r() * .8]); S.deb = []; for (i = 0; i < 6; i++) S.deb.push([r() * S.w, r()]); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h; sky(g, w, h, "rgba(10,22,40,.55)", "rgba(4,10,20,.8)");
      radial(g, w * .7, h * .1, w * .6, [60, 110, 170], .25);
      drawSky(g, S.B, "#0c1a2c", [255, 210, 130], t, true);
      var lv = h * (.6 + .05 * Math.sin(t * .5));
      for (var L = 0; L < 3; L++) { g.beginPath(); g.moveTo(0, h); for (var x = 0; x <= w; x += 4) g.lineTo(x, lv + L * 6 + Math.sin(x * .05 + t * (1.6 - L * .3) + L) * 2.4 + n1(x * .02 + t * .7 + L) * 2); g.lineTo(w, h); g.closePath();
        var gr = g.createLinearGradient(0, lv, 0, h); gr.addColorStop(0, rgba([40, 120, 220], .55 - L * .1)); gr.addColorStop(1, rgba([6, 30, 70], .9)); g.fillStyle = gr; g.fill(); }
      glow(g, "rgba(140,210,255,.9)", 8); g.strokeStyle = "rgba(170,225,255,.8)"; g.lineWidth = 1.2; g.beginPath(); for (x = 0; x <= w; x += 4) { var y = lv + Math.sin(x * .05 + t * 1.6) * 2.4 + n1(x * .02 + t * .7) * 2; x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); noGlow(g);
      g.fillStyle = "rgba(255,210,130,.25)"; S.B.forEach(function (b, i) { if (b[1] < lv) for (var k = 0; k < 3; k++) g.fillRect(b[0] + 3 + Math.sin(t * 2 + i + k) * 2, lv + 6 + k * 7, b[2] * .5, 1); });
      g.fillStyle = "rgba(40,30,20,.9)"; S.deb.forEach(function (d) { d[0] = (d[0] + dt * 12) % (w + 20); g.fillRect(d[0] - 10, lv + 2 + Math.sin(t * 2 + d[1] * 9) * 1.5, 6 + d[1] * 6, 2.5); });
      g.strokeStyle = "rgba(170,205,255,.35)"; g.lineWidth = 1; g.beginPath(); S.rain.forEach(function (p) { p[1] += dt * 260 * p[2]; p[0] -= dt * 60 * p[2]; if (p[1] > h) { p[1] = -10; p[0] = Math.random() * (w + 40); } g.moveTo(p[0], p[1]); g.lineTo(p[0] - 3 * p[2], p[1] + 12 * p[2]); }); g.stroke();
      if (Math.sin(t * .9) > .985) { g.fillStyle = "rgba(200,220,255,.18)"; g.fillRect(0, 0, w, h); } } };

  SC.storm = { init: function (S) { var r = S.r; S.P = []; for (var i = 0; i < 1100; i++) { var rad = 6 + Math.pow(r(), .8) * S.w * .55, arm = Math.floor(r() * 3); S.P.push([arm * TAU / 3 + (r() - .5) * (.5 + rad / S.w), rad, .4 + r() * .6, r()]); } S.bolt = 0; },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, cx = w * .52, cy = h * .5; g.fillStyle = "rgba(3,8,16,.35)"; g.fillRect(0, 0, w, h);
      radial(g, cx, cy, w * .5, [70, 120, 170], .22); g.globalCompositeOperation = "lighter";
      S.P.forEach(function (p) { p[0] += dt * (1.6 / (p[1] * .05 + 1)); var a = p[0] - t * .35 + Math.log(p[1]) * 2.6, x = cx + Math.cos(a) * p[1], y = cy + Math.sin(a) * p[1] * .78;
        var al = Math.min(1, p[1] / 22) * (1 - p[1] / (w * .6)) * .95 * p[2]; if (al <= 0) return; g.fillStyle = p[3] > .92 ? rgba([160, 220, 255], al) : rgba([235, 242, 255], al); var sz = 1 + (1 - p[1] / (w * .6)) * 1.4; g.beginPath(); g.arc(x, y, sz, 0, TAU); g.fill(); });
      for (var cb = 0; cb < 9; cb++) { var ca = (cb % 3) * TAU / 3 - t * .35, cr = 12 + Math.floor(cb / 3) * 16; radial(g, cx + Math.cos(ca + Math.log(cr) * 2.6) * cr, cy + Math.sin(ca + Math.log(cr) * 2.6) * cr * .78, 24, [225, 235, 255], .14); }
      g.globalCompositeOperation = "source-over"; g.fillStyle = "rgba(2,6,14,.95)"; g.beginPath(); g.arc(cx, cy, 5.5, 0, TAU); g.fill();
      glow(g, "rgba(170,220,255,1)", 10); g.strokeStyle = "rgba(200,235,255,.8)"; g.lineWidth = 1; g.beginPath(); g.arc(cx, cy, 7.5, 0, TAU); g.stroke(); noGlow(g);
      S.bolt -= dt; if (S.bolt < -2.2 + Math.random()) { S.bolt = .18; S.bx = cx + (Math.random() - .5) * w * .5; S.by = cy + (Math.random() - .5) * h * .5; }
      if (S.bolt > 0) { glow(g, "rgba(190,210,255,1)", 14); g.strokeStyle = "rgba(235,240,255," + (S.bolt * 5) + ")"; g.lineWidth = 1.4; g.beginPath(); var x = S.bx, y = S.by; g.moveTo(x, y); for (var i = 0; i < 6; i++) { x += (Math.random() - .5) * 14; y += 6; g.lineTo(x, y); } g.stroke(); noGlow(g); radial(g, S.bx, S.by, 40, [180, 200, 255], .35 * S.bolt * 5); } } };

  SC.quake = { init: function (S) { S.D = []; for (var y = 8; y < S.h - 30; y += 9) for (var x = 6; x < S.w; x += 9) S.D.push([x, y]); S.B = skyline(S.r, S.w, S.h - 30, 0, 8, 30); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, ex = w * .42, ey = h * .42; g.fillStyle = "rgba(4,8,14,.55)"; g.fillRect(0, 0, w, h);
      var per = 1.6, ph = (t % per) / per;
      S.D.forEach(function (d) { var dx = d[0] - ex, dy = d[1] - ey, dist = Math.sqrt(dx * dx + dy * dy), wave = Math.exp(-Math.pow((dist - ph * w * .8) / 14, 2)) * (1 - ph);
        var o = wave * 4; g.fillStyle = rgba(wave > .2 ? [255, 170, 80] : [120, 160, 200], .25 + wave * .7); g.fillRect(d[0] + dx / (dist + 1) * o - .7, d[1] + dy / (dist + 1) * o - .7, 1.5 + wave * 1.5, 1.5 + wave * 1.5); });
      for (var k = 0; k < 3; k++) { var p2 = ((t + k * per / 3) % per) / per; glow(g, "rgba(255,150,60,.9)", 10); g.strokeStyle = rgba([255, 160, 70], .7 * (1 - p2)); g.lineWidth = 1.5; g.beginPath(); g.arc(ex, ey, p2 * w * .8, 0, TAU); g.stroke(); } noGlow(g);
      radial(g, ex, ey, 22, [255, 140, 50], .8); g.fillStyle = "#fff4dc"; g.beginPath(); g.arc(ex, ey, 2.2, 0, TAU); g.fill();
      var sh = Math.max(0, 1 - ph * 3) * 2.2; g.save(); g.translate((Math.random() - .5) * sh, 0); drawSky(g, S.B, "#0b1522", [255, 200, 120], t, false); g.restore();
      g.fillStyle = "rgba(0,0,0,.55)"; g.fillRect(0, h - 30, w, 30); glow(g, "rgba(255,160,70,1)", 6); g.strokeStyle = "#ffb15c"; g.lineWidth = 1.2; g.beginPath();
      for (var x = 0; x <= w; x += 2) { var tt = t * 60 - (w - x), env = Math.exp(-Math.pow(((tt / 60) % per) / per * 6 - .6, 2) * 1.5) * 10 + .6; var y = h - 15 + n1(tt * .9) * env; x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); noGlow(g); } };

  SC.tsunami = { init: function (S) { S.coast = []; for (var y = -10; y <= S.h + 10; y += 6) S.coast.push([S.w * .8 + n1(y * .07) * 10 + (y / S.h) * 12, y]); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, ox = w * .1, oy = h * .25; sky(g, w, h, "rgba(4,20,40,.75)", "rgba(2,12,26,.85)");
      g.strokeStyle = "rgba(90,160,220,.12)"; g.lineWidth = 1; for (var y = 4; y < h; y += 7) { g.beginPath(); for (var x = 0; x < w * .82; x += 6) { var yy = y + Math.sin(x * .08 + t * 2 + y) * 1.2; x ? g.lineTo(x, yy) : g.moveTo(x, yy); } g.stroke(); }
      var per = 4, ph = (t % per) / per;
      for (var k = 0; k < 4; k++) { var r = (ph + k * .08) * w * 1.1; if (r <= 0) continue; var a = (1 - k * .22) * (1 - Math.max(0, ph - .75) * 3);
        glow(g, "rgba(120,230,255,1)", 12); g.strokeStyle = rgba(k ? [90, 200, 255] : [230, 255, 255], .85 * a * (k ? .5 : 1)); g.lineWidth = k ? 1 : 2.4; g.beginPath(); g.arc(ox, oy, r, -.35, 1.6); g.stroke(); } noGlow(g);
      radial(g, ox, oy, 20, [120, 220, 255], .6);
      g.beginPath(); g.moveTo(w, -10); S.coast.forEach(function (p) { g.lineTo(p[0], p[1]); }); g.lineTo(w, h + 10); g.closePath(); g.fillStyle = "#1a1712"; g.fill();
      var hit = ph > .6 && ph < .8 ? (1 - Math.abs(ph - .7) * 10) : 0; glow(g, "rgba(200,255,255,1)", 14); g.strokeStyle = rgba([200, 250, 255], .35 + hit * .65); g.lineWidth = 1.5 + hit * 2; g.beginPath(); S.coast.forEach(function (p, i) { i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); }); g.stroke(); noGlow(g);
      for (var i = 0; i < 26; i++) { var p = S.coast[(i * 3) % S.coast.length]; g.fillStyle = "rgba(255,210,130," + (.4 + .4 * Math.sin(t * 3 + i)) + ")"; g.fillRect(p[0] + 4 + (i % 5) * 3, p[1], 1.4, 1.4); } } };

  SC.landslide = { init: function (S) { var r = S.r; S.rk = []; for (var i = 0; i < 26; i++) S.rk.push([r(), r(), 2 + r() * 5, r() * TAU, r()]); S.dust = []; },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h; sky(g, w, h, "rgba(18,22,30,.6)", "rgba(10,10,12,.85)");
      function sy(x) { return h * .12 + (x / w) * h * .78 + Math.sin(x * .03) * 4; }
      g.beginPath(); g.moveTo(0, h); for (var x = 0; x <= w; x += 6) g.lineTo(x, sy(x)); g.lineTo(w, h); g.closePath(); var gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, "#3a2a1c"); gr.addColorStop(1, "#1a120b"); g.fillStyle = gr; g.fill();
      glow(g, "rgba(255,140,60,.8)", 6); g.strokeStyle = "rgba(255,150,70,.6)"; g.lineWidth = 1; g.beginPath(); g.moveTo(w * .05, sy(w * .05) + 4); for (x = w * .05; x < w * .45; x += 6) g.lineTo(x, sy(x) + 4 + n1(x * .2) * 2); g.stroke(); noGlow(g);
      S.rk.forEach(function (k) { k[0] += dt * (.08 + k[4] * .12); if (k[0] > 1.05) { k[0] = -.05; k[1] = Math.random(); } var x = k[0] * w, y = sy(x) - k[2] + Math.abs(Math.sin(t * 6 + k[4] * 9)) * -2; k[3] += dt * 5;
        S.dust.push([x, y, 0]); g.save(); g.translate(x, y); g.rotate(k[3]); g.fillStyle = k[4] > .5 ? "#7a5a3c" : "#5c4430"; g.beginPath(); for (var j = 0; j < 6; j++) { var a = j / 6 * TAU, rr = k[2] * (.75 + ((j * 7 + k[4] * 10) % 3) * .12); g.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); } g.closePath(); g.fill(); g.restore(); });
      if (S.dust.length > 260) S.dust.splice(0, S.dust.length - 260);
      S.dust.forEach(function (d) { d[2] += dt; d[1] -= dt * 6; g.fillStyle = "rgba(160,130,100," + Math.max(0, .14 - d[2] * .07) + ")"; g.beginPath(); g.arc(d[0] - d[2] * 8, d[1], 2 + d[2] * 6, 0, TAU); g.fill(); });
      S.dust = S.dust.filter(function (d) { return d[2] < 2; });
      g.strokeStyle = "rgba(170,200,255,.25)"; g.beginPath(); for (var i = 0; i < 50; i++) { var rx = (i * 53 + t * 140) % w, ry = (i * 37 + t * 260) % h; g.moveTo(rx, ry); g.lineTo(rx - 2, ry + 8); } g.stroke(); } };

  function fireField(S, n) { var a = []; for (var i = 0; i < n; i++) a.push([0, 0, 1, 0, 0]); return a; }
  SC.wildfire = { init: function (S) { var r = S.r; S.trees = []; for (var x = 0; x < S.w; x += 9 + r() * 8) S.trees.push([x, 14 + r() * 22]); S.F = fireField(S, 260); S.E = fireField(S, 70); S.SM = fireField(S, 40); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, hz = h * .74; sky(g, w, h, "rgba(20,8,10,.7)", "rgba(60,18,8,.85)"); radial(g, w * .5, hz, w * .7, [255, 90, 20], .35);
      S.SM.forEach(function (p) { if (p[2] >= 1) { p[0] = Math.random() * w; p[1] = hz; p[2] = Math.random() * .3; p[3] = 10 + Math.random() * 14; } p[2] += dt * .12; p[1] -= dt * 22; p[0] -= dt * 10; g.fillStyle = "rgba(40,30,30," + (.35 * (1 - p[2])) + ")"; g.beginPath(); g.arc(p[0], p[1], p[3] * (1 + p[2] * 2), 0, TAU); g.fill(); });
      g.fillStyle = "#090605"; S.trees.forEach(function (tr) { var x = tr[0], th = tr[1]; g.beginPath(); g.moveTo(x, hz - th); g.lineTo(x - th * .28, hz); g.lineTo(x + th * .28, hz); g.closePath(); g.fill(); }); g.fillRect(0, hz, w, h - hz);
      g.globalCompositeOperation = "lighter";
      S.F.forEach(function (p) { if (p[2] >= 1) { p[0] = Math.random() * w; p[1] = hz + 2; p[2] = Math.random() * .2; p[3] = 3 + Math.random() * 6; p[4] = .6 + Math.random() * .8; } p[2] += dt * .9 * p[4]; p[1] -= dt * 34 * p[4]; p[0] += Math.sin(t * 4 + p[0]) * dt * 10; flame(g, p[0], p[1], p[3] * (1.2 - p[2] * .6), p[2]); });
      S.E.forEach(function (p) { if (p[2] >= 1) { p[0] = Math.random() * w; p[1] = hz; p[2] = 0; p[4] = .5 + Math.random(); } p[2] += dt * .35; p[1] -= dt * 40 * p[4]; p[0] += Math.sin(t * 3 + p[4] * 9) * dt * 20; g.fillStyle = "rgba(255,190,90," + (1 - p[2]) + ")"; g.fillRect(p[0], p[1], 1.4, 1.4); });
      g.globalCompositeOperation = "source-over"; } };

  SC.fire = { init: function (S) { var r = S.r; S.B = skyline(r, S.w, S.h * .86, 0, S.h * .18, S.h * .4); S.F = fireField(S, 150); S.SM = fireField(S, 34); var mid = S.B[Math.floor(S.B.length / 2)]; mid[1] = S.h * .86 - S.h * .58; mid[3] = S.h * .58; mid[2] = 26; S.T = mid; },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, b = S.T, fx = b[0] + b[2] / 2, fy = b[1]; sky(g, w, h, "rgba(10,10,16,.7)", "rgba(30,14,10,.85)"); radial(g, fx, fy + 20, w * .5, [255, 100, 30], .3);
      S.SM.forEach(function (p) { if (p[2] >= 1) { p[0] = fx + (Math.random() - .5) * 14; p[1] = fy; p[2] = Math.random() * .2; p[3] = 6 + Math.random() * 8; } p[2] += dt * .15; p[1] -= dt * 26; p[0] += dt * 14; g.fillStyle = "rgba(50,44,44," + (.4 * (1 - p[2])) + ")"; g.beginPath(); g.arc(p[0], p[1], p[3] * (1 + p[2] * 2.4), 0, TAU); g.fill(); });
      drawSky(g, S.B, "#0b0f18", [255, 200, 120], t, false);
      for (var yy = b[1] + 6; yy < b[1] + b[3] - 6; yy += 8) for (var xx = b[0] + 3; xx < b[0] + b[2] - 3; xx += 6) { var a = .5 + .5 * n1(t * 5 + xx + yy); g.fillStyle = rgba([255, 120 + a * 80 | 0, 40], .5 + a * .5); g.fillRect(xx, yy, 3, 4); }
      g.globalCompositeOperation = "lighter"; S.F.forEach(function (p) { if (p[2] >= 1) { p[0] = b[0] + Math.random() * b[2]; p[1] = b[1] + Math.random() * 10; p[2] = Math.random() * .2; p[3] = 3 + Math.random() * 5; p[4] = .7 + Math.random() * .6; } p[2] += dt * 1.1 * p[4]; p[1] -= dt * 30; p[0] += Math.sin(t * 5 + p[3]) * dt * 8; flame(g, p[0], p[1], p[3] * (1.3 - p[2] * .7), p[2]); }); g.globalCompositeOperation = "source-over";
      var s = Math.sin(t * 9) > 0; radial(g, w * .2, h * .9, 22, s ? [255, 40, 40] : [40, 90, 255], .6); g.fillStyle = "#c0322b"; g.fillRect(w * .16, h * .88, 18, 6); } };

  SC.drought = { init: function (S) { var r = S.r, top = S.h * .52; S.top = top; S.C = []; for (var y = top + 4; y < S.h; y += 10) for (var x = -6; x < S.w + 6; x += 14) S.C.push([x + r() * 8, y + r() * 5]); S.p = r(); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, top = S.top; sky(g, w, h, "rgba(120,70,30,.55)", "rgba(40,20,8,.75)"); radial(g, w * .78, h * .2, w * .5, [255, 190, 90], .55);
      glow(g, "rgba(255,210,120,1)", 30); g.fillStyle = "#ffd67a"; g.beginPath(); g.arc(w * .78, h * .2, 11, 0, TAU); g.fill(); noGlow(g);
      g.save(); g.translate(w * .78, h * .2); g.rotate(t * .1); g.strokeStyle = "rgba(255,220,140,.35)"; for (var i = 0; i < 16; i++) { g.rotate(TAU / 16); g.beginPath(); g.moveTo(16, 0); g.lineTo(26 + Math.sin(t * 2 + i) * 3, 0); g.stroke(); } g.restore();
      var gr = g.createLinearGradient(0, top, 0, h); gr.addColorStop(0, "#8a5e34"); gr.addColorStop(1, "#4a2e16"); g.fillStyle = gr; g.fillRect(0, top, w, h - top);
      g.strokeStyle = "rgba(30,14,4,.85)"; g.lineWidth = 1; S.C.forEach(function (c, i) { g.beginPath(); g.moveTo(c[0], c[1]); g.lineTo(c[0] + 10 + (i % 3), c[1] + ((i * 7) % 5) - 2); g.lineTo(c[0] + 6, c[1] + 9); g.stroke(); });
      g.strokeStyle = "rgba(255,230,180,.08)"; for (var k = 0; k < 8; k++) { var yy = top - ((t * 18 + k * 9) % 60); g.beginPath(); for (var x = 0; x <= w; x += 5) g.lineTo(x, yy + Math.sin(x * .1 + t * 3 + k) * 1.5); g.stroke(); }
      g.strokeStyle = "#2a1a0e"; g.lineWidth = 1.4; g.beginPath(); g.moveTo(w * .25, top + 2); g.quadraticCurveTo(w * .25 + 4, top - 14, w * .25 + 12, top - 10); g.moveTo(w * .25 + 2, top - 6); g.quadraticCurveTo(w * .25 - 8, top - 14, w * .25 - 10, top - 4); g.stroke(); } };

  SC.temp = { init: function (S) { S.c = document.createElement("canvas"); S.c.width = 48; S.c.height = 30; S.cx = S.c.getContext("2d"); S.img = S.cx.createImageData(48, 30); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, d = S.img.data; function pal(v) { var s = [[20, 40, 140], [30, 140, 220], [80, 220, 200], [250, 230, 90], [250, 120, 40], [220, 30, 40]], f = Math.max(0, Math.min(.999, v)) * 5, i = Math.floor(f), u = f - i; return [s[i][0] + (s[i + 1][0] - s[i][0]) * u, s[i][1] + (s[i + 1][1] - s[i][1]) * u, s[i][2] + (s[i + 1][2] - s[i][2]) * u]; }
      for (var y = 0; y < 30; y++) for (var x = 0; x < 48; x++) { var v = .5 + .28 * Math.sin(x * .18 + t * .5) * Math.cos(y * .21 - t * .3) + .22 * n1(x * .11 + y * .07 + t * .4) - (y / 30 - .5) * .35 + .15 * Math.sin(t * .35); var c = pal(v), o = (y * 48 + x) * 4; d[o] = c[0]; d[o + 1] = c[1]; d[o + 2] = c[2]; d[o + 3] = 175; }
      S.cx.putImageData(S.img, 0, 0); g.imageSmoothingEnabled = true; g.drawImage(S.c, 0, 0, w, h);
      g.strokeStyle = "rgba(255,255,255,.12)"; g.lineWidth = 1; for (var k = 1; k < 6; k++) { g.beginPath(); for (x = 0; x <= w; x += 4) { var yy = k * h / 6 + Math.sin(x * .03 + t * .5 + k) * 6; x ? g.lineTo(x, yy) : g.moveTo(x, yy); } g.stroke(); }
      var bx = w - 18, by = 26, bh = h - 60; for (k = 0; k < bh; k++) { var c2 = pal(1 - k / bh); g.fillStyle = rgba(c2.map(Math.round), .95); g.fillRect(bx, by + k, 6, 1); } g.strokeStyle = "rgba(255,255,255,.5)"; g.strokeRect(bx - .5, by - .5, 7, bh + 1);
      var m = by + bh * (.5 - .4 * Math.sin(t * .35)); g.fillStyle = "#fff"; g.beginPath(); g.moveTo(bx - 2, m); g.lineTo(bx - 7, m - 3); g.lineTo(bx - 7, m + 3); g.fill(); } };

  SC.volcano = { init: function (S) { S.L = fireField(S, 50); S.A = fireField(S, 70); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, cx = w * .5, cy = h * .45; sky(g, w, h, "rgba(14,8,12,.7)", "rgba(40,12,6,.85)"); radial(g, cx, cy, w * .45, [255, 80, 20], .35);
      S.A.forEach(function (p) { if (p[2] >= 1) { p[0] = cx + (Math.random() - .5) * 8; p[1] = cy; p[2] = Math.random() * .2; p[3] = 5 + Math.random() * 8; } p[2] += dt * .1; p[1] -= dt * (30 - p[2] * 20); p[0] += dt * (6 + p[2] * 40); g.fillStyle = "rgba(60,52,52," + (.45 * (1 - p[2])) + ")"; g.beginPath(); g.arc(p[0], p[1], p[3] * (1 + p[2] * 3), 0, TAU); g.fill(); });
      g.beginPath(); g.moveTo(w * .1, h); g.lineTo(cx - 12, cy); g.lineTo(cx + 12, cy); g.lineTo(w * .9, h); g.closePath(); var gr = g.createLinearGradient(0, cy, 0, h); gr.addColorStop(0, "#2a1814"); gr.addColorStop(1, "#0c0806"); g.fillStyle = gr; g.fill();
      glow(g, "rgba(255,100,20,1)", 10); g.strokeStyle = "rgba(255," + (110 + 60 * Math.sin(t * 4) | 0) + ",40,.9)"; g.lineWidth = 2; [[-6, .62], [3, .78], [9, .55]].forEach(function (f) { g.beginPath(); g.moveTo(cx + f[0], cy + 1); var x = cx + f[0], y = cy; for (var i = 0; i < 10; i++) { y += (h - cy) * f[1] / 10; x += f[0] * .9 + n1(i + f[0]) * 3; g.lineTo(x, y); } g.stroke(); }); noGlow(g);
      radial(g, cx, cy, 18, [255, 200, 90], .9); g.globalCompositeOperation = "lighter";
      S.L.forEach(function (p) { if (p[2] >= 1) { p[0] = cx; p[1] = cy; p[3] = (Math.random() - .5) * 60; p[4] = -60 - Math.random() * 70; p[2] = 0; } p[2] += dt * .55; p[4] += dt * 110; p[0] += p[3] * dt; p[1] += p[4] * dt; flame(g, p[0], p[1], 3.2, p[2] * .8); }); g.globalCompositeOperation = "source-over"; } };

  SC.impact = { init: function (S) { var r = S.r; S.st = []; for (var i = 0; i < 90; i++) S.st.push([r() * S.w, r() * S.h, r()]); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h; g.fillStyle = "#03050c"; g.fillRect(0, 0, w, h); S.st.forEach(function (s) { g.fillStyle = "rgba(220,230,255," + (.3 + .7 * Math.abs(Math.sin(t * (1 + s[2]) + s[2] * 9))) * (.4 + s[2] * .6) + ")"; g.fillRect(s[0], s[1], s[2] > .8 ? 1.6 : 1, s[2] > .8 ? 1.6 : 1); });
      var ex = w * .5, ey = h * 2.05, er = h * 1.45; var gr = g.createRadialGradient(ex, ey, er * .96, ex, ey, er * 1.08); gr.addColorStop(0, "rgba(40,110,220,.0)"); gr.addColorStop(.45, "rgba(80,170,255,.55)"); gr.addColorStop(1, "rgba(80,170,255,0)"); g.fillStyle = gr; g.beginPath(); g.arc(ex, ey, er * 1.08, 0, TAU); g.fill();
      g.fillStyle = "#06142a"; g.beginPath(); g.arc(ex, ey, er, 0, TAU); g.fill(); g.fillStyle = "rgba(255,200,120,.5)"; for (var i = 0; i < 40; i++) { var a = -Math.PI / 2 + (i / 40 - .5) * 1.1, rr = er - 3 - (i % 4) * 4; g.fillRect(ex + Math.cos(a) * rr, ey + Math.sin(a) * rr, 1.2, 1.2); }
      var per = 5, ph = (t % per) / per, mx = w * (.08 + ph * .5), my = h * (.05 + ph * .62);
      if (ph < .9) { var tg = g.createLinearGradient(mx - 70, my - 55, mx, my); tg.addColorStop(0, "rgba(255,140,60,0)"); tg.addColorStop(1, "rgba(255,200,120,.9)"); g.strokeStyle = tg; g.lineWidth = 3; g.lineCap = "round"; g.beginPath(); g.moveTo(mx - 70, my - 55); g.lineTo(mx, my); g.stroke(); radial(g, mx, my, 14, [255, 230, 190], 1); g.fillStyle = "#fff"; g.beginPath(); g.arc(mx, my, 2.2, 0, TAU); g.fill(); }
      else { var f = (ph - .9) * 10; radial(g, mx, my, 40 + f * 80, [255, 240, 220], 1 - f); g.strokeStyle = "rgba(255,220,180," + (1 - f) + ")"; g.lineWidth = 2; g.beginPath(); g.arc(mx, my, f * 90, 0, TAU); g.stroke(); } } };

  SC.war = { init: function (S) { var w = S.w, h = S.h; S.T = [[w * .62, h * .48], [w * .7, h * .62]]; S.M = [[w * .05, h * .9, 0, 0], [w * .95, h * .85, 1, 1.2], [w * .1, h * .2, 0, 2.3], [w * .92, h * .15, 1, 3.1]]; S.X = []; },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h; g.fillStyle = "rgba(4,8,6,.4)"; g.fillRect(0, 0, w, h); var per = 4;
      S.T.forEach(function (tg, i) { g.save(); g.translate(tg[0], tg[1]); g.rotate(t * (i ? -1 : 1) * .8); g.strokeStyle = "rgba(255,80,60,.8)"; g.lineWidth = 1; g.beginPath(); g.arc(0, 0, 10, 0, TAU); g.stroke(); for (var k = 0; k < 4; k++) { g.rotate(TAU / 4); g.beginPath(); g.moveTo(13, 0); g.lineTo(18, 0); g.stroke(); } g.restore(); });
      S.M.forEach(function (m, i) { var tg = S.T[m[2]], ph = ((t + m[3]) % per) / per, cx = (m[0] + tg[0]) / 2, cy = Math.min(m[1], tg[1]) - h * .45; if (ph > .8) return;
        var u = ph / .8; function P(s) { var a = (1 - s) * (1 - s), b = 2 * (1 - s) * s, c = s * s; return [a * m[0] + b * cx + c * tg[0], a * m[1] + b * cy + c * tg[1]]; }
        glow(g, "rgba(255,120,60,1)", 8); g.strokeStyle = "rgba(255,150,80,.8)"; g.lineWidth = 1.4; g.beginPath(); for (var s = Math.max(0, u - .35); s <= u; s += .02) { var p = P(s); s === Math.max(0, u - .35) ? g.moveTo(p[0], p[1]) : g.lineTo(p[0], p[1]); } g.stroke(); noGlow(g);
        var hd = P(u); radial(g, hd[0], hd[1], 8, [255, 230, 200], .9); if (u > .97 && !m[5]) { m[5] = 1; S.X.push([tg[0], tg[1], 0]); } if (u < .5) m[5] = 0;
        if (i === 1 && u > .55 && u < .6) { radial(g, hd[0], hd[1], 26, [120, 180, 255], .7); } });
      S.X.forEach(function (x) { x[2] += dt; var f = x[2] / 1.2; radial(g, x[0], x[1], 30 + f * 30, [255, 170, 80], (1 - f) * .9); g.strokeStyle = "rgba(255,200,140," + (1 - f) + ")"; g.lineWidth = 1.5; g.beginPath(); g.arc(x[0], x[1], f * 46, 0, TAU); g.stroke(); });
      S.X = S.X.filter(function (x) { return x[2] < 1.2; }); } };

  function crowd(r, n, x0, x1, y0, y1) { var a = []; for (var i = 0; i < n; i++) a.push([x0 + r() * (x1 - x0), y0 + r() * (y1 - y0), r() * TAU, r()]); return a; }
  SC.ethnic = { init: function (S) { var w = S.w, h = S.h; S.A = crowd(S.r, 70, w * .06, w * .42, h * .18, h * .85); S.B = crowd(S.r, 70, w * .58, w * .94, h * .18, h * .85); S.sp = []; },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, mx = w * .5; g.fillStyle = "rgba(4,6,12,.5)"; g.fillRect(0, 0, w, h); radial(g, mx, h * .5, h * .7, [255, 60, 60], .12 + .08 * Math.sin(t * 2));
      glow(g, "rgba(255,90,80,1)", 10); g.strokeStyle = "rgba(255,110,100,.85)"; g.setLineDash([5, 5]); g.lineDashOffset = -t * 20; g.lineWidth = 1.4; g.beginPath(); g.moveTo(mx, 6); g.lineTo(mx, h - 6); g.stroke(); g.setLineDash([]); noGlow(g);
      function side(P, c, dir) { P.forEach(function (p) { p[2] += dt * (1 + p[3]); var push = Math.max(0, Math.sin(t * 1.3 + p[3] * 3)) * 1.6; var x = p[0] + Math.cos(p[2]) * 2 + dir * push * (p[3] > .6 ? 6 : 2), y = p[1] + Math.sin(p[2] * 1.3) * 2;
        if (Math.abs(x - mx) < 10 && Math.random() < .02) S.sp.push([mx, y, 0]); glow(g, rgba(c, 1), 6); g.fillStyle = rgba(c, .9); g.beginPath(); g.arc(x, y, 1.8, 0, TAU); g.fill(); g.beginPath(); g.arc(x, y - 3.5, 1.2, 0, TAU); g.fill(); }); noGlow(g); }
      side(S.A, [255, 190, 80], 1); side(S.B, [110, 170, 255], -1);
      S.sp.forEach(function (s) { s[2] += dt * 2; for (var i = 0; i < 5; i++) { var a = i / 5 * TAU + s[1]; g.strokeStyle = "rgba(255,240,200," + (1 - s[2]) + ")"; g.beginPath(); g.moveTo(s[0], s[1]); g.lineTo(s[0] + Math.cos(a) * s[2] * 10, s[1] + Math.sin(a) * s[2] * 10); g.stroke(); } }); S.sp = S.sp.filter(function (s) { return s[2] < 1; }); } };

  SC.protest = { init: function (S) { var w = S.w, h = S.h; S.sq = [w * .58, h * .48]; S.roads = [[[0, h * .48], S.sq], [[w * .58, 0], S.sq], [[w, h * .7], S.sq], [[w * .2, h], S.sq]]; S.P = []; for (var i = 0; i < 220; i++) S.P.push([Math.floor(S.r() * 4), S.r(), S.r()]); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, sq = S.sq; g.fillStyle = "rgba(6,8,14,.55)"; g.fillRect(0, 0, w, h);
      g.strokeStyle = "rgba(140,170,210,.18)"; g.lineWidth = 9; S.roads.forEach(function (r) { g.beginPath(); g.moveTo(r[0][0], r[0][1]); g.lineTo(r[1][0], r[1][1]); g.stroke(); }); g.lineWidth = 1;
      g.strokeStyle = "rgba(140,170,210,.08)"; for (var x = 0; x < w; x += 22) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); } for (var y = 0; y < h; y += 22) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
      for (var k = 0; k < 3; k++) { var p2 = ((t * .5 + k / 3) % 1); g.strokeStyle = "rgba(255,220,120," + (.6 * (1 - p2)) + ")"; g.beginPath(); g.arc(sq[0], sq[1], 10 + p2 * 50, 0, TAU); g.stroke(); }
      radial(g, sq[0], sq[1], 34, [255, 210, 120], .35);
      S.P.forEach(function (p) { p[1] += dt * (.05 + p[2] * .05); if (p[1] > 1) p[1] = 0; var r = S.roads[p[0]], u = Math.min(1, p[1] * 1.15), x, y;
        if (p[1] < .87) { x = r[0][0] + (r[1][0] - r[0][0]) * u + (p[2] - .5) * 6; y = r[0][1] + (r[1][1] - r[0][1]) * u + (p[2] - .5) * 6; } else { var a = p[2] * TAU + t * .2, rr = 4 + (p[1] - .87) * 140; x = sq[0] + Math.cos(a) * rr; y = sq[1] + Math.sin(a) * rr * .8; }
        g.fillStyle = p[2] > .9 ? "rgba(255,120,90,.95)" : "rgba(255,236,190,.85)"; g.fillRect(x - .8, y - .8, 1.8, 1.8); }); } };

  SC.riot = { init: function (S) { S.C = crowd(S.r, 110, S.w * .05, S.w * .95, S.h * .45, S.h * .95); S.F = fireField(S, 90); S.G = fireField(S, 24); S.spots = [[S.w * .3, S.h * .72], [S.w * .68, S.h * .6]]; },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h; g.fillStyle = "rgba(6,6,10,.55)"; g.fillRect(0, 0, w, h); var on = Math.sin(t * 10) > 0;
      radial(g, w * .1, h * .3, w * .6, on ? [255, 40, 40] : [40, 80, 255], .22); radial(g, w * .9, h * .3, w * .6, on ? [40, 80, 255] : [255, 40, 40], .22);
      S.G.forEach(function (p) { if (p[2] >= 1) { p[0] = w * (.4 + Math.random() * .3); p[1] = h * .55; p[2] = 0; p[3] = 8 + Math.random() * 10; } p[2] += dt * .2; p[0] += dt * 14; p[1] -= dt * 6; g.fillStyle = "rgba(170,175,185," + (.1 * (1 - p[2])) + ")"; g.beginPath(); g.arc(p[0], p[1], p[3] * (1 + p[2] * 1.4), 0, TAU); g.fill(); });
      S.C.forEach(function (p) { p[2] += dt * (2 + p[3] * 3); var x = p[0] + Math.cos(p[2]) * 3, y = p[1] + Math.sin(p[2] * 1.7) * 2; g.fillStyle = "rgba(230,230,240,.75)"; g.beginPath(); g.arc(x, y, 1.6, 0, TAU); g.fill(); g.beginPath(); g.arc(x, y - 3, 1.1, 0, TAU); g.fill(); });
      g.globalCompositeOperation = "lighter"; S.F.forEach(function (p, i) { var sp = S.spots[i % 2]; if (p[2] >= 1) { p[0] = sp[0] + (Math.random() - .5) * 14; p[1] = sp[1]; p[2] = Math.random() * .2; p[3] = 3 + Math.random() * 4; } p[2] += dt * 1.2; p[1] -= dt * 26; flame(g, p[0], p[1], p[3] * (1.3 - p[2] * .7), p[2]); }); g.globalCompositeOperation = "source-over"; } };

  SC.epidemic = { init: function (S) { var r = S.r, w = S.w, h = S.h; S.N = []; for (var i = 0; i < 38; i++) S.N.push([w * (.06 + r() * .88), h * (.1 + r() * .8)]); S.E = []; S.N.forEach(function (a, i) { var d = S.N.map(function (b, j) { return [Math.hypot(a[0] - b[0], a[1] - b[1]), j]; }).sort(function (x, y) { return x[0] - y[0]; }); for (var k = 1; k <= 3; k++) if (d[k][1] > i) S.E.push([i, d[k][1]]); });
      S.at = S.N.map(function (a) { return Math.hypot(a[0] - S.N[0][0], a[1] - S.N[0][1]); }); var mx = Math.max.apply(null, S.at); S.at = S.at.map(function (v) { return v / mx; }); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, per = 9, ph = (t % per) / per * 1.25; g.fillStyle = "rgba(4,8,10,.5)"; g.fillRect(0, 0, w, h);
      S.E.forEach(function (e) { var a = S.N[e[0]], b = S.N[e[1]], ia = S.at[e[0]] < ph, ib = S.at[e[1]] < ph; g.strokeStyle = ia && ib ? "rgba(255,90,80,.45)" : "rgba(120,200,180,.18)"; g.lineWidth = 1; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
        if (ia !== ib) { var src = ia ? a : b, dst = ia ? b : a, u = (t * 1.5) % 1; g.fillStyle = "#ff8a7a"; g.fillRect(src[0] + (dst[0] - src[0]) * u - 1, src[1] + (dst[1] - src[1]) * u - 1, 2.2, 2.2); } });
      S.N.forEach(function (n, i) { var inf = S.at[i] < ph, age = ph - S.at[i]; if (inf) { radial(g, n[0], n[1], 14 + Math.sin(t * 4 + i) * 3, [255, 70, 60], .55); if (age < .06) { g.strokeStyle = "rgba(255,150,130," + (1 - age / .06) + ")"; g.beginPath(); g.arc(n[0], n[1], age / .06 * 22, 0, TAU); g.stroke(); } }
        g.fillStyle = inf ? "#ffd2c8" : "#9fe6d0"; g.beginPath(); g.arc(n[0], n[1], i ? 2 : 3, 0, TAU); g.fill(); }); } };

  SC.cyber = { init: function (S) { var r = S.r, w = S.w, h = S.h; S.tgt = [w * .78, h * .42]; S.N = []; for (var i = 0; i < 26; i++) S.N.push([w * (.05 + r() * .9), h * (.1 + r() * .78)]); S.N.push(S.tgt);
      S.pk = []; for (i = 0; i < 70; i++) S.pk.push([Math.floor(r() * 26), Math.floor(r() * 27), r(), .3 + r() * .7]); S.cols = []; for (i = 0; i < Math.floor(w / 9); i++) S.cols.push([i * 9 + 3, r() * h, .5 + r()]); S.hex = "0123456789ABCDEF"; },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, T = S.tgt, per = 8, ph = (t % per) / per, atk = ph > .35 && ph < .85, ai = atk ? Math.min(1, (ph - .35) * 6) * Math.min(1, (.85 - ph) * 6) : 0;
      g.fillStyle = "rgba(2,6,12,.55)"; g.fillRect(0, 0, w, h);
      g.font = "8px ui-monospace,Menlo,Consolas,monospace"; S.cols.forEach(function (c, i) { c[1] += dt * 24 * c[2]; if (c[1] > h + 40) c[1] = -40; for (var k = 0; k < 6; k++) { var ch = S.hex[(i * 7 + k * 3 + Math.floor(t * 8 * c[2])) % 16]; g.fillStyle = atk ? "rgba(255,80,90," + (.05 + .1 * (k === 0)) + ")" : "rgba(80,255,190," + (.05 + .1 * (k === 0)) + ")"; g.fillText(ch, c[0], c[1] - k * 9); } });
      function arc(a, b, u) { var mx = (a[0] + b[0]) / 2, my = Math.min(a[1], b[1]) - Math.abs(a[0] - b[0]) * .25, s = 1 - u; return [s * s * a[0] + 2 * s * u * mx + u * u * b[0], s * s * a[1] + 2 * s * u * my + u * u * b[1]]; }
      g.strokeStyle = "rgba(90,200,255,.12)"; g.lineWidth = 1; for (var i = 0; i < S.N.length - 1; i += 2) { var a = S.N[i], b = S.N[(i + 5) % S.N.length]; g.beginPath(); for (var u = 0; u <= 1; u += .1) { var p = arc(a, b, u); u ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); } g.stroke(); }
      g.globalCompositeOperation = "lighter";
      S.pk.forEach(function (k, j) { var hostile = atk && j % 3 !== 0; k[2] += dt * k[3] * (hostile ? .9 : .35); if (k[2] > 1) { k[2] = 0; k[0] = Math.floor(Math.random() * 26); k[1] = Math.floor(Math.random() * 27); }
        var a = S.N[k[0]], b = hostile ? T : S.N[k[1]], p = arc(a, b, k[2]), q = arc(a, b, Math.max(0, k[2] - .06)); g.strokeStyle = hostile ? "rgba(255,70,90,.9)" : "rgba(90,220,255,.75)"; g.lineWidth = hostile ? 1.6 : 1.1; g.beginPath(); g.moveTo(q[0], q[1]); g.lineTo(p[0], p[1]); g.stroke(); });
      g.globalCompositeOperation = "source-over";
      S.N.forEach(function (n, i) { if (n === T) return; g.fillStyle = "rgba(150,230,255,.85)"; g.fillRect(n[0] - 1, n[1] - 1, 2, 2); });
      radial(g, T[0], T[1], 36, atk ? [255, 50, 70] : [60, 200, 255], .35 + ai * .4);
      g.save(); g.translate(T[0], T[1]); g.rotate(t * .4); g.strokeStyle = atk ? "rgba(255,110,120," + (.6 + .4 * Math.sin(t * 20)) + ")" : "rgba(120,230,255,.8)"; g.lineWidth = 1.4; glow(g, atk ? "rgba(255,60,80,1)" : "rgba(80,220,255,1)", 10);
      g.beginPath(); for (i = 0; i <= 6; i++) { var a2 = i / 6 * TAU, rr = 15 + ai * 3 * Math.sin(t * 30); g.lineTo(Math.cos(a2) * rr, Math.sin(a2) * rr); } g.stroke(); noGlow(g); g.restore();
      g.fillStyle = atk ? "#ff7c8a" : "#bff2ff"; g.beginPath(); g.arc(T[0], T[1], 3, 0, TAU); g.fill();
      var bw = 54, bx = 12, by = h - 76; g.fillStyle = "rgba(0,0,0,.45)"; g.fillRect(bx - 4, by + 18, bw + 8, 30); g.font = "600 8px ui-monospace,Menlo,Consolas,monospace"; g.fillStyle = atk ? "#ff8a96" : "#7fffd0"; g.fillText(atk ? "TRAFFIC ▲ ANOMALY" : "TRAFFIC NORMAL", bx, by + 28);
      for (i = 0; i < 12; i++) { var v = .25 + .2 * n1(t * 2 + i) + (atk ? .5 * ai * (i / 12) : 0); g.fillStyle = atk && i > 6 ? "rgba(255,90,100,.9)" : "rgba(90,230,200,.8)"; g.fillRect(bx + i * 4.6, by + 44 - v * 14, 3.2, v * 14); }
      if (atk && Math.random() < .18) { var sy = Math.random() * h, sh = 4 + Math.random() * 10, img; try { img = g.getImageData(0, sy * S.dpr, w * S.dpr, sh * S.dpr); g.putImageData(img, (Math.random() - .5) * 14 * S.dpr, sy * S.dpr); } catch (e) {} g.fillStyle = "rgba(255,40,80,.12)"; g.fillRect(0, sy, w, sh); } } };


  /* ---------- 2026-11-17 scenes: heat, cold, outage, radiation ---------- */
  SC.heat = { init: function (S) { var r = S.r; S.B = skyline(r, S.w, S.h * .8, 0, S.h * .14, S.h * .46); S.H = []; for (var i = 0; i < 26; i++) S.H.push([r() * S.w, r(), .4 + r() * .6]); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, cx = w * .72, cy = h * .26, p = .5 + .5 * Math.sin(t * 1.3);
      sky(g, w, h, "rgba(70,24,6,.75)", "rgba(20,6,2,.9)"); radial(g, cx, cy, w * .7, [255, 120, 30], .30 + .08 * p); radial(g, cx, cy, h * .22, [255, 200, 90], .9);
      glow(g, "rgba(255,170,60,.9)", 14); g.fillStyle = "rgba(255,226,150,.95)"; g.beginPath(); g.arc(cx, cy, h * .085 + p * 2, 0, TAU); g.fill(); noGlow(g);
      g.strokeStyle = "rgba(255,190,90,.35)"; g.lineWidth = 2; for (var k = 0; k < 12; k++) { var a = k / 12 * TAU + t * .12, r0 = h * .12, r1 = h * (.17 + .02 * Math.sin(t * 2 + k)); g.beginPath(); g.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); g.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1); g.stroke(); }
      drawSky(g, S.B, "#1c0d07", [255, 200, 120], t, false); g.fillStyle = "rgba(30,12,6,.95)"; g.fillRect(0, h * .8, w, h * .2);
      g.lineWidth = 1.2; S.H.forEach(function (q) { q[1] -= dt * .12 * q[2]; if (q[1] < 0) { q[1] = 1; q[0] = Math.random() * w; } var y0 = h * (.45 + q[1] * .4); g.strokeStyle = rgba([255, 200, 140], .25 * Math.sin(q[1] * Math.PI)); g.beginPath();
        for (var y = 0; y < 28; y += 2) { var xx = q[0] + Math.sin(y * .45 + t * 4 + q[2] * 9) * 3; y ? g.lineTo(xx, y0 - y) : g.moveTo(xx, y0 - y); } g.stroke(); });
      var bx = w * .1, by = h * .2, bh = h * .5, lv = .72 + .12 * Math.sin(t * .6); g.fillStyle = "rgba(255,255,255,.12)"; g.fillRect(bx, by, 8, bh);
      var gr = g.createLinearGradient(0, by + bh, 0, by); gr.addColorStop(0, "rgba(255,200,60,.95)"); gr.addColorStop(1, "rgba(230,40,30,.95)"); g.fillStyle = gr; g.fillRect(bx + 1, by + bh * (1 - lv), 6, bh * lv);
      g.beginPath(); g.arc(bx + 4, by + bh + 8, 9, 0, TAU); g.fillStyle = "rgba(235,60,30,.95)"; g.fill(); } };

  SC.cold = { init: function (S) { var r = S.r; S.B = skyline(r, S.w, S.h * .78, 0, S.h * .1, S.h * .34); S.F = []; for (var i = 0; i < 220; i++) S.F.push([r() * S.w, r() * S.h, .4 + r() * 1.2, r() * TAU]); S.acc = 0; },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, gust = .5 + .5 * Math.sin(t * .7);
      sky(g, w, h, "rgba(10,24,48,.85)", "rgba(30,52,82,.9)"); radial(g, w * .2, h * .15, w * .5, [150, 200, 255], .18);
      drawSky(g, S.B, "#0e1c30", [255, 220, 160], t, false);
      g.fillStyle = "rgba(235,244,255,.9)"; S.B.forEach(function (b) { g.fillRect(b[0], b[1] - 2, b[2], 3); });
      S.acc = Math.min(h * .07, S.acc + dt * 1.2); g.fillStyle = "rgba(225,238,252,.95)"; g.beginPath(); g.moveTo(0, h); for (var x = 0; x <= w; x += 6) g.lineTo(x, h * .78 - S.acc * (.7 + .3 * Math.sin(x * .03))); g.lineTo(w, h); g.fill();
      g.strokeStyle = "rgba(200,225,255,.25)"; g.lineWidth = 1; for (var k = 0; k < 5; k++) { var yy = h * (.2 + k * .12), xo = ((t * 120 * (1 + gust) + k * 90) % (w + 160)) - 160; g.beginPath(); g.moveTo(xo, yy); g.bezierCurveTo(xo + 40, yy - 6, xo + 80, yy + 6, xo + 140, yy); g.stroke(); }
      g.fillStyle = "rgba(255,255,255,.9)"; S.F.forEach(function (f) { f[1] += dt * 26 * f[2]; f[0] += dt * (18 + 50 * gust) * f[2] + Math.sin(t * 2 + f[3]) * .3; if (f[1] > h) { f[1] = -4; f[0] = Math.random() * w - 40; } if (f[0] > w + 4) f[0] = -4; g.globalAlpha = .4 + .5 * (f[2] / 1.6); g.beginPath(); g.arc(f[0], f[1], f[2], 0, TAU); g.fill(); }); g.globalAlpha = 1;
      var cx = w * .86, cy = h * .2, s = h * .07; glow(g, "rgba(170,220,255,.9)", 8); g.strokeStyle = "rgba(210,236,255,.9)"; g.lineWidth = 1.6; for (k = 0; k < 6; k++) { var a = k * TAU / 6 + t * .2; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a) * s, cy + Math.sin(a) * s); g.stroke(); } noGlow(g); } };

  SC.outage = { init: function (S) { var r = S.r; S.B = skyline(r, S.w, S.h * .82, 0, S.h * .16, S.h * .5); S.spark = 0; },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, cyc = (t % 9) / 9, front = cyc < .5 ? cyc * 2 : 1, back = cyc > .75 ? (cyc - .75) * 4 : 0;
      sky(g, w, h, "rgba(4,8,16,.9)", "rgba(10,14,26,.95)");
      S.B.forEach(function (b) { var dark = (b[0] / w) < front && (b[0] / w) >= back; g.fillStyle = dark ? "#05080f" : "#0f1a2c"; g.fillRect(b[0], b[1], b[2], b[3]);
        if (!dark) for (var yy = b[1] + 4; yy < b[1] + b[3] - 3; yy += 5) for (var xx = b[0] + 2; xx < b[0] + b[2] - 2; xx += 4) { if (((xx * 7 + yy * 13 + (b[4] * 100 | 0)) % 5) < 2) { g.fillStyle = "rgba(255,214,140,.6)"; g.fillRect(xx, yy, 1.6, 2); } } });
      var fx = front * w; if (front < 1) { g.strokeStyle = "rgba(140,200,255,.5)"; g.lineWidth = 1; g.beginPath(); g.moveTo(fx, h * .1); g.lineTo(fx, h * .82); g.stroke(); }
      g.strokeStyle = "rgba(160,170,190,.6)"; g.lineWidth = 1.4; var px = [w * .08, w * .38, w * .68, w * .98]; px.forEach(function (x) { g.beginPath(); g.moveTo(x, h * .82); g.lineTo(x - 8, h * .34); g.lineTo(x + 8, h * .34); g.closePath(); g.stroke(); g.beginPath(); g.moveTo(x - 14, h * .37); g.lineTo(x + 14, h * .37); g.stroke(); });
      g.beginPath(); for (var i = 0; i < 3; i++) { g.moveTo(px[i] + 14, h * .37); g.quadraticCurveTo((px[i] + px[i + 1]) / 2, h * .45, px[i + 1] - 14, h * .37); } g.stroke();
      if (Math.sin(t * 5.3) > .96 || (cyc > .02 && cyc < .05)) { var sx = px[1] + 14, sy = h * .37; glow(g, "rgba(150,200,255,1)", 16); g.strokeStyle = "rgba(220,240,255,.95)"; g.lineWidth = 2; g.beginPath(); g.moveTo(sx, sy); for (i = 1; i < 5; i++) g.lineTo(sx + (Math.random() - .5) * 18, sy + i * 6); g.stroke(); noGlow(g); }
      var lx = w * (.3 + .25 * Math.sin(t * .8)), ly = h * .7; var gr = g.createRadialGradient(lx, ly, 0, lx, ly, h * .16); gr.addColorStop(0, "rgba(255,240,200,.35)"); gr.addColorStop(1, "rgba(255,240,200,0)"); g.fillStyle = gr; g.beginPath(); g.moveTo(lx, ly); g.arc(lx, ly, h * .16, -2.1, -1.0); g.closePath(); g.fill();
      g.fillStyle = "rgba(255,248,220,.95)"; g.fillRect(lx - 2, ly - 1, 4, 3); } };

  SC.radiation = { init: function (S) { var r = S.r; S.P = []; for (var i = 0; i < 160; i++) S.P.push([r() * S.w, r() * S.h, .3 + r() * .8]); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, cx = w * .5, base = h * .82;
      sky(g, w, h, "rgba(26,28,16,.85)", "rgba(10,12,8,.95)"); radial(g, w * .5, h * .05, w * .8, [200, 210, 120], .12);
      g.fillStyle = "rgba(210,220,150,.55)"; S.P.forEach(function (p) { p[1] += dt * 14 * p[2]; p[0] += Math.sin(t + p[2] * 9) * .15; if (p[1] > base) { p[1] = -3; p[0] = Math.random() * w; } g.globalAlpha = .25 + .5 * p[2]; g.fillRect(p[0], p[1], 1.6 * p[2] + .6, 1.6 * p[2] + .6); }); g.globalAlpha = 1;
      g.fillStyle = "#1a1e14"; g.fillRect(0, base, w, h - base); g.fillStyle = "#2c3324"; g.fillRect(cx - w * .22, base - h * .36, w * .44, h * .36); g.fillStyle = "#3a4230"; g.fillRect(cx - w * .24, base - h * .38, w * .48, h * .04);
      g.fillStyle = "rgba(255,226,150,.85)"; g.fillRect(cx - w * .05, base - h * .14, w * .1, h * .14); radial(g, cx, base - h * .07, w * .12, [255, 220, 140], .25);
      for (var k = 0; k < 3; k++) { var ph = ((t * .5 + k / 3) % 1); g.strokeStyle = rgba([210, 240, 90], .55 * (1 - ph)); g.lineWidth = 1.5; g.beginPath(); g.arc(w * .14, h * .22, 6 + ph * h * .14, 0, TAU); g.stroke(); }
      g.fillStyle = "rgba(210,240,90,.95)"; g.beginPath(); g.arc(w * .14, h * .22, 4, 0, TAU); g.fill(); } };

  SC.water = { init: function (S) { var r = S.r; S.P = []; for (var i = 0; i < 90; i++) S.P.push([r() * S.w, S.h * (.55 + r() * .4), r(), .3 + r() * .7]); S.B = []; for (i = 0; i < 26; i++) S.B.push([r() * S.w, S.h, .3 + r() * .7]); },
    draw: function (g, S, t, dt) { var w = S.w, h = S.h, wl = h * .52;
      sky(g, w, h, "rgba(8,20,32,.9)", "rgba(10,26,36,.95)"); radial(g, w * .2, h * .1, w * .5, [120, 170, 210], .14);
      g.fillStyle = "#1a2a2e"; g.fillRect(w * .78, h * .18, w * .22, h * .36); g.fillStyle = "#26383c"; g.fillRect(w * .62, h * .44, w * .2, h * .05);
      var gr = g.createLinearGradient(0, wl, 0, h); gr.addColorStop(0, "rgba(40,110,150,.85)"); gr.addColorStop(1, "rgba(8,34,52,.95)"); g.fillStyle = gr; g.beginPath(); g.moveTo(0, h);
      for (var x = 0; x <= w; x += 4) g.lineTo(x, wl + Math.sin(x * .04 + t * 1.4) * 2 + n1(x * .02 + t * .5) * 1.5); g.lineTo(w, h); g.fill();
      var ox = w * .63, oy = h * .49, spread = (t % 12) / 12, pr = w * (.08 + spread * .5);
      var pg = g.createRadialGradient(ox, oy + h * .05, 0, ox, oy + h * .05, pr); pg.addColorStop(0, "rgba(150,120,40,.75)"); pg.addColorStop(.6, "rgba(120,110,50,.35)"); pg.addColorStop(1, "rgba(110,100,60,0)");
      g.fillStyle = pg; g.beginPath(); g.ellipse(ox - pr * .35, oy + h * .12, pr, h * .16 * (.6 + spread), 0, 0, TAU); g.fill();
      g.fillStyle = "rgba(170,140,60,.9)"; for (var k = 0; k < 4; k++) { var yy = oy + ((t * 40 + k * 9) % 22); g.fillRect(ox - 3, yy, 6, 3); }
      S.P.forEach(function (p) { p[0] -= dt * 8 * p[3]; if (p[0] < -4) p[0] = w + 4; g.fillStyle = p[2] < .5 ? "rgba(190,160,80,.55)" : "rgba(220,230,240,.35)"; g.fillRect(p[0], p[1] + Math.sin(t * 2 + p[2] * 9) * 1.5, 2, 2); });
      S.B.forEach(function (b) { b[1] -= dt * 18 * b[2]; if (b[1] < wl) { b[1] = h; b[0] = Math.random() * w; } g.strokeStyle = "rgba(200,230,255,.4)"; g.beginPath(); g.arc(b[0], b[1], 1.6 + b[2] * 1.5, 0, TAU); g.stroke(); });
      var dx = w * .14, dy = h * .24 + ((t * 30) % (h * .22)); glow(g, "rgba(150,210,255,.9)", 8); g.fillStyle = "rgba(170,220,255,.95)"; g.beginPath(); g.moveTo(dx, dy - 7); g.quadraticCurveTo(dx + 6, dy + 2, dx, dy + 5); g.quadraticCurveTo(dx - 6, dy + 2, dx, dy - 7); g.fill(); noGlow(g);
      g.fillStyle = "rgba(200,210,220,.85)"; g.fillRect(dx - 14, h * .16, 28, 6); g.fillRect(dx - 3, h * .16, 6, h * .07);
      var bx = w * .06, by = h * .62; g.strokeStyle = "rgba(255,200,80,.9)"; g.lineWidth = 2; g.beginPath(); g.moveTo(bx, by - 18); g.lineTo(bx + 20, by + 16); g.lineTo(bx - 20, by + 16); g.closePath(); g.stroke(); g.fillStyle = "rgba(255,200,80,.95)"; g.fillRect(bx - 1, by - 6, 2, 12); g.fillRect(bx - 1, by + 9, 2, 3); } };

  /* ---------- runtime ---------- */
  var live = [], RM = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  function setup(cv) {
    var k = cv.getAttribute("data-k"), sc = SC[k]; if (!sc) return null;
    var o = { cv: cv, k: k, sc: sc, S: null, vis: false, t0: (vt || performance.now() / 1000) - 2 - Math.random() * 7, last: 0 };
    o.resize = function () { var r = cv.getBoundingClientRect(); if (!r.width) return false; var dpr = LOW > 1 ? 1 : Math.min(2, window.devicePixelRatio || 1); cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr);
      var seed = 0; for (var i = 0; i < k.length; i++) seed = seed * 31 + k.charCodeAt(i); o.S = { w: r.width, h: r.height, dpr: dpr, r: R(seed + 7) }; sc.init(o.S); o.g = cv.getContext("2d"); return true; };
    return o;
  }
  function frame(o, now, dt) { var g = o.g, S = o.S; if (!S) return; g.setTransform(S.dpr, 0, 0, S.dpr, 0, 0); g.clearRect(0, 0, S.w, S.h); var t = now - o.t0; try { o.sc.draw(g, S, t, dt); } catch (e) {} g.setTransform(S.dpr, 0, 0, S.dpr, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = "source-over"; noGlow(g); hud(g, S.w, S.h, o.k, t, o.k === "cyber" ? "rgba(255,120,140,.9)" : null); }
  var io = "IntersectionObserver" in window ? new IntersectionObserver(function (es) { es.forEach(function (e) { var o = e.target._hz; if (o) o.vis = e.isIntersecting; }); }, { rootMargin: "80px" }) : null;
  function scan() { document.querySelectorAll("canvas.hzcv").forEach(function (cv) { if (cv._hz) return; var o = setup(cv); if (!o) return; cv._hz = o; live.push(o); if (io) io.observe(cv); else o.vis = true; }); }
  /* reduced motion: keep moving, at half speed (stopping looked broken on phones with that setting on).
     Adaptive quality: the loop measures real frame time. On slow phones it drops the glow effect (LOW 1), then
     draws at lower resolution, 20 fps and only the 6 cards nearest the centre of the screen (LOW 2), so the
     motion stays smooth instead of freezing. Fast devices keep full quality. */
  var lastT = 0, vt = 0, SP = RM ? .5 : 1, ema = 0, calm = 0, nextDraw = 0;
  function loop(ms) { var now0 = ms / 1000, raw = now0 - (lastT || now0), dt = Math.min(.05, raw) * SP; lastT = now0; vt = vt ? vt + dt : now0; var now = vt;
    if (raw > 0 && raw < 1) { ema = ema ? ema * .9 + raw * .1 : raw;
      if (ema > .045 && LOW < 2) { calm = 0; LOW++; ema = 1 / 40; live.forEach(function (o) { o.S = null; }); }
      else if (ema < .02 && LOW > 0 && ++calm > 600) { calm = 0; LOW--; live.forEach(function (o) { o.S = null; }); } }
    live = live.filter(function (o) { return document.body.contains(o.cv); });
    if (LOW > 1 && now0 < nextDraw) { requestAnimationFrame(loop); return; } if (LOW > 1) nextDraw = now0 + 1 / 20;
    var vis = live.filter(function (o) { return o.vis; }), cy = innerHeight / 2;
    if (LOW > 1 && vis.length > 6) { vis.forEach(function (o) { var r = o.cv.getBoundingClientRect(); o.dc = Math.abs(r.top + r.height / 2 - cy); }); vis.sort(function (a, b) { return a.dc - b.dc; }); vis = vis.slice(0, 6); }
    vis.forEach(function (o) { var r = o.cv.getBoundingClientRect(); if (!o.S || Math.abs(r.width - o.S.w) > 1) { if (!o.resize()) return; } frame(o, now, LOW > 1 ? dt * 3 : dt); });
    requestAnimationFrame(loop); }
  new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState !== "loading") scan(); else document.addEventListener("DOMContentLoaded", scan);
  requestAnimationFrame(loop);
})();
