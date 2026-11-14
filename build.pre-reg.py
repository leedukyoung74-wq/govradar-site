#!/usr/bin/env python3
"""Build the public GOV RADAR static site.

Input : export/countries/*.json   (ArtifactData export of the radar's "countries" collection)
Output: dist/                      (deploy as-is to Cloudflare Pages / Vercel / any static host)

Usage : python3 build.py [--base https://radar.wmm-hoa.com]
"""
import json, glob, os, re, sys, shutil, html, unicodedata, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from i18n import LANGS, LANG_NAME, RTL, T, INDUSTRIES, X
CT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "content.json"), encoding="utf8"))
def tx(L, k): return X.get(L, {}).get(k) or X["en"][k]

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(ROOT, "src"), os.path.join(ROOT, "dist")
BASE = "https://radar.wmm-hoa.com"
if "--base" in sys.argv: BASE = sys.argv[sys.argv.index("--base") + 1].rstrip("/")
TODAY = (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=9)).strftime("%Y-%m-%d")
FLAGCSS = "https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css"

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)
def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

META = json.load(open(os.path.join(SRC, "countries_meta.json"), encoding="utf8"))
NAMES = json.load(open(os.path.join(SRC, "names.json"), encoding="utf8"))
BY = {c["iso"]: c for c in META}
for c in META: c["slug"] = slug(c["en"])
DATA = {}
for f in glob.glob(os.path.join(ROOT, "export", "countries", "*.json")):
    j = json.load(open(f, encoding="utf8")); d = j.get("data", j); iso = j.get("id") or os.path.basename(f)[:2]
    if iso in BY: DATA[iso] = d

def nm(iso, L): return NAMES.get(iso, {}).get(L) or BY[iso]["en"]
def done(iso): return bool(DATA.get(iso, {}).get("agenda"))
def G(d, k, L):
    """Field in the viewer's language: ko -> base; others -> i18n[L] -> en -> base."""
    if not d: return None
    if L == "ko": return d.get(k)
    v = (d.get("i18n") or {}).get(L, {}).get(k)
    if v: return v
    v = (d.get("en") or {}).get(k)
    if v not in (None, [], ""): return v
    return d.get(k)
def risk_txt(d, L):
    r = d.get("risk") or {}
    if L != "ko" and d.get("risk_en"): r = {**r, **d["risk_en"]}
    return r
def url(L, iso=None): return f"/{L}/" + (f"{BY[iso]['slug']}/" if iso else "")
def flag(iso, cls=""): return f'<span class="fi fi-{iso.lower()} {cls}" aria-hidden="true"></span>'
def lvl(iso):
    r = (DATA.get(iso) or {}).get("risk") or {}
    return r.get("level") if r.get("level") in ("high", "medium", "low") else None

# ---------------------------------------------------------------- layout
def head(L, title, desc, path, alt_paths, extra=""):
    t = T[L]
    alts = "".join(f'<link rel="alternate" hreflang="{l}" href="{BASE}{p}">' for l, p in alt_paths.items())
    alts += f'<link rel="alternate" hreflang="x-default" href="{BASE}{alt_paths.get("en", path)}">'
    return f"""<!doctype html><html lang="{L}" dir="{'rtl' if L in RTL else 'ltr'}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}{path}">{alts}
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{BASE}{path}"><meta property="og:image" content="{BASE}/assets/og.jpg"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0a0a0a"><link rel="icon" href="/assets/mark.png"><link rel="apple-touch-icon" href="/assets/mark.png">
<link rel="stylesheet" href="{FLAGCSS}"><link rel="stylesheet" href="/assets/site.css">
<link rel="alternate" type="application/rss+xml" title="GOV RADAR" href="/feeds/{L if L in ('ko','en') else 'en'}/all.xml">
{extra}</head><body>
<header class="nav"><div class="in">
<a class="brand" href="/{L}/"><img src="/assets/logo-h.webp" alt="GOV RADAR" width="132" height="44"></a>
<nav class="links"><a href="/{L}/#map">{e(t['cta_map'])}</a><a href="/{L}/#earth">{e(tx(L,'n_eh'))}</a><a href="/{L}/#foresight">{e(tx(L,'n_fs'))}</a><a href="/{L}/#board">{e(t['biz'])}</a><a href="/{L}/#events">{e(t['events'])}</a><a href="/{L}/#plans">{e(t['plans_h'])}</a><a href="/{L}/account/">{e(t['member_area'])}</a></nav>
<select class="langsel" aria-label="{e(t['lang'])}" onchange="location.href=this.value">{''.join(f'<option value="{e(p)}" {"selected" if l==L else ""}>{LANG_NAME[l]}</option>' for l,p in alt_paths.items())}</select>
<button class="btn sm" id="loginbtn" data-t-login="{e(t['login'])}" data-t-logout="{e(t['logout'])}">{e(t['login'])}</button>
</div></header>{prepbar(L)}<main>"""

def prepbar(L):
    lk = "ko" if L == "ko" else "en"
    chips = "".join(f'<button data-pp="{x["id"]}">{e(x[lk])}</button>' for x in CT["prep"]["scenarios"])
    panels = "".join(f'<div class="pp" data-pp="{x["id"]}" hidden><h3>{e(x[lk])}</h3><ul>{"".join(f"<li>{e(i)}</li>" for i in x[lk+"_items"])}</ul></div>' for x in CT["prep"]["scenarios"])
    src = "".join(f'<li><a href="{e(z["url"])}" target="_blank" rel="noopener">{e(z["title"])}</a></li>' for z in CT["prep"]["sources"])
    return f'''<div class="prepbar"><div class="in"><b>{e(tx(L,"prep_t"))}</b><div class="pchips">{chips}</div><span class="tick" id="htick"></span></div></div>
<div class="preppanel" id="preppanel" hidden><div class="in"><div>{panels}</div><div><p class="note">{e(tx(L,"prep_src"))}</p><ul class="src">{src}</ul><button class="btn sm" id="pp-x">×</button></div></div></div>'''

def foot(L):
    t = T[L]
    return f"""</main><footer><div class="in">
<img src="/assets/emblem.png" alt="" width="44" height="44" class="femb">
<div class="lic"><a href="https://www.ftc.go.kr/bizCommPop.do?wrkr_no=5898801039" target="_blank" rel="noopener">{e(t['biz_info'])}</a><span class="bar"></span><span>ONLINE LICENCE : 제2024-서울서초-2185호</span></div>
<p class="corp">{e(t['foot_corp'])} · E-mail 73036396@naver.com</p>
<div class="sites"><a href="https://www.wmm-hoa.com" target="_blank" rel="noopener"><b>WORLD MAKING MEMBERS</b><span>www.wmm-hoa.com ↗</span></a><a href="https://www.gcsme.kr" target="_blank" rel="noopener"><b>GCSME KOREA</b><span>www.gcsme.kr ↗</span></a></div>
<p class="corp"><a href="/{L}/feeds/">{e(t['feed'])}</a> · <a href="/{L}/embed/">{e(t['embed'])}</a></p>
<p class="corp">{e(t['disc'])}</p></div></footer>
<div class="modal" id="authm" hidden><div class="mbox"><button class="x" id="authx" aria-label="close">×</button><h3>{e(t['login'])}</h3>
<p class="note" id="authsoon">{e(t['login_soon'])}</p>
<form id="authf" hidden><label for="authe">{e(t['email'])}</label><input id="authe" type="email" required autocomplete="email"><button class="btn pri" type="submit">{e(t['send_link'])}</button><p class="note" id="authmsg" data-sent="{e(t['link_sent'])}"></p></form></div></div>
<script>window.RADAR_LANG="{L}";window.RADAR_T={json.dumps(dict(members_only=t['members_only'],rl=t['rl']),ensure_ascii=False)};</script>
<script src="/assets/config.js"></script><script src="/assets/site.js" defer></script></body></html>"""

def ld(obj): return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'
ORG = {"@type": "Organization", "name": "WORLD MAKING MEMBERS Co., Ltd.", "alternateName": ["월드메이킹멤버스", "WMM"], "url": "https://www.wmm-hoa.com", "logo": BASE + "/assets/emblem.png", "email": "73036396@naver.com"}

# ---------------------------------------------------------------- country page
def lst(items, fmt):
    items = [x for x in (items or []) if x]
    return "<ul>" + "".join(fmt(x) for x in items) + "</ul>" if items else ""

def sec(id_, h, body):
    return f'<section class="sec" id="{id_}"><h2>{e(h)}</h2>{body}</section>' if body else ""

def country_page(iso, L):
    t, d, c = T[L], DATA.get(iso) or {}, BY[iso]
    name = nm(iso, L)
    path = url(L, iso); alts = {l: url(l, iso) for l in LANGS}
    title = t["title_cty"].format(c=name)
    summ = G(d, "summary", L) or ""
    desc = (summ[:150] + "…") if len(summ) > 150 else (summ or t["desc_cty"].format(c=name))
    r = risk_txt(d, L); lv = lvl(iso)
    body = []
    if not done(iso):
        body.append(f'<p class="summary">{e(t["notyet"])}</p>')
    else:
        body.append(f'<p class="summary">{e(summ)}</p>')
        body.append(sec("leader", t["leader"], f"<p>{e(G(d,'leader',L))}</p>" if G(d,'leader',L) else ""))
        body.append(sec("agenda", t["agenda"], lst(G(d, "agenda", L), lambda x: f"<li>{e(x)}</li>")))
        def pj(p):
            p = p if isinstance(p, dict) else {"title": p}
            kv = "".join(f'<div class="kv"><span>{e(t[k])}</span><span>{e(p.get(k))}</span></div>' for k in ("ministry", "budget", "status") if p.get(k))
            link = f'<a href="{e(p["url"])}" rel="nofollow noopener" target="_blank">{e(t["sources"])}</a>' if str(p.get("url","")).startswith("https://") else ""
            return f'<details class="folder"><summary><b>{e(p.get("title"))}</b>{f"<span class=bd>{e(p.get(chr(98)+chr(117)+chr(100)+chr(103)+chr(101)+chr(116)))}</span>" if p.get("budget") else ""}</summary><div class="fb">{f"<p>{e(p.get(chr(100)+chr(101)+chr(116)+chr(97)+chr(105)+chr(108)))}</p>" if p.get("detail") else ""}{kv}{link}</div></details>'
        pjs = G(d, "projects", L) or []
        body.append(sec("projects", t["projects"], "".join(pj(p) for p in pjs)))
        def bz(b):
            b = b if isinstance(b, dict) else {"title": b}
            return f'<div class="card"><h3>{e(b.get("title"))}</h3>{f"<p>{e(b.get(chr(119)+chr(104)+chr(121)))}</p>" if b.get("why") else ""}{f"<p class=note>{e(b.get(chr(116)+chr(97)+chr(114)+chr(103)+chr(101)+chr(116)))}</p>" if b.get("target") else ""}</div>'
        bzs = G(d, "biz", L) or [{"title": x} for x in (d.get("items") or [])]
        body.append(sec("biz", t["biz"], f'<div class="cards">{"".join(bz(b) for b in bzs)}</div>' if bzs else ""))
        def td(x):
            return f'<li><b>{e(x.get("title"))}</b><span class="note"> · {e(x.get("buyer",""))}{" · "+e(t["deadline"])+" "+e(x.get("deadline")) if x.get("deadline") else ""}</span> <button class="btn xs member" data-act="watch" data-iso="{iso}" data-title="{e(x.get("title"))}" data-deadline="{e(x.get("deadline",""))}">{e(t["watch"])}</button></li>'
        body.append(sec("tenders", t["tenders"], lst(G(d, "tenders", L), td)))
        def oda(x): return f'<li><b>{e(x.get("title"))}</b><span class="note"> · {e(" · ".join(str(v) for v in [x.get("program"), x.get("stage"), x.get("amount")] if v))}</span></li>'
        body.append(sec("oda", t["oda"], lst(G(d, "oda", L), oda)))
        def kw(x): return f'<li><b>{e(x.get("company"))}</b> — {e(x.get("title"))} <span class="note">{e(" · ".join(str(v) for v in [x.get("year"), x.get("value")] if v))}</span></li>'
        body.append(sec("krwins", t["krwins"], lst(G(d, "krwins", L), kw)))
        def ks(x): return f'<li><b>{e(x.get("title"))}</b><span class="note"> · {e(x.get("org",""))}</span>{" — "+e(x.get("detail")) if x.get("detail") else ""}</li>'
        body.append(sec("krsupport", t["krsupport"], lst(G(d, "krsupport", L), ks)))
        g = G(d, "gov", L) or {}
        gn = lst(g.get("notices"), lambda x: f"<li>{e(x)}</li>")
        gl = f'<p><a href="{e((d.get("gov") or {}).get("url"))}" target="_blank" rel="noopener nofollow">{e(g.get("title") or (d.get("gov") or {}).get("title"))}</a></p>' if str((d.get("gov") or {}).get("url", "")).startswith("https://") else ""
        body.append(sec("gov", t["gov"], gl + gn))
    # risk/econ/sanctions always (risk exists for all)
    if r:
        cols = "".join(f'<div><b>{lab}</b><p>{e(" · ".join(r.get(k) or []) or "—")}</p></div>' for k, lab in (("disaster", "🌪"), ("conflict", "⚔"), ("epidemic", "🦠")))
        body.append(sec("risk", t["risk"], f'<p>{f"<span class=lvl data-l={lv}>{e(t[chr(114)+chr(108)][lv])}</span>" if lv else ""} <span class="note">{e(r.get("checked",""))}</span></p><div class="risk">{cols}</div>'))
    ag = CT["agencies"]["country"].get(iso)
    if ag: body.append(sec("agencies", tx(L, "ag"), "<ul>" + "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(n)}</a></li>' for n, u in ag) + "</ul>"))
    body.append(f'<section class="sec" id="localhaz" data-iso="{iso}" hidden><h2>{e(tx(L,"n_eh"))}</h2><ul></ul></section>')
    ec = G(d, "econ", L)
    if ec: body.append(sec("econ", t["econ"], f'<p>{e(ec.get("rating","—"))} · K-SURE {e(ec.get("ksure","—"))} · {e((ec.get("fx") or {}).get("code",""))} {e((ec.get("fx") or {}).get("change_30d",""))}</p>'))
    sc = G(d, "sanctions", L)
    if sc: body.append(sec("sanctions", t["sanctions"], f'<p>{e(", ".join(sc.get("programs") or []) or "—")}</p><p class="note">{e(sc.get("summary",""))}</p>'))
    src = lst(d.get("sources"), lambda s: f'<li><a href="{e(s.get("url"))}" target="_blank" rel="noopener nofollow">{e(s.get("title") or s.get("url"))}</a></li>' if str(s.get("url","")).startswith("https://") else "")
    body.append(sec("sources", t["sources"], src))
    # sidebar
    same = [x for x in META if x["r"] == c["r"] and x["iso"] != iso and done(x["iso"])][:12]
    side = f"""<aside class="side">
<div class="box"><b>{e(t['ai_cta'])}</b><textarea id="askq" rows="3" aria-label="{e(t['ai_cta'])}"></textarea><button class="btn pri member" data-act="ask" data-iso="{iso}">→</button><div id="askout" class="note"></div></div>
<div class="box"><b>{e(t['alert_cta'])}</b><button class="btn member" data-act="follow" data-iso="{iso}">{e(t['cta_join'])}</button></div>
<div class="box"><b>{e(t['more_cty'])}</b><div class="mini">{''.join(f'<a href="{url(L,x["iso"])}">{flag(x["iso"])} {e(nm(x["iso"],L))}</a>' for x in same)}</div></div>
<div class="box gc"><img src="/assets/emblem.png" alt="" width="40" height="40"><span>GCSME · Global &amp; Commonwealth SME Club<br><a href="https://www.gcsme.kr" target="_blank" rel="noopener">gcsme.kr</a></span></div>
</aside>"""
    jl = ld({"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "inLanguage": L,
             "dateModified": d.get("updated") or TODAY, "about": {"@type": "Country", "name": c["en"]},
             "publisher": ORG, "mainEntityOfPage": BASE + path, "image": BASE + "/assets/og.jpg"})
    crumbs = ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "GOV RADAR", "item": BASE + f"/{L}/"},
        {"@type": "ListItem", "position": 2, "name": name, "item": BASE + path}]})
    hero = f"""<section class="chero"><div class="in">
<p class="crumb"><a href="/{L}/">GOV RADAR</a> / {e(t['regions'][c['r']])}</p>
<div class="ct">{flag(iso, 'big')}<div><h1>{e(name)}</h1><p class="alt">{e(c['en'] if L!='en' else c['ko'])} · {iso}{' · Commonwealth' if c['cw'] else ''}</p></div></div>
<p class="meta">{e(t['updated'])} {e(d.get('updated','—'))}{(' · '+e(t['asof'])+' '+e(d.get('asof'))) if d.get('asof') else ''}{f" · <span class=lvl data-l={lv}>{e(t['rl'][lv])}</span>" if lv else ''}</p>
</div></section>"""
    return head(L, title, desc, path, alts, jl + crumbs) + hero + f'<div class="in cgrid"><article>{"".join(body)}</article>{side}</div>' + foot(L)

# ---------------------------------------------------------------- home
def opps():
    out = []
    rank = {"high": 0, "medium": 1, "low": 2}
    for iso, d in DATA.items():
        for i, b in enumerate(d.get("biz") or []):
            if isinstance(b, dict):
                be = ((d.get("en") or {}).get("biz") or [None] * 99)
                be = be[i] if i < len(be) and isinstance(be[i], dict) else {}
                out.append({"iso": iso, "fit": b.get("fit"), "ko": b.get("title"), "en": be.get("title") or b.get("title"), "why_ko": b.get("why", ""), "why_en": be.get("why") or b.get("why", ""), "u": d.get("updated", "")})
    out.sort(key=lambda x: x["u"], reverse=True); out.sort(key=lambda x: rank.get(x["fit"], 3))
    return out

def events():
    out = []
    for iso, d in DATA.items():
        for ev in d.get("events") or []:
            if (ev.get("end") or ev.get("date") or "") >= TODAY: out.append({**ev, "iso": iso})
    return sorted(out, key=lambda x: x.get("date", ""))

def earth_section(L):
    keys = ["quake", "tsunami", "volcano", "storm", "space", "asteroid", "weather", "fire", "epidemic"]
    eh = tx(L, "eh")
    cards = "".join(f'<div class="ecard" data-k="{k}"><h3>{e(eh[k])}</h3><div class="eb">…</div></div>' for k in keys)
    agk = tx(L, "ag_k")
    dirl = "".join(f'<div><span class="k">{e(agk.get(a["k"], a["k"]))}</span><a href="{e(a["url"])}" target="_blank" rel="noopener">{e(a["name"])}</a></div>' for a in CT["agencies"]["global"])
    return f'''<section class="band alt" id="earth"><div class="in"><p class="eyebrow">EARTH &amp; SPACE MONITOR</p><h2>{e(tx(L,"eh_h"))}</h2><p class="note">{e(tx(L,"eh_p"))} <span id="eh-at"></span></p>
<div class="earth" id="earthg" data-none="{e(tx(L,"eh_none"))}" data-ld="{e(tx(L,"eh_ld"))}" data-kp="{e(tx(L,"eh_kp"))}">{cards}</div>
<details class="dirw"><summary>{e(tx(L,"eh_dir"))}</summary><div class="dir">{dirl}</div></details></div></section>'''

def foresight_section(L):
    lk = "ko" if L == "ko" else "en"
    play = "".join(f'''<div class="fs-card"><h3>{e(x[lk])}</h3><h4>{e(tx(L,"fs_sig"))}</h4><ul>{"".join(f"<li>{e(i)}</li>" for i in x["sig_"+lk])}</ul><h4>{e(tx(L,"fs_move"))}</h4><ul>{"".join(f"<li>{e(i)}</li>" for i in x["move_"+lk])}</ul><h4>{e(tx(L,"fs_prep"))}</h4><ul>{"".join(f"<li>{e(i)}</li>" for i in x["prep_"+lk])}</ul></div>''' for x in CT["foresight"])
    return f'''<section class="band" id="foresight"><div class="in"><p class="eyebrow">FORESIGHT · PREMIUM</p><h2>{e(tx(L,"fs_h"))}</h2><p class="note">{e(tx(L,"fs_p"))}</p>
<div id="fsweek" class="lock"><b>{e(tx(L,"fs_lock"))}</b><p>{e(tx(L,"fs_week"))} · {e(tx(L,"fs_moves"))}</p><button class="btn pri" data-act="join">{e(T[L]["cta_join"])}</button></div>
<h3 class="pl">{e(tx(L,"fs_play"))}</h3><div class="fs-grid">{play}</div><p class="note">{e(tx(L,"fs_disc"))}</p></div></section>'''

def home(L):
    t = T[L]; path = f"/{L}/"; alts = {l: f"/{l}/" for l in LANGS}
    n_done = sum(done(i) for i in BY); n_t = sum(len(DATA.get(i, {}).get("tenders") or []) for i in BY)
    O = opps(); n_b = len(O); last = max([d.get("updated", "") for d in DATA.values()] or [""])
    regions = "".join(f'<button class="chip" data-r="{k}">{e(v)}</button>' for k, v in t["regions"].items())
    grid = "".join(f'<a class="flag {"done" if done(c["iso"]) else ""}" data-r="{c["r"]}" data-n="{e((nm(c["iso"],L)+" "+c["en"]+" "+c["ko"]).lower())}" href="{url(L,c["iso"])}">{flag(c["iso"])}<span>{e(nm(c["iso"],L))}</span>{f"<i class=rk data-l={lvl(c[chr(105)+chr(115)+chr(111)])}></i>" if lvl(c["iso"]) in ("high","medium") else ""}</a>'
                   for c in sorted(META, key=lambda c: nm(c["iso"], L)))
    lk = "ko" if L == "ko" else "en"
    board = "".join(f'<a class="opp" href="{url(L,o["iso"])}#biz"><span class="who">{flag(o["iso"])} {e(nm(o["iso"],L))}{" <i class=fit>"+e(t["fit"])+"</i>" if o["fit"]=="high" else ""}</span><b>{e(o[lk])}</b><span class="note">{e(o["why_"+lk][:120])}</span></a>' for o in O[:24])
    evs = events()[:12]
    evh = "".join(f'<a class="ev" href="{url(L,x["iso"])}#events"><span class="d">{e(x.get("date","")[5:].replace("-","/"))}</span><span>{flag(x["iso"])} <b>{e(x.get("title_en") if L!="ko" and x.get("title_en") else x.get("title"))}</b><br><span class="note">{e(x.get("org",""))} · {e(x.get("city",""))}</span></span></a>' for x in evs) or f'<p class="note">—</p>'
    plans = "".join(f'<div class="plan{" mid" if i==1 else ""}"><span class="tier">{e(a)}</span><b class="price">{e(b)}</b><p>{e(c)}</p></div>' for i, (a, b, c) in enumerate(t["plans"]))
    jl = ld({"@context": "https://schema.org", "@type": "WebSite", "name": "GOV RADAR", "url": BASE + "/", "inLanguage": L, "publisher": ORG, "description": t["desc_home"]})
    return head(L, t["title_home"], t["desc_home"], path, alts, jl + '<script src="https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/js/jsvectormap.min.js" defer></script><script src="https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/maps/world.js" defer></script>') + f"""
<section class="hero"><div class="in"><div>
<p class="eb"><i class="live"></i>WMM × GCSME · 193</p>
<h1>{e(t['tagline']).replace('정부가 ','정부가<br>',1)}</h1><p class="lede">{e(t['lede']).replace('모았습니다. ','모았습니다.<br>',1)}</p>
<div class="cta"><a class="btn pri" href="#map">{e(t['cta_map'])}</a><button class="btn ghost" data-act="join">{e(t['cta_join'])}</button></div>
<p class="byline"><img src="/assets/emblem.png" alt="" width="24" height="24">WORLD MAKING MEMBERS × GCSME</p></div>
<img class="hlogo" src="/assets/logo-v.webp" alt="GOV RADAR" width="280" height="310">
<div class="kpis"><div><b>{n_done}<small>/193</small></b><span>{e(t['k_done'])}</span></div><div><b>{n_t}</b><span>{e(t['k_tend'])}</span></div><div><b>{n_b}</b><span>{e(t['k_biz'])}</span></div><div><b>{e(last[5:].replace('-','/') or '—')}</b><span>{e(t['k_last'])}</span></div></div>
</div></section>
<section class="band" id="map"><div class="in"><h2>{e(t['map_h'])}</h2>
<div class="mapbox"><div id="wmap" data-lang="{L}"></div></div>
<div class="filters"><input id="q" type="search" placeholder="{e(t['search'])}" aria-label="{e(t['search'])}"><button class="chip on" data-r="ALL">{e(t['all'])}</button>{regions}</div>
<div class="grid" id="grid">{grid}</div></div></section>
<section class="band alt" id="board"><div class="in"><h2>{e(t['board_h'])}</h2><p class="note">{e(t['board_p'])}</p><div class="board">{board}</div></div></section>
<section class="band" id="events"><div class="in"><h2>{e(t['ev_h'])}</h2><div class="evs">{evh}</div></div></section>
{earth_section(L)}{foresight_section(L)}
<section class="band alt" id="plans"><div class="in"><h2>{e(t['plans_h'])}</h2><div class="plans">{plans}</div><p class="cta"><button class="btn pri" data-act="join">{e(t['cta_join'])}</button></p></div></section>
""" + foot(L)

# ---------------------------------------------------------------- feeds, widget, sitemap
def rss(L, key=None):
    t = T[L]; lk = "ko" if L == "ko" else "en"; items = []
    kws = [k.lower() for k in INDUSTRIES[key][2]] if key else None
    for iso, d in DATA.items():
        if not done(iso): continue
        for kind, arr in (("tender", G(d, "tenders", L)), ("biz", G(d, "biz", L)), ("oda", G(d, "oda", L))):
            for x in arr or []:
                if not isinstance(x, dict): continue
                txt = json.dumps(x, ensure_ascii=False).lower()
                if kws and not any(k in txt for k in kws): continue
                items.append((d.get("updated", TODAY), iso, kind, x))
    items.sort(key=lambda z: z[0], reverse=True)
    def it(u, iso, kind, x):
        link = BASE + url(L, iso) + {"tender": "#tenders", "biz": "#biz", "oda": "#oda"}[kind]
        title = f"[{nm(iso, L)}] {x.get('title','')}"
        dsc = x.get("why") or x.get("detail") or (f"{t['deadline']} {x.get('deadline')}" if x.get("deadline") else "")
        pub = datetime.datetime.strptime(u or TODAY, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0900")
        return f"<item><title>{e(title)}</title><link>{link}</link><guid isPermaLink=\"false\">{e(iso+kind+x.get('title',''))}</guid><pubDate>{pub}</pubDate><description>{e(dsc)}</description></item>"
    ttl = "GOV RADAR" + (f" · {INDUSTRIES[key][0 if L=='ko' else 1]}" if key else "")
    return f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{e(ttl)}</title><link>{BASE}/{L}/</link><description>{e(t["desc_home"])}</description><language>{L}</language>{"".join(it(*z) for z in items[:80])}</channel></rss>'

def feeds_page(L):
    t = T[L]; fl = "ko" if L == "ko" else "en"
    rows = f'<li><a href="/feeds/{fl}/all.xml">GOV RADAR · ALL</a></li>' + "".join(f'<li><a href="/feeds/{fl}/{k}.xml">{e(v[0] if fl=="ko" else v[1])}</a></li>' for k, v in INDUSTRIES.items())
    return head(L, t["feed"] + " | GOV RADAR", t["desc_home"], f"/{L}/feeds/", {l: f"/{l}/feeds/" for l in LANGS}) + f'<section class="band"><div class="in"><h1>{e(t["feed"])}</h1><ul class="feeds">{rows}</ul><p class="note">RSS → LinkedIn · Naver Blog · Slack · Teams · Feedly</p></div></section>' + foot(L)

def embed_page(L):
    t = T[L]
    code1 = f'<iframe src="{BASE}/widget/?lang={L}" style="width:100%;height:520px;border:0" loading="lazy" title="GOV RADAR"></iframe>'
    code2 = f'<script src="{BASE}/embed.js" data-lang="{L}" data-industry="ai-digital" async></script>'
    return head(L, t["embed"] + " | GOV RADAR", t["desc_home"], f"/{L}/embed/", {l: f"/{l}/embed/" for l in LANGS}) + f"""<section class="band"><div class="in"><h1>{e(t['embed'])}</h1>
<p>iframe</p><pre class="code">{e(code1)}</pre><p>script (?lang= ko/en/es/fr/ar/vi/id · ?industry= {', '.join(INDUSTRIES)} · ?iso= VN)</p><pre class="code">{e(code2)}</pre>
<iframe src="/widget/?lang={L}" style="width:100%;height:520px;border:1px solid #ddd;border-radius:12px" title="preview"></iframe></div></section>""" + foot(L)

def account_page(L):
    ko = L == "ko"; t = T[L]
    lab = (lambda k, e_: k if ko else e_)
    inds = "".join(f'<label class="chk"><input type="checkbox" name="ind" value="{k}"> {e(v[0] if ko else v[1])}</label>' for k, v in INDUSTRIES.items())
    return head(L, t["member_area"] + " | GOV RADAR", t["desc_home"], f"/{L}/account/", {l: f"/{l}/account/" for l in LANGS}) + f"""<section class="band"><div class="in acct">
<h1>{e(t['member_area'])}</h1><p class="note" id="acct-st">{e(t['members_only'])}</p>
<form id="acct" hidden>
<label>{lab('회사명','Company')}<input name="company"></label>
<fieldset><legend>{lab('관심 분야 (알림 기준)','Industries (for alerts)')}</legend><div class="chks">{inds}</div></fieldset>
<div class="two"><label>{lab('연 매출 (억 원)','Revenue (KRW 100M)')}<input name="revenue_100m" type="number" min="0"></label><label>{lab('업력 (년)','Years in business')}<input name="years" type="number" min="0"></label></div>
<div class="two"><label>{lab('해외·공공 실적 (건)','Public / overseas projects')}<input name="projects" type="number" min="0"></label><label>{lab('직원 수','Employees')}<input name="employees" type="number" min="0"></label></div>
<label>{lab('보유 인증 (쉼표로)','Certifications (comma-separated)')}<input name="certs"></label>
<fieldset><legend>{lab('알림 받는 방법','Alert channels')}</legend>
<label class="chk"><input type="checkbox" name="alert_email" checked> {lab('이메일 (새 기회·마감 D-7/D-3)','Email (new opportunities, D-7/D-3 deadlines)')}</label>
<label class="chk"><input type="checkbox" name="alert_kakao"> {lab('카카오톡 알림톡','KakaoTalk AlimTalk')}</label>
<label>{lab('휴대폰 번호 (카카오 알림용)','Mobile number (Kakao)')}<input name="kakao_phone" inputmode="tel" placeholder="01012345678"></label>
<label>{lab('Slack 웹훅 URL (회사 채널)','Slack webhook URL (company channel)')}<input name="slack_webhook" placeholder="https://hooks.slack.com/services/..."></label>
<label>{lab('Microsoft Teams 웹훅 URL','Microsoft Teams webhook URL')}<input name="teams_webhook" placeholder="https://....webhook.office.com/..."></label>
<label class="chk"><input type="checkbox" name="marketing_consent"> {lab('[선택] 맞춤 사업 기회·행사 등 광고성 정보 수신에 동의합니다 (언제든 철회 가능)','[Optional] I agree to receive promotional information about matching opportunities and events (withdraw any time)')}</label>
</fieldset>
<button class="btn pri" type="submit">{lab('저장','Save')}</button><p class="note" id="acct-msg"></p></form></div></section>""" + foot(L)

def widget():
    return """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GOV RADAR widget</title>
<link rel="stylesheet" href="%s"><style>
body{margin:0;font-family:"NEXON Lv1 Gothic OTF","Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;background:#0a0a0a;color:#f2f2ef}
header{display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid #2b2b2a}header img{height:30px}header a{margin-left:auto;color:#f2f2ef;font-size:12px}
ul{list-style:none;margin:0;padding:6px 0}li a{display:flex;gap:10px;align-items:flex-start;padding:10px 14px;color:#f2f2ef;text-decoration:none;border-bottom:1px solid #1d1d1c}li a:hover{background:#151515}
.fi{width:1.4em;line-height:1em;margin-top:3px;flex:none}small{display:block;color:#9a9a96;font-size:12px}b.t{font-size:14px}
</style></head><body><header><img src="/assets/logo-h.webp" alt="GOV RADAR" style="width:auto;height:30px;filter:none"><a id="more" href="/" target="_blank" rel="noopener">→</a></header><ul id="l"></ul>
<script>
const p=new URLSearchParams(location.search),L=p.get("lang")||"ko",ind=p.get("industry"),iso=(p.get("iso")||"").toUpperCase();
document.getElementById("more").href="/"+L+"/";
fetch("/data/opps.json").then(r=>r.json()).then(o=>{let a=o.items;if(iso)a=a.filter(x=>x.iso===iso);if(ind)a=a.filter(x=>(x.ind||[]).includes(ind));
 const lk=L==="ko"?"ko":"en";document.getElementById("l").innerHTML=a.slice(0,12).map(x=>`<li><a href="/${L}/${x.slug}/#${x.kind}" target="_blank" rel="noopener"><span class="fi fi-${x.iso.toLowerCase()}"></span><span><b class="t"></b><small></small></span></a></li>`).join("");
 [...document.querySelectorAll("#l li")].forEach((li,i)=>{const x=a[i];li.querySelector(".t").textContent=x[lk]||x.en;li.querySelector("small").textContent=(x.names[L]||x.names.en)+(x.deadline?" · "+x.deadline:"")})});
</script></body></html>""" % FLAGCSS

def embed_js():
    return """(function(){var s=document.currentScript,L=s.getAttribute('data-lang')||'ko',ind=s.getAttribute('data-industry')||'',iso=s.getAttribute('data-iso')||'',h=s.getAttribute('data-height')||'520';
var f=document.createElement('iframe');f.src='%s/widget/?lang='+encodeURIComponent(L)+(ind?'&industry='+encodeURIComponent(ind):'')+(iso?'&iso='+encodeURIComponent(iso):'');
f.style.cssText='width:100%%;height:'+h+'px;border:0;border-radius:12px';f.loading='lazy';f.title='GOV RADAR';s.parentNode.insertBefore(f,s.nextSibling);})();""" % BASE

def build():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT + "/assets"); os.makedirs(OUT + "/data")
    for f in ("emblem.png", "og.jpg", "spot.jpg", "paper.jpg", "logo-h.webp", "logo-h-lg.webp", "logo-v.webp", "mark.png"): shutil.copy(os.path.join(SRC, f), OUT + "/assets/" + f)
    for f in glob.glob(os.path.join(ROOT, "web", "*")): shutil.copy(f, OUT + "/assets/")
    W = lambda p, s: (os.makedirs(os.path.dirname(OUT + p), exist_ok=True), open(OUT + p, "w", encoding="utf8").write(s))
    urls = []
    for L in LANGS:
        W(f"/{L}/index.html", home(L)); urls.append((f"/{L}/", {l: f"/{l}/" for l in LANGS}))
        W(f"/{L}/feeds/index.html", feeds_page(L)); W(f"/{L}/embed/index.html", embed_page(L)); W(f"/{L}/account/index.html", account_page(L))
        for c in META:
            W(f"/{L}/{c['slug']}/index.html", country_page(c["iso"], L))
            urls.append((url(L, c["iso"]), {l: url(l, c["iso"]) for l in LANGS}))
    for L in ("ko", "en"):
        W(f"/feeds/{L}/all.xml", rss(L))
        for k in INDUSTRIES: W(f"/feeds/{L}/{k}.xml", rss(L, k))
    # data for map, search, widget
    cj = [{"iso": c["iso"], "slug": c["slug"], "r": c["r"], "done": done(c["iso"]), "risk": lvl(c["iso"]), "names": NAMES[c["iso"]]} for c in META]
    W("/data/countries.json", json.dumps(cj, ensure_ascii=False))
    hz = os.path.join(ROOT, "export", "hazards.json")
    W("/data/hazards.json", open(hz, encoding="utf8").read() if os.path.exists(hz) else "{}")
    oi = []
    for iso, d in DATA.items():
        if not done(iso): continue
        en = d.get("en") or {}
        for kind, arr, arr_en in (("biz", d.get("biz"), en.get("biz")), ("tenders", d.get("tenders"), en.get("tenders")), ("oda", d.get("oda"), en.get("oda"))):
            for i, x in enumerate(arr or []):
                if not isinstance(x, dict): continue
                xe = arr_en[i] if isinstance(arr_en, list) and i < len(arr_en) and isinstance(arr_en[i], dict) else {}
                txt = (json.dumps(x, ensure_ascii=False) + json.dumps(xe, ensure_ascii=False)).lower()
                ind = [k for k, v in INDUSTRIES.items() if any(w.lower() in txt for w in v[2])]
                oi.append({"iso": iso, "slug": BY[iso]["slug"], "kind": kind, "ko": x.get("title"), "en": xe.get("title") or x.get("title"), "deadline": x.get("deadline", ""), "fit": x.get("fit"), "ind": ind, "names": NAMES[iso], "u": d.get("updated", "")})
    oi.sort(key=lambda x: x["u"], reverse=True)
    W("/data/opps.json", json.dumps({"updated": TODAY, "items": oi}, ensure_ascii=False))
    for iso, d in DATA.items():
        if done(iso):
            c = {k: v for k, v in d.items() if k not in ("history",)}
            W(f"/data/c/{iso}.json", json.dumps({"iso": iso, "name": BY[iso]["en"], **c}, ensure_ascii=False))
    W("/widget/index.html", widget()); W("/embed.js", embed_js())
    # root: language pick
    W("/index.html", f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GOV RADAR — 193 governments</title>
<meta name="description" content="{e(T['en']['desc_home'])}"><link rel="canonical" href="{BASE}/en/">{''.join(f'<link rel="alternate" hreflang="{l}" href="{BASE}/{l}/">' for l in LANGS)}<link rel="alternate" hreflang="x-default" href="{BASE}/en/">
<meta property="og:image" content="{BASE}/assets/og.jpg"><link rel="icon" href="/assets/mark.png">
<script>var n=(navigator.language||"en").slice(0,2).toLowerCase(),L={json.dumps(LANGS)};location.replace("/"+(L.indexOf(n)>=0?n:"en")+"/");</script>
<style>body{{background:#0a0a0a;color:#f2f2ef;font-family:system-ui;display:grid;place-items:center;min-height:100vh;margin:0}}a{{color:#f2f2ef;margin:0 8px}}</style></head>
<body><div><h1>GOV RADAR</h1>{''.join(f'<a href="/{l}/">{LANG_NAME[l]}</a>' for l in LANGS)}</div></body></html>""")
    W("/404.html", home("en").replace("<title>", "<title>404 · ", 1))
    # sitemap (with hreflang), robots, llms.txt, headers
    sm = ['<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p, alts in urls:
        iso = next((c["iso"] for c in META if p.endswith("/" + c["slug"] + "/")), None)
        lm = (DATA.get(iso) or {}).get("updated", TODAY) if iso else TODAY
        sm.append(f"<url><loc>{BASE}{p}</loc><lastmod>{lm}</lastmod>" + "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{BASE}{a}"/>' for l, a in alts.items()) + "</url>")
    sm.append("</urlset>"); W("/sitemap.xml", "".join(sm))
    W("/robots.txt", f"User-agent: *\nAllow: /\nDisallow: /widget/\n\nSitemap: {BASE}/sitemap.xml\n")
    llms = [f"# GOV RADAR (WMM × GCSME)", "", f"> {T['en']['desc_home']}", "", "Publisher: WORLD MAKING MEMBERS Co., Ltd. (Seoul) with Global & Commonwealth SME Club (London). Contact 73036396@naver.com", "", "## Countries (English)"]
    llms += [f"- [{c['en']}]({BASE}{url('en', c['iso'])}): {((DATA.get(c['iso']) or {}).get('en') or {}).get('summary', '')[:160]}" for c in META if done(c["iso"])]
    llms += ["", "## 국가 (한국어)"] + [f"- [{c['ko']}]({BASE}{url('ko', c['iso'])})" for c in META if done(c["iso"])]
    W("/llms.txt", "\n".join(llms) + "\n")
    W("/_headers", "/assets/*\n  Cache-Control: public, max-age=604800\n/data/*\n  Cache-Control: public, max-age=3600\n  Access-Control-Allow-Origin: *\n/widget/*\n  Content-Security-Policy: frame-ancestors *\n/*\n  X-Content-Type-Options: nosniff\n")
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"built {n} files · {sum(done(i) for i in BY)} researched countries · {len(oi)} opportunities · base {BASE}")

if __name__ == "__main__": build()
