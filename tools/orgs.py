#!/usr/bin/env python3
"""'프로젝트를 이끄는 세 주체' showcase — ONE source for every screen that shows it:
welcome home (/welcome/), welcome projects (/welcome/projects/) and the GOV RADAR main page (/<lang>/).
  python3 tools/orgs.py          -> writes the block into tools/welcome_src/{index,projects}/index.html (between markers)
  build.py imports html(L) for the main page; non-Korean text comes from the welcome translations (tools/welcome_i18n)."""
import importlib, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
A, B = "<!--orgs:start-->", "<!--orgs:end-->"
CSS = """<style id="gx-orgs-css">
@property --gxa{syntax:"<angle>";inherits:false;initial-value:0deg}
.gx-orgs{position:relative;overflow:hidden;isolation:isolate;background:#050a16;color:#fff;padding:120px 20px 130px;font-family:"WMM Nexon","NEXON Lv1 Gothic OTF",inherit;word-break:keep-all}
.gx-orgs .gx-sweep{position:absolute;left:50%;top:50%;width:160vmax;height:160vmax;transform:translate(-50%,-50%);background:conic-gradient(from 0deg,transparent 0 290deg,rgba(64,140,255,.20) 345deg,rgba(120,180,255,.32) 359deg,transparent 360deg);animation:gxspin 10s linear infinite;z-index:-2;pointer-events:none}
.gx-orgs .gx-rings{position:absolute;inset:0;z-index:-1;pointer-events:none;background:radial-gradient(circle at 50% 50%,transparent 0 22%,rgba(255,255,255,.05) 22.2% 22.4%,transparent 22.6% 38%,rgba(255,255,255,.045) 38.2% 38.4%,transparent 38.6% 56%,rgba(255,255,255,.04) 56.2% 56.4%,transparent 56.6%),radial-gradient(circle at 15% 10%,rgba(201,162,74,.16),transparent 40%),radial-gradient(circle at 85% 90%,rgba(60,120,255,.18),transparent 45%)}
.gx-in{position:relative;max-width:1180px;margin:0 auto}
.gx-orgs h2{margin:0;font-size:clamp(30px,4.2vw,48px);font-weight:700;letter-spacing:-.02em;line-height:1.25;text-align:center;text-wrap:balance}
.gx-orgs h2::after{content:"";display:block;width:84px;height:3px;margin:22px auto 0;background:linear-gradient(90deg,#c9a24a,#f3d98b,#c9a24a);border-radius:2px;box-shadow:0 0 18px rgba(243,217,139,.6)}
.gx-lede{max-width:720px;margin:22px auto 64px;text-align:center;font-size:17px;line-height:1.8;color:#c9d3e6;text-wrap:pretty}
.gx-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:30px}
.gx-card{--gxa:0deg;position:relative;display:flex;flex-direction:column;border-radius:20px;background:linear-gradient(180deg,#111d38,#0a1329);color:#fff;text-decoration:none;isolation:isolate;transition:transform .6s cubic-bezier(.2,.8,.2,1),box-shadow .6s;box-shadow:0 20px 50px rgba(0,0,0,.45)}
.gx-card::before{content:"";position:absolute;inset:-1.5px;border-radius:21.5px;padding:1.5px;background:conic-gradient(from var(--gxa),#c9a24a,#3f7bff 25%,#f3d98b 50%,#3f7bff 75%,#c9a24a);-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:.55;animation:gxborder 6s linear infinite;z-index:-1;transition:opacity .5s}
.gx-card:hover,.gx-card:focus-visible{transform:translateY(-12px);box-shadow:0 34px 70px rgba(0,0,0,.6),0 0 46px rgba(201,162,74,.28);outline:none}
.gx-card:hover::before,.gx-card:focus-visible::before{opacity:1}
.gx-ph{position:relative;height:240px;display:grid;place-items:center;overflow:hidden;border-radius:20px 20px 0 0;background:radial-gradient(circle at 50% 55%,#1d3463 0,#0b1530 62%,#080f22 100%)}
.gx-ph::before{content:"";position:absolute;width:210px;height:210px;border-radius:50%;background:conic-gradient(from 0deg,transparent 0 200deg,rgba(243,217,139,.0) 220deg,rgba(243,217,139,.55) 330deg,transparent 360deg);filter:blur(6px);animation:gxspin 5.5s linear infinite}
.gx-ph::after{content:"";position:absolute;width:176px;height:176px;border-radius:50%;border:1px solid rgba(243,217,139,.35);box-shadow:0 0 40px rgba(64,140,255,.25) inset}
.gx-ph img{position:relative;z-index:1;width:150px;height:150px;object-fit:contain;filter:drop-shadow(0 0 22px rgba(201,162,74,.45));animation:gxfloat 5s ease-in-out infinite}
.gx-ph.photo{background-size:cover;background-position:center}
.gx-ph.photo::before,.gx-ph.photo::after{display:none}
.gx-ph.photo .gx-zoom{position:absolute;inset:0;background:inherit;background-size:cover;background-position:center;transition:transform 1.4s cubic-bezier(.2,.8,.2,1)}
.gx-card:hover .gx-zoom{transform:scale(1.08)}
.gx-shine{position:absolute;inset:0;border-radius:20px;overflow:hidden;pointer-events:none}
.gx-shine::before{content:"";position:absolute;top:0;left:-70%;width:45%;height:100%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.16),transparent);transform:skewX(-18deg);transition:left 1s ease}
.gx-card:hover .gx-shine::before{left:135%}
.gx-bd{display:flex;flex-direction:column;flex:1;padding:30px 30px 32px}
.gx-bd h3{margin:0 0 14px;font-size:24px;font-weight:700;letter-spacing:-.01em}
.gx-bd p{margin:0;font-size:15.5px;line-height:1.8;color:#c3cde0;text-wrap:pretty}
.gx-bd ul{list-style:none;margin:22px 0 26px;padding:0}
.gx-bd li{position:relative;padding:11px 0 11px 22px;border-top:1px solid rgba(255,255,255,.08);font-size:15px}
.gx-bd li::before{content:"";position:absolute;left:2px;top:50%;width:7px;height:7px;margin-top:-3.5px;background:#d9b65c;transform:rotate(45deg);box-shadow:0 0 10px rgba(243,217,139,.7)}
.gx-go{margin-top:auto;display:inline-flex;align-items:center;gap:10px;font-weight:700;font-size:16px;color:#f0d68a}
.gx-go i{font-style:normal;display:inline-block;transition:transform .4s}
.gx-card:hover .gx-go i{transform:translateX(8px)}
.gx-rv{opacity:0;transform:translateY(36px);transition:opacity .9s ease,transform .9s cubic-bezier(.2,.8,.2,1)}
.gx-rv.on{opacity:1;transform:none}
@keyframes gxspin{to{transform:translate(-50%,-50%) rotate(360deg)}}
.gx-ph::before{animation-name:gxspin2}@keyframes gxspin2{to{transform:rotate(360deg)}}
@keyframes gxborder{to{--gxa:360deg}}
@keyframes gxfloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@media (max-width:980px){.gx-grid{grid-template-columns:1fr;max-width:560px;margin:0 auto}.gx-orgs{padding:84px 16px 96px}}
@media (prefers-reduced-motion:reduce){.gx-orgs *,.gx-orgs *::before,.gx-orgs .gx-sweep{animation:none!important;transition:none!important}.gx-rv{opacity:1;transform:none}}
html[dir=rtl] .gx-bd li{padding:11px 22px 11px 0}html[dir=rtl] .gx-bd li::before{left:auto;right:2px}html[dir=rtl] .gx-go i{transform:scaleX(-1)}
</style>"""
JS = """<script>(function(){var s=document.querySelectorAll(".gx-rv");if(!("IntersectionObserver" in window)){[].forEach.call(s,function(e){e.classList.add("on")});return}
var o=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add("on");o.unobserve(x.target)}})},{threshold:.15});[].forEach.call(s,function(e,i){e.style.transitionDelay=(i%3)*0.15+"s";o.observe(e)})})();</script>"""
def body(member_href):
    return f"""<section class="gx-orgs" id="orgs" aria-labelledby="gx-orgs-h"><div class="gx-sweep" aria-hidden="true"></div><div class="gx-rings" aria-hidden="true"></div><div class="gx-in">
<h2 id="gx-orgs-h">프로젝트를 이끄는 세 주체</h2>
<p class="gx-lede">한국 법인과 영국 본사 네트워크, 그리고 사업마다 꾸리는 컨소시엄이 역할을 나눠 프로젝트를 기획하고 실행합니다.</p>
<div class="gx-grid">
<a class="gx-card gx-rv" href="https://www.wmm-hoa.com" target="_blank" rel="noopener"><span class="gx-shine"></span><div class="gx-ph"><img src="/assets/brand-wmm-white.webp" alt="WORLD MAKING MEMBERS" loading="lazy"></div><div class="gx-bd">
<h3>월드메이킹멤버스 (WMM)</h3>
<p>2021년 12월 서울에서 설립한 경영컨설팅 법인입니다. GOV RADAR를 운영하고, GCSME의 한국 운영법인으로 한국 기업의 해외 진출과 프로젝트 파트너십을 맡습니다.</p>
<ul><li>GOV RADAR 운영</li><li>해외 진출·프로젝트 파트너십</li><li>GCSME 한국 운영법인</li></ul>
<span class="gx-go">소개자료 보기 <i>→</i></span></div></a>
<a class="gx-card gx-rv" href="https://www.gcsme.kr/" target="_blank" rel="noopener"><span class="gx-shine"></span><div class="gx-ph"><img src="/assets/brand-gcsme-crest.webp" alt="GCSME" loading="lazy"></div><div class="gx-bd">
<h3>GCSME</h3>
<p>Global &amp; Commonwealth SME Club. 영국 런던에 본사를 둔 중소기업 국제 네트워크로, 193개국 네트워크 안에서 80개국 이상에 컨설팅을 해 왔습니다.</p>
<ul><li>영국 런던 본사</li><li>193개국 네트워크</li><li>80개국 이상 컨설팅</li></ul>
<span class="gx-go">GCSME 한국지사 <i>→</i></span></div></a>
<a class="gx-card gx-rv" href="{member_href}"><span class="gx-shine"></span><div class="gx-ph photo" style="background-image:linear-gradient(rgba(5,10,22,.35),rgba(5,10,22,.75)),url('https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=900&q=60')"><span class="gx-zoom"></span></div><div class="gx-bd">
<h3>전략적 컨소시엄</h3>
<p>대학·연구기관·은행·국제기구·정부기관·대사관·기업·전문가가 사업마다 팀을 꾸려 함께 수행하는 온라인 협의체입니다.</p>
<ul><li>사업별 팀 구성</li><li>협약 대학 박사진 검토</li><li>온라인 협업</li></ul>
<span class="gx-go">멤버십 보기 <i>→</i></span></div></a>
</div></div></section>"""
def block(member_href="/welcome/membership/"):
    return A + CSS + body(member_href) + JS + B
NEW_KEYS = ["GCSME 한국지사", "소개자료 보기"]
def html(L):
    """Main GOV RADAR page block in language L (same text as the welcome pages)."""
    WL = ("ko", "en", "es", "fr", "ar", "vi", "id")
    base = "/welcome/" if L == "ko" else f"/welcome/{L if L in WL else 'en'}/"
    s = block(base + "membership/")
    if L == "ko": return s
    keys = json.load(open(os.path.join(HERE, "welcome_i18n", "keys.json"), encoding="utf-8"))
    sys.path.insert(0, os.path.join(HERE, "welcome_i18n"))
    try: T = importlib.import_module(L if L in ("en", "es", "fr", "ar", "vi", "id") else "en").T
    except Exception: T = importlib.import_module("en").T
    pairs = sorted(((keys[i], T[i]) for i in range(len(keys)) if i in T and keys[i]), key=lambda p: -len(p[0]))
    for k, v in pairs: s = s.replace(k, v)
    if re.search(r">[^<]*[가-힣][^<]*<", s):   # anything left untranslated -> leave the block out rather than show Korean
        return ""
    return s
if __name__ == "__main__":
    for sub, anchor in (("", '<section aria-label="Partners"'), ("projects/", None)):
        p = os.path.join(HERE, "welcome_src", sub, "index.html"); s = open(p, encoding="utf-8").read()
        if A in s: s = re.sub(re.escape(A) + r".*?" + re.escape(B), lambda m: block(), s, flags=re.S)
        elif anchor: s = s.replace(anchor, block() + "\n" + anchor, 1)
        else: s = re.sub(r'<section class="pj-s" id="orgs">.*?</div></div></section>', lambda m: block(), s, count=1, flags=re.S)
        open(p, "w", encoding="utf-8").write(s)
    k = json.load(open(os.path.join(HERE, "welcome_i18n", "keys.json"), encoding="utf-8"))
    for x in NEW_KEYS:
        if x not in k: k.append(x)
    json.dump(k, open(os.path.join(HERE, "welcome_i18n", "keys.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("orgs block synced")
