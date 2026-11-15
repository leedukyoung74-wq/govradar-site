#!/usr/bin/env python3
"""Build /cyber/ (ko) and /cyber/en/ from tools/cyber_data.py into cf/extra/cyber/."""
import os, sys, json, html
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cyber_data as C
import alerts_build as AB
OUT = os.path.join(HERE, "..", "cf", "extra", "cyber")
E = lambda s: html.escape(str(s), quote=True)
BASE = "https://radar.wmm-hoa.com"

GATE = r'''<script>(function(){try{var q=location.search,a=(q.match(/[?&]auth=(login|signup|reset)/)||[])[1];if(a){document.addEventListener("DOMContentLoaded",function(){window.WMMAuth&&WMMAuth.open(a)});return}if(/[?&]stay=/.test(q)||/(access_token|confirmation_token|recovery_token|invite_token|error_description)=/.test(location.hash)||/\/(legal|member|pay)\//.test(location.pathname))return;if(localStorage.getItem("wmm.auth.v1")||localStorage.getItem("gv_code"))return}catch(e){return}var l=document.documentElement.lang||"ko";if(["ko","en","es","fr","ar","vi","id"].indexOf(l)<0)l="en";location.replace("/welcome/"+(l==="ko"?"":l+"/"))})();</script>'''

CSS = r'''
@font-face{font-family:"WMM Nexon";font-weight:300;font-display:swap;src:local("NEXON Lv1 Gothic OTF Light"),url("/assets/fonts/NEXONLv1GothicOTFLight.woff") format("woff")}
@font-face{font-family:"WMM Nexon";font-weight:400;font-display:swap;src:local("NEXON Lv1 Gothic OTF"),url("/assets/fonts/NEXONLv1GothicOTF.woff") format("woff")}
@font-face{font-family:"WMM Nexon";font-weight:700;font-display:swap;src:local("NEXON Lv1 Gothic OTF Bold"),url("/assets/fonts/NEXONLv1GothicOTFBold.woff") format("woff")}
:root{--bg:#05080e;--p1:#0c121c;--p2:#121a27;--ink:#eef3fa;--soft:#c3cedc;--muted:#8695a8;--line:#1f2a3a;--cy:#5fd8ff;--red:#ff5d6c;--amb:#f2b24a;--grn:#59d6a4;--gold:#c9a45c;--f:"WMM Nexon","NEXON Lv1 Gothic OTF","Apple SD Gothic Neo","Malgun Gothic",sans-serif;color-scheme:dark}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--soft);font:17px/1.65 var(--f)}
a{color:var(--cy)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
section.s{padding:84px 0;border-top:1px solid var(--line)}
section.s.alt{background:var(--p1)}
h2{color:var(--ink);font-size:clamp(26px,3.4vw,40px);line-height:1.25;font-weight:700;margin:0 0 14px;letter-spacing:-.5px}
.lede{max-width:46em;color:var(--soft);font-size:18px;margin-bottom:34px}
.hero{padding:56px 0 64px;background:#03060b}
.hero .in{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);gap:44px;align-items:center}
.hero h1{color:#fff;font-size:clamp(34px,5vw,60px);line-height:1.15;margin:12px 0 18px;letter-spacing:-1px}
.hero .crumb{font-size:14px;color:var(--muted)}.hero .crumb a{color:var(--muted)}
.hero p.lead{font-size:clamp(17px,1.8vw,20px);color:var(--soft)}
.mv{position:relative;aspect-ratio:16/10;border-radius:14px;overflow:hidden;background:#05090f;box-shadow:0 0 0 1px rgba(140,200,255,.15) inset}
.mv canvas{position:absolute;inset:0;width:100%;height:100%;display:block}
.mv .cap{position:absolute;left:12px;top:10px;z-index:6;font:700 13px/1.2 var(--f);color:#fff;background:rgba(0,0,0,.6);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:4px 10px}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;margin-top:40px}
.stats div{min-width:0}.stats b{display:block;color:#fff;font-size:clamp(26px,3vw,38px);line-height:1.1}.stats span{display:block;font-size:14px;color:var(--soft)}.stats small{color:var(--red);font-size:13px}
.jump{display:flex;flex-wrap:wrap;gap:8px;margin-top:30px}
.jump a{font-size:14px;color:var(--ink);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:7px 14px;background:var(--p2)}
.kinds{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.kd{background:var(--p2);border-radius:10px;padding:22px;min-width:0}
.kd h3{color:#fff;font-size:20px;margin:0 0 8px}.kd p{margin:0 0 10px;font-size:15.5px}.kd .dm{color:var(--amb);font-size:14.5px}.kd .ex{color:var(--muted);font-size:14px;border-top:1px solid var(--line);padding-top:10px;margin-top:12px}
.flt{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}
.flt button{font:600 14px/1 var(--f);color:var(--soft);background:var(--p2);border:1px solid var(--line);border-radius:999px;padding:9px 14px;cursor:pointer}
.flt button[aria-pressed=true]{background:var(--ink);color:#05080e;border-color:var(--ink)}
.ev{display:grid;grid-template-columns:220px 130px minmax(0,1fr);gap:22px;padding:24px 0;border-top:1px solid var(--line)}
.pic{margin:0;min-width:0}.pic img{display:block;width:100%;aspect-ratio:3/2;object-fit:cover;border-radius:8px;filter:saturate(.9)}.pic figcaption{font-size:11.5px;color:var(--muted);margin-top:5px}.pic figcaption a{color:var(--muted)}
.ev .d{color:var(--muted);font-size:14px}.ev .d b{display:block;color:var(--ink);font-size:17px}
.ev h3{color:#fff;font-size:20px;line-height:1.35;margin:6px 0 8px}
.ev p{margin:0 0 8px;font-size:16px}.ev .j{font-size:15px;color:var(--ink)}.ev .sr{font-size:13px;color:var(--muted)}
.bd{display:inline-block;font:700 12.5px/1 var(--f);border-radius:999px;padding:5px 9px;margin-right:6px}
.bd.atk{background:rgba(255,93,108,.16);color:#ff8a95}.bd.susp{background:rgba(242,178,74,.16);color:#f6c56f}.bd.no{background:rgba(160,175,195,.16);color:#c3cedc}.bd.vuln{background:rgba(95,216,255,.14);color:#8fe4ff}
.bd.ty{background:transparent;border:1px solid var(--line);color:var(--muted);font-weight:400}
.hist{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 34px}
.hi{padding:16px 0;border-top:1px solid var(--line);min-width:0}.hi b{color:#fff;font-size:17px}.hi .d{color:var(--muted);font-size:14px}.hi p{font-size:15px;margin:4px 0 0}
.chain{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}
.chain div{background:var(--p2);border-radius:10px;padding:18px;min-width:0;position:relative}.chain b{color:var(--cy);font-size:14px}.chain h3{color:#fff;font-size:17px;margin:6px 0}.chain p{font-size:14px;color:var(--muted);margin:0}
.rm{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.rm div{background:var(--p2);border-radius:10px;padding:22px;min-width:0}.rm h3{color:#fff;font-size:18px;margin:0 0 10px}.rm p{font-size:15.5px;margin:0}
table.pp{width:100%;border-collapse:collapse;font-size:15px}table.pp th,table.pp td{text-align:left;padding:12px 10px;border-top:1px solid var(--line);vertical-align:top}table.pp th{color:var(--ink)}table.pp thead th{color:var(--muted);font-weight:400;font-size:14px}
.tsc{overflow-x:auto}
.todo{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;margin-top:40px}.todo ol{padding-left:20px;margin:0}.todo li{margin:6px 0;font-size:15.5px}
.call{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:40px}.call div{background:#1a0f13;border-radius:10px;padding:20px}.call b{display:block;color:#fff;font-size:36px;line-height:1}.call span{font-size:15px}
.src li{font-size:14px;margin:4px 0}
footer{border-top:1px solid var(--line);padding:30px 0;font-size:14px;color:var(--muted)}
.areas{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
.ar{background:var(--p2);border-radius:12px;padding:22px 20px;min-width:0;border-top:3px solid var(--c)}
.ar .ic{display:inline-grid;place-items:center;width:54px;height:54px;border-radius:14px;color:var(--c);background:color-mix(in srgb,var(--c) 16%,transparent);margin-bottom:12px}
.ar h3{color:#fff;font-size:21px;margin:0 0 12px}.ar dl{margin:0}.ar dt{font-size:12.5px;font-weight:700;color:var(--c);margin-top:10px;letter-spacing:.3px}.ar dd{margin:2px 0 0;font-size:15px;color:var(--soft)}
.td{min-width:0;background:var(--p2);border-radius:12px;overflow:hidden}.td figure{margin:0;position:relative}.td img{display:block;width:100%;aspect-ratio:12/7;object-fit:cover}
.td figure span{position:absolute;left:0;right:0;bottom:0;padding:40px 18px 14px;color:#fff;font-weight:700;font-size:20px;background:linear-gradient(transparent,rgba(0,0,0,.82))}
.td ol{padding:16px 18px 0 38px;margin:0}.td .cr{font-size:11.5px;padding:8px 18px 14px;margin:0}.td .cr a{color:var(--muted)}
@media(max-width:1000px){.areas{grid-template-columns:1fr 1fr}}@media(max-width:560px){.areas{grid-template-columns:1fr}}
.cws{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.cw{background:var(--p2);border-radius:12px;padding:18px 18px 12px;min-width:0}.cw h4{color:#fff;font-size:18px;margin:0 0 10px;display:flex;gap:10px;align-items:center}.cw .fl{font-size:24px;line-height:1}
.cw ul{list-style:none;padding:0;margin:0}.cw li{padding:8px 0;border-top:1px solid var(--line)}.cw li b{display:block;color:var(--cy);font-size:17px;word-break:break-all}.cw li span{font-size:13.5px;color:var(--soft)}
@media(max-width:1000px){.cws{grid-template-columns:1fr 1fr}}@media(max-width:560px){.cws{grid-template-columns:1fr}}
.chw{background:radial-gradient(ellipse at 20% 50%,rgba(255,93,108,.08),transparent 60%),var(--p2);border-radius:16px;padding:18px}
.chs{display:block;width:100%;height:auto;overflow:visible}.chs.v{display:none}
.chs .nb{fill:#0b111b;stroke:var(--c);stroke-width:1.4}.chs .np{fill:none;stroke:var(--c);stroke-width:2;opacity:0;animation:chp 3.2s ease-in-out infinite}
.chs .nd:nth-of-type(2) .np{animation-delay:.6s}.chs .nd:nth-of-type(3) .np{animation-delay:.9s}.chs .nd:nth-of-type(4) .np{animation-delay:1.5s}.chs .nd:nth-of-type(5) .np{animation-delay:1.7s}.chs .nd:nth-of-type(6) .np{animation-delay:2.3s}
@keyframes chp{0%,100%{opacity:0}40%{opacity:.9}}
.chs .lb{fill:none;stroke:rgba(255,255,255,.08);stroke-width:6}.chs .lf{fill:none;stroke-width:2;stroke-dasharray:6 10;animation:chd 1.2s linear infinite;opacity:.85}.chs .lr{stroke-dasharray:3 6}
@keyframes chd{to{stroke-dashoffset:-32}}
.nt{height:100%;padding:16px 18px;display:flex;flex-direction:column;gap:3px;font-family:var(--f);color:var(--soft)}
.nt .ni{display:inline-grid;place-items:center;width:36px;height:36px;border-radius:10px;color:var(--c);background:color-mix(in srgb,var(--c) 18%,transparent);margin-bottom:6px}
.nt em{font-style:normal;font-size:12.5px;font-weight:700;color:var(--c)}.nt b{color:#fff;font-size:17px;line-height:1.3}.nt small{font-size:13px;color:var(--muted);line-height:1.4}
@media(max-width:760px){.chs.h{display:none}.chs.v{display:block}.chw{padding:10px}}
@media(prefers-reduced-motion:reduce){.chs .lf,.chs .np{animation:none}.chs .dot{display:none}}
.cmap{background:#020807;border-top:1px solid #0f2a24;padding:56px 0 40px}.cm-wrap{max-width:1600px;margin:0 auto;padding:0 20px}
.cm-head{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap;margin-bottom:18px}.cm-eb{font-size:12px;letter-spacing:4px;color:#3fe0a8;margin:0 0 6px}.cmap h2{margin:0 0 8px}.cm-sub{font-size:15px;color:#8fb3a8;margin:0}
.cm-lg{display:flex;flex-wrap:wrap;gap:8px}.cm-lg button{font:600 14px/1 var(--f);color:#d6efe7;background:#08201b;border:1px solid #1d4a3f;border-radius:999px;padding:9px 13px;cursor:pointer;display:inline-flex;gap:7px;align-items:center}
.cm-lg button[aria-pressed=false]{opacity:.45}.cm-lg i{width:11px;height:11px;border-radius:50%;background:var(--c);box-shadow:0 0 10px var(--c)}.cm-lg b{color:#fff}
.cm-box{position:relative;border-radius:18px;overflow:hidden;background:radial-gradient(ellipse at 50% 45%,#0b2a24 0%,#04110e 62%,#020807 100%);box-shadow:0 0 0 1px #12382f inset,0 30px 80px rgba(0,0,0,.6)}
#cmsvg{display:block;width:100%;height:auto;max-height:calc(100vh - 180px)}#cmsvg .land{fill:#123b33;stroke:#2c7a68;stroke-width:.6}#cmsvg .land.hit{fill:#1d5a4c;stroke:#49c9a3}
#cmsvg .grat{fill:none;stroke:#1a4a3f;stroke-width:.5;opacity:.6}#cmsvg .ring{fill:none;stroke:#2fd59c;stroke-opacity:.16}#cmsvg .axis{stroke:#2fd59c;stroke-opacity:.12}
.pt circle.c{stroke:#fff;stroke-width:1.2}.pt .p1,.pt .p2{fill:none;stroke-width:1.6;transform-box:fill-box;transform-origin:center;animation:cmp 2.4s ease-out infinite}.pt .p2{animation-delay:1.2s}
@keyframes cmp{0%{transform:scale(.4);opacity:.95}100%{transform:scale(3.4);opacity:0}}.pt{cursor:pointer;transition:opacity .3s}.pt.off{display:none}.pt.fl circle.c{filter:url(#glow)}.pt.fl .c{r:9}
.pt text.nn{font:700 12px var(--f);fill:#fff;stroke:none;opacity:1}.pt text.lb{font:600 13px var(--f);fill:#e9fff7;paint-order:stroke;stroke:#020807;stroke-width:3px;pointer-events:none;opacity:0;transition:opacity .4s}.pt.fl text.lb,.pt:hover text.lb{opacity:1}
.cm-sw{position:absolute;left:50%;top:50%;width:160%;aspect-ratio:1;transform:translate(-50%,-50%) rotate(0deg);border-radius:50%;pointer-events:none;background:conic-gradient(from 0deg,rgba(63,224,168,0) 0deg,rgba(63,224,168,0) 300deg,rgba(63,224,168,.22) 352deg,rgba(150,255,215,.55) 360deg);mix-blend-mode:screen}
.cm-tip{position:absolute;z-index:5;max-width:280px;background:rgba(2,12,10,.94);border:1px solid #2c7a68;border-radius:10px;padding:10px 12px;font-size:13.5px;color:#d6efe7;pointer-events:none}.cm-tip b{display:block;color:#fff;font-size:14.5px;margin:2px 0}
.cm-hud{position:absolute;right:14px;top:12px;display:flex;gap:14px;font:600 11px ui-monospace,Menlo,monospace;color:#5ff0bd;letter-spacing:1px}
@media(max-width:760px){.cmap{padding:40px 0 28px}.cm-box{border-radius:12px}.pt text.lb{font-size:24px}.pt text.nn{font-size:16px}}
@media(max-width:900px){.hero .in{grid-template-columns:1fr}.kinds,.rm,.todo,.call{grid-template-columns:1fr}.hist{grid-template-columns:1fr}.chain{grid-template-columns:1fr 1fr}.stats{grid-template-columns:1fr 1fr}.ev{grid-template-columns:1fr;gap:8px}.pic img{aspect-ratio:16/8}section.s{padding:56px 0}}
'''

ICO = {  # original line icons, 24x24
 0: ("#ffcf4a", '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>'),
 1: ("#5fd8ff", '<path d="M12 12v9M8 21h8"/><circle cx="12" cy="10" r="2"/><path d="M8.5 6.5a5 5 0 0 0 0 7M15.5 6.5a5 5 0 0 1 0 7M5.6 3.6a9 9 0 0 0 0 12.8M18.4 3.6a9 9 0 0 1 0 12.8"/>'),
 2: ("#59d6a4", '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.6"/><path d="M6 9.5v5M18 9.5v5"/>'),
 3: ("#6fb6ff", '<path d="M12 3s6 6.6 6 11a6 6 0 0 1-12 0c0-4.4 6-11 6-11z"/><path d="M9 14.5a3 3 0 0 0 3 3"/>'),
 4: ("#f2b24a", '<path d="M4 11h16v2a8 8 0 0 1-16 0z"/><path d="M8 7c0-1.5 1-2 1-3.5M12 7c0-1.5 1-2 1-3.5M16 7c0-1.5 1-2 1-3.5"/>'),
 5: ("#ff6b7a", '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M12 10.5v6M9 13.5h6"/>'),
 6: ("#b58cff", '<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z"/><rect x="9" y="11" width="6" height="5" rx="1"/><path d="M10 11V9.5a2 2 0 0 1 4 0V11"/>'),
 7: ("#8fe0c8", '<rect x="4" y="3" width="16" height="14" rx="3"/><path d="M4 11h16M8 21l2-4M16 21l-2-4"/><circle cx="8.5" cy="14" r="1"/><circle cx="15.5" cy="14" r="1"/>'),
}
def ico(i):
    c, d = ICO[i]
    return f'<span class="ic" style="--c:{c}"><svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg></span>'
TPH = {"p": ("photo-1685342654383-584d56907425", "a-flashlight-sitting-on-the-floor-of-a-room-XCnqwORjlWg"),
       "b": ("photo-1774600134168-b9ebd714e4e1", "team-collaborating-on-laptops-in-modern-office-N3Bf0ArT5J0"),
       "g": ("photo-1700049775359-6f53cd16114e", "a-room-filled-with-lots-of-desks-covered-in-monitors-5ma_XqDCiG4")}

CHC = ["#ff5d6c", "#ffcf4a", "#5fd8ff", "#6fb6ff", "#ff8fb3", "#c9a45c"]
CHI = [ '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17v.5"/>', '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>', '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M2 10h20M6 15h4"/>',
        '<path d="M12 3s6 6.6 6 11a6 6 0 0 1-12 0c0-4.4 6-11 6-11z"/>', '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M12 10.5v6M9 13.5h6"/>', '<path d="M3 20h18M5 20V10l7-5 7 5v10M9 20v-5h6v5"/>']
def node(k, x, y, w, h, i):
    a, b, c = C.CHAIN[k]; col = CHC[k]
    return (f'<g class="nd" style="--c:{col}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" class="nb"/><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" class="np"/>'
            f'<foreignObject x="{x}" y="{y}" width="{w}" height="{h}"><div xmlns="http://www.w3.org/1999/xhtml" class="nt"><span class="ni"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{CHI[k]}</svg></span>'
            f'<em>{E(a[i])}</em><b>{E(b[i])}</b><small>{E(c[i])}</small></div></foreignObject></g>')
def link(x1, y1, x2, y2, col, d=0, vert=False):
    if vert: mid = (y1 + y2) / 2; path = f"M{x1} {y1} C{x1} {mid} {x2} {mid} {x2} {y2}"
    else: mid = (x1 + x2) / 2; path = f"M{x1} {y1} C{mid} {y1} {mid} {y2} {x2} {y2}"
    return (f'<path d="{path}" class="lb"/><path d="{path}" class="lf" style="stroke:{col};animation-delay:{d}s"/>'
            f'<circle r="4" fill="{col}" class="dot"><animateMotion dur="2.6s" begin="{d}s" repeatCount="indefinite" path="{path}"/></circle>')
def chain_svg(i):
    W, H, w, h = 1180, 470, 250, 150
    X = [10, 320, 630, 920]; Yc = (H - h) / 2; Ya, Yb = 40, H - 40 - h
    P = {0: (X[0], Yc), 1: (X[1], Ya), 2: (X[1], Yb), 3: (X[2], Ya), 4: (X[2], Yb), 5: (X[3], Yc)}
    L = ""
    for a, b, d in ((0, 1, 0), (0, 2, .3), (1, 3, .9), (1, 4, 1.2), (2, 3, 1.1), (2, 4, .8), (3, 5, 1.8), (4, 5, 2.0)):
        L += link(P[a][0] + w, P[a][1] + h / 2, P[b][0], P[b][1] + h / 2, CHC[a], d)
    L += f'<path d="M{X[1]+w/2} {Ya+h} L{X[1]+w/2} {Yb}" class="lb"/><path d="M{X[1]+w/2} {Ya+h} L{X[1]+w/2} {Yb}" class="lf lr" style="stroke:{CHC[1]}"/>'
    N = "".join(node(k, P[k][0], P[k][1], w, h, i) for k in range(6))
    hz = f'<svg class="chs h" viewBox="0 0 {W} {H}" role="img" aria-label="cascade">{L}{N}</svg>'
    W2, w2, h2 = 380, 360, 132
    Y = [0, 190, 380, 570, 760, 950]
    L2 = ""
    for k in range(5): L2 += link(W2 / 2, Y[k] + h2, W2 / 2, Y[k + 1], CHC[k], k * .4, True)
    N2 = "".join(node(k, 10, Y[k], w2, h2, i) for k in range(6))
    vt = f'<svg class="chs v" viewBox="0 0 {W2} {Y[5]+h2+4}" role="img" aria-label="cascade">{L2}{N2}</svg>'
    return hz + vt

def map_data(i):
    pts = []
    for n, r in enumerate(C.REC):
        for lo, la, pk, pe in C.REC_PTS[n]:
            pts.append({"x": lo, "y": la, "v": r[3], "p": (pk, pe)[i], "t": r[5][i], "d": r[0].replace("-", "."), "e": n})
    for n, h in enumerate(C.HIST):
        for lo, la, pk, pe in C.HIST_PTS[n]:
            pts.append({"x": lo, "y": la, "v": "hist", "p": (pk, pe)[i], "t": h[4][i], "d": h[0].replace("-", "."), "e": -1})
    return json.dumps(pts, ensure_ascii=False)

T = {
 "ko": dict(title="사이버 공격 — 지금 세계에서 일어나는 일과 준비 · GOV RADAR", desc="사이버 공격 12가지 유형, 2026년 9~11월 국내외 사건(실제 공격과 단순 장애 구분), 역대 주요 사건, 한국 가정·기업·정부의 준비 사항 — GOV RADAR",
   crumb="재난 지도", h1="사이버 공격<br>지금 세계에서 일어나는 일과 준비", lead="해킹·디도스·랜섬웨어가 전력·금융·식수·식량·의료까지 멈출 수 있습니다. 2026년 9~11월 국내외 사건을 실제 공격과 단순 장애로 나눠 보여 주고, 가정·기업·정부가 지금 할 일을 정리했습니다.",
   cap="사이버 공격 · 모션 그래픽", rel="관련 이미지(사건 현장 사진 아님)", upd="기준일", j=[("map","사건 지도"),("kinds","공격 유형 12가지"),("now","최근 사건"),("hist","역대 주요 사건"),("chain","연쇄 피해"),("rumor","소문 확인"),("prep","준비 사항"),("src","출처")],
   kh="사이버 공격은 어떻게 일어나나 — 12가지 유형", kl="같은 '해킹'이라도 수법과 피해가 다릅니다. 유형마다 실제로 일어난 사례를 함께 붙였습니다.", dmg="주요 피해", ex="실제 사례",
   nh="최근 사건 — 실제 공격과 단순 장애를 구분해서", nl="2026년 9~11월 국내외 사건입니다. 장애가 났다고 모두 해킹은 아닙니다. 사건마다 지금까지 확인된 판정을 붙였습니다.",
   f=[("all","전체"),("atk","실제 공격"),("susp","조사 중·의심"),("no","공격 아님"),("vuln","취약점"),("KR","한국 관련")],
   v={"atk":"실제 공격","susp":"조사 중·의심","no":"공격 아님","vuln":"취약점"}, jl="판정", sl="출처",
   hh="역대 주요 사건", hl="세계와 한국의 사이버 사건 가운데 지금 준비에 교훈이 큰 사건입니다.",
   ch="한 곳이 멈추면 어디까지 번지나", cl="전력·통신·금융·식수·식량·의료는 서로 연결돼 있습니다. 아래는 위험이 번지는 구조이며 특정 날짜의 예측이 아닙니다.",
   rh="돌고 있는 소문, 사실은", rl="인터넷에 퍼진 주장과 공식 확인 내용을 나란히 놓았습니다.",
   ph="지금 준비할 것 — 가정·기업·정부", pl="공격을 안 당하는 것보다, 당하거나 장애가 나도 필수 기능을 빨리 되살리는 것이 핵심입니다.", pth=["분야","개인·가정","기업·기관","정부·지자체"],
   cwh="나라별 사이버 피해 신고처", cwn="✓ 표시는 2026년 11월 15일 각국 공식 사이트에서 확인한 번호입니다. 생명이 위험하면 먼저 각국 긴급번호(한국 112·119, 미국 911, 유럽 112)로 연락하세요.", tp="개인·가정 먼저 할 일", tb="기업·기관 먼저 할 일", tg="정부·지자체 먼저 할 일", callh="한국에서 피해를 입었다면 바로 신고",
   sh="출처", sn="사건 사진은 언론사 저작권 때문에 싣지 않고, 내용과 관련된 무료 라이선스(Unsplash) 이미지를 넣었습니다. 이 페이지는 공개 보도와 기관 발표를 바탕으로 정리했습니다. 조사 중인 사건은 결론이 바뀔 수 있습니다. 배후 귀속은 발표 기관의 판단을 그대로 옮겼습니다.",
   foot="GOV RADAR · 월드메이킹멤버스(WMM) · 문의 73036396@naver.com", other="English"),
 "en": dict(title="Cyberattacks — what is happening now and how to prepare · GOV RADAR", desc="Twelve kinds of cyberattack, recent incidents worldwide (real attacks vs plain outages), landmark cases and what households, companies and governments should do — GOV RADAR",
   crumb="Hazard map", h1="Cyberattacks<br>what is happening, and how to prepare", lead="Hacking, DDoS and ransomware can stop power, money, water, food and healthcare. We separate real attacks from plain outages in incidents from September to November 2026, and set out what households, companies and governments can do now.",
   cap="Cyberattack · motion graphic", rel="Related image, not the incident", upd="As of", j=[("map","Incident map"),("kinds","12 kinds"),("now","Recent incidents"),("hist","Landmark cases"),("chain","Knock-on effects"),("rumor","Rumour check"),("prep","Preparation"),("src","Sources")],
   kh="How cyberattacks happen — 12 kinds", kl="'Hacking' covers very different methods and harms. Each kind comes with real cases.", dmg="Main harm", ex="Real cases",
   nh="Recent incidents — real attacks vs plain outages", nl="Incidents from September to November 2026. Not every outage is a hack; each item carries the verdict known so far.",
   f=[("all","All"),("atk","Real attacks"),("susp","Suspected"),("no","Not an attack"),("vuln","Vulnerability"),("KR","Korea")],
   v={"atk":"Attack","susp":"Suspected","no":"Not an attack","vuln":"Vulnerability"}, jl="Verdict", sl="Sources",
   hh="Landmark cases", hl="Past incidents in Korea and worldwide with the biggest lessons for preparation.",
   ch="If one thing stops, how far does it spread?", cl="Power, communications, money, water, food and healthcare depend on each other. This shows how risk spreads — it is not a forecast for any date.",
   rh="Rumours, checked", rl="What is circulating online beside what officials have confirmed.",
   ph="What to prepare — households, companies, governments", pl="The goal is not to never be hit, but to restore essential functions quickly when an attack or outage happens.", pth=["Area","Households","Companies","Government"],
   cwh="Where to report, by country", cwn="✓ = checked on official sites on 15 Nov 2026. If life is at risk, call the local emergency number first (112 in Europe and Korea, 911 in the US).", tp="Households: first steps", tb="Companies: first steps", tg="Government: first steps", callh="If you are hit in Korea, report it",
   sh="Sources", sn="News photos are copyrighted, so each incident shows a related free-licence (Unsplash) image instead. Compiled from public reporting and official statements. Conclusions on open investigations may change. Attributions are as stated by the named agency or company.",
   foot="GOV RADAR · WORLD MAKING MEMBERS (WMM) · 73036396@naver.com", other="한국어")}

def page(L):
    t = T[L]; i = 0 if L == "ko" else 1
    path = "/cyber/" if L == "ko" else "/cyber/en/"
    kinds = "".join(f'<div class="kd" id="k-{k}"><h3>{E(n[i])}</h3><p>{E(d[i])}</p><p class="dm">{E(t["dmg"])} · {E(dm[i])}</p><p class="ex">{E(t["ex"])} · {E(ex[i])}</p></div>' for k, n, d, dm, ex in C.TYPES)
    TN = {k: n[i] for k, n, *_ in C.TYPES}
    rec = sorted(C.REC, key=lambda r: r[0], reverse=True)
    def dfmt(d): return d.replace("-", ".")
    evs = ""
    for r in rec:
        d, reg, isos, v, ty, tt, wh, jd, sx = r
        pk = C.REC_PH[C.REC.index(r)]; pid, slug = C.PH[pk]
        pic = (f'<figure class="pic"><img src="https://images.unsplash.com/{pid}?auto=format&fit=crop&w=480&h=320&q=70" srcset="https://images.unsplash.com/{pid}?auto=format&fit=crop&w=480&h=320&q=70 480w, https://images.unsplash.com/{pid}?auto=format&fit=crop&w=960&h=640&q=70 960w" sizes="(max-width:900px) 100vw, 220px" alt="" loading="lazy" referrerpolicy="no-referrer">'
               f'<figcaption>{E(t["rel"])} · <a href="https://unsplash.com/photos/{slug}" target="_blank" rel="noopener">Unsplash</a></figcaption></figure>')
        srcs = " · ".join(f'<a href="{E(C.SRC[n-1][1])}" target="_blank" rel="noopener nofollow">{E(C.SRC[n-1][0].split(" — ")[0])}</a>' for n in sx)
        evs += (f'<article class="ev" id="ev-{C.REC.index(r)}" data-v="{v}" data-iso="{" ".join(isos)}">{pic}<div class="d"><b>{dfmt(d)}</b>{E(reg[i])}</div><div>'
                f'<span class="bd {v}">{E(t["v"][v])}</span>' + (f'<span class="bd ty">{E(TN.get(ty, ""))}</span>' if ty else "") +
                f'<h3>{E(tt[i])}</h3><p>{E(wh[i])}</p><p class="j"><b>{E(t["jl"])}</b> · {E(jd[i])}</p><p class="sr">{E(t["sl"])} · {srcs}</p></div></article>')
    hist = "".join(f'<div class="hi"><span class="bd {v}">{E(t["v"][v])}</span><span class="d">{dfmt(d)} · {E(reg[i])}</span><br><b>{E(tt[i])}</b><p>{E(nt[i])}</p></div>' for d, reg, v, ty, tt, nt in C.HIST)
    stats = "".join(f'<div><b>{E(n if L=="ko" else n.replace("63억 달러","$6.3bn"))}</b><span>{E(a[i])}</span><small>{E(b[i])}</small></div>' for n, a, b in C.STATS)
    chain = "".join(f'<div><b>{E(a[i])}</b><h3>{E(b[i])}</h3><p>{E(c[i])}</p></div>' for a, b, c in C.CHAIN)
    rumor = "".join(f'<div><h3>{E(a[i])}</h3><p>{E(b[i])}</p></div>' for a, b in C.RUMOR)
    who = t["pth"][1:]
    prep = "".join(f'<div class="ar" style="--c:{ICO[n][0]}">{ico(n)}<h3>{E(a[i])}</h3><dl><dt>{E(who[0])}</dt><dd>{E(b[i])}</dd><dt>{E(who[1])}</dt><dd>{E(c[i])}</dd><dt>{E(who[2])}</dt><dd>{E(d[i])}</dd></dl></div>' for n, (a, b, c, d) in enumerate(C.PREP))
    todo = "".join(f'<div class="td"><figure><img src="https://images.unsplash.com/{TPH[k][0]}?auto=format&fit=crop&w=720&h=420&q=70" alt="" loading="lazy" referrerpolicy="no-referrer"><span>{E(t[h])}</span></figure><ol>' + "".join(f"<li>{E(x[i])}</li>" for x in C.TODO[k]) + f'</ol><p class="cr"><a href="https://unsplash.com/photos/{TPH[k][1]}" target="_blank" rel="noopener">Unsplash</a></p></div>' for k, h in (("p", "tp"), ("b", "tb"), ("g", "tg")))
    call = "".join(f'<div><b>{n}</b><span>{E(d[i])}</span></div>' for n, d in C.CALL)
    def flag(iso): return "".join(chr(0x1F1E6 + ord(ch) - 65) for ch in iso)
    callw = "".join(f'<div class="cw"><h4><span class="fl">{flag(iso)}</span>{E(nm[i])}</h4><ul>' + "".join(f'<li><b>{E(n)}</b><span>{E(d[i])}</span></li>' for n, d in es) + "</ul></div>" for iso, nm, es in C.CALLW)
    seen = set(); src = ""
    for n, u in C.SRC:
        if u in seen: continue
        seen.add(u); src += f'<li><a href="{E(u)}" target="_blank" rel="noopener nofollow">{E(n)}</a></li>'
    flt = "".join(f'<button type="button" data-f="{k}" aria-pressed="{"true" if k=="all" else "false"}">{E(n)}</button>' for k, n in t["f"])
    jump = "".join(f'<a href="#{k}">{E(n)}</a>' for k, n in t["j"])
    other = "/cyber/en/" if L == "ko" else "/cyber/"
    alt = f'<link rel="alternate" hreflang="ko" href="{BASE}/cyber/"><link rel="alternate" hreflang="en" href="{BASE}/cyber/en/">'
    sub = json.dumps([["#" + k, n] for k, n in t["j"]], ensure_ascii=False)
    return f'''<!DOCTYPE html>
<html lang="{L}">
<head>{GATE}
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(t["title"])}</title><meta name="description" content="{E(t["desc"])}">
<link rel="canonical" href="{BASE}{path}">{alt}
<meta property="og:title" content="{E(t["title"])}"><meta property="og:description" content="{E(t["desc"])}"><meta property="og:image" content="{BASE}/assets/og-govradar.jpg"><meta property="og:url" content="{BASE}{path}">
<link rel="icon" href="/assets/mark.png"><style>{CSS}</style></head>
<body>
<script>window.GVH_LANG_URL=function(l){{return l==="ko"?"/cyber/":"/cyber/en/"}};window.GVH_SUB=function(){{return {sub}}};</script><script src="/assets/gvhdr.js" data-l="{L}" data-g="world" data-a="cyber"></script>
<section class="hero"><div class="wrap"><div class="in"><div>
<p class="crumb"><a href="/hazards/">GOV RADAR · {E(t["crumb"])}</a> · <a href="{other}">{E(t["other"])}</a></p>
<h1>{t["h1"]}</h1><p class="lead">{E(t["lead"])}</p>
<div class="jump">{jump}</div></div>
<div class="mv"><canvas class="hzcv" data-k="cyber" aria-hidden="true"></canvas><span class="cap">{E(t["cap"])}</span></div></div>
<div class="stats">{stats}</div><p style="font-size:13px;color:var(--muted);margin-top:14px">{E(t["upd"])} {C.UPDATED} · {"국내 통계: 과학기술정보통신부·KISA 2026년 상반기 사이버위협 동향(7월 30일)" if L=="ko" else "Korean figures: MSIT/KISA H1 2026 cyber-threat report (30 Jul)"}</p></div></section>
<section class="s" id="kinds"><div class="wrap"><h2>{E(t["kh"])}</h2><p class="lede">{E(t["kl"])}</p><div class="kinds">{kinds}</div></div></section>
<section class="cmap" id="map"><div class="cm-wrap"><div class="cm-head"><div><p class="cm-eb">LIVE RADAR · CYBER INCIDENTS</p><h2>{"뉴스에 나온 사이버 사건, 세계 지도로" if L=="ko" else "Cyber incidents in the news, on the map"}</h2>
<p class="cm-sub">{"점을 누르면 아래 사건 설명으로 이동합니다. 레이더가 지나갈 때 지점이 밝아집니다. 기준일 " if L=="ko" else "Tap a point to jump to the incident. Points flare as the sweep passes. As of "}{C.UPDATED}</p></div>
<div class="cm-lg"><button type="button" data-k="atk" aria-pressed="true"><i style="--c:#ff4d5e"></i>{t["v"]["atk"]} <b id="n-atk"></b></button><button type="button" data-k="susp" aria-pressed="true"><i style="--c:#ffb238"></i>{t["v"]["susp"]} <b id="n-susp"></b></button><button type="button" data-k="no" aria-pressed="true"><i style="--c:#59c7ff"></i>{t["v"]["no"]} <b id="n-no"></b></button><button type="button" data-k="hist" aria-pressed="false"><i style="--c:#d9b45f"></i>{"역대 주요 사건" if L=="ko" else "Landmark cases"} <b id="n-hist"></b></button></div></div>
<div class="cm-box" id="cmbox"><svg id="cmsvg" viewBox="0 0 1600 760" preserveAspectRatio="xMidYMid meet" aria-label="map"></svg><div class="cm-sw" id="cmsw"></div><div class="cm-tip" id="cmtip" hidden></div><div class="cm-hud"><span>● SWEEP</span><span id="cmcnt"></span></div></div></div></section>
<section class="s alt" id="now"><div class="wrap"><h2>{E(t["nh"])}</h2><p class="lede">{E(t["nl"])}</p><div class="flt" id="flt">{flt}</div><div id="evs">{evs}</div></div></section>
<section class="s" id="hist"><div class="wrap"><h2>{E(t["hh"])}</h2><p class="lede">{E(t["hl"])}</p><div class="hist">{hist}</div></div></section>
<section class="s alt" id="chain"><div class="wrap"><h2>{E(t["ch"])}</h2><p class="lede">{E(t["cl"])}</p><div class="chw">{chain_svg(i)}</div></div></section>
<section class="s" id="alerts"><div class="wrap">{AB.strip(L)}</div></section>
<section class="s" id="rumor"><div class="wrap"><h2>{E(t["rh"])}</h2><p class="lede">{E(t["rl"])}</p><div class="rm">{rumor}</div></div></section>
<section class="s alt" id="prep"><div class="wrap"><h2>{E(t["ph"])}</h2><p class="lede">{E(t["pl"])}</p>
<div class="areas">{prep}</div>
<div class="todo">{todo}</div><h3 style="color:#fff;font-size:20px;margin:48px 0 0">{E(t["callh"])}</h3><div class="call" style="margin-top:16px">{call}</div>
<h3 id="callw" style="color:#fff;font-size:24px;margin:56px 0 6px">{E(t["cwh"])}</h3><p style="font-size:15px;color:var(--muted);margin:0 0 20px">{E(t["cwn"])}</p><div class="cws">{callw}</div></div></section>
<section class="s" id="src"><div class="wrap"><h2>{E(t["sh"])}</h2><p class="lede" style="font-size:15px">{E(t["sn"])}</p><ol class="src">{src}</ol></div></section>
<footer><div class="wrap">{E(t["foot"])}</div></footer><div style="background:#0a0a0a;display:flex;justify-content:center;align-items:center;padding:40px 16px 44px"><a href="https://www.wmm-hoa.com" target="_blank" rel="noopener"><img src="/assets/wmm-logo-white.png" alt="WORLD MAKING MEMBERS" width="150" height="150" style="display:block;width:150px;height:150px"></a></div>
<script src="/hazards/hzfx.js"></script><script src="/hazards/hzfx2.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script><script src="https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js"></script><script src="/hazards/world.js"></script>
<script>(function(){{var P={map_data(i)},C={{atk:"#ff4d5e",susp:"#ffb238",no:"#59c7ff",vuln:"#b58cff",hist:"#d9b45f"}},ON={{atk:1,susp:1,no:1,vuln:1,hist:0}};
if(!window.d3||!window.TOPO)return;var W=1600,H=760,svg=d3.select("#cmsvg"),pr=d3.geoNaturalEarth1().fitExtent([[10,10],[W-10,H-10]],{{type:"Sphere"}}),pa=d3.geoPath(pr);
svg.append("defs").html('<filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>');
svg.append("path").attr("class","grat").attr("d",pa(d3.geoGraticule10()));
var fs=topojson.feature(TOPO,TOPO.objects.countries).features.filter(function(f){{return f.id!=="010"}});
var hit={{}};P.forEach(function(p){{fs.forEach(function(f){{if(!hit[f.id]&&d3.geoContains(f,[p.x,p.y]))hit[f.id]=1}})}});
svg.append("g").selectAll("path").data(fs).join("path").attr("class",function(f){{return "land"+(hit[f.id]?" hit":"")}}).attr("d",pa);
var cx=W/2,cy=H/2;for(var r=120;r<900;r+=120)svg.append("circle").attr("class","ring").attr("cx",cx).attr("cy",cy).attr("r",r);
svg.append("line").attr("class","axis").attr("x1",0).attr("x2",W).attr("y1",cy).attr("y2",cy);svg.append("line").attr("class","axis").attr("y1",0).attr("y2",H).attr("x1",cx).attr("x2",cx);
var cnt={{atk:0,susp:0,no:0,hist:0}},grp={{}},Q=[];P.forEach(function(p){{cnt[p.v]=(cnt[p.v]||0)+1;var k=p.x+","+p.y+","+(p.v==="vuln"?"no":p.v);if(!grp[k]){{grp[k]={{x:p.x,y:p.y,v:p.v,p:p.p,d:p.d,e:p.e,items:[]}};Q.push(grp[k])}}grp[k].items.push(p)}});
var vo={{atk:0,susp:1,no:2,vuln:3,hist:4}},sk={{}};Q.forEach(function(q){{var xy=pr([q.x,q.y]),k2=q.x+","+q.y,n=sk[k2]||0;sk[k2]=n+1;q.X=xy[0]+n*16;q.Y=xy[1]-n*10;q.A=(Math.atan2(q.Y-cy,q.X-cx)*180/Math.PI+90+360)%360;q.n=q.items.length}});P=Q.sort(function(a,b){{return vo[b.v]-vo[a.v]}});
for(var k in cnt){{var el=document.getElementById("n-"+k);if(el)el.textContent=cnt[k]}}
var g=svg.append("g").selectAll("g").data(P).join("g").attr("class",function(p){{return "pt v-"+p.v+(ON[p.v]?"":" off")}}).attr("transform",function(p){{return "translate("+p.X+","+p.Y+")"}});
g.append("circle").attr("class","p1").attr("r",8).attr("stroke",function(p){{return C[p.v]}});g.append("circle").attr("class","p2").attr("r",8).attr("stroke",function(p){{return C[p.v]}});
g.append("circle").attr("class","c").attr("r",function(p){{return p.v==="hist"?5:(p.n>1?11:6.5)}}).attr("fill",function(p){{return C[p.v]}});
g.filter(function(p){{return p.n>1}}).append("text").attr("class","nn").attr("text-anchor","middle").attr("y",4.5).text(function(p){{return p.n}});
g.append("text").attr("class","lb").attr("x",function(p){{return p.n>1?16:12}}).attr("y",4).text(function(p){{return p.p+(p.n>1?" · "+p.n+"{"건" if L=="ko" else ""}":"")}});
var tip=document.getElementById("cmtip"),box=document.getElementById("cmbox");
g.on("mouseenter",function(ev,p){{tip.hidden=false;tip.innerHTML="<span>"+p.p+"</span>"+p.items.slice(0,6).map(function(x){{return "<b>"+x.d+" · "+x.t.replace(/</g,"&lt;")+"</b>"}}).join("")+(p.items.length>6?"<span>+"+(p.items.length-6)+"</span>":"")}}).on("mousemove",function(ev){{var b=box.getBoundingClientRect();tip.style.left=Math.min(b.width-290,ev.clientX-b.left+14)+"px";tip.style.top=(ev.clientY-b.top+14)+"px"}}).on("mouseleave",function(){{tip.hidden=true}})
 .on("click",function(ev,p){{if(p.e<0){{location.hash="#hist";return}}var a=document.getElementById("ev-"+p.e);if(!a)return;a.style.display="";a.scrollIntoView({{behavior:"smooth",block:"start"}});a.animate([{{background:"rgba(255,77,94,.18)"}},{{background:"transparent"}}],{{duration:1800}})}});
function vis(){{var n=0;g.classed("off",function(p){{var o=!ON[p.v];if(!o)n++;return o}});document.getElementById("cmcnt").textContent=n+" {"POINTS" if L=="en" else "지점"}"}}vis();
document.querySelectorAll(".cm-lg button").forEach(function(b){{b.onclick=function(){{var k=b.dataset.k;ON[k]=ON[k]?0:1;if(k==="no")ON.vuln=ON.no;b.setAttribute("aria-pressed",!!ON[k]);vis()}}}});
if(innerWidth<760){{var xs=P.map(function(p){{return p.X}}),ys=P.map(function(p){{return p.Y}}),x0=Math.min.apply(null,xs)-60,x1=Math.max.apply(null,xs)+60,y0=Math.min.apply(null,ys)-60,y1=Math.max.apply(null,ys)+60;svg.attr("viewBox",x0+" "+y0+" "+(x1-x0)+" "+(y1-y0))}}
var sw=document.getElementById("cmsw"),t0=performance.now(),RM=matchMedia("(prefers-reduced-motion: reduce)").matches;
function loop(ms){{var a=((ms-t0)/1000*60)%360;sw.style.transform="translate(-50%,-50%) rotate("+a+"deg)";g.classed("fl",function(p){{var d=(a-p.A+360)%360;return d<28}});if(!RM)requestAnimationFrame(loop)}}requestAnimationFrame(loop);
}})();</script>
<script>(function(){{var b=document.querySelectorAll("#flt button"),ev=document.querySelectorAll("#evs .ev");b.forEach(function(x){{x.onclick=function(){{var f=x.dataset.f;b.forEach(function(y){{y.setAttribute("aria-pressed",y===x)}});ev.forEach(function(e){{var ok=f==="all"||(f==="KR"?(" "+e.dataset.iso+" ").indexOf(" KR ")>=0:e.dataset.v===f);e.style.display=ok?"":"none"}})}}}})}})();</script>
</body></html>'''

def main():
    os.makedirs(os.path.join(OUT, "en"), exist_ok=True)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf8").write(page("ko"))
    open(os.path.join(OUT, "en", "index.html"), "w", encoding="utf8").write(page("en"))
    print("[cyber] built ko, en ·", len(C.REC), "recent ·", len(C.HIST), "landmark")

if __name__ == "__main__":
    main()
