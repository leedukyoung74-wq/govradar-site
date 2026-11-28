# -*- coding: utf-8 -*-
"""About page (/L/about/): a sign-up page built on the live feeds. Hero radar plots countries with open tenders on a
North-Pole-centred world map (Korea at the top); every number on the page is computed from the daily feeds."""
import json, os
from about_txt import K
ROOT = os.path.dirname(os.path.abspath(__file__))
SUMMARY = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/cty/_summary.json"

def _summary():
    try: return json.load(open(os.path.join(ROOT, "data_branch", "feeds", "cty", "_summary.json"), encoding="utf-8"))
    except Exception: return {}
def _cent():
    try: return json.load(open(os.path.join(ROOT, "src", "centroids.json")))
    except Exception: return {}

def fmt(n, L):
    s = f"{int(n):,}"
    return s.replace(",", ".") if L in ("es", "vi", "id") else s.replace(",", " ") if L == "fr" else s
def money(v, L):
    if L == "ko": return f"약 {fmt(round(v / 1e8), L)}억 달러"
    b = v / 1e9; x = f"{b:.1f}"
    if L in ("es", "fr", "vi", "id"): x = x.replace(".", ",")
    return f"US${x}bn" if L in ("en", "ar") else f"US$ {x} bn" if L in ("es", "fr") else f"US${x} tỷ" if L == "vi" else f"US${x} miliar"

CSS = """
.ab{word-break:keep-all;overflow-wrap:anywhere;--nv:#050e1f;--nv2:#0b1f3a;--gd:#e9c46a;--iv:#f4f1ea;--tx:#0d1726}
.ab section{position:relative}.ab .w{max-width:1200px;margin:0 auto;padding:0 32px}
.ab h1,.ab h2{letter-spacing:-.02em}
.ab-hero{background:var(--nv);color:#fff;padding:72px 0 0;overflow:hidden}
.ab-hg{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:40px;align-items:center}
.ab-hero h1{font-size:clamp(34px,4.7vw,70px);line-height:1.08;margin:0 0 26px;font-weight:700}
.ab-hero .lede{font-size:19px;line-height:1.75;color:#c9d3e0;max-width:34em;margin:0 0 34px}
.ab-cta{display:flex;flex-wrap:wrap;gap:14px 24px;align-items:center}
.ab-b{display:inline-block;background:var(--gd);color:#071226;font-weight:700;font-size:17px;padding:16px 30px;border-radius:0;border:0;cursor:pointer;text-decoration:none;font-family:inherit}
.ab-b:hover{background:#f2d58a}.ab-l{color:#fff;font-size:16px;text-decoration:underline;text-underline-offset:5px}
.ab-rd{position:relative;width:100%;max-width:600px;margin-inline-start:auto;aspect-ratio:1}
.ab-rd canvas{width:100%;height:100%;display:block}
.ab-cap{font-size:13px;color:#7f8ea5;margin:10px 0 0;max-width:600px;margin-inline-start:auto}
.ab-ctw{background:#081830;margin-top:56px}.ab-ct{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:24px;padding:34px 32px 46px}
.ab-ct b{display:block;font-size:clamp(28px,3.2vw,44px);color:var(--gd);font-weight:700;line-height:1.1}
.ab-ct>div>span{display:block;font-size:15px;color:#fff;margin-top:6px}.ab-ct small{display:block;font-size:13px;color:#8b9ab0;margin-top:3px}
.ab-why{background:var(--iv);color:var(--tx);padding:130px 0}
.ab h2{font-size:clamp(30px,3.6vw,50px);line-height:1.2;margin:0 0 18px;max-width:20em}
.ab-why .f{display:grid;grid-template-columns:minmax(0,6fr) minmax(0,5fr);gap:40px;align-items:baseline;padding:44px 0}
.ab-why .f+.f{margin-top:8px}
.ab-why .f b{white-space:nowrap;font-size:clamp(40px,5.6vw,92px);line-height:1;color:var(--nv2);font-weight:700;letter-spacing:-.03em}
.ab-why .f p{font-size:19px;line-height:1.75;margin:0}
.ab .fine{font-size:13.5px;color:#6b7686;margin-top:24px}
.ab-st{background:var(--nv2);color:#fff;padding:130px 0}
.ab-st .ld,.ab-pl .ld,.ab-pr .ld{font-size:18px;line-height:1.7;max-width:40em;margin:0 0 56px;color:inherit;opacity:.85}
.ab-tr{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:22px;position:relative;list-style:none;margin:0;padding:34px 0 0}
.ab-tr:before{content:"";position:absolute;top:7px;inset-inline:0;height:2px;background:var(--gd);opacity:.55}
.ab-tr li{position:relative}.ab-tr li:before{content:"";position:absolute;top:-34px;inset-inline-start:0;width:16px;height:16px;border-radius:50%;background:var(--gd)}
.ab-tr h3{font-size:20px;color:var(--gd);margin:0 0 10px}.ab-tr p{font-size:15.5px;line-height:1.65;color:#d6deea;margin:0 0 14px}
.ab-tr a{color:#fff;font-size:15px;text-decoration:underline;text-underline-offset:4px}
.ab-pl{background:#fff;color:var(--tx);padding:130px 0}
.ab-pl .r{display:grid;grid-template-columns:220px minmax(0,1fr);gap:32px;padding:34px 36px;background:#f5f6f8}
.ab-pl .r+.r{margin-top:12px}.ab-pl .r:first-of-type{background:var(--nv2);color:#fff}
.ab-pl .r h3{font-size:28px;margin:0}.ab-pl .r small{display:block;font-size:15px;margin-top:6px;opacity:.75}
.ab-pl ol{margin:0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
.ab-pl ol li{font-size:16.5px;line-height:1.6}
.ab-pl .r:first-of-type ol li:first-child button{all:unset;cursor:pointer;text-decoration:underline;text-underline-offset:4px;font-weight:700;color:var(--gd)}
.ab-more{margin-top:28px}.ab-more a{color:var(--nv2);font-weight:700;text-decoration:underline;text-underline-offset:5px}
.ab-sm{background:var(--iv);color:var(--tx);padding:130px 0}
.ab-smg{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:64px;align-items:center}
.ab-smg img{width:100%;height:auto;display:block;box-shadow:0 30px 60px rgba(5,14,31,.22)}
.ab-smg p{font-size:18px;line-height:1.75;margin:0 0 30px}
.ab-b2{display:inline-block;border:2px solid var(--nv2);color:var(--nv2);font-weight:700;font-size:16px;padding:14px 26px;text-decoration:none}
.ab-sm .ab-b{background:var(--nv2);color:#fff}
.ab-pr{background:#fff;color:var(--tx);padding:130px 0}
.ab-pr .p{display:grid;grid-template-columns:240px 260px minmax(0,1fr);gap:28px;padding:30px 0;align-items:baseline}
.ab-pr .p+.p{border-top:1px solid #e6e8ec}
.ab-pr .p h3{font-size:21px;margin:0}.ab-pr .p b{font-size:26px;color:var(--nv2)}.ab-pr .p p{font-size:16px;line-height:1.65;margin:0;color:#3b4554}
.ab-co{background:var(--nv);color:#fff;padding:130px 0}
.ab-org{display:grid;grid-template-columns:1fr 1fr;gap:56px;margin:0 0 80px}
.ab-org img{height:64px;width:auto;margin-bottom:20px;display:block}
.ab-org h3{font-size:24px;margin:0 0 12px}.ab-org p{font-size:17px;line-height:1.75;color:#c9d3e0;margin:0}
.ab-prm{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr);gap:56px}
.ab-prm h3{font-size:22px;color:var(--gd);margin:0 0 18px}
.ab-prm ul{margin:0;padding:0;list-style:none}.ab-prm li{font-size:17px;line-height:1.6;padding:12px 0;color:#e6ebf2}
.ab-src{width:100%;border-collapse:collapse;font-size:15px}.ab-src th{text-align:start;color:#8b9ab0;font-weight:400;padding:8px 10px 8px 0}
.ab-src td{padding:12px 10px 12px 0;color:#e6ebf2;vertical-align:top;border-top:1px solid rgba(255,255,255,.12)}
.ab-co .fine{color:#8b9ab0}.ab-co a{color:#fff}
.ab-end{color:#fff;padding:150px 0 120px;background:#050e1f;overflow:hidden}
.ab-end>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.3}
.ab-end .w{position:relative}.ab-end h2{font-size:clamp(34px,5vw,68px);max-width:16em}
.ab-end p{font-size:19px;line-height:1.7;color:#dbe2ec;max-width:34em;margin:0 0 36px}
.ab-end .pc{margin-top:60px}.ab-end .pc p,.ab-end .pc{font-size:12px!important;color:#9fb0c6}.ab-end .pc a{color:#9fb0c6}
@media(max-width:1000px){.ab-tr{grid-template-columns:repeat(3,minmax(0,1fr));row-gap:48px}.ab-tr:before{display:none}.ab-pr .p{grid-template-columns:1fr 1fr}.ab-pr .p p{grid-column:1/-1}.ab-ct{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.ab .w{padding:0 16px}.ab-hero{padding-top:40px}.ab-hg{grid-template-columns:1fr;gap:8px}.ab-rd{max-width:440px;margin:0 auto}.ab-cap{margin:6px auto 0;text-align:center}
.ab-hero .lede{font-size:17px}.ab-ctw{margin-top:36px}.ab-ct{grid-template-columns:1fr 1fr;gap:22px 16px;padding:28px 16px 34px}.ab-ct div:last-child{grid-column:1/-1}
.ab-why,.ab-st,.ab-pl,.ab-sm,.ab-pr,.ab-co{padding:84px 0}.ab-why .f{grid-template-columns:1fr;gap:10px;padding:28px 0}.ab-why .f p{font-size:17px}
.ab-tr{grid-template-columns:1fr;padding:0;padding-inline-start:30px;row-gap:34px}.ab-tr:before{display:block;top:0;bottom:0;width:2px;height:auto;inset-inline-start:7px;inset-inline-end:auto}.ab-tr li:before{top:4px;inset-inline-start:-30px}
.ab-pl .r{grid-template-columns:1fr;gap:16px;padding:26px 20px}.ab-pl ol{grid-template-columns:1fr;gap:10px}
.ab-smg,.ab-org,.ab-prm{grid-template-columns:1fr;gap:36px}.ab-pr .p{grid-template-columns:1fr;gap:6px}.ab-end{padding:100px 0 80px}
.ab-src th:last-child,.ab-src td:last-child{display:none}}
"""

JS = r"""(function(){var cv=document.getElementById("abRadar");if(!cv)return;var D=JSON.parse(cv.dataset.d),cx=cv.getContext("2d"),W=0,R=0,dpr=Math.min(2,window.devicePixelRatio||1),
rm=matchMedia("(prefers-reduced-motion: reduce)").matches,SP=(rm?.5:1)*Math.PI*2/8000,s=0,last=0,run=true,lab=[],P=[];
function size(){var b=cv.getBoundingClientRect();W=b.width;if(!W)return;cv.width=W*dpr;cv.height=W*dpr;cx.setTransform(dpr,0,0,dpr,0,0);R=W/2-6;
 P=D.b.map(function(x){var r=R*Math.min(1,(90-x[0])/150),a=-(x[1]-127.8)*Math.PI/180-Math.PI/2;return{x:W/2+r*Math.cos(a),y:W/2+r*Math.sin(a),a:((a%(2*Math.PI))+2*Math.PI)%(2*Math.PI),n:x[2],t:x[3],seen:-1}})}
function kr(){var r=R*(90-35.9)/150;return{x:W/2,y:W/2-r}}
function frame(t){if(!run)return;requestAnimationFrame(frame);if(t-last<33)return;var dt=last?Math.min(t-last,100):33;last=t;s=(s+SP*dt)%(2*Math.PI);draw(t)}
function draw(t){var c=W/2;cx.clearRect(0,0,W,W);cx.strokeStyle="rgba(233,196,106,.16)";cx.lineWidth=1;
 [60,30,0,-30].forEach(function(l){cx.beginPath();cx.arc(c,c,R*(90-l)/150,0,7);cx.stroke()});
 for(var m=0;m<12;m++){var a=m*Math.PI/6;cx.beginPath();cx.moveTo(c,c);cx.lineTo(c+R*Math.cos(a),c+R*Math.sin(a));cx.stroke()}
 if(cx.createConicGradient){var g=cx.createConicGradient(s-1.1,c,c);g.addColorStop(0,"rgba(233,196,106,0)");g.addColorStop(1.1/(2*Math.PI),"rgba(233,196,106,.28)");g.addColorStop(1.1/(2*Math.PI)+.0001,"rgba(233,196,106,0)");
  cx.fillStyle=g;cx.beginPath();cx.moveTo(c,c);cx.arc(c,c,R,s-1.1,s);cx.closePath();cx.fill()}else{cx.fillStyle="rgba(233,196,106,.12)";cx.beginPath();cx.moveTo(c,c);cx.arc(c,c,R,s-.6,s);cx.closePath();cx.fill()}
 cx.strokeStyle="rgba(233,196,106,.9)";cx.lineWidth=1.5;cx.beginPath();cx.moveTo(c,c);cx.lineTo(c+R*Math.cos(s),c+R*Math.sin(s));cx.stroke();
 P.forEach(function(p){var d=((s-p.a)%(2*Math.PI)+2*Math.PI)%(2*Math.PI),gl=Math.max(0,1-d/3.6),rr=(2.2+Math.sqrt(p.n)*1.25)*(1+gl*.7);
  cx.fillStyle="rgba(233,196,106,"+(.22+.78*gl)+")";cx.beginPath();cx.arc(p.x,p.y,rr,0,7);cx.fill();
  if(d<.06&&p.seen!==Math.floor(t/1500)&&p.n>=2&&!lab.some(function(o){return Math.abs(o.p.x-p.x)<110&&Math.abs(o.p.y-p.y)<26})){p.seen=Math.floor(t/1500);lab.push({p:p,t:t});if(lab.length>4)lab.shift()}});
 var k=kr();cx.strokeStyle="#fff";cx.lineWidth=1.5;cx.beginPath();cx.arc(k.x,k.y,6,0,7);cx.stroke();cx.fillStyle="#fff";cx.font="600 13px "+getComputedStyle(cv).fontFamily;cx.textAlign="center";cx.fillText(D.k,k.x,k.y-12);
 cx.font="13px "+getComputedStyle(cv).fontFamily;lab=lab.filter(function(L){var age=(t-L.t)/2600;if(age>1)return false;var al=age<.15?age/.15:1-(age-.15)/.85,tx=L.p.t+" · "+L.p.n,tw=cx.measureText(tx).width+14,
  x=Math.max(tw/2+2,Math.min(W-tw/2-2,L.p.x)),y=L.p.y-16;cx.globalAlpha=al;cx.fillStyle="rgba(5,14,31,.88)";cx.fillRect(x-tw/2,y-15,tw,21);cx.fillStyle="#fff";cx.fillText(tx,x,y);cx.globalAlpha=1;return true})}
size();addEventListener("resize",size);
if("IntersectionObserver"in window)new IntersectionObserver(function(e){var v=e[0].isIntersecting;if(v&&!run){run=true;last=0;requestAnimationFrame(frame)}else if(!v)run=false}).observe(cv);
document.addEventListener("visibilitychange",function(){if(document.hidden)run=false;else if(!run){run=true;last=0;requestAnimationFrame(frame)}});
requestAnimationFrame(frame);
fetch(cv.dataset.src,{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){var f=new Intl.NumberFormat(document.documentElement.lang);
 var set=function(k,v){document.querySelectorAll('[data-k="'+k+'"]').forEach(function(e){e.textContent=f.format(v)})};set("tn",j.t.n);set("tc",j.t.c);set("pn",j.p.n);set("an",j.a.n);
}).catch(function(){})})();"""

def page(L, C):
    e = C["e"]; t = K.get(L) or K["en"]; S = _summary(); cen = _cent()
    tn = S.get("t", {}).get("n", 0); tc = S.get("t", {}).get("c", 0); pn = S.get("p", {}).get("n", 0); pusd = S.get("p", {}).get("usd", 0)
    an = S.get("a", {}).get("n", 0); kr = S.get("a", {}).get("kr", 0); fr_, to_ = S.get("a", {}).get("from", ""), S.get("a", {}).get("to", "")
    gap = S.get("gap") or 0; upd = (S.get("updated") or "")[:10]
    span = lambda k, v: f'<span data-k="{k}">{fmt(v, L)}</span>'
    V = dict(tn=span("tn", tn), tc=span("tc", tc), pn=span("pn", pn), pusd=money(pusd, L), an=span("an", an), kr=fmt(kr, L), gap=gap, upd=upd, **{"from": fr_, "to": to_})
    F = lambda s: s.format(**V)
    blips = [[*cen[i], n, C["nm"](i, L) if i in C["BY"] else i] for i, n in sorted(S.get("blips", {}).items(), key=lambda kv: -kv[1]) if i in cen]
    dd = e(json.dumps({"b": blips, "k": t["korea"]}, ensure_ascii=False))
    href = {"country": f"/{L}/#map", "pipe": f"/{L}/win/#pipe", "board": f"/{L}/mdb/#deadlines", "fit": f"/{L}/pricing/?p=fit#order",
            "awards": f"/{L}/win/#awards", "partner": f"/{L}/consortium/"}
    AR = "←" if L == "ar" else "→"
    toc = t["toc"]; ph = C["img"]("port", "", w=1600)
    counters = (f'<div><b>{span("tn", tn)}</b><span>{e(t["c_t"])}</span><small>{F(t["c_tc"])}</small></div>'
                f'<div><b>{span("pn", pn)}</b><span>{e(t["c_p"])}</span><small>{e(money(pusd, L))}</small></div>'
                f'<div><b>{span("an", an)}</b><span>{e(t["c_a"])}</span><small>{F(t["c_ad"])}</small></div>'
                f'<div><b>193+23</b><span>{e(t["c_cov"])}</span></div><div><b>7</b><span>{e(t["c_lang"])}</span></div>')
    facts = "".join(f'<div class="f"><b>{F(b)}</b><p>{F(p)}</p></div>' for b, p in t["p_facts"])
    stages = "".join(f'<li><h3>{e(n)}</h3><p>{F(x)}</p><a href="{href[k]}">{e(lk)} {AR}</a></li>' for n, x, lk, k in t["stages"])
    def steps(i, ss):
        out = []
        for j, x in enumerate(ss):
            out.append(f'<li><button type="button" data-auth="signup">{e(x)}</button></li>' if (i == 0 and j == 0) else f'<li>{e(x)}</li>')
        return "".join(out)
    plan = "".join(f'<div class="r"><div><h3>{e(w)}</h3><small>{e(c)}</small></div><ol>{steps(i, ss)}</ol></div>' for i, (w, c, ss) in enumerate(t["plan"]))
    prices = "".join(f'<div class="p"><h3>{e(n)}</h3><b>{e(pr)}</b><p>{e(w)}</p></div>' for n, pr, w in t["pr_rows"])
    orgs = "".join(f'<div><img src="/assets/{im}" alt="{e(n)}" loading="lazy"><h3>{e(n)}</h3><p>{e(p)}</p></div>' for (n, p), im in zip(t["orgs"], ("brand-wmm-white.webp", "brand-gcsme-crest.webp")))
    srcs = "".join(f'<tr><td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td></tr>' for a, b, c in t["srcs"])
    sample = "sample-ko.webp" if L == "ko" else "sample-en.webp"
    body = f'''<style>{CSS}</style><div class="ab">
<section class="ab-hero" id="about-top" data-toc="{e(toc[0])}"><div class="w"><div class="ab-hg"><div><h1>{t["h1"]}</h1><p class="lede">{e(t["lede"])}</p>
<div class="ab-cta"><button class="ab-b" data-auth="signup">{e(t["cta1"])}</button><a class="ab-l" href="/{L}/mdb/#deadlines">{e(t["cta2"])} {AR}</a></div></div>
<div><div class="ab-rd"><canvas id="abRadar" data-d="{dd}" data-src="{SUMMARY}" role="img" aria-label="{e(t["cap"])}"></canvas></div><p class="ab-cap">{e(t["cap"])}</p></div></div>
</div><div class="ab-ctw"><div class="w ab-ct">{counters}</div></div></section>
<section class="ab-why" id="why" data-toc="{e(toc[1])}"><div class="w"><h2>{e(t["p_h"])}</h2>{facts}<p class="fine">{F(t["p_note"])}</p></div></section>
<section class="ab-st" id="stages" data-toc="{e(toc[2])}"><div class="w"><h2>{e(t["l_h"])}</h2><p class="ld">{e(t["l_lede"])}</p><ol class="ab-tr">{stages}</ol></div></section>
<section class="ab-pl" id="plan" data-toc="{e(toc[3])}"><div class="w"><h2>{e(t["a_h"])}</h2><p class="ld">{e(t["a_lede"])}</p>{plan}<p class="ab-more"><a href="/{L}/win/#plan">{e(t["a_link"])} {AR}</a></p></div></section>
<section class="ab-sm"><div class="w ab-smg"><a href="/{L}/sample/"><img src="/assets/{sample}" alt="{e(t["s_b1"])}" loading="lazy" width="1200" height="900"></a>
<div><h2>{e(t["s_h"])}</h2><p>{e(t["s_p"])}</p><div class="ab-cta"><a class="ab-b" href="/{L}/sample/">{e(t["s_b1"])}</a><a class="ab-b2" href="/{L}/request/">{e(t["s_b2"])}</a></div></div></div></section>
<section class="ab-pr" id="prices" data-toc="{e(toc[4])}"><div class="w"><h2>{e(t["pr_h"])}</h2>{prices}<p class="fine">{e(t["pr_note"])} <a href="/{L}/pricing/">{e(t["pr_link"])} {AR}</a></p></div></section>
<section class="ab-co" id="company" data-toc="{e(toc[5])}"><div class="w"><h2>{e(t["w_h"])}</h2><div class="ab-org">{orgs}</div>
<div class="ab-prm"><div><h3>{e(t["prom_h"])}</h3><ul>{"".join(f"<li>{e(x)}</li>" for x in t["proms"])}</ul></div>
<div><h3>{e(t["src_h"])}</h3><table class="ab-src"><thead><tr>{"".join(f"<th>{e(x)}</th>" for x in t["src_c"])}</tr></thead><tbody>{srcs}</tbody></table><p class="fine">{e(t["src_note"])}</p>
<p class="fine">{e(t["contact"])}: <a href="mailto:leedukyoung74@gmail.com">leedukyoung74@gmail.com</a></p></div></div></div></section>
<section class="ab-end">{ph}<div class="w"><h2>{t["f_h"]}</h2><p>{e(t["f_p"])}</p><div class="ab-cta"><button class="ab-b" data-auth="signup">{e(t["cta1"])}</button><a class="ab-l" href="{C["paylink"](L, "fit")}">{e(t["f_b2"])} {AR}</a></div>
<div class="pc">{C["credit"](["port"], L == "ko")}</div></div></section></div>
<script>{JS}</script>'''
    jl = C["ld"]({"@context": "https://schema.org", "@type": "AboutPage", "name": t["title"], "inLanguage": L, "publisher": C["ORG"], "description": t["desc"]})
    extra = jl + ('<meta name="gv-tr" content="1">' if L not in ("ko", "en") else "")
    return C["head"](L, t["title"], t["desc"], f"/{L}/about/", {l: f"/{l}/about/" for l in C["LANGS"]}, extra) + body + C["foot"](L)
