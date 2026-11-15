#!/usr/bin/env python3
"""Build /cyber/ (ko) and /cyber/en/ from tools/cyber_data.py into cf/extra/cyber/."""
import os, sys, json, html
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cyber_data as C
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
.ev{display:grid;grid-template-columns:150px minmax(0,1fr);gap:22px;padding:24px 0;border-top:1px solid var(--line)}
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
.todo{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;margin-top:40px}.todo div{min-width:0}.todo h3{color:#fff;font-size:19px;margin:0 0 10px}.todo ol{padding-left:20px;margin:0}.todo li{margin:6px 0;font-size:15.5px}
.call{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:40px}.call div{background:#1a0f13;border-radius:10px;padding:20px}.call b{display:block;color:#fff;font-size:36px;line-height:1}.call span{font-size:15px}
.src li{font-size:14px;margin:4px 0}
footer{border-top:1px solid var(--line);padding:30px 0;font-size:14px;color:var(--muted)}
@media(max-width:900px){.hero .in{grid-template-columns:1fr}.kinds,.rm,.todo,.call{grid-template-columns:1fr}.hist{grid-template-columns:1fr}.chain{grid-template-columns:1fr 1fr}.stats{grid-template-columns:1fr 1fr}.ev{grid-template-columns:1fr;gap:6px}section.s{padding:56px 0}}
'''

T = {
 "ko": dict(title="사이버 공격 — 지금 세계에서 일어나는 일과 준비 · GOV RADAR", desc="사이버 공격 12가지 유형, 2026년 9~11월 국내외 사건(실제 공격과 단순 장애 구분), 역대 주요 사건, 한국 가정·기업·정부의 준비 사항 — GOV RADAR",
   crumb="재난 지도", h1="사이버 공격<br>지금 세계에서 일어나는 일과 준비", lead="해킹·디도스·랜섬웨어가 전력·금융·식수·식량·의료까지 멈출 수 있습니다. 2026년 9~11월 국내외 사건을 실제 공격과 단순 장애로 나눠 보여 주고, 가정·기업·정부가 지금 할 일을 정리했습니다.",
   cap="사이버 공격 · 모션 그래픽", upd="기준일", j=[("kinds","공격 유형 12가지"),("now","최근 사건"),("hist","역대 주요 사건"),("chain","연쇄 피해"),("rumor","소문 확인"),("prep","준비 사항"),("src","출처")],
   kh="사이버 공격은 어떻게 일어나나 — 12가지 유형", kl="같은 '해킹'이라도 수법과 피해가 다릅니다. 유형마다 실제로 일어난 사례를 함께 붙였습니다.", dmg="주요 피해", ex="실제 사례",
   nh="최근 사건 — 실제 공격과 단순 장애를 구분해서", nl="2026년 9~11월 국내외 사건입니다. 장애가 났다고 모두 해킹은 아닙니다. 사건마다 지금까지 확인된 판정을 붙였습니다.",
   f=[("all","전체"),("atk","실제 공격"),("susp","조사 중·의심"),("no","공격 아님"),("vuln","취약점"),("KR","한국 관련")],
   v={"atk":"실제 공격","susp":"조사 중·의심","no":"공격 아님","vuln":"취약점"}, jl="판정", sl="출처",
   hh="역대 주요 사건", hl="세계와 한국의 사이버 사건 가운데 지금 준비에 교훈이 큰 사건입니다.",
   ch="한 곳이 멈추면 어디까지 번지나", cl="전력·통신·금융·식수·식량·의료는 서로 연결돼 있습니다. 아래는 위험이 번지는 구조이며 특정 날짜의 예측이 아닙니다.",
   rh="돌고 있는 소문, 사실은", rl="인터넷에 퍼진 주장과 공식 확인 내용을 나란히 놓았습니다.",
   ph="지금 준비할 것 — 가정·기업·정부", pl="공격을 안 당하는 것보다, 당하거나 장애가 나도 필수 기능을 빨리 되살리는 것이 핵심입니다.", pth=["분야","개인·가정","기업·기관","정부·지자체"],
   tp="개인·가정 먼저 할 일", tb="기업·기관 먼저 할 일", tg="정부·지자체 먼저 할 일", callh="피해를 입었다면 바로 신고",
   sh="출처", sn="이 페이지는 공개 보도와 기관 발표를 바탕으로 정리했습니다. 조사 중인 사건은 결론이 바뀔 수 있습니다. 배후 귀속은 발표 기관의 판단을 그대로 옮겼습니다.",
   foot="GOV RADAR · 월드메이킹멤버스(WMM) · 문의 73036396@naver.com", other="English"),
 "en": dict(title="Cyberattacks — what is happening now and how to prepare · GOV RADAR", desc="Twelve kinds of cyberattack, recent incidents worldwide (real attacks vs plain outages), landmark cases and what households, companies and governments should do — GOV RADAR",
   crumb="Hazard map", h1="Cyberattacks<br>what is happening, and how to prepare", lead="Hacking, DDoS and ransomware can stop power, money, water, food and healthcare. We separate real attacks from plain outages in incidents from September to November 2026, and set out what households, companies and governments can do now.",
   cap="Cyberattack · motion graphic", upd="As of", j=[("kinds","12 kinds"),("now","Recent incidents"),("hist","Landmark cases"),("chain","Knock-on effects"),("rumor","Rumour check"),("prep","Preparation"),("src","Sources")],
   kh="How cyberattacks happen — 12 kinds", kl="'Hacking' covers very different methods and harms. Each kind comes with real cases.", dmg="Main harm", ex="Real cases",
   nh="Recent incidents — real attacks vs plain outages", nl="Incidents from September to November 2026. Not every outage is a hack; each item carries the verdict known so far.",
   f=[("all","All"),("atk","Real attacks"),("susp","Suspected"),("no","Not an attack"),("vuln","Vulnerability"),("KR","Korea")],
   v={"atk":"Attack","susp":"Suspected","no":"Not an attack","vuln":"Vulnerability"}, jl="Verdict", sl="Sources",
   hh="Landmark cases", hl="Past incidents in Korea and worldwide with the biggest lessons for preparation.",
   ch="If one thing stops, how far does it spread?", cl="Power, communications, money, water, food and healthcare depend on each other. This shows how risk spreads — it is not a forecast for any date.",
   rh="Rumours, checked", rl="What is circulating online beside what officials have confirmed.",
   ph="What to prepare — households, companies, governments", pl="The goal is not to never be hit, but to restore essential functions quickly when an attack or outage happens.", pth=["Area","Households","Companies","Government"],
   tp="Households: first steps", tb="Companies: first steps", tg="Government: first steps", callh="If you are hit in Korea, report it",
   sh="Sources", sn="Compiled from public reporting and official statements. Conclusions on open investigations may change. Attributions are as stated by the named agency or company.",
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
        srcs = " · ".join(f'<a href="{E(C.SRC[n-1][1])}" target="_blank" rel="noopener nofollow">{E(C.SRC[n-1][0].split(" — ")[0])}</a>' for n in sx)
        evs += (f'<article class="ev" data-v="{v}" data-iso="{" ".join(isos)}"><div class="d"><b>{dfmt(d)}</b>{E(reg[i])}</div><div>'
                f'<span class="bd {v}">{E(t["v"][v])}</span>' + (f'<span class="bd ty">{E(TN.get(ty, ""))}</span>' if ty else "") +
                f'<h3>{E(tt[i])}</h3><p>{E(wh[i])}</p><p class="j"><b>{E(t["jl"])}</b> · {E(jd[i])}</p><p class="sr">{E(t["sl"])} · {srcs}</p></div></article>')
    hist = "".join(f'<div class="hi"><span class="bd {v}">{E(t["v"][v])}</span><span class="d">{dfmt(d)} · {E(reg[i])}</span><br><b>{E(tt[i])}</b><p>{E(nt[i])}</p></div>' for d, reg, v, ty, tt, nt in C.HIST)
    stats = "".join(f'<div><b>{E(n if L=="ko" else n.replace("63억 달러","$6.3bn"))}</b><span>{E(a[i])}</span><small>{E(b[i])}</small></div>' for n, a, b in C.STATS)
    chain = "".join(f'<div><b>{E(a[i])}</b><h3>{E(b[i])}</h3><p>{E(c[i])}</p></div>' for a, b, c in C.CHAIN)
    rumor = "".join(f'<div><h3>{E(a[i])}</h3><p>{E(b[i])}</p></div>' for a, b in C.RUMOR)
    prep = "".join(f'<tr><th>{E(a[i])}</th><td>{E(b[i])}</td><td>{E(c[i])}</td><td>{E(d[i])}</td></tr>' for a, b, c, d in C.PREP)
    todo = "".join(f'<div><h3>{E(t[h])}</h3><ol>' + "".join(f"<li>{E(x[i])}</li>" for x in C.TODO[k]) + "</ol></div>" for k, h in (("p", "tp"), ("b", "tb"), ("g", "tg")))
    call = "".join(f'<div><b>{n}</b><span>{E(d[i])}</span></div>' for n, d in C.CALL)
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
<section class="s alt" id="now"><div class="wrap"><h2>{E(t["nh"])}</h2><p class="lede">{E(t["nl"])}</p><div class="flt" id="flt">{flt}</div><div id="evs">{evs}</div></div></section>
<section class="s" id="hist"><div class="wrap"><h2>{E(t["hh"])}</h2><p class="lede">{E(t["hl"])}</p><div class="hist">{hist}</div></div></section>
<section class="s alt" id="chain"><div class="wrap"><h2>{E(t["ch"])}</h2><p class="lede">{E(t["cl"])}</p><div class="chain">{chain}</div></div></section>
<section class="s" id="rumor"><div class="wrap"><h2>{E(t["rh"])}</h2><p class="lede">{E(t["rl"])}</p><div class="rm">{rumor}</div></div></section>
<section class="s alt" id="prep"><div class="wrap"><h2>{E(t["ph"])}</h2><p class="lede">{E(t["pl"])}</p>
<div class="tsc"><table class="pp"><thead><tr>{"".join(f"<th>{E(x)}</th>" for x in t["pth"])}</tr></thead><tbody>{prep}</tbody></table></div>
<div class="todo">{todo}</div><h3 style="color:#fff;font-size:20px;margin:48px 0 0">{E(t["callh"])}</h3><div class="call" style="margin-top:16px">{call}</div></div></section>
<section class="s" id="src"><div class="wrap"><h2>{E(t["sh"])}</h2><p class="lede" style="font-size:15px">{E(t["sn"])}</p><ol class="src">{src}</ol></div></section>
<footer><div class="wrap">{E(t["foot"])}</div></footer><div style="background:#0a0a0a;display:flex;justify-content:center;align-items:center;padding:40px 16px 44px"><a href="https://www.wmm-hoa.com" target="_blank" rel="noopener"><img src="/assets/wmm-logo-white.png" alt="WORLD MAKING MEMBERS" width="150" height="150" style="display:block;width:150px;height:150px"></a></div>
<script src="/hazards/hzfx.js"></script><script src="/hazards/hzfx2.js"></script>
<script>(function(){{var b=document.querySelectorAll("#flt button"),ev=document.querySelectorAll("#evs .ev");b.forEach(function(x){{x.onclick=function(){{var f=x.dataset.f;b.forEach(function(y){{y.setAttribute("aria-pressed",y===x)}});ev.forEach(function(e){{var ok=f==="all"||(f==="KR"?(" "+e.dataset.iso+" ").indexOf(" KR ")>=0:e.dataset.v===f);e.style.display=ok?"":"none"}})}}}})}})();</script>
</body></html>'''

def main():
    os.makedirs(os.path.join(OUT, "en"), exist_ok=True)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf8").write(page("ko"))
    open(os.path.join(OUT, "en", "index.html"), "w", encoding="utf8").write(page("en"))
    print("[cyber] built ko, en ·", len(C.REC), "recent ·", len(C.HIST), "landmark")

if __name__ == "__main__":
    main()
