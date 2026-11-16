/* GOV RADAR · cyx.js — motion scenes for "what can be attacked remotely" (cyber page).
   <canvas class="cyx" data-k="plane|ship|car|grid|solar|water|med|train|sat|crane|iot|phone">.
   Animates only visible canvases; half speed when the OS asks for reduced motion. No text in the drawings
   except codes, so every language can use them. */
(function () {
  "use strict";
  var TAU = Math.PI * 2, RED = "#ff5d6c", CY = "#5fd8ff", GRN = "#59d6a4", AMB = "#f2b24a", INK = "#eef3fa", DIM = "rgba(195,206,220,.35)";
  function cyc(t, p) { return (t % p) / p; }
  function ease(x) { return x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x); }
  function ring(g, x, y, r, c, a, lw) { g.globalAlpha = a; g.strokeStyle = c; g.lineWidth = lw || 1.4; g.beginPath(); g.arc(x, y, r, 0, TAU); g.stroke(); g.globalAlpha = 1; }
  function dot(g, x, y, r, c, a) { g.globalAlpha = a == null ? 1 : a; g.fillStyle = c; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); g.globalAlpha = 1; }
  function glow(g, x, y, r, c, a) { var gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, c); gr.addColorStop(1, "rgba(0,0,0,0)"); g.globalAlpha = a; g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2); g.globalAlpha = 1; }
  function line(g, x1, y1, x2, y2, c, a, lw, dash) { g.globalAlpha = a; g.strokeStyle = c; g.lineWidth = lw || 1; if (dash) g.setLineDash(dash); g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke(); g.setLineDash([]); g.globalAlpha = 1; }
  function packets(g, x1, y1, x2, y2, t, c, n, sp) { for (var i = 0; i < n; i++) { var u = cyc(t * (sp || .6) + i / n, 1); dot(g, x1 + (x2 - x1) * u, y1 + (y2 - y1) * u, 1.8, c, Math.sin(u * Math.PI)); } }
  function bg(g, w, h, top, bot) {
    var gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, top || "#081222"); gr.addColorStop(1, bot || "#03060c"); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.globalAlpha = .07; g.strokeStyle = "#7fb6ff"; g.lineWidth = 1; var s = 22; g.beginPath();
    for (var x = 0; x < w; x += s) { g.moveTo(x + .5, 0); g.lineTo(x + .5, h); } for (var y = 0; y < h; y += s) { g.moveTo(0, y + .5); g.lineTo(w, y + .5); } g.stroke(); g.globalAlpha = 1;
  }
  function attacker(g, x, y, t, s) { // hooded node: red pulsing diamond with rings
    s = s || 1; for (var i = 0; i < 3; i++) ring(g, x, y, (6 + cyc(t + i / 3, 1) * 26) * s, RED, (1 - cyc(t + i / 3, 1)) * .7);
    g.fillStyle = RED; g.beginPath(); g.moveTo(x, y - 6 * s); g.lineTo(x + 6 * s, y); g.lineTo(x, y + 6 * s); g.lineTo(x - 6 * s, y); g.closePath(); g.fill(); glow(g, x, y, 22 * s, "rgba(255,93,108,.6)", .7);
  }
  function hud(g, w, h, code, t, atk) {
    g.font = "600 9px ui-monospace,Menlo,Consolas,monospace"; g.textBaseline = "alphabetic";
    g.fillStyle = "rgba(0,0,0,.5)"; g.fillRect(8, h - 22, g.measureText(code).width + 26, 15);
    dot(g, 15, h - 14.5, 3, atk ? RED : GRN, .6 + .4 * Math.sin(t * 6)); g.fillStyle = atk ? "#ff9aa5" : "#9fffd6"; g.fillText(code, 22, h - 11);
    var s = Math.floor(t), tc = "T+" + ("0" + Math.floor(s / 60) % 60).slice(-2) + ":" + ("0" + s % 60).slice(-2) + ":" + ("0" + Math.floor((t % 1) * 30)).slice(-2);
    if (w > 240) { var tw = g.measureText(tc).width; g.fillStyle = "rgba(0,0,0,.5)"; g.fillRect(w - tw - 18, h - 22, tw + 10, 15); g.fillStyle = "rgba(220,232,245,.85)"; g.fillText(tc, w - tw - 13, h - 11); }
    g.strokeStyle = "rgba(95,216,255,.45)"; g.lineWidth = 1.2; var c = 10;
    [[6, 6, 1, 1], [w - 6, 6, -1, 1], [6, h - 28, 1, -1], [w - 6, h - 28, -1, -1]].forEach(function (k) { g.beginPath(); g.moveTo(k[0], k[1] + c * k[3]); g.lineTo(k[0], k[1]); g.lineTo(k[0] + c * k[2], k[1]); g.stroke(); });
  }
  function scanline(g, w, h, t) { var y = cyc(t, 4) * h; var gr = g.createLinearGradient(0, y - 30, 0, y); gr.addColorStop(0, "rgba(95,216,255,0)"); gr.addColorStop(1, "rgba(95,216,255,.08)"); g.fillStyle = gr; g.fillRect(0, y - 30, w, 30); }

  // ── shapes
  function planeShape(g, x, y, s, ang, fill, stroke) {
    g.save(); g.translate(x, y); g.rotate(ang || 0); g.scale(s, s); g.beginPath();
    g.moveTo(22, 0); g.lineTo(14, -2.2); g.lineTo(2, -2.4); g.lineTo(-6, -16); g.lineTo(-10, -16); g.lineTo(-5, -2.4); g.lineTo(-14, -2.2); g.lineTo(-19, -8); g.lineTo(-22, -8); g.lineTo(-19, 0);
    g.lineTo(-22, 8); g.lineTo(-19, 8); g.lineTo(-14, 2.2); g.lineTo(-5, 2.4); g.lineTo(-10, 16); g.lineTo(-6, 16); g.lineTo(2, 2.4); g.lineTo(14, 2.2); g.closePath();
    if (fill) { g.fillStyle = fill; g.fill(); } if (stroke) { g.strokeStyle = stroke; g.lineWidth = 1.2 / s; g.setLineDash([3 / s, 2 / s]); g.stroke(); g.setLineDash([]); } g.restore();
  }
  function shipShape(g, x, y, s, c) {
    g.save(); g.translate(x, y); g.scale(s, s); g.fillStyle = c; g.beginPath(); g.moveTo(-34, -4); g.lineTo(30, -4); g.lineTo(38, -12); g.lineTo(36, 4); g.lineTo(-30, 4); g.closePath(); g.fill();
    g.fillRect(-26, -12, 10, 8); g.fillRect(16, -16, 8, 12); // tanks / bridge
    g.beginPath(); g.arc(-4, -6, 7, Math.PI, 0); g.arc(8, -6, 7, Math.PI, 0); g.fill(); g.restore();
  }
  function satShape(g, x, y, s, ang) {
    g.save(); g.translate(x, y); g.rotate(ang); g.scale(s, s); g.fillStyle = "#c3cedc"; g.fillRect(-4, -4, 8, 8);
    g.fillStyle = "#2c6ea8"; g.fillRect(-18, -3, 12, 6); g.fillRect(6, -3, 12, 6); g.strokeStyle = "#7fb6ff"; g.lineWidth = .6;
    for (var i = -16; i < -6; i += 3) { g.beginPath(); g.moveTo(i, -3); g.lineTo(i, 3); g.stroke(); } for (i = 8; i < 18; i += 3) { g.beginPath(); g.moveTo(i, -3); g.lineTo(i, 3); g.stroke(); } g.restore();
  }
  function tower(g, x, y, h, c) { g.strokeStyle = c; g.lineWidth = 1.3; g.beginPath(); g.moveTo(x - 8, y); g.lineTo(x, y - h); g.lineTo(x + 8, y); g.moveTo(x - 6, y - h * .25); g.lineTo(x + 6, y - h * .25); g.moveTo(x - 4, y - h * .55); g.lineTo(x + 4, y - h * .55); g.moveTo(x - 11, y - h * .8); g.lineTo(x + 11, y - h * .8); g.moveTo(x - 6, y - h * .25); g.lineTo(x + 4, y - h * .55); g.moveTo(x + 6, y - h * .25); g.lineTo(x - 4, y - h * .55); g.stroke(); }
  function house(g, x, y, s, lit) { g.fillStyle = "#0f1a2a"; g.beginPath(); g.moveTo(x - 9 * s, y); g.lineTo(x - 9 * s, y - 10 * s); g.lineTo(x, y - 17 * s); g.lineTo(x + 9 * s, y - 10 * s); g.lineTo(x + 9 * s, y); g.closePath(); g.fill(); g.strokeStyle = "rgba(127,182,255,.35)"; g.lineWidth = 1; g.stroke(); if (lit > 0) { g.globalAlpha = lit; g.fillStyle = "#ffd47a"; g.fillRect(x - 5 * s, y - 8 * s, 4 * s, 4 * s); g.fillRect(x + 1 * s, y - 8 * s, 4 * s, 4 * s); glow(g, x, y - 6 * s, 14 * s, "rgba(255,212,122,.5)", lit * .6); g.globalAlpha = 1; } }
  function camera(g, x, y, s, c) { g.fillStyle = c; g.save(); g.translate(x, y); g.scale(s, s); g.fillRect(-7, -4, 12, 8); g.beginPath(); g.moveTo(5, -2); g.lineTo(9, -4); g.lineTo(9, 4); g.lineTo(5, 2); g.fill(); g.fillRect(-2, 4, 2, 4); g.restore(); }
  function server(g, x, y, w2, h2, hot) { g.fillStyle = "#101c2c"; g.fillRect(x - w2 / 2, y - h2 / 2, w2, h2); g.strokeStyle = hot ? RED : "rgba(127,182,255,.6)"; g.lineWidth = 1.2; g.strokeRect(x - w2 / 2, y - h2 / 2, w2, h2); for (var i = 0; i < 3; i++) { var yy = y - h2 / 2 + 6 + i * (h2 - 8) / 3; line(g, x - w2 / 2 + 4, yy, x + w2 / 2 - 10, yy, "rgba(127,182,255,.4)", 1); dot(g, x + w2 / 2 - 6, yy, 1.6, hot ? RED : GRN, .9); } }

  // ── scenes: draw(g, w, h, t) returns true while "under attack"
  var S = {};
  S.plane = function (g, w, h, t) {
    bg(g, w, h, "#0a1830", "#04070e");
    for (var i = 0; i < 3; i++) { var sx = w * (.2 + i * .3), sy = 18 + (i % 2) * 8; satShape(g, sx, sy, .8, .3); }
    var z = Math.max(1, w / 330), u = cyc(t, 12), px = -40 + (w + 80) * u, py = h * .48 + Math.sin(u * TAU) * 10;
    var ph = cyc(t, 12), atk = ph > .3 && ph < .85, k = atk ? ease((ph - .3) / .15) * (1 - ease((ph - .7) / .15)) : 0;
    for (i = 0; i < 3; i++) line(g, w * (.2 + i * .3), 22, px, py, CY, .25 + .2 * Math.sin(t * 3 + i), 1, [2, 4]);
    var jx = w * .62, jy = h - 34; attacker(g, jx, jy, t * .9, 1); if (atk) for (i = 0; i < 4; i++) ring(g, jx, jy, 10 + cyc(t * .7 + i / 4, 1) * w * .5, RED, (1 - cyc(t * .7 + i / 4, 1)) * .35 * k, 1.2);
    // true track
    g.globalAlpha = .35; g.strokeStyle = CY; g.setLineDash([4, 5]); g.beginPath(); for (var x = 0; x <= px; x += 6) { var uu = (x + 40) / (w + 80); g.lineTo(x, h * .48 + Math.sin(uu * TAU) * 10); } g.stroke(); g.setLineDash([]); g.globalAlpha = 1;
    planeShape(g, px, py, .9 * z, Math.cos(u * TAU) * .12, INK); glow(g, px, py, 30 * z, "rgba(95,216,255,.25)", .6);
    if (k > .02) { var gx = px + 30 * k * z, gy = py + 44 * k * z; planeShape(g, gx, gy, .9 * z, Math.cos(u * TAU) * .12, null, "rgba(255,93,108," + (.9 * k) + ")"); line(g, px, py, gx, gy, RED, .6 * k, 1, [2, 3]); glow(g, gx, gy, 26, "rgba(255,93,108,.5)", k * .6); }
    scanline(g, w, h, t); return atk;
  };
  S.ship = function (g, w, h, t) {
    bg(g, w, h, "#071526", "#020509"); var sea = h * .58;
    for (var r = 0; r < 7; r++) { g.globalAlpha = .18 + r * .03; g.strokeStyle = "#2c6ea8"; g.beginPath(); for (var x = 0; x <= w; x += 8) g.lineTo(x, sea + r * 9 + Math.sin(x * .05 + t * 1.5 + r) * 2); g.stroke(); } g.globalAlpha = 1;
    satShape(g, w * .78, 20, .8, -.2); var sx = w * .38 + Math.sin(t * .3) * 8, sy = sea - 2 + Math.sin(t * 1.4) * 1.5;
    var ph = cyc(t, 10), atk = ph > .35, k = atk ? ease((ph - .35) / .2) : 0;
    line(g, w * .78, 24, sx, sy - 14, CY, .35 * (1 - k * .8), 1, [2, 4]);
    for (var i = 0; i < 10; i++) dot(g, sx - 40 - i * 14, sea + 14 + Math.sin(i) * 2, 2, GRN, .7 - i * .06);
    if (k > 0) { for (i = 0; i < 10; i++) dot(g, sx + 10 - i * 14 * (1 - .3 * k), sea + 14 - i * 6 * k + 40 * k, 2, RED, (.8 - i * .07) * k); var gx = sx + 60 * k, gy = sea + 52 * k; g.globalAlpha = .9 * k; shipShape(g, gx, gy - 8, .6, "rgba(255,93,108,.0)"); g.strokeStyle = RED; g.setLineDash([3, 2]); g.strokeRect(gx - 22, gy - 16, 44, 14); g.setLineDash([]); g.globalAlpha = 1; attacker(g, w * .9, h - 30, t, .9); packets(g, w * .9, h - 30, w * .78, 26, t, RED, 4, .8); }
    shipShape(g, sx, sy, Math.max(1, w / 330), "#c9d6e6"); dot(g, sx + 20, sy - 18, 2, atk ? RED : GRN, .5 + .5 * Math.sin(t * 8));
    scanline(g, w, h, t); return atk;
  };
  S.car = function (g, w, h, t) {
    bg(g, w, h, "#0a1424", "#04070e"); var vx = w * .5, hz = h * .2;
    g.fillStyle = "#0c1522"; g.beginPath(); g.moveTo(vx - 10, hz); g.lineTo(vx + 10, hz); g.lineTo(w * .95, h); g.lineTo(w * .05, h); g.closePath(); g.fill();
    for (var i = 0; i < 8; i++) { var u = cyc(t * .8 + i / 8, 1), y1 = hz + (h - hz) * u * u, y2 = hz + (h - hz) * Math.min(1, (u + .05) * (u + .05)); line(g, vx, y1, vx, y2, "#e9c46a", .3 + .6 * u, 1 + 2 * u); }
    line(g, vx - 10, hz, w * .05, h, DIM, .6); line(g, vx + 10, hz, w * .95, h, DIM, .6);
    var cx = vx, cy = h * .66, ph = cyc(t, 9), atk = ph > .45, fl = atk && Math.sin(t * 12) > 0;
    g.fillStyle = "#d9e3ef"; g.beginPath(); g.moveTo(cx - 26, cy + 18); g.lineTo(cx - 22, cy - 8); g.lineTo(cx - 14, cy - 20); g.lineTo(cx + 14, cy - 20); g.lineTo(cx + 22, cy - 8); g.lineTo(cx + 26, cy + 18); g.closePath(); g.fill();
    g.fillStyle = "#16263b"; g.fillRect(cx - 15, cy - 16, 30, 9); g.fillStyle = "#0b1320"; g.fillRect(cx - 28, cy + 14, 8, 8); g.fillRect(cx + 20, cy + 14, 8, 8);
    [-1, 1].forEach(function (s) { dot(g, cx + s * 18, cy + 6, 3.2, fl ? AMB : "#ff5d6c", fl ? 1 : .8); if (fl) glow(g, cx + s * 18, cy + 6, 22, "rgba(242,178,74,.8)", .8); });
    var clx = w * .16, cly = 30; g.fillStyle = "#16263b"; g.beginPath(); g.arc(clx - 8, cly, 8, 0, TAU); g.arc(clx + 4, cly - 4, 10, 0, TAU); g.arc(clx + 14, cly + 2, 7, 0, TAU); g.fill(); g.strokeStyle = CY; g.globalAlpha = .6; g.stroke(); g.globalAlpha = 1;
    var phx = w * .84, phy = 34; g.strokeStyle = GRN; g.lineWidth = 1.4; g.strokeRect(phx - 7, phy - 12, 14, 24); dot(g, phx, phy + 8, 1.4, GRN, 1);
    packets(g, phx, phy, clx + 10, cly, t, GRN, 4, .5); packets(g, clx, cly + 6, cx, cy - 20, t, atk ? RED : CY, 5, .7);
    if (atk) { attacker(g, w * .1, h * .55, t, .9); packets(g, w * .1, h * .55, clx, cly + 8, t, RED, 5, .9); }
    scanline(g, w, h, t); return atk;
  };
  S.grid = function (g, w, h, t) {
    bg(g, w, h, "#09121f", "#030508"); var gy = h - 30, ph = cyc(t, 10), atk = ph > .35 && ph < .85, cut = ph > .45 && ph < .85;
    var tw = [w * .12, w * .34, w * .56]; tw.forEach(function (x) { tower(g, x, gy, h * .5, "rgba(195,206,220,.55)"); });
    for (var i = 0; i < 2; i++) { g.strokeStyle = cut ? "rgba(195,206,220,.2)" : "rgba(95,216,255,.6)"; g.lineWidth = 1; g.beginPath(); g.moveTo(tw[0] - 11, gy - h * .4 + i * 6); for (var j = 1; j < 3; j++) g.quadraticCurveTo((tw[j - 1] + tw[j]) / 2, gy - h * .32 + i * 6, tw[j] - 11, gy - h * .4 + i * 6); g.quadraticCurveTo(w * .7, gy - h * .3, w * .72, gy - 30); g.stroke(); if (!cut) packets(g, tw[0], gy - h * .4, tw[2], gy - h * .4, t + i * .3, CY, 3, .7); }
    var bx = w * .72, by = gy - 18; g.fillStyle = "#101c2c"; g.fillRect(bx - 14, by - 12, 28, 24); g.strokeStyle = cut ? RED : GRN; g.strokeRect(bx - 14, by - 12, 28, 24);
    g.save(); g.translate(bx, by); g.rotate(cut ? -.6 : 0); line(g, -8, 0, 8, 0, cut ? RED : GRN, 1, 2.4); g.restore();
    for (i = 0; i < 6; i++) { var hx = w * .8 + (i % 3) * 22 - 6, hyy = gy - (i < 3 ? 0 : 26); var off = cut ? ease((ph - .45) / .05 - i * .4) : 0; house(g, hx, hyy, .8, 1 - off); }
    attacker(g, w * .2, 26, t, .8); if (atk) { packets(g, w * .2, 26, bx, by - 12, t, RED, 6, 1.1); line(g, w * .2, 26, bx, by - 12, RED, .25, 1, [3, 4]); }
    scanline(g, w, h, t); return atk;
  };
  S.solar = function (g, w, h, t) {
    bg(g, w, h, "#0d1626", "#04070c"); var ph = cyc(t, 10), atk = ph > .4;
    for (var r = 0; r < 3; r++) for (var c = 0; c < 5; c++) {
      var x = w * .08 + c * w * .14 + r * 10, y = h * .48 + r * 22, wave = atk ? Math.max(0, Math.sin((c + r) * .8 - (ph - .4) * 20)) : 0, lum = atk ? .15 + .2 * (1 - wave) : .55 + .1 * Math.sin(t * 2 + c);
      g.fillStyle = "rgba(44,110,168," + lum + ")"; g.beginPath(); g.moveTo(x, y); g.lineTo(x + w * .12, y); g.lineTo(x + w * .12 - 8, y + 16); g.lineTo(x - 8, y + 16); g.closePath(); g.fill(); g.strokeStyle = "rgba(127,182,255,.5)"; g.lineWidth = .8; g.stroke();
      line(g, x + w * .06, y, x + w * .06 - 4, y + 16, "rgba(127,182,255,.35)", 1, .6);
    }
    var ix = w * .84, iy = h * .68; g.fillStyle = "#16263b"; g.fillRect(ix - 16, iy - 22, 32, 40); g.strokeStyle = "rgba(127,182,255,.6)"; g.strokeRect(ix - 16, iy - 22, 32, 40); dot(g, ix - 8, iy - 14, 2, GRN, .9);
    var mx = ix + 8, my = iy + 8; dot(g, mx, my, 3, RED, .5 + .5 * Math.sin(t * 7)); for (var i = 0; i < 3; i++) ring(g, mx, my, 4 + cyc(t + i / 3, 1) * 18, RED, (1 - cyc(t + i / 3, 1)) * .6);
    var sun = 40 + Math.sin(t * .4) * 3; glow(g, w * .12, 26, sun, "rgba(255,212,122,.5)", .8); dot(g, w * .12, 26, 9, "#ffd47a", .9);
    g.fillStyle = "#16263b"; g.beginPath(); g.arc(w * .72 - 8, 28, 8, 0, TAU); g.arc(w * .72 + 4, 24, 10, 0, TAU); g.arc(w * .72 + 14, 30, 7, 0, TAU); g.fill();
    packets(g, ix, iy - 22, w * .72, 34, t, atk ? RED : CY, 5, atk ? 1 : .5);
    scanline(g, w, h, t); return atk;
  };
  S.water = function (g, w, h, t) {
    bg(g, w, h, "#08131f", "#030508"); var ph = cyc(t, 11), atk = ph > .3 && ph < .75, k = atk ? ease((ph - .3) / .2) : (ph >= .75 ? 1 - ease((ph - .75) / .15) : 0);
    var tx = w * .3, ty = h * .58; g.fillStyle = "#0f1d2e"; g.fillRect(tx - 40, ty - 40, 80, 60); g.strokeStyle = "rgba(127,182,255,.6)"; g.strokeRect(tx - 40, ty - 40, 80, 60);
    var lev = ty + 20 - 44 - Math.sin(t) * 2; g.fillStyle = "rgba(95,216,255," + (.35 - k * .1) + ")"; g.fillRect(tx - 39, lev, 78, ty + 19 - lev);
    g.fillStyle = "rgba(255,93,108," + (k * .25) + ")"; g.fillRect(tx - 39, lev, 78, ty + 19 - lev);
    g.strokeStyle = "rgba(127,182,255,.5)"; g.lineWidth = 4; g.beginPath(); g.moveTo(tx + 40, ty); g.lineTo(w * .9, ty); g.moveTo(w * .9, ty); g.lineTo(w * .9, h - 26); g.stroke();
    for (var i = 0; i < 10; i++) { var u = cyc(t * .5 + i / 10, 1); dot(g, tx + 40 + (w * .9 - tx - 40) * u, ty, 1.6, k > .5 ? RED : CY, .9); }
    var gx = w * .66, gy2 = h * .3, r = 22; g.strokeStyle = "rgba(195,206,220,.5)"; g.lineWidth = 2; g.beginPath(); g.arc(gx, gy2, r, Math.PI, 0); g.stroke();
    g.strokeStyle = RED; g.lineWidth = 3; g.beginPath(); g.arc(gx, gy2, r, -.6, 0); g.stroke();
    var a = Math.PI + (.25 + .7 * k) * Math.PI; line(g, gx, gy2, gx + Math.cos(a) * (r - 4), gy2 + Math.sin(a) * (r - 4), k > .6 ? RED : INK, 1, 2); dot(g, gx, gy2, 3, INK, 1);
    attacker(g, w * .12, 24, t, .8); if (atk) packets(g, w * .12, 24, gx - r, gy2, t, RED, 5, 1);
    if (ph >= .75) { dot(g, w * .52, h - 24, 4, GRN, .9); packets(g, w * .52, h - 24, gx, gy2 + 4, t, GRN, 4, 1.2); }
    scanline(g, w, h, t); return atk;
  };
  S.med = function (g, w, h, t) {
    bg(g, w, h, "#0a1220", "#030508"); var ph = cyc(t, 9), atk = ph > .45 && ph < .8, base = h * .52;
    g.strokeStyle = atk ? RED : GRN; g.lineWidth = 2; g.beginPath();
    for (var x = 0; x <= w; x += 2) { var tt = x / 60 - t * 1.6, b = ((tt % 1) + 1) % 1, y = 0;
      if (atk) y = Math.sin(tt * 19) * 10 * Math.random() * .6 + Math.sin(tt * 7) * 8; else { if (b > .42 && b < .46) y = -34; else if (b > .46 && b < .5) y = 18; else if (b > .38 && b < .42) y = 6; else if (b > .6 && b < .7) y = -6 * Math.sin((b - .6) / .1 * Math.PI); }
      if (x === 0) g.moveTo(x, base + y); else g.lineTo(x, base + y); } g.stroke();
    var hx = Math.min(w * .22, 70), hy = 30; g.fillStyle = "#16263b"; g.beginPath(); g.ellipse(hx, hy, 14, 10, 0, 0, TAU); g.fill(); g.strokeStyle = "rgba(127,182,255,.7)"; g.lineWidth = 1.2; g.stroke(); line(g, hx + 14, hy, hx + 26, hy + 10, "rgba(127,182,255,.7)", 1, 1.2);
    for (var i = 0; i < 3; i++) { g.globalAlpha = .6 - i * .15; g.strokeStyle = CY; g.beginPath(); g.arc(hx, hy, 18 + i * 7, -.6, .6); g.stroke(); } g.globalAlpha = 1;
    if (atk || ph > .4) { attacker(g, w * .85, 30, t, .8); for (i = 0; i < 3; i++) { g.globalAlpha = (atk ? .8 : .3) - i * .2; g.strokeStyle = RED; g.lineWidth = 1.4; g.beginPath(); g.arc(w * .85, 30, 14 + i * 9 + cyc(t * 2, 1) * 8, Math.PI - .6, Math.PI + .6); g.stroke(); } g.globalAlpha = 1; }
    if (ph > .8) { dot(g, w - 24, h - 34, 5, GRN, .9); ring(g, w - 24, h - 34, 9 + cyc(t * 2, 1) * 8, GRN, .6); }
    scanline(g, w, h, t); return atk;
  };
  S.train = function (g, w, h, t) {
    bg(g, w, h, "#09121f", "#030508"); var ty = h * .62, ph = cyc(t, 10), atk = ph > .35 && ph < .85, k = atk ? ease((ph - .35) / .25) : 0;
    line(g, 0, ty + 8, w, ty + 8, "rgba(195,206,220,.6)", 1, 1.5); line(g, 0, ty + 14, w, ty + 14, "rgba(195,206,220,.6)", 1, 1.5);
    for (var x = (-(t * 30) % 14); x < w; x += 14) line(g, x, ty + 6, x - 3, ty + 16, "rgba(195,206,220,.25)", 1, 2);
    if (!this._p) this._p = 0; var v = 70 * (1 - k); this._p = (this._p + v * (1 / 60)) % (w + 220);
    var tx = -180 + this._p; for (var c = 0; c < 4; c++) { var cx = tx + c * 46; g.fillStyle = c === 3 ? "#d9e3ef" : "#a9b8ca"; g.beginPath(); if (c === 3) { g.moveTo(cx, ty - 14); g.lineTo(cx + 34, ty - 14); g.quadraticCurveTo(cx + 46, ty - 10, cx + 44, ty + 6); g.lineTo(cx, ty + 6); } else g.rect(cx, ty - 14, 42, 20); g.fill(); g.fillStyle = "#16263b"; for (var wi = 0; wi < 3; wi++) g.fillRect(cx + 5 + wi * 11, ty - 10, 7, 6); }
    var sx = w * .78, sy = ty - 34; line(g, sx, sy, sx, ty + 6, "rgba(195,206,220,.6)", 1, 1.5); g.fillStyle = "#0b1320"; g.fillRect(sx - 5, sy - 18, 10, 18); dot(g, sx, sy - 13, 3, atk ? "#333" : GRN, 1); dot(g, sx, sy - 5, 3, atk ? RED : "#333", 1); if (atk) glow(g, sx, sy - 5, 14, "rgba(255,93,108,.7)", .8);
    var ax = w * .15, ay = 24; line(g, ax, ay, ax, ay + 24, "rgba(195,206,220,.6)", 1, 1.5); attacker(g, ax, ay, t, .8);
    if (atk) for (var i = 0; i < 4; i++) { var u = cyc(t * .8 + i / 4, 1); g.globalAlpha = (1 - u) * .7; g.strokeStyle = RED; g.lineWidth = 1.4; g.beginPath(); g.arc(ax, ay, 10 + u * w * .7, .1, 1.2); g.stroke(); } g.globalAlpha = 1;
    scanline(g, w, h, t); return atk;
  };
  S.sat = function (g, w, h, t) {
    bg(g, w, h, "#050a14", "#02040a"); for (var i = 0; i < 40; i++) dot(g, (i * 97) % w, (i * 53) % (h * .6), .8, "#fff", .3 + .3 * Math.sin(t + i));
    var ex = w / 2, ey = h * 1.9, er = h * 1.45; var gr = g.createRadialGradient(ex, ey - er * .3, er * .2, ex, ey, er); gr.addColorStop(0, "#14365c"); gr.addColorStop(1, "#061224"); g.fillStyle = gr; g.beginPath(); g.arc(ex, ey, er, 0, TAU); g.fill();
    glow(g, ex, ey - er, 60, "rgba(95,216,255,.25)", 1);
    var ph = cyc(t, 10), atk = ph > .35, k = atk ? (ph - .35) / .5 : 0, sx = w / 2 + Math.sin(t * .3) * w * .1, sy = 30;
    satShape(g, sx, sy, 1.1, Math.sin(t * .5) * .2);
    var n = 9; for (i = 0; i < n; i++) { var a = -Math.PI / 2 + (i - (n - 1) / 2) * .11, tx = ex + Math.cos(a) * er, ty = ey + Math.sin(a) * er, off = k * n > i;
      line(g, sx, sy + 4, tx, ty, off ? RED : CY, off ? .12 : .3, 1, [2, 4]); dot(g, tx, ty - 3, 3, off ? "#3a4656" : GRN, 1); if (!off) glow(g, tx, ty - 3, 10, "rgba(89,214,164,.6)", .5); else if (k * n - i < 1) ring(g, tx, ty - 3, 4 + (k * n - i) * 14, RED, 1 - (k * n - i)); }
    var wx = w * .86, wy = h - 40; line(g, wx, wy, wx, wy - 26, "rgba(195,206,220,.7)", 1, 1.5); var rot = atk ? t * .3 : t * 4; for (i = 0; i < 3; i++) { var b = rot + i * TAU / 3; line(g, wx, wy - 26, wx + Math.cos(b) * 14, wy - 26 + Math.sin(b) * 14, "rgba(220,232,245,.85)", 1, 1.6); }
    if (atk) { attacker(g, w * .1, 28, t, .8); packets(g, w * .1, 28, sx, sy, t, RED, 5, 1); }
    scanline(g, w, h, t); return atk;
  };
  S.crane = function (g, w, h, t) {
    bg(g, w, h, "#0a1424", "#030508"); var gy = h - 24, ph = cyc(t, 10), atk = ph > .5;
    for (var r = 0; r < 4; r++) { g.globalAlpha = .25; g.strokeStyle = "#2c6ea8"; g.beginPath(); for (var x = w * .55; x <= w; x += 8) g.lineTo(x, gy + 4 + r * 5 + Math.sin(x * .06 + t * 1.5 + r) * 1.5); g.stroke(); } g.globalAlpha = 1;
    var cx = w * .32, top = h * .18; g.strokeStyle = AMB; g.lineWidth = 2;
    g.beginPath(); g.moveTo(cx - 30, gy); g.lineTo(cx - 24, top + 20); g.moveTo(cx + 10, gy); g.lineTo(cx + 4, top + 20); g.moveTo(cx - 24, top + 20); g.lineTo(cx + 4, top + 20); g.moveTo(cx - 60, top + 22); g.lineTo(w * .92, top + 22); g.moveTo(cx - 60, top + 30); g.lineTo(w * .92, top + 30); g.stroke();
    for (x = cx - 56; x < w * .9; x += 12) line(g, x, top + 22, x + 6, top + 30, AMB, .6, 1);
    var u = atk ? .55 : (Math.sin(t * .6) * .5 + .5), trx = cx + 20 + u * (w * .5), hook = top + 30 + 30 + Math.sin(t * .6 + 1) * 18 * (atk ? 0 : 1);
    g.fillStyle = "#c3cedc"; g.fillRect(trx - 8, top + 24, 16, 8); line(g, trx, top + 32, trx, hook, "rgba(220,232,245,.8)", 1, 1);
    g.fillStyle = ["#c0392b", "#2c6ea8", "#59d6a4"][Math.floor(t / 6) % 3]; g.fillRect(trx - 16, hook, 32, 14);
    shipShape(g, w * .78, gy + 2, .9, "#7c8aa0");
    var mx = cx - 10, my = top + 40; g.fillStyle = "#101c2c"; g.fillRect(mx - 7, my - 5, 14, 10); g.strokeStyle = atk ? RED : "rgba(127,182,255,.6)"; g.strokeRect(mx - 7, my - 5, 14, 10); dot(g, mx + 3, my, 1.8, atk ? RED : GRN, .5 + .5 * Math.sin(t * 9));
    if (atk) { for (var i = 0; i < 3; i++) ring(g, mx, my, 6 + cyc(t + i / 3, 1) * 30, RED, (1 - cyc(t + i / 3, 1)) * .7); attacker(g, w * .1, 26, t, .8); packets(g, mx, my, w * .1, 26, t, RED, 5, 1); }
    scanline(g, w, h, t); return atk;
  };
  S.iot = function (g, w, h, t) {
    bg(g, w, h, "#09121f", "#030508"); var ph = cyc(t, 10), k = ph < .2 ? 0 : Math.min(1, (ph - .2) / .4), atk = k > 0;
    var cols = Math.max(5, Math.floor(w / 46)), rows = 3, sx = w * .62, sy = h * .5; server(g, w * .86, h * .45, 34, 46, k > .7);
    for (var r = 0; r < rows; r++) for (var c = 0; c < cols - 2; c++) { var x = 22 + c * ((w * .66) / (cols - 2)), y = 28 + r * (h - 70) / (rows - 1), id = (c * 7 + r * 13) % 17 / 17, inf = k > id;
      camera(g, x, y, 1, inf ? RED : "rgba(195,206,220,.75)"); if (inf) { glow(g, x, y, 14, "rgba(255,93,108,.6)", .5); if (k > .7) packets(g, x + 9, y, w * .86 - 17, h * .45, t + id, RED, 2, 1.1); } }
    if (k > .7) for (var i = 0; i < 3; i++) ring(g, w * .86, h * .45, 26 + cyc(t * 2 + i / 3, 1) * 30, RED, (1 - cyc(t * 2 + i / 3, 1)) * .6);
    attacker(g, w * .1, h - 34, t, .7);
    scanline(g, w, h, t); return atk;
  };
  S.phone = function (g, w, h, t) {
    bg(g, w, h, "#0a1220", "#030508"); var ph = cyc(t, 9), atk = ph > .35, px = w * .5, py = h * .48, pz = Math.max(1, h / 190), pw = 54 * pz, phh = 96 * pz;
    g.fillStyle = "#0e1828"; g.beginPath(); if (g.roundRect) g.roundRect(px - pw / 2, py - phh / 2, pw, phh, 10); else g.rect(px - pw / 2, py - phh / 2, pw, phh); g.fill(); g.strokeStyle = atk ? RED : "rgba(220,232,245,.8)"; g.lineWidth = 2; g.stroke();
    g.fillStyle = "#16263b"; g.fillRect(px - pw / 2 + 5, py - phh / 2 + 10, pw - 10, phh - 22);
    var m = ease(Math.min(1, ph / .3)); if (ph > .1) { g.globalAlpha = Math.min(1, (ph - .1) * 5); g.fillStyle = CY; g.fillRect(px - 18, py - 30 + (1 - m) * 10, 30, 12); g.globalAlpha = 1; }
    if (atk) { var k = ease((ph - .35) / .2); for (var i = 0; i < 3; i++) ring(g, px, py, 30 + cyc(t + i / 3, 1) * 50, RED, (1 - cyc(t + i / 3, 1)) * .5 * k);
      dot(g, px - 10, py + 8, 5, RED, .5 + .5 * Math.sin(t * 8)); dot(g, px + 10, py + 8, 5, RED, .5 + .5 * Math.cos(t * 8)); g.fillStyle = INK; g.fillRect(px - 11, py + 5, 2, 6); g.beginPath(); g.arc(px + 10, py + 8, 2, 0, TAU); g.fill();
      packets(g, px, py, w * .88, 30, t, RED, 6, 1); server(g, w * .88, 30, 26, 22, true); }
    attacker(g, w * .12, h - 34, t, .8); packets(g, w * .12, h - 34, px - pw / 2, py, t, atk ? RED : "rgba(255,93,108,.4)", 4, .7);
    g.globalAlpha = .9; g.strokeStyle = "rgba(220,232,245,.6)"; g.lineWidth = 1.5; var hx = px + 34, hy = py + 40; g.beginPath(); g.arc(hx, hy, 6, 0, TAU); g.stroke(); line(g, hx - 5, hy - 5, hx + 5, hy + 5, RED, 1, 2); g.globalAlpha = 1;
    scanline(g, w, h, t); return atk;
  };
  var CODE = { plane: "EXP-01 GNSS", ship: "EXP-02 AIS", car: "EXP-03 CAN/APP", grid: "EXP-04 SCADA", solar: "EXP-05 INV", water: "EXP-06 PLC", med: "EXP-07 RF", train: "EXP-08 RADIO", sat: "EXP-09 SATCOM", crane: "EXP-10 MODEM", iot: "EXP-11 BOTNET", phone: "EXP-12 0-CLICK" };

  var RM = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches, SP = RM ? .5 : 1, live = [];
  var io = "IntersectionObserver" in window ? new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.target._x) e.target._x.vis = e.isIntersecting; }); }, { rootMargin: "60px" }) : null;
  function size(o) { var r = o.cv.getBoundingClientRect(); if (r.width < 10) return false; var d = Math.min(2, window.devicePixelRatio || 1); o.cv.width = Math.round(r.width * d); o.cv.height = Math.round(r.height * d); o.w = r.width; o.h = r.height; o.d = d; o.g = o.cv.getContext("2d"); return true; }
  function scan() { document.querySelectorAll("canvas.cyx").forEach(function (cv) { if (cv._x || !S[cv.dataset.k]) return; var o = { cv: cv, k: cv.dataset.k, t: Math.random() * 3, ctx: {}, vis: !io }; cv._x = o; live.push(o); if (io) io.observe(cv); }); }
  var last = 0; function loop(ms) { var now = ms / 1000, dt = Math.min(.05, now - (last || now)) * SP; last = now;
    live.forEach(function (o) { if (!o.vis) return; var r = o.cv.getBoundingClientRect(); if (!o.g || Math.abs(r.width - o.w) > 1) { if (!size(o)) return; }
      o.t += dt; var g = o.g; g.setTransform(o.d, 0, 0, o.d, 0, 0); g.clearRect(0, 0, o.w, o.h); var atk = false; try { atk = S[o.k].call(o.ctx, g, o.w, o.h, o.t); } catch (e) {}
      g.globalAlpha = 1; hud(g, o.w, o.h, CODE[o.k], o.t, atk); o.cv.parentNode && o.cv.parentNode.classList.toggle("on", !!atk); });
    requestAnimationFrame(loop); }
  new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState !== "loading") scan(); else document.addEventListener("DOMContentLoaded", scan);
  requestAnimationFrame(loop);
})();
