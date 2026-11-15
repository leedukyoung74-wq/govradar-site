#!/usr/bin/env python3
"""Build /alerts/ (ko) and /alerts/en/ — governments telling people to prepare — plus a strip reused on
/cyber/, /hazards/ and the main-site world-watch page."""
import os, sys, html, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import alerts_data as A
E = lambda s: html.escape(str(s), quote=True)
OUT = os.path.join(HERE, "..", "cf", "extra", "alerts")
BASE = "https://radar.wmm-hoa.com"
def flag(iso): return "".join(chr(0x1F1E6 + ord(c) - 65) for c in iso)
def dfmt(d): return d.replace("-", ".")
GL = {"mil": ("군 대비", "Military"), "gov": ("정부 권고", "Government advice"), "fact": ("사실 확인", "Fact check")}
GC = {"mil": "#7fb0ff", "gov": "#f2b24a", "fact": "#59d6a4"}

CARD_CSS = '''
.hls{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.hl{position:relative;display:flex;flex-direction:column;background:#f4efe4;color:#16130f;border-radius:6px;overflow:hidden;text-decoration:none;min-width:0;box-shadow:0 10px 30px rgba(0,0,0,.35);font-family:"WMM Nexon","NEXON Lv1 Gothic OTF","Apple SD Gothic Neo",sans-serif}
.hl .mast{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:10px 14px;border-bottom:3px double #16130f;font-size:12px;letter-spacing:.4px}
.hl .mast b{font-size:13px;letter-spacing:.5px}.hl .hlf{font-size:20px;line-height:1;flex:none}.hl .mast .fl{font-size:22px;line-height:1}
.hl .grp{align-self:flex-start;margin:12px 14px 0;font-size:11px;font-weight:700;color:#fff;background:var(--gc);border-radius:3px;padding:3px 7px}
.hl h3{font-size:21px;line-height:1.32;margin:8px 14px 10px;font-weight:700;letter-spacing:-.3px;color:#16130f}
.hl .by{margin:0 14px;font-size:12.5px;color:#5b5346;border-top:1px solid #cfc6b4;padding-top:8px}
.hl .tg{display:flex;flex-wrap:wrap;gap:5px;margin:10px 14px 14px}.hl .tg span{font-size:11.5px;border:1px solid #16130f;border-radius:999px;padding:2px 8px}
.hl .go{margin-top:auto;padding:10px 14px;background:#16130f;color:#f4efe4;font-size:13px;font-weight:700}
.hl:hover{transform:translateY(-2px)}.hl{transition:transform .2s}
.hlstrip{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(260px,1fr);gap:16px;overflow-x:auto;padding:6px 2px 16px;scroll-snap-type:x mandatory}.hlstrip .hl{scroll-snap-align:start}
@media(max-width:1000px){.hls{grid-template-columns:1fr 1fr}}@media(max-width:600px){.hls{grid-template-columns:1fr}.hlstrip{grid-auto-columns:82%}}
'''

OUT_EN = {"Greek City Times (EU 보도자료 IP/26/2324 인용)": "Greek City Times (citing EU press release IP/26/2324)", "한국일보": "Hankook Ilbo"}
SRC_EN = {"Fox News — 국방부 FORTRESS 계획": "Fox News — Pentagon FORTRESS plan", "Utility Dive — 육군 소형 원자로 업체 선정": "Utility Dive — Army picks micro-reactor vendors",
          "The Vibes — 나라별 권고 기간 비교 (2026.11.2)": "The Vibes — advice periods compared by country (2 Nov 2026)", "국민재난안전포털 — 비상시 국민행동요령": "Korea Safety Portal — what to do in an emergency"}
def oname(o, L): return o if L == "ko" else OUT_EN.get(o, o)

def card(it, L, href=None):
    i = 0 if L == "ko" else 1
    d, iso, who, outlet, url, hd, body, lst, tags, grp = it
    tg = "".join(f"<span>{E(A.TAGS[t][i])}</span>" for t in tags[:5])
    return (f'<a class="hl" href="{E(href or url)}" {"" if href else "target=_blank rel=\"noopener nofollow\""} style="--gc:{GC[grp]}">'
            f'<div class="mast"><span class="hlf">{flag(iso)}</span><b>{E(who[i])}</b><span>{dfmt(d)}</span></div><span class="grp">{E(GL[grp][i])}</span>'
            f'<h3>{E(hd[i])}</h3><p class="by">{E(oname(outlet, L))}{" · 요약" if L=="ko" else " · our summary"}</p><div class="tg">{tg}</div>'
            f'<span class="go">{("원문 보기 →" if L=="ko" else "Read the source →") if not href else ("전체 보기 →" if L=="ko" else "Read more →")}</span></a>')

def items_sorted(): return sorted(A.ITEMS, key=lambda x: x[0], reverse=True)

def strip(L, n=8, title=True):
    """Headline-card strip for other pages."""
    ko = L == "ko"; link = "/alerts/" if ko else "/alerts/en/"
    its = items_sorted()[:n]
    h = ("<h2>각국 정부의 대비 권고 — 지금 세계는 무엇을 준비하라고 하나</h2><p class=\"lede\">전쟁·자연재해·감염병·사이버 공격에 공통으로, 미국 국방부와 유럽·일본·영국 정부가 군과 국민에게 내린 대비 지시와 권고입니다.</p>" if ko else
         "<h2>What governments are telling people to prepare for</h2><p class=\"lede\">Across war, disasters, epidemics and cyberattacks: what the Pentagon and governments in Europe, Japan and the UK have told troops and the public.</p>") if title else ""
    return (f'<style>{CARD_CSS}</style>{h}<div class="hlstrip">' + "".join(card(it, L, link + "#a-" + it[0] + "-" + it[1]) for it in its) +
            f'</div><p style="margin-top:6px"><a href="{link}" style="font-weight:700">{"나라별 대비 권고 전체 보기 →" if ko else "See every country →"}</a></p>')

CSS = r'''
@font-face{font-family:"WMM Nexon";font-weight:400;font-display:swap;src:local("NEXON Lv1 Gothic OTF"),url("/assets/fonts/NEXONLv1GothicOTF.woff") format("woff")}
@font-face{font-family:"WMM Nexon";font-weight:700;font-display:swap;src:local("NEXON Lv1 Gothic OTF Bold"),url("/assets/fonts/NEXONLv1GothicOTFBold.woff") format("woff")}
:root{--bg:#07090d;--p1:#0e121a;--p2:#141a24;--ink:#eef3fa;--soft:#c3cedc;--muted:#8695a8;--line:#222b38;--gold:#c9a45c;--f:"WMM Nexon","NEXON Lv1 Gothic OTF","Apple SD Gothic Neo","Malgun Gothic",sans-serif;color-scheme:dark}
*{box-sizing:border-box;margin:0}body{background:var(--bg);color:var(--soft);font:17px/1.65 var(--f)}a{color:#8fd4ff}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}section.s{padding:76px 0;border-top:1px solid var(--line)}section.s.alt{background:var(--p1)}
h2{color:var(--ink);font-size:clamp(26px,3.3vw,40px);line-height:1.25;margin:0 0 14px}.lede{max-width:46em;font-size:18px;margin-bottom:30px}
.hero{padding:60px 0 56px}.hero h1{color:#fff;font-size:clamp(34px,5vw,60px);line-height:1.15;margin:10px 0 16px;letter-spacing:-1px}.hero p{font-size:clamp(17px,1.8vw,20px);max-width:44em}.crumb{font-size:14px;color:var(--muted)}.crumb a{color:var(--muted)}
.bars{display:grid;gap:10px;margin-top:10px}.br{display:grid;grid-template-columns:190px minmax(0,1fr) 90px;gap:14px;align-items:center}.br span{font-size:15px;color:var(--ink)}.br i{display:block;height:16px;border-radius:999px;background:var(--c)}.br b{font-size:15px;color:#fff;text-align:right}
.flt{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}.flt button{font:600 14px/1 var(--f);color:var(--soft);background:var(--p2);border:1px solid var(--line);border-radius:999px;padding:9px 14px;cursor:pointer}.flt button[aria-pressed=true]{background:var(--ink);color:#07090d}
.it{display:grid;grid-template-columns:360px minmax(0,1fr);gap:28px;padding:30px 0;border-top:1px solid var(--line);scroll-margin-top:120px}
.it .tx h4{color:#fff;font-size:15px;margin:0 0 6px;color:var(--gold)}.it .tx p{margin:0 0 12px;font-size:16.5px}.it .ls{background:var(--p2);border-left:3px solid var(--gold);padding:12px 16px;border-radius:6px;font-size:15.5px;color:var(--ink)}.it .src{font-size:13px;color:var(--muted);margin-top:10px}
.note{font-size:14px;color:var(--muted)}
footer{border-top:1px solid var(--line);padding:30px 0;font-size:14px;color:var(--muted)}
@media(max-width:900px){.it{grid-template-columns:1fr;gap:14px}.br{grid-template-columns:110px minmax(0,1fr) 70px}section.s{padding:52px 0}}
'''
GATE = r'''<script>(function(){try{var q=location.search;if(/[?&]stay=/.test(q)||/(access_token|confirmation_token|recovery_token|invite_token|error_description)=/.test(location.hash))return;if(localStorage.getItem("wmm.auth.v1")||localStorage.getItem("gv_code"))return}catch(e){return}var l=document.documentElement.lang||"ko";location.replace("/welcome/"+(l==="ko"?"":"en/"))})();</script>'''
DAYS = [("미국 국방부 — 본토 주요 기지", "US DoD — major bases", 90, "90일", "90 days", "#7fb0ff"), ("독일", "Germany", 10, "최대 10일", "up to 10 days", "#f2b24a"),
        ("스웨덴 · 노르웨이", "Sweden · Norway", 7, "최대 7일", "up to 7 days", "#f2b24a"), ("일본", "Japan", 7, "3일~7일", "3–7 days", "#f2b24a"),
        ("EU · 프랑스 · 영국 · 캐나다 · 네덜란드 · 덴마크 · 벨기에", "EU · France · UK · Canada · Netherlands · Denmark · Belgium", 3, "3일(72시간)", "3 days (72 h)", "#f2b24a"),
        ("한국 (기존 요령)", "Korea (existing guidance)", 3, "2~3일 생존배낭", "2–3 day go-bag", "#59d6a4")]

def page(L):
    ko = L == "ko"; i = 0 if ko else 1; path = "/alerts/" if ko else "/alerts/en/"
    T = dict(title=("각국 정부의 대비 권고 — 군과 국민에게 무엇을 준비하라고 했나 · GOV RADAR" if ko else "What governments tell people to prepare for · GOV RADAR"),
             desc=("미국 국방부 기지 90일 자립, EU 72시간, 영국 Be Ready, 일본 방재청 3일~1주일 등 각국 정부의 대비 지시와 권고를 헤드라인 카드로 정리" if ko else "Pentagon 90-day bases, EU 72 hours, UK Be Ready, Japan 3–7 days and more, as headline cards"))
    mx = max(x[2] for x in DAYS)
    bars = "".join(f'<div class="br"><span>{E(a if ko else b)}</span><i style="--c:{c};width:{max(6, round(n/mx*100))}%"></i><b>{E(dk if ko else de)}</b></div>' for a, b, n, dk, de, c in DAYS)
    fl = [("all", "전체", "All"), ("mil", "군 대비", "Military"), ("gov", "정부 권고", "Government"), ("fact", "사실 확인", "Fact check"),
          ("energy", "에너지", "Energy"), ("food", "식량", "Food"), ("water", "물", "Water"), ("cyber", "사이버", "Cyber"), ("war", "전쟁·분쟁", "War")]
    flt = "".join(f'<button type="button" data-f="{k}" aria-pressed="{"true" if k=="all" else "false"}">{E(a if ko else b)}</button>' for k, a, b in fl)
    its = ""
    for it in items_sorted():
        d, iso, who, outlet, url, hd, body, lst, tags, grp = it
        its += (f'<article class="it" id="a-{d}-{iso}" data-g="{grp}" data-t="{" ".join(tags)}">{card(it, L)}<div class="tx"><h4>{flag(iso)} {E(who[i])} · {dfmt(d)}</h4><p>{E(body[i])}</p>'
                + (f'<div class="ls"><b>{"준비 목록" if ko else "Checklist"}</b> · {E(lst[i])}</div>' if lst else "") +
                f'<p class="src">{"출처" if ko else "Source"} · <a href="{E(url)}" target="_blank" rel="noopener nofollow">{E(oname(outlet, L))}</a></p></div></article>')
    extra = "".join(f'<li><a href="{E(u)}" target="_blank" rel="noopener nofollow">{E(n if ko else SRC_EN.get(n, n))}</a></li>' for n, u in A.SRC_EXTRA)
    sub = json.dumps([["#days", "나라별 기간" if ko else "Days by country"], ["#list", "헤드라인" if ko else "Headlines"], ["#src", "출처" if ko else "Sources"]], ensure_ascii=False)
    return f'''<!DOCTYPE html><html lang="{L}"><head>{GATE}<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(T["title"])}</title><meta name="description" content="{E(T["desc"])}"><link rel="canonical" href="{BASE}{path}">
<link rel="alternate" hreflang="ko" href="{BASE}/alerts/"><link rel="alternate" hreflang="en" href="{BASE}/alerts/en/">
<meta property="og:title" content="{E(T["title"])}"><meta property="og:description" content="{E(T["desc"])}"><meta property="og:image" content="{BASE}/assets/og-govradar.jpg">
<link rel="icon" href="/assets/mark.png"><style>{CSS}{CARD_CSS}</style></head><body>
<script>window.GVH_LANG_URL=function(l){{return l==="ko"?"/alerts/":"/alerts/en/"}};window.GVH_SUB=function(){{return {sub}}};</script><script src="/assets/gvhdr.js" data-l="{L}" data-g="world" data-a="alerts"></script>
<section class="hero"><div class="wrap"><p class="crumb"><a href="/cyber/{"" if ko else "en/"}">{"사이버 공격" if ko else "Cyberattacks"}</a> · <a href="/hazards/">{"재난 지도" if ko else "Hazard map"}</a> · <a href="/{L}/conflict/">{"세계 상황" if ko else "World watch"}</a> · <a href="{"/alerts/en/" if ko else "/alerts/"}">{"English" if ko else "한국어"}</a></p>
<h1>{"각국 정부의 대비 권고" if ko else "What governments tell people to prepare for"}</h1>
<p>{"전쟁·분쟁, 자연재해, 감염병, 사이버 공격에 공통으로 — 미국 국방부는 기지가 90일 스스로 버티도록, 유럽·영국·일본·캐나다는 가정이 3일~1주일 버티도록 준비하라고 했습니다. 각국 발표와 보도를 헤드라인 카드로 모았습니다." if ko else "Across war, disasters, epidemics and cyberattacks, the Pentagon wants bases able to hold out 90 days, and Europe, the UK, Japan and Canada want households ready for three days to a week. Here are the announcements as headline cards."}</p>
<p class="note" style="margin-top:12px">{"헤드라인 카드는 언론사 화면 캡처가 아니라, 기사 내용을 우리 말로 요약해 신문 1면처럼 꾸민 카드입니다(언론사 사진·지면은 저작권 때문에 싣지 않음). 카드를 누르면 원문으로 갑니다. 기준일 " if ko else "Cards are our own summaries styled as front pages, not screenshots (outlets' photos and layouts are copyrighted). Tap a card for the original. As of "}{A.UPDATED}</p></div></section>
<section class="s alt" id="days"><div class="wrap"><h2>{"누가 며칠을 버티라고 했나" if ko else "How long are people told to hold out?"}</h2><p class="lede">{"가정 권고는 대부분 3일(72시간)이고, 북유럽·일본은 1주일, 독일은 최대 10일입니다. 미군은 기지 단위로 90일을 목표로 합니다." if ko else "Most household advice is 3 days; the Nordics and Japan say a week, Germany up to 10 days. The US military aims for 90 days per base."}</p><div class="bars">{bars}</div></div></section>
<section class="s" id="list"><div class="wrap"><h2>{"헤드라인으로 보는 각국 발표" if ko else "The announcements, as headlines"}</h2><div class="flt" id="flt">{flt}</div><div id="its">{its}</div></div></section>
<section class="s alt" id="src"><div class="wrap"><h2>{"출처" if ko else "Sources"}</h2><p class="note">{"각 카드의 원문 링크와 아래 자료를 바탕으로 정리했습니다. 정부 발표 원문과 보도 내용이 다를 수 있어, 중요한 판단은 각국 정부 공식 사이트를 확인하세요." if ko else "Each card links to its source; see also the list below. Check official government sites before acting."}</p><ul style="margin-top:12px">{extra}</ul></div></section>
<footer><div class="wrap">GOV RADAR · {"월드메이킹멤버스(WMM)" if ko else "WORLD MAKING MEMBERS (WMM)"} · 73036396@naver.com</div></footer><div style="background:#0a0a0a;display:flex;justify-content:center;padding:40px 16px 44px"><a href="https://www.wmm-hoa.com" target="_blank" rel="noopener"><img src="/assets/wmm-logo-white.png" alt="WORLD MAKING MEMBERS" width="150" height="150"></a></div>
<script>(function(){{var b=document.querySelectorAll("#flt button"),it=document.querySelectorAll("#its .it");b.forEach(function(x){{x.onclick=function(){{var f=x.dataset.f;b.forEach(function(y){{y.setAttribute("aria-pressed",y===x)}});it.forEach(function(e){{var ok=f==="all"||e.dataset.g===f||(" "+e.dataset.t+" ").indexOf(" "+f+" ")>=0;e.style.display=ok?"":"none"}})}}}})}})();</script>
</body></html>'''

def patch_hazards():
    p = os.path.join(HERE, "..", "cf", "extra", "hazards", "index.html"); s = open(p, encoding="utf8").read()
    block = f'<!--ALERTS--><style>[data-al][hidden]{{display:none!important}}</style><section class="alt" id="alerts"><div class="in" data-al="ko">{strip("ko")}</div><div class="in" data-al="en" hidden>{strip("en")}</div></section><!--/ALERTS-->'
    if "<!--ALERTS-->" in s: s = re.sub(r"<!--ALERTS-->.*?<!--/ALERTS-->", lambda m: block, s, flags=re.S)
    else: s = s.replace('<section class="alt" id="apophis">', block + '\n<section class="alt" id="apophis">', 1)
    open(p, "w", encoding="utf8").write(s)

def main():
    os.makedirs(os.path.join(OUT, "en"), exist_ok=True)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf8").write(page("ko"))
    open(os.path.join(OUT, "en", "index.html"), "w", encoding="utf8").write(page("en"))
    patch_hazards()
    print("[alerts] built ko, en ·", len(A.ITEMS), "items")

if __name__ == "__main__":
    main()
