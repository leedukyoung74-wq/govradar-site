#!/usr/bin/env python3
"""Build the public GOV RADAR static site.

Input : export/countries/*.json   (ArtifactData export of the radar's "countries" collection)
Output: dist/                      (deploy as-is to Cloudflare Pages / Vercel / any static host)

Usage : python3 build.py [--base https://radar.wmm-hoa.com]
"""
import json, glob, os, re, sys, shutil, html, unicodedata, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from i18n import LANGS, LANG_NAME, RTL, T, INDUSTRIES, X
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from i18n2 import AT, NAV, MENU, PREP_T, LANG_SHORT, PLANS, PLAN_NOTE
CT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "content.json"), encoding="utf8"))
RX = {
 "ko": dict(rg_h="자치·특별 지역", rg_p="국가 안에서 자체 의회·예산·법을 가진 지역입니다. 중앙정부와 별도로 사업·입찰을 냅니다.", rg_parent="소속 국가", rg_stat="자치 지위·권한", rg_wait="이 지역 자료는 평일 아침 점검 때 차례로 채워집니다.",
   rgt=dict(auto="자치지역", special="특별자치", sar="특별행정구", dev="자치정부", terr="해외 자치령", defacto="사실상 독립"),
   rs=dict(capital="수도", established="설립", law="근거법", government="정부 형태", powers="지역 권한", reserved="중앙정부 권한", next="다음 일정")),
 "en": dict(rg_h="Autonomous & special regions", rg_p="Regions with their own parliament, budget and laws. They run projects and tenders separately from the national government.", rg_parent="Country", rg_stat="Autonomy & powers", rg_wait="This region is filled in during the weekday morning update.",
   rgt=dict(auto="Autonomous region", special="Special autonomy", sar="Special admin. region", dev="Devolved government", terr="Overseas territory", defacto="De facto state"),
   rs=dict(capital="Capital", established="Established", law="Legal basis", government="Government", powers="Regional powers", reserved="Reserved to national govt", next="Next milestone")),
}
for _k, _v in RX.items(): X.setdefault(_k, {}).update(_v)
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

# Korean pages: show Korean names for tender titles, buyers and agencies kept in the original language.
# The English (and other-language) pages keep the original, so copy it into d["en"] first when missing.
import copy as _copy
_KO = json.load(open(os.path.join(SRC, "ko_names.json"), encoding="utf8"))
for _d in DATA.values():
    _en = _d.setdefault("en", {})
    for _k, _fs in (("tenders", ("title", "buyer")), ("projects", ("title", "ministry")), ("oda", ("title", "agency")), ("krsupport", ("title", "org")), ("events", ("title", "org"))):
        _lst = _d.get(_k)
        if not isinstance(_lst, list): continue
        if _k not in _en: _en[_k] = _copy.deepcopy(_lst)
        for _x in _lst:
            if isinstance(_x, dict):
                for _f in _fs:
                    if isinstance(_x.get(_f), str) and _x[_f] in _KO: _x[_f] = _KO[_x[_f]]
    _g = _d.get("gov")
    if isinstance(_g, dict) and _g.get("title") in _KO:
        _en.setdefault("gov", {}).setdefault("title", _g["title"]); _g["title"] = _KO[_g["title"]]

REGS = json.load(open(os.path.join(SRC, "regions.json"), encoding="utf8"))
for x in REGS:
    p = BY[x["parent"]]
    BY[x["iso"]] = {**x, "r": p["r"], "cw": False, "reg": True, "slug": p["slug"] + "/" + slug(x["en"].split(" (")[0])}
    NAMES[x["iso"]] = {"ko": x["ko"], "en": x["en"]}
for f in glob.glob(os.path.join(ROOT, "export", "regions", "*.json")):
    j = json.load(open(f, encoding="utf8")); d = j.get("data", j); code = j.get("id") or os.path.basename(f)[:-5]
    if code in BY: DATA[code] = d
# --- translated country content (es/fr/ar/vi/id), merged over en by index ---
def _merge_tr(base, tr):
    if isinstance(base, dict) and isinstance(tr, dict):
        out = dict(base)
        for k, v in tr.items():
            if k in base: out[k] = _merge_tr(base[k], v)
            elif isinstance(v, str) and v: out[k] = v
        return out
    if isinstance(base, list) and isinstance(tr, list):
        return [_merge_tr(b, tr[i]) if i < len(tr) else b for i, b in enumerate(base)]
    if isinstance(base, str) and isinstance(tr, str) and tr.strip(): return tr
    return base
TRDIR = os.path.join(SRC, "i18n_data")
for _L in ("es", "fr", "ar", "vi", "id"):
    for f in glob.glob(os.path.join(TRDIR, _L, "*.json")):
        iso = os.path.basename(f)[:-5]
        d = DATA.get(iso)
        if not d or not d.get("en"): continue
        try: tr = json.load(open(f, encoding="utf8"))
        except Exception: continue
        if isinstance(tr, dict) and iso in tr and len(tr) == 1: tr = tr[iso]
        m = {k: _merge_tr(d["en"].get(k), v) for k, v in tr.items() if k in d["en"]}
        d.setdefault("i18n", {}).setdefault(_L, {}).update(m)
def is_reg(iso): return bool(BY.get(iso, {}).get("reg"))
def regs_of(p): return [x for x in REGS if x["parent"] == p]

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
def flag(iso, cls=""):
    b = BY.get(iso) or {}
    if b.get("reg"): iso = b.get("f") or b["parent"]
    return f'<span class="fi fi-{iso.lower()} {cls}" aria-hidden="true"></span>'
def lvl(iso):
    r = (DATA.get(iso) or {}).get("risk") or {}
    return r.get("level") if r.get("level") in ("high", "medium", "low") else None

JSVM = '<script src="https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/js/jsvectormap.min.js" defer></script><script src="https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/maps/world.js" defer></script>'
# ---------------------------------------------------------------- layout
FONTLINK = {
 "ar": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;600;700&display=swap",
 "vi": "https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;600;700&display=swap",
}
for _l in ("en", "es", "fr", "id"): FONTLINK[_l] = "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap"
def navhtml(L):
    items = "".join(f'<a href="/{L}/{p}">{e(lbl)}</a>' for p, lbl in NAV[L])
    return items
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
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>{f'<link rel="stylesheet" href="{FONTLINK[L]}">' if L in FONTLINK else ''}
<link rel="stylesheet" href="{FLAGCSS}"><link rel="stylesheet" href="/assets/site.css">
<link rel="alternate" type="application/rss+xml" title="GOV RADAR" href="/feeds/{L if L in ('ko','en') else 'en'}/all.xml">
{extra}</head><body>
<header class="nav"><div class="in">
<a class="brand" href="/{L}/"><img src="/assets/logo-h.webp" alt="GOV RADAR" width="132" height="44"></a>
<nav class="links" id="navlinks">{navhtml(L)}</nav>
<div class="navr"><label class="langw"><span class="lcode">{LANG_SHORT[L]}</span><select class="langsel" aria-label="{e(t['lang'])}" onchange="gvLang(this)">{''.join(f'<option value="{e(p)}" data-l="{l}" {"selected" if l==L else ""}>{LANG_NAME[l]}</option>' for l,p in alt_paths.items())}</select></label>
<button class="btn sm" id="loginbtn">{e(AT[L]['login'])}</button>
<button class="burger" id="burger" aria-label="{e(MENU[L])}" aria-expanded="false" aria-controls="navlinks"><span></span><span></span><span></span></button></div>
</div></header>{prepbar(L) if path.endswith("/prepare/") else ""}<main>"""

def prepbar(L):
    lk = "ko" if L == "ko" else "en"
    nm_ = lambda x: (PREP_T.get(L) or {}).get(x["id"]) or x[lk]
    chips = "".join(f'<button data-pp="{x["id"]}">{e(nm_(x))}</button>' for x in CT["prep"]["scenarios"])
    panels = "".join(f'<div class="pp" data-pp="{x["id"]}" hidden><h3>{e(x[lk])}</h3><ul>{"".join(f"<li>{e(i)}</li>" for i in x[lk+"_items"])}</ul></div>' for x in CT["prep"]["scenarios"])
    src = "".join(f'<li><a href="{e(z["url"])}" target="_blank" rel="noopener">{e(z["title"])}</a></li>' for z in CT["prep"]["sources"])
    return f'''<div class="prepbar"><div class="in"><b>{e(tx(L,"prep_t"))}</b><a class="pkit" href="/{L}/prepare/">{ {"ko":"비축 키트","en":"Stockpile kit","es":"Kit de reservas","fr":"Kit de réserves","ar":"حقيبة الطوارئ","vi":"Bộ dự trữ","id":"Kit persediaan"}[L] }</a><div class="pchips">{chips}</div><span class="tick" id="htick"></span></div></div>
<div class="preppanel" id="preppanel" hidden><div class="in"><div>{panels}</div><div><p class="note">{e(tx(L,"prep_src"))}</p><ul class="src">{src}</ul><button class="btn sm" id="pp-x">×</button></div></div></div>'''

def foot(L):
    t = T[L]
    return f"""</main><footer><div class="in">
<div class="flogos"><a href="https://www.wmm-hoa.com" target="_blank" rel="noopener" class="flogo"><img src="/assets/wmm-logo.png" alt="월드메이킹멤버스 주식회사 로고" width="52" height="52" class="wmm"><span><b>월드메이킹멤버스 주식회사</b><small>WORLD MAKING MEMBERS</small></span></a><a href="https://www.gcsme.kr" target="_blank" rel="noopener" class="flogo"><img src="/assets/gcsme-logo.jpg" alt="GCSME KOREA 로고" width="52" height="52" class="gc"><span><b>GCSME KOREA</b><small>Global &amp; Commonwealth SME Club</small></span></a><a href="https://www.gcsme.club" target="_blank" rel="noopener" class="flogo"><img src="/assets/gcsme-club.webp" alt="Global &amp; Commonwealth SME Club 로고" width="76" height="52" class="gclub"><span><b>Global &amp; Commonwealth SME Club</b><small>www.gcsme.club</small></span></a></div>
<div class="lic"><a href="https://www.ftc.go.kr/bizCommPop.do?wrkr_no=5898801039" target="_blank" rel="noopener">{e(t['biz_info'])}</a><span class="bar"></span><span>ONLINE LICENCE : 제2024-서울서초-2185호</span></div>
<p class="corp">{e(t['foot_corp'])} · E-mail 73036396@naver.com</p>
<div class="sites"><a href="https://www.wmm-hoa.com" target="_blank" rel="noopener"><b>WORLD MAKING MEMBERS</b><span>www.wmm-hoa.com ↗</span></a><a href="https://www.gcsme.kr" target="_blank" rel="noopener"><b>GCSME KOREA</b><span>www.gcsme.kr ↗</span></a><a href="https://www.gcsme.club" target="_blank" rel="noopener"><b>GLOBAL &amp; COMMONWEALTH SME CLUB</b><span>www.gcsme.club ↗</span></a></div>
<p class="corp"><a href="/{L}/notices/">{"본사 공지" if L=="ko" else "HQ notices"}</a> · <a href="/{L}/solutions/">{"진출 지원" if L=="ko" else "Who it's for"}</a> · <a href="/{L}/individuals/">{"개인 참여" if L=="ko" else "For individuals"}</a> · <a href="/{L}/gcsme/">{"GCSME 회원" if L=="ko" else "GCSME members"}</a> · <a href="/{L}/partners/">{"파트너 프로그램" if L=="ko" else "Partner programme"}</a> · <a href="/{L}/pricing/">{"주문·요금" if L=="ko" else "Orders & pricing"}</a> · <a href="/{L}/how/">{"서비스 진행 방식" if L=="ko" else "How it works"}</a> · <a href="/{L}/sample/">{"샘플 브리프" if L=="ko" else "Sample brief"}</a> · <a href="/{L}/about/">{"구축 현황" if L=="ko" else "Build status"}</a> · <a href="/{L}/mdb/">{"국제기구 조달" if L=="ko" else "MDB & UN tenders"}</a> · <a href="/{L}/conflict/">{"분쟁 상황판" if L=="ko" else "Conflict watch"}</a> · <a href="/{L}/prepare/">{"비축 키트" if L=="ko" else "Stockpile kit"}</a> · <a href="/{L}/verify/">{"검증 원칙" if L=="ko" else "Verification"}</a> · <a href="/{L}/projects/">{"프로젝트 랩" if L=="ko" else "Project Lab"}</a> · <a href="/{L}/consortium/">{"컨소시엄" if L=="ko" else "Consortium"}</a> · <a href="/{L}/experts/">{"검증원·전문가 참여" if L=="ko" else "Work with us"}</a> · <a href="/{L}/contracts/">{"계약서" if L=="ko" else "Contracts"}</a></p>
<p class="corp"><a href="/{L}/legal/terms/">{"이용약관" if L=="ko" else "Terms"}</a> · <a href="/{L}/legal/privacy/"><b>{"개인정보 처리방침" if L=="ko" else "Privacy"}</b></a> · <a href="/{L}/legal/refund/">{"환불 정책" if L=="ko" else "Refunds"}</a> · <a href="/{L}/legal/disclaimer/">{"면책 안내" if L=="ko" else "Disclaimer"}</a> · <a href="/{L}/feeds/">{e(t['feed'])}</a> · <a href="/{L}/embed/">{e(t['embed'])}</a></p>
<p class="corp">{e(t['disc'])}</p></div></footer>
<div class="fband"><a href="https://www.wmm-hoa.com" target="_blank" rel="noopener"><img src="/assets/wmm-logo-white.png" alt="WORLD MAKING MEMBERS" width="150" height="150"></a></div>
<div class="modal" id="authm" hidden><div class="mbox"><button class="x" id="authx" aria-label="close">×</button><h3 id="auth-h">{e(AT[L]['login'])}</h3>
<p class="note" id="authsoon" hidden></p>
<button class="btn gbtn" id="auth-google" type="button" hidden><svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg> {e(AT[L]['google'])}</button>
<form id="authf" hidden novalidate>
<label id="auth-name-w" hidden>{e(AT[L]['name'])}<input id="authn" autocomplete="name"></label>
<label id="auth-email-w">{e(AT[L]['email'])}<input id="authe" type="email" required autocomplete="email"></label>
<label id="auth-pw-w">{e(AT[L]['pw'])}<input id="authp" type="password" minlength="8" autocomplete="current-password"></label>
<label id="auth-age-w" hidden>{e(AT[L]['age'])}<select id="auth-age">{''.join(f'<option value="{k}">{e(v)}</option>' for k,v in AT[L]['age_opts'])}</select></label>
<label class="chk" id="auth-terms-w" hidden><input type="checkbox" id="auth-terms"> <span>{AT[L]['terms']}</span></label>
<button class="btn pri" type="submit" id="auth-sub">{e(AT[L]['login'])}</button>
<p class="note" id="authmsg" aria-live="polite"></p><p class="note" id="auth-sw"></p></form></div></div>
<script>window.RADAR_LANG="{L}";window.RADAR_T={json.dumps(dict(members_only=t['members_only'],rl=t['rl'],ask_soon=AT[L]['ask_soon']),ensure_ascii=False)};window.RADAR_AT={json.dumps({k:v for k,v in AT[L].items() if k not in ("terms","age_opts")},ensure_ascii=False)};</script>
<script src="/assets/config.js"></script><script src="/assets/auth.js"></script><script src="/assets/site.js" defer></script></body></html>"""

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
    if iso in GUIDES:
        body.append(f'<p class="regbar"><a class="chip" href="{url(L,iso)}guide/">{"How to sell to this government →" if L!="ko" else "이 나라 정부에 파는 법 →"}</a> <a class="chip" href="/{L}/mdb/">{"Development bank tenders" if L!="ko" else "개발은행·국제기구 조달"}</a></p>')
    if c.get("reg"):
        P = BY[c["parent"]]
        body.append(f'<p class="regbar"><span>{e(tx(L,"rg_parent"))}</span> <a class="chip" href="{url(L,P["iso"])}">{flag(P["iso"])} {e(nm(P["iso"],L))}</a></p>')
    elif regs_of(iso):
        body.append(f'<p class="regbar"><span>{e(tx(L,"rg_h"))}</span> ' + " ".join(f'<a class="chip" href="{url(L,x["iso"])}">{e(nm(x["iso"],L))}</a>' for x in regs_of(iso)) + '</p>')
    if not done(iso):
        body.append(f'<p class="summary">{e(tx(L,"rg_wait") if c.get("reg") else t["notyet"])}</p>')
    else:
        body.append(f'<p class="summary">{e(summ)}</p>')
        body.append(P3.next_box(iso, L, C3(), d))
        st = G(d, "status", L)
        if st:
            rs = tx(L, "rs")
            body.append(sec("status", tx(L, "rg_stat"), "".join(f'<div class="kv"><span>{e(rs[k])}</span><span>{e(" · ".join(st[k]) if isinstance(st[k], list) else st[k])}</span></div>' for k in rs if st.get(k))))
        body.append(sec("leader", t["leader"], f"<p>{e(G(d,'leader',L))}</p>" if G(d,'leader',L) else ""))
        body.append(sec("agenda", t["agenda"], lst(G(d, "agenda", L), lambda x: f"<li>{e(x)}</li>")))
        def pj(p):
            p = p if isinstance(p, dict) else {"title": p}
            kv = "".join(f'<div class="kv"><span>{e(t[k])}</span><span>{e(p.get(k))}</span></div>' for k in ("ministry", "budget", "status") if p.get(k))
            link = f'<a href="{e(p["url"])}" rel="nofollow noopener" target="_blank">{e(t["sources"])}</a>' if str(p.get("url","")).startswith("https://") else ""
            return f'<details class="folder"><summary><b>{e(p.get("title"))}</b>{f"<span class=bd>{e(p.get(chr(98)+chr(117)+chr(100)+chr(103)+chr(101)+chr(116)))}</span>" if p.get("budget") else ""}</summary><div class="fb">{f"<p>{e(p.get(chr(100)+chr(101)+chr(116)+chr(97)+chr(105)+chr(108)))}</p>" if p.get("detail") else ""}{kv}{link}</div></details>'
        pjs = G(d, "projects", L) or []
        body.append(sec("projects", t["projects"], "".join(pj(p) for p in pjs)))
        bzs = G(d, "biz", L) or [{"title": x} for x in (d.get("items") or [])]
        pi = pub_idx(len(bzs))
        def bz(b, i):
            b = b if isinstance(b, dict) else {"title": b}
            if i == pi:
                return f'<div class="card"><p class="note">{"이번 주 공개" if L=="ko" else "Open this week"}</p><h3>{e(b.get("title"))}</h3>{f"<p>{e(b.get(chr(119)+chr(104)+chr(121)))}</p>" if b.get("why") else ""}{f"<p class=note>{e(b.get(chr(116)+chr(97)+chr(114)+chr(103)+chr(101)+chr(116)))}</p>" if b.get("target") else ""}</div>'
            return f'<a class="card locked" data-mi="{i}" data-iso="{iso}" href="{P3.paylink(L, "biz", iso)}"><h3>{e(b.get("title"))}</h3><p class="note">🔒 {"이유·대상 바이어 — 분석 회원 월 19,800원" if L=="ko" else "Why-now and buyers — analysis member ₩19,800/mo"}</p></a>'
        body.append(sec("biz", t["biz"], (f'<div class="cards">{"".join(bz(b, i) for i, b in enumerate(bzs))}</div>' + (lockbox(L, iso, len(bzs) - 1) if len(bzs) > 1 else "")) if bzs else ""))
        def td(x):
            return f'<li><b>{e(x.get("title"))}</b><span class="note"> · {e(x.get("buyer",""))}{" · "+e(t["deadline"])+" "+e(x.get("deadline")) if x.get("deadline") else ""}</span> <button class="btn xs member" data-act="watch" data-iso="{iso}" data-title="{e(x.get("title"))}" data-deadline="{e(x.get("deadline",""))}">{e(t["watch"])}</button></li>'
        tds = [x for x in (G(d, "tenders", L) or []) if x]
        body.append(sec("tenders", t["tenders"], ("<ul>" + "".join(td(x) for x in tds) + "</ul>") if tds else ""))
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
    if c.get("reg"): same = [BY[x["iso"]] for x in REGS if x["iso"] != iso][:12]
    side = f"""<aside class="side">
<div class="box"><b>{"이 나라 진출 브리프" if L=="ko" else "Market-entry brief for this country"}</b><p class="note">{"정부 과제·입찰·한국 지원·위험을 사람이 검수해 5영업일 안에 보내 드립니다." if L=="ko" else "Priorities, tenders, Korean support and risks, reviewed by a person and delivered within five business days."}</p><a class="btn pri" href="/{L}/pricing/?p=brief&c={e(name)}#order">{"견적 요청" if L=="ko" else "Request a quote"}</a></div>
<div class="box"><b>{e(t['alert_cta'])}</b><button class="btn member" data-act="follow" data-iso="{iso}">{e(t['cta_join'])}</button></div>
<div class="box"><b>{e(t['more_cty'])}</b><div class="mini">{''.join(f'<a href="{url(L,x["iso"])}">{flag(x["iso"])} {e(nm(x["iso"],L))}</a>' for x in same)}</div></div>
<div class="box gc"><img src="/assets/emblem.png" alt="" width="40" height="40"><span>GCSME · Global &amp; Commonwealth SME Club<br><a href="https://www.gcsme.kr" target="_blank" rel="noopener">gcsme.kr</a></span></div>
</aside>"""
    jl = ld({"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "inLanguage": L,
             "dateModified": d.get("updated") or TODAY, "about": ({"@type": "AdministrativeArea", "name": c["en"], "containedInPlace": {"@type": "Country", "name": BY[c["parent"]]["en"]}} if c.get("reg") else {"@type": "Country", "name": c["en"]}),
             "publisher": ORG, "mainEntityOfPage": BASE + path, "image": BASE + "/assets/og.jpg"})
    crumbs = ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "GOV RADAR", "item": BASE + f"/{L}/"},
        {"@type": "ListItem", "position": 2, "name": name, "item": BASE + path}]})
    hero = f"""<section class="chero"><div class="in">
<p class="crumb"><a href="/{L}/">GOV RADAR</a> / {e(t['regions'][c['r']])}{(' / <a href="'+url(L,c['parent'])+'">'+e(nm(c['parent'],L))+'</a> / '+e(tx(L,'rgt')[c['type']])) if c.get('reg') else ''}</p>
<div class="ct">{flag(iso, 'big')}<div><h1>{e(name)}</h1><p class="alt">{e(c['en'] if L!='en' else c['ko'])} · {iso}{' · Commonwealth' if c.get('cw') else ''}</p></div></div>
<p class="meta">{e(t['updated'])} {e(d.get('updated','—'))}{(' · '+e(t['asof'])+' '+e(d.get('asof'))) if d.get('asof') else ''}{f" · <span class=lvl data-l={lv}>{e(t['rl'][lv])}</span>" if lv else ''}</p>
</div></section>"""
    return head(L, title, desc, path, alts, jl + crumbs) + hero + f'<div class="in cgrid"><article>{"".join(body)}</article>{side}</div>' + foot(L)

STK = json.load(open(os.path.join(SRC, "stock.json"), encoding="utf8"))
GUIDES = json.load(open(os.path.join(SRC, "guides.json"), encoding="utf8"))
for _iso, _d in DATA.items():
    if isinstance(_d.get("guide"), dict): GUIDES[_iso] = _d["guide"]
MDBI = [("WB","World Bank","세계은행","https://projects.worldbank.org/en/projects-operations/procurement",["world bank","세계은행","ibrd"]),
 ("ADB","Asian Development Bank","아시아개발은행","https://www.adb.org/projects/tenders",["adb","asian development bank","아시아개발은행"]),
 ("AfDB","African Development Bank","아프리카개발은행","https://www.afdb.org/en/projects-and-operations/procurement",["afdb","african development bank","아프리카개발은행"]),
 ("IDB","Inter-American Development Bank","미주개발은행","https://www.iadb.org/en/how-we-can-work-together/procurement/procurement-projects/procurement-notices",["inter-american","미주개발은행"]),
 ("EBRD","EBRD","유럽부흥개발은행","https://ecepp.ebrd.com",["ebrd","유럽부흥개발은행"]),
 ("AIIB","AIIB","아시아인프라투자은행","https://www.aiib.org/en/opportunities/business/project-procurement/index.html",["aiib","아시아인프라투자은행"]),
 ("UNGM","UN Global Marketplace","UN 조달 (UNGM)","https://www.ungm.org",["ungm","undp","unicef","unops","유엔","unido"]),
 ("KR","Korea EDCF · KOICA","한국 EDCF·KOICA","",["edcf","koica","수출입은행","대외경제협력기금","코이카"])]
def mdb_items():
    out = []
    for iso, d in DATA.items():
        en = d.get("en") or {}
        for kind, arr, arr_en in (("oda", d.get("oda") or [], en.get("oda") or []), ("tenders", d.get("tenders") or [], en.get("tenders") or [])):
            for i, x in enumerate(arr):
                if not isinstance(x, dict): continue
                txt = json.dumps(x, ensure_ascii=False).lower().replace("남아프리카개발은행", "dbsa")
                m = next((b for b in MDBI if any(k in txt for k in b[4])), None)
                if m: out.append({"iso": iso, "b": m, "kind": kind, "x": x, "xe": arr_en[i] if i < len(arr_en) and isinstance(arr_en[i], dict) else {}})
    return out
def guide_page(iso, L):
    g = GUIDES[iso]; en = L != "ko"; c = BY[iso]; name = nm(iso, L)
    v = lambda k: ((g.get("en") or {}).get(k) or g.get(k)) if en else g.get(k)
    title = (f"How to sell to the Government of {c['en']}" if en else f"{name} 정부에 파는 법 — 조달 포털·등록·현지 요건")
    li = lambda a: "<ul>" + "".join(f"<li>{e(x)}</li>" for x in (a or [])) + "</ul>"
    body = f"""<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a> / <a href="{url(L,iso)}">{e(name)}</a></p><div class="ct">{flag(iso,'big')}<div><h1>{e(title)}</h1><p class="alt">{"Checked" if en else "확인일"} {e(g.get('checked',''))}</p></div></div></div></section>
<div class="in stock"><blockquote class="summary">{e(v('who') or '')}</blockquote>
<h2>{"Procurement portals" if en else "조달 포털"}</h2><ul>{''.join(f'<li><a href="{e(p["url"])}" target="_blank" rel="noopener nofollow">{e(p["name"])}</a>{"" if en else " — "+e(p.get("note",""))}</li>' for p in g.get('portals',[]))}</ul>
<h2>{"How to take part" if en else "참여 순서"}</h2><ol>{''.join(f"<li>{e(x)}</li>" for x in (v('steps') or []))}</ol>
<h2>{"Local preference & limits" if en else "현지 우대·제한"}</h2>{li(v('local'))}
<p><b>{"Bid language" if en else "입찰 언어"}</b> · {e(v('lang') or '—')}</p>
{f'<h2>{"Development-bank projects" if en else "개발은행 사업"}</h2><p>{e(v("mdb"))}</p>' if v('mdb') else ''}
{f'<h2>{"Good to know" if en else "알아 둘 점"}</h2>'+li(v('tips')) if v('tips') else ''}
<h2>{"Sources" if en else "자료 원문"}</h2><ul class="src">{''.join(f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener">{e(x["title"])}</a></li>' for x in g.get('sources',[]))}</ul>
<p class="note">{"Summary of public sources. Check the original and latest rules before bidding." if en else "공개 자료 요약입니다. 입찰 전 원문과 최신 규정을 확인하세요."}</p>
<p><a class="btn pri" href="{url(L,iso)}">{e(name)} {"radar" if en else "레이더 보기"}</a> <a class="btn" href="/{L}/mdb/">{"Development bank tenders" if en else "개발은행·국제기구 조달"}</a></p></div>"""
    jl = ld({"@context": "https://schema.org", "@type": "HowTo", "name": title, "inLanguage": L, "step": [{"@type": "HowToStep", "text": x} for x in (v('steps') or [])]})
    return head(L, title + " · GOV RADAR", (v('who') or '')[:150], f"{url(L,iso)}guide/", {l: f"{url(l,iso)}guide/" for l in LANGS}, jl) + body + foot(L)
def mdb_page(L):
    en = L != "ko"; items = mdb_items()
    t_ = "Tenders & deadlines — governments and development banks" if en else "입찰·마감 보드 — 각국 정부와 개발은행"
    inst = "".join(f'<a class="card" href="{e(b[3])}" target="_blank" rel="noopener"><h3>{e(b[1] if en else b[2])} ↗</h3></a>' for b in MDBI if b[3])
    rows = "".join(f'<div class="card"><p class="note"><a href="{url(L,x["iso"])}">{flag(x["iso"])} {e(nm(x["iso"],L))}</a> · {e(x["b"][1] if en else x["b"][2])}</p><h3>{e((x["xe"].get("title") if en else None) or x["x"].get("title",""))}</h3><p class="note">{e(" · ".join(str(v) for v in [x["x"].get("buyer") or x["x"].get("agency"), x["x"].get("value") or x["x"].get("amount"), x["x"].get("deadline")] if v))}</p>{f"<a href={chr(34)}{e(x[chr(120)][chr(117)+chr(114)+chr(108)])}{chr(34)} target=_blank rel=noopener>{chr(8599)}</a>" if str(x["x"].get("url","")).startswith("https://") else ""}</div>' for x in items)
    body = f"""<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{e(t_)}</h1></div></section>
<div class="in stock"><h2 id="deadlines">{"Open tenders by deadline" if en else "마감일 순 열린 입찰"}</h2><p class="note">{"Choose your field. Deadlines are taken from the original notices; always check the notice before bidding." if en else "분야를 고르세요. 마감일은 원문 공고 기준이며, 입찰 전 반드시 원문을 확인하세요."} <a href="{P3.paylink(L, "fit")}">{"Partnership consultation (free) →" if en else "프로젝트 파트너십 무료 상담 →"}</a> · <a href="/{L}/pricing/?p=fit#order">{"Fit review ₩100,000 →" if en else "공고 1건 적합도 검토 10만 원 →"}</a></p>{P3.deadline_board(L, C3())}
<h2>{"Development banks and UN agencies" if en else "개발은행·국제기구"}</h2><p class="summary">{"Lender-financed projects follow the lender's procurement rules and are more open to foreign firms. Start by registering on each institution's portal." if en else "차관 사업은 해당 기관의 조달 규정을 따라 외국 기업에 상대적으로 열려 있습니다. 기관별 포털 등록부터 시작하세요."}</p>
<h2>{"Institution portals" if en else "기관별 조달 포털"}</h2><div class="cards">{inst}</div>
<h2>{"Projects in the radar" if en else "레이더에 잡힌 사업"} ({len(items)})</h2><div class="cards">{rows or '<p class="note">—</p>'}</div></div>"""
    return head(L, t_ + " · GOV RADAR", t_, f"/{L}/mdb/", {l: f"/{l}/mdb/" for l in LANGS}) + body + foot(L)

CONF = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "conflict.json"), encoding="utf-8"))
ME = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "mideast.json"), encoding="utf-8"))
VPOL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "verify.json"), encoding="utf-8"))
VBC = {"ok":"#067647;background:#ecfdf3;border-color:#75e0a7","mid":"#b54708;background:#fffaeb;border-color:#fec84b","low":"#475467;background:#f9fafb;border-color:#d0d5dd","bad":"#b42318;background:#fef3f2;border-color:#fda29b"}
def vbh(v, en):
    x = VPOL["verdicts"].get(v, VPOL["verdicts"]["unv"])
    return f'<span class="vb" style="color:{VBC[x["c"]]}" title="{e(x["d_en"] if en else x["d_ko"])}">{e(x["en"] if en else x["ko"])}</span>'
def policy_html(en):
    r = VPOL["rules_en" if en else "rules_ko"]
    return (f'<h2>{"Verification policy" if en else "GOV RADAR 검증 원칙"}</h2><ol>' + "".join(f"<li>{e(x)}</li>" for x in r) + "</ol>"
            + '<ul class="src">' + "".join(f'<li><b>T{x["n"]}</b> {e(x["en"] if en else x["ko"])}</li>' for x in VPOL["tiers"]) + "</ul>"
            + '<p class="vleg">' + "".join(f'{vbh(k,en)} {e(VPOL["verdicts"][k]["d_en"] if en else VPOL["verdicts"][k]["d_ko"])}<br>' for k in VPOL["verdicts"] if k != "unv") + "</p>")
VCSS = "<style>.vb{display:inline-block;font-size:11px;font-weight:700;padding:1px 6px;border-radius:4px;margin-right:6px;border:1px solid;white-space:nowrap}.cfh{border-left:4px solid #b42318}.sref a{font-size:11px;margin-left:3px}.vleg{line-height:2;font-size:13px}</style>"
GEO = {"iran": dict(focus="IR,OM,AE,SA,QA,KW,IQ,BH", hl="IR", pts=[[26.57, 56.25]]),
       "ukraine": dict(focus="UA,BY,MD,RO", hl="UA", pts=[[48.0, 37.8]]),
       "korea": dict(focus="KR,KP,JP", hl="KP", pts=[[38.3, 127.0], [39.0, 125.75]]),
       "taiwan": dict(focus="TW,PH,JP", hl="TW", pts=[[24.5, 119.6]]),
       "lebanon": dict(focus="LB,IL,SY,JO,CY", hl="LB", pts=[[33.1, 35.5]])}
WORLDPTS = [[26.57, 56.25], [48.0, 37.8], [38.3, 127.0], [24.5, 119.6], [33.1, 35.5]]
SCEN = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "scenarios.json"), encoding="utf-8"))
def hotmap(focus, hl="", pts=(), cls=""):
    return f"""<div class="hotmap {cls}" data-focus="{e(focus)}" data-hl="{e(hl)}" data-pts='{json.dumps(list(pts))}' role="img" aria-label="radar map"></div>"""
def scen_html(L):
    en = L != "ko"
    cards = "".join(f'<div class="card"><h3>{flag(x["iso"]) if x["iso"]!="UN" else "🌐"} {e(x["en"] if en else x["ko"])}</h3><p>{e(x["s_en"] if en else x["s_ko"])}</p><ul>' + "".join(f"<li>{e(i)}</li>" for i in (x["prep_en"] if en else x["prep_ko"])) + f'</ul><p class="now">{vbh(x["v"], en)}<b>{"Now" if en else "현재 실제 지표"}</b> · {e(x["now_en"] if en else x["now_ko"])}</p></div>' for x in SCEN["items"])
    return f'<h2 id="scenarios">{"Preparedness scenarios (hypothetical)" if en else "국가별 대비 시나리오 (가정)"}</h2><div class="callout">{e(SCEN["note_en"] if en else SCEN["note_ko"])}</div><div class="scen">{cards}</div>'
def liveboard(L, mode="full"):
    names = {iso: [nm(iso, L), BY[iso]["slug"]] for iso in BY if not BY[iso].get("reg")}
    names.setdefault("TW", [{"ko": "대만", "es": "Taiwán", "fr": "Taïwan", "ar": "تايوان", "vi": "Đài Loan", "id": "Taiwan"}.get(L, "Taiwan"), ""])
    hd = {"ko": ("지금 세계 상황 — 확인된 사실만", "매일 아침 자동 갱신 · 2곳 이상 독립 출처 또는 정부·국제기구 공식 발표만 싣습니다"),
          "en": ("World situation now — verified facts only", "Updated automatically every morning · only facts confirmed by 2+ independent sources or an official statement")}.get(L) or ("World situation now — verified facts only", "Updated automatically every morning · only facts confirmed by 2+ independent sources or an official statement")
    return (f'<div class="liveboard" data-mode="{mode}" data-names=\'{e(json.dumps(names, ensure_ascii=False))}\'>'
            f'<h2>{e(hd[0])}</h2><p class="note">{e(hd[1])}</p><div class="lb-body"><p class="note">…</p></div></div>')
def conflict_page(L):
    en = L != "ko"; C = CONF; S = C["sources"]
    sr = lambda a: '<span class="sref">' + "".join(f'<a href="{e(S[i]["u"])}" target="_blank" rel="noopener">[{i+1}]</a>' for i in (a or []) if i < len(S)) + "</span>"
    t_ = "Conflict watch — verified facts only" if en else "전쟁·분쟁 상황판 — 확인된 사실만"
    LV = {"war": "WAR" if en else "전쟁", "tension": "TENSION" if en else "긴장", "watch": "WATCH" if en else "경계"}
    def gm(h):
        g = GEO.get(h["id"]) or dict(focus=h["iso"], hl=h["iso"], pts=[])
        return hotmap(g["focus"], g["hl"], g["pts"])
    cards = "".join(f'<div class="card"><div class="cf-h2"><div><h3>{flag(h["iso"])} {e(h["en"] if en else h["ko"])} <span class="lv {h["level"]}">{LV.get(h["level"],"")}</span></h3><p class="note">{e(h["status_en"] if en else h["status_ko"])}</p></div>{gm(h)}</div><ul>' + "".join(f'<li>{vbh(f["v"],en)}{e(f["en"] if en else f["ko"])}{sr(f.get("src"))}</li>' for f in h["facts"] if f["v"] != "unv") + f'</ul><p class="note">{e(h["biz_en"] if en else h["biz_ko"])}</p></div>' for h in C["hotspots"])
    prep = "".join(f'<li>{vbh(p["v"],en)}{e(p["en"] if en else p["ko"])}{sr(p.get("src"))}' + (f'<br><small class="note">{e(p.get("note_en") if en else p.get("note_ko"))}</small>' if (p.get("note_en") if en else p.get("note_ko")) else "") + "</li>" for p in C["prep"] if p["v"] != "unv")
    claims = "".join(f'<li>{vbh(p["v"],en)}“{e(p["en"] if en else p["ko"])}”<br><small class="note">{e(p["note_en"] if en else p["note_ko"])}</small></li>' for p in C["claims"])
    srcs = "".join(f'<li><a href="{e(z["u"])}" target="_blank" rel="noopener">{e(z["t"])}</a> <small class="note">T{z["tier"]}</small></li>' for z in S)
    body = f"""<section class="chero img-cf"><div class="in cfhero"><div><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{e(t_)}</h1><p class="lede">{"US DoD, JCS, CENTCOM, NATO and EU statements cross-checked with wire services and defence press." if en else "미 국방부·합참·CENTCOM·NATO·EU 발표를 통신사·국방 전문매체와 교차 확인합니다."}</p></div>{hotmap("WORLD", "IR,UA,KP,TW,LB", WORLDPTS)}</div></section>
<div class="in stock">{liveboard(L)}<h2 style="margin-top:40px">{"Detail with sources" if en else "출처가 달린 상세 내용"}</h2><blockquote class="summary cfh"><b>{"As of" if en else "기준일"} {e(C["updated"])}</b> · {e(C["summary_en"] if en else C["summary_ko"])}<br><small class="note">{e(C["advice_en"] if en else C["advice_ko"])}</small></blockquote>
<div class="cards c2">{cards}</div>
{scen_html(L)}
<h2>{"National preparedness policies — fact-checked" if en else "각국 대비 정책 — 사실 확인"}</h2><ul>{prep}</ul>
<h2>{"Circulating claims — verdicts" if en else "떠도는 주장 판정"}</h2><ul>{claims}</ul>
<div class="card" style="border-left:4px solid #b54708"><p class="note">{"WEEKLY · ANALYSIS MEMBERS" if en else "주간 · 분석 회원"}</p><h3>{"Hormuz & Middle East risk brief" if en else "호르무즈·중동 리스크 브리프"}</h3><p><b>{e(ME["week"])}</b> — {e(ME["headline_en"] if en else ME["headline_ko"])}</p><p class="note">{"Full indicators (oil, transit, insurance), item-by-item verdicts and the weekly action checklist are for BUILD M2+ members." if en else "유가·통항·보험 지표, 항목별 검증 판정, 이번 주 할 일 체크리스트 전체는 BUILD M2 이상 회원에게 제공합니다."}</p><p><a class="btn pri" href="{P3.paylink(L, "risk")}">{"Analysis member · ₩19,800/mo →" if en else "분석 회원 월 19,800원으로 보기 →"}</a></p></div>
<p><a class="btn" href="/{L}/prepare/">{"Home stockpile kit →" if en else "가정 비축 키트 →"}</a> <a class="btn" href="/{L}/verify/">{"Verification policy" if en else "검증 원칙"}</a></p>
<h2>{"Sources" if en else "출처"}</h2><ol class="src">{srcs}</ol></div>"""
    jl = ld({"@context": "https://schema.org", "@type": "WebPage", "name": t_, "inLanguage": L, "dateModified": C["updated"], "publisher": ORG})
    return head(L, t_ + " · GOV RADAR", (C["summary_en"] if en else C["summary_ko"])[:155], f"/{L}/conflict/", {l: f"/{l}/conflict/" for l in LANGS}, jl + VCSS + JSVM + '<script src="/assets/hotmap.js" defer></script>') + body + foot(L)
def verify_page(L):
    en = L != "ko"; t_ = "How GOV RADAR verifies information" if en else "GOV RADAR는 정보를 이렇게 검증합니다"
    body = f"""<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{e(t_)}</h1></div></section>
<div class="in stock"><p class="summary">{"Every country, region, tender and conflict item is cross-checked daily. Each item carries a verdict and its sources; unverified items are not published." if en else "국가·지역·입찰·분쟁 정보는 매일 교차검증합니다. 항목마다 판정과 출처를 함께 싣고, 확인되지 않은 내용은 공개하지 않습니다."}</p>{policy_html(en)}
<p><a class="btn" href="/{L}/conflict/">{"Conflict watch" if en else "전쟁·분쟁 상황판"}</a></p></div>"""
    return head(L, t_ + " · GOV RADAR", t_, f"/{L}/verify/", {l: f"/{l}/verify/" for l in LANGS}, VCSS) + body + foot(L)
import gen_build_section as GB
import pages2 as P2
import pages3 as P3
def about_page(L):
    lk = "ko" if L == "ko" else "en"; a = GB.A[lk]
    sec_ = GB.section(lk).replace(GB.BASE + f"/{lk}/", f"/{L}/")
    jl = ld({"@context": "https://schema.org", "@type": "AboutPage", "name": a["h"], "inLanguage": L, "publisher": ORG, "description": a["lede"]})
    return head(L, a["h"] + " · GOV RADAR", a["lede"][:150], f"/{L}/about/", {l: f"/{l}/about/" for l in LANGS}, jl + GB.CSS) + sec_ + foot(L)

def stock_page(L):
    en = L != "ko"; k = (lambda x, a: x[a + "_en"] if en else x[a + "_ko"]); nmk = (lambda x: x["en"] if en else x["ko"])
    pri = {"must": "Essential", "rec": "Recommended", "if": "If applicable"} if en else {"must": "필수", "rec": "권장", "if": "해당 시 필수"}
    H = (dict(t="Home stockpile kit — what, how much, which products", d="A practical home stockpile list: 20 categories, quantities for 2 adults over 14 days, and the actual products to buy.", cat="Full list of essentials", q="Quantities — 2 adults · 14 days", pr="Actual products", prp="Compare prices and stock through the links. No retailer partnership.", sf="Safety first", src="Sources")
         if en else dict(t="가정 비축 키트 — 무엇을, 얼마나, 어떤 제품으로", d="생활필수품 20개 분류, 성인 2명·14일 비축 수량, 실제로 살 제품 구성까지 한 페이지에 정리했습니다.", cat="생활필수품 전체 리스트", q="비축 수량 — 성인 2명 · 14일", pr="실제 제품 구성", prp="가격과 재고는 링크에서 비교하세요. 특정 판매처와 제휴하지 않았습니다.", sf="꼭 지킬 것", src="자료 원문"))
    def qv(q):
        if q["mode"] == "pd": return f'{q["per"]*28}{q["unit_ko"]} {"+" if en else "이상"}'
        if q["mode"] == "scale": return f'{q["lo"]}~{q["hi"]}{" " if en else ""}{q["unit_en"] if en else q["unit_ko"]}'
        return (q["txt_en"] if en else q["txt_ko"]).replace("{d}", "14").replace("{p}", "2")
    CN = {c["id"]: nmk(c) for c in STK["cats"]}
    from urllib.parse import quote
    body = f"""<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{e(H['t'])}</h1></div></section>
<div class="in stock">
<blockquote class="summary">{e(STK['giles']['en' if en else 'ko'])}<br><small class="note">{e(STK['giles']['note_en' if en else 'note_ko'])}</small></blockquote>
<div class="cards">{''.join(f'<div class="card"><h3>{e(nmk(x))}</h3><p>{e(k(x,"p"))}</p></div>' for x in STK['stages'])}</div>
<h2>{e(H['cat'])}</h2><div class="cards">{''.join(f'<div class="card"><h3>{e(nmk(c))} <span class="st-pri {c["pri"]}">{pri[c["pri"]]}</span></h3><p>{e(k(c,"items"))}</p></div>' for c in STK['cats'])}</div>
<h2>{e(H['q'])}</h2><table class="qt">{''.join(f'<tr><td>{e(nmk(q))}</td><td><b>{e(qv(q))}</b></td></tr>' for q in STK['qty'])}</table>
<h2>{e(H['pr'])}</h2><p class="note">{e(H['prp'])}</p><div class="cards">{''.join(f'<div class="card"><p class="note">{e(CN.get(x["cat"],""))}</p><h3>{e(nmk(x))}</h3><p>{e(k(x,"spec"))}</p><p><a href="https://search.shopping.naver.com/search/all?query={quote(x["q"])}" target="_blank" rel="noopener nofollow">{"Naver Shopping" if en else "네이버쇼핑"}</a> · <a href="https://www.coupang.com/np/search?q={quote(x["q"])}" target="_blank" rel="noopener nofollow">{"Coupang" if en else "쿠팡"}</a></p></div>' for x in STK['products'])}</div>
<h2>{e(H['sf'])}</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in STK['safety_en' if en else 'safety_ko'])}</ul>
<h2>{e(H['src'])}</h2><ul class="src">{''.join(f'<li><a href="{e(z["url"])}" target="_blank" rel="noopener">{e(z["title"])}</a></li>' for z in STK['sources'])}</ul>
</div>"""
    jl = ld({"@context": "https://schema.org", "@type": "HowTo", "name": H["t"], "inLanguage": L, "supply": [{"@type": "HowToSupply", "name": nmk(c)} for c in STK["cats"]], "step": [{"@type": "HowToStep", "name": nmk(x), "text": k(x, "p")} for x in STK["stages"]]})
    return head(L, H["t"] + " · GOV RADAR", H["d"], f"/{L}/prepare/", {l: f"/{l}/prepare/" for l in LANGS}, jl) + body + foot(L)

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

def hotband(L):
    en = L != "ko"; items = ""
    for h in CONF["hotspots"]:
        g = GEO.get(h["id"]) or dict(focus=h["iso"], hl=h["iso"], pts=[])
        items += f'<a href="/{L}/conflict/">{hotmap(g["focus"], g["hl"], g["pts"])}<span><span class="lv {h["level"]}">{ {"war":"WAR" if en else "전쟁","tension":"TENSION" if en else "긴장","watch":"WATCH" if en else "경계"}.get(h["level"],"") }</span> {e(h["en"] if en else h["ko"])}</span></a>'
    return f'<section class="hotband"><div class="in"><h2>{"Hot zones now — verified" if en else "지금 주목할 분쟁 지역 — 검증된 사실만"}</h2><p class="note">{e(CONF["updated"])} · <a href="/{L}/conflict/" style="color:inherit">{"Open conflict watch →" if en else "분쟁 상황판 열기 →"}</a></p><div class="hgrid">{items}</div></div></section>'
WEEK = datetime.date.fromisoformat(TODAY).isocalendar()[1]
def pub_idx(n): return (WEEK % n) if n else 0   # which business opportunity shows its WHY publicly this week
def lockbox(L, iso, n):
    ko = L == "ko"
    return (f'<div class="lockbox"><b>{"나머지 "+str(n)+"건의 이유·대상 바이어" if ko else f"Why-now and target buyers for the other {n}"}</b>'
            f'<p class="note">{"무료 회원은 매월 3개국까지 사람이 검수한 요약을 이메일로 받습니다(24시간 안 발송). BUILD 회원은 제한 없이 받습니다." if ko else "Free members get a human-reviewed summary by email for up to 3 countries a month (sent within 24h). BUILD members get them all."}</p>'
            f'<p class="cta"><a class="btn pri" href="{P3.paylink(L, "biz", iso)}">{"분석 회원 월 19,800원으로 전체 보기" if ko else "See all — analysis member ₩19,800/mo"}</a> <a class="btn" href="/{L}/unlock/?c={iso}">{"무료로 3개국 요약 받기" if ko else "Get 3 countries free"}</a></p></div>')

def C3():
    return dict(e=e, head=head, foot=foot, url=url, flag=flag, nm=nm, DATA=DATA, BY=BY, LANGS=LANGS, TODAY=TODAY, G=G)

P3._NM = lambda iso, L: nm(iso, L)

def home(L):
    t = T[L]; path = f"/{L}/"; alts = {l: f"/{l}/" for l in LANGS}
    n_done = sum(done(i) for i in BY if not is_reg(i)); n_t = sum(len(DATA.get(i, {}).get("tenders") or []) for i in BY)
    O = opps(); n_b = len(O); last = max([max(d.get("updated", "") or "", ((d.get("risk") or {}).get("checked") or "")) for d in DATA.values()] or [""])
    regions = "".join(f'<button class="chip" data-r="{k}">{e(v)}</button>' for k, v in t["regions"].items())
    grid = "".join(f'<a class="flag {"done" if done(c["iso"]) else ""}" data-r="{c["r"]}" data-n="{e((nm(c["iso"],L)+" "+c["en"]+" "+c["ko"]).lower())}" href="{url(L,c["iso"])}">{flag(c["iso"])}<span>{e(nm(c["iso"],L))}</span>{f"<i class=rk data-l={lvl(c[chr(105)+chr(115)+chr(111)])}></i>" if lvl(c["iso"]) in ("high","medium") else ""}</a>'
                   for c in sorted(META, key=lambda c: nm(c["iso"], L)))
    lk = "ko" if L == "ko" else "en"
    board = "".join(f'<a class="opp{"" if j < 6 else " lk"}" href="{url(L,o["iso"])+"#biz" if j < 6 else P3.paylink(L, "biz", o["iso"])}"><span class="who">{flag(o["iso"])} {e(nm(o["iso"],L))}{" <i class=fit>"+e(t["fit"])+"</i>" if o["fit"]=="high" else ""}</span><b>{e(o[lk])}</b><span class="note">{e(o["why_"+lk][:120]) if j < 6 else ("🔒 이유·대상 바이어 — 분석 회원 월 19,800원" if L=="ko" else "🔒 Why-now & buyers — analysis member ₩19,800/mo")}</span></a>' for j, o in enumerate(O[:24]))
    evs = events()[:12]
    evh = "".join(f'<a class="ev" href="{url(L,x["iso"])}#events"><span class="d">{e(x.get("date","")[5:].replace("-","/"))}</span><span>{flag(x["iso"])} <b>{e(x.get("title_en") if L!="ko" and x.get("title_en") else x.get("title"))}</b><br><span class="note">{e(x.get("org",""))} · {e(x.get("city",""))}</span></span></a>' for x in evs) or f'<p class="note">—</p>'
    plans = "".join(f'<div class="plan{" mid" if a.startswith("BUILD M2") else ""}"><span class="tier">{e(a)}</span><b class="price">{e(b)}</b><p>{e(c)}</p></div>' for i, (a, b, c) in enumerate(PLANS[L]))
    jl = ld({"@context": "https://schema.org", "@type": "WebSite", "name": "GOV RADAR", "url": BASE + "/", "inLanguage": L, "publisher": ORG, "description": t["desc_home"]})
    return head(L, t["title_home"], t["desc_home"], path, alts, jl + JSVM + '<script src="/assets/hotmap.js" defer></script>') + f"""
<section class="hero"><div class="in"><div>
<p class="eb"><i class="live"></i>{({"ko":"193개국 추적 · {n}개국 심층 조사","es":"193 gobiernos seguidos · {n} analizados a fondo","fr":"193 gouvernements suivis · {n} étudiés en détail","ar":"نتابع 193 حكومة · {n} مدروسة بعمق","vi":"Theo dõi 193 chính phủ · {n} nước nghiên cứu sâu","id":"Memantau 193 pemerintah · {n} diteliti mendalam"}.get(L,"Tracking 193 governments · {n} researched in depth")).replace("{n}",str(n_done))}</p>
<h1>{e(t['tagline']).replace('정부가 ','정부가<br>',1)}</h1><p class="lede">{e(t['lede']).replace('모았습니다. ','모았습니다.<br>',1)}</p>
<div class="cta"><a class="btn pri" href="#map">{e(t['cta_map'])}</a><button class="btn ghost" data-act="join">{e(t['cta_join'])}</button></div>
<p class="byline"><img src="/assets/emblem.png" alt="" width="24" height="24">WORLD MAKING MEMBERS × GCSME</p></div>
<a class="hradar" href="#map" aria-label="GOV RADAR"><span class="hp"></span><span class="hp p2"></span><img src="/assets/govradar-logo.webp" alt="GOV RADAR" width="640" height="709"><span class="hsw"></span><span class="hbl b1"></span><span class="hbl b2"></span><span class="hbl b3"></span><span class="hbl b4"></span>{"".join(f'<span class="htg t{i+1}">{x}</span>' for i, x in enumerate((["🇻🇳 정부 사업", "🇰🇪 입찰 마감 D-7", "🇸🇦 ODA", "🌐 세계은행 공고"] if L=="ko" else ["🇻🇳 Programmes", "🇰🇪 Tender D-7", "🇸🇦 Aid projects", "🌐 World Bank"])))}</a>
<div class="kpis"><div><b>{n_done}<small>/193</small></b><span>{e(t['k_done'])}</span></div><div><b>{n_t}</b><span>{e(t['k_tend'])}</span></div><div><b>{n_b}</b><span>{e(t['k_biz'])}</span></div><div><b>{e(last[5:].replace('-','/') or '—')}</b><span>{e(t['k_last'])}</span></div></div>
</div></section>
{P3.edge_html(L)}<section class="band segband"><div class="in"><h2>{"이런 분들이 여기서 사업을 만듭니다" if L=="ko" else "Who does business here"}</h2>{P3.segments_html(L, L=="ko")}<p class="cta"><a class="btn pri" href="/{L}/solutions/">{"분야별로 무엇을 얻는지 보기" if L=="ko" else "See what each sector offers"}</a> <a class="btn" href="/{L}/individuals/">{"개인으로 참여하기" if L=="ko" else "Join as an individual"}</a> <a class="btn" href="/{L}/pricing/">{"주문·요금" if L=="ko" else "Orders & pricing"}</a></p></div></section>
<section class="band" id="hqnotice"><div class="in"><h2>{"본사 프로젝트 공지 — WMM · GCSME KOREA · GCSME 영국 본사" if L=="ko" else "Headquarters notices — WMM · GCSME KOREA · GCSME UK"}</h2><div class="ntcs">{P3.LTR(L, P3.notice_items(L, C3(), 3))}</div><p class="cta"><a class="btn" href="/{L}/notices/">{"공지 전체 보기" if L=="ko" else "All notices"}</a></p></div></section>
<section class="band" id="world-now"><div class="in">{liveboard(L, "home")}<p class="cta"><a class="btn" href="/{L}/conflict/">{"전쟁·분쟁·재해 상황판 전체 보기" if L=="ko" else "Open the full situation board"}</a></p></div></section>
<section class="band alt" id="deadlines"><div class="in"><h2>{"마감이 다가오는 입찰" if L=="ko" else "Tenders closing soon"}</h2><p class="note">{"원문 공고 기준 · 분야별로 보려면 입찰·마감 보드로" if L=="ko" else "Dates from the original notices · filter by field on the tender board"}</p>{P3.deadline_board(L, C3(), limit=8, home=True)}<p class="cta"><a class="btn pri" href="/{L}/mdb/#deadlines">{"입찰·마감 보드 전체 보기" if L=="ko" else "Open the full tender board"}</a> <button class="btn" data-auth="signup">{e(t['cta_join'])}</button></p></div></section>
<section class="band" id="map"><div class="in"><h2>{e(t['map_h'])}</h2>
<div class="mapbox"><div id="wmap" data-lang="{L}"></div></div>
<div class="filters"><input id="q" type="search" placeholder="{e(t['search'])}" aria-label="{e(t['search'])}"><button class="chip on" data-r="ALL">{e(t['all'])}</button>{regions}</div>
<div class="grid" id="grid">{grid}</div></div></section>
<section class="band alt" id="board"><div class="in"><h2>{e(t['board_h'])}</h2><p class="note">{e(t['board_p'])}</p><div class="board">{board}</div></div></section>
{hotband(L)}
<section class="band" id="events"><div class="in"><h2>{e(t['ev_h'])}</h2><div class="evs">{evh}</div></div></section>
<section class="band" id="autoreg"><div class="in"><h2>{e(tx(L,'rg_h'))}</h2><p class="note">{e(tx(L,'rg_p'))}</p>
<div class="grid rgrid">{"".join(f'<a class="flag {"done" if done(x["iso"]) else ""}" href="{url(L,x["iso"])}">{flag(x["iso"])}<span>{e(nm(x["iso"],L))}<small>{e(nm(x["parent"],L))} · {e(tx(L,"rgt")[x["type"]])}</small></span></a>' for x in REGS)}</div></div></section>
{earth_section(L)}{foresight_section(L)}
<section class="band ordband" id="plans"><div class="in"><h2>{"정보는 무료, 분석은 주문하세요" if L=="ko" else "Data is free. Order the analysis."}</h2>
<p class="lede" {"dir=ltr" if L=="ar" else ""}>{"분석 회원(월 19,800원), 국가 진출 브리프, 입찰 적합도 검토를 견적·계좌이체로 받습니다(자동갱신 없음). 프로젝트 파트너십은 첫 상담이 무료입니다." if L=="ko" else "Analysis membership (₩19,800/mo), market-entry briefs and tender fit reviews, by quote and bank transfer (no auto-renewal). The first project-partnership consultation is free."}</p>
<p class="cta"><a class="btn pri" href="/{L}/pricing/">{"주문·요금 보기" if L=="ko" else "See orders & pricing"}</a> <a class="btn" href="/{L}/consortium/">{"대학·기관 컨소시엄" if L=="ko" else "University & institution consortium"}</a></p>
{P3.credit([s_[0] for s_ in P3.SEG], L=="ko")}</div></section>
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
        dsc = x.get("detail") or (f"{t['deadline']} {x.get('deadline')}" if x.get("deadline") else "")
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
<h1>{e(t['member_area'])}</h1>
<div id="acct-out"><p class="note">{e(t['members_only'])}</p><p><button class="btn pri" data-auth="login">{e(AT[L]['login'])}</button> <button class="btn" data-auth="signup">{e(AT[L]['signup'])}</button></p></div>
<div id="acct-in" hidden><p><b id="acct-st"></b> · <span class="lv watch" id="acct-tier"></span> <button class="btn sm" id="acct-logout" type="button">{e(t['logout'])}</button></p>
<p class="note">{lab('등급 변경·결제는 73036396@naver.com 으로 문의하세요. 등급은 다음 로그인 때 반영됩니다.','To change plan or pay, contact 73036396@naver.com. Plan changes apply at your next sign-in.')}</p>
<h3>{lab('내 입찰 관심 목록','My watchlist')}</h3><ul id="acct-watch"></ul></div>
<form id="acct" hidden>
<label>{lab('회사명','Company')}<input name="company"></label>
<fieldset><legend>{lab('관심 분야 (알림 기준)','Industries (for alerts)')}</legend><div class="chks">{inds}</div></fieldset>
<div class="two"><label>{lab('연 매출 (억 원)','Revenue (KRW 100M)')}<input name="revenue_100m" type="number" min="0"></label><label>{lab('업력 (년)','Years in business')}<input name="years" type="number" min="0"></label></div>
<div class="two"><label>{lab('해외·공공 실적 (건)','Public / overseas projects')}<input name="projects" type="number" min="0"></label><label>{lab('직원 수','Employees')}<input name="employees" type="number" min="0"></label></div>
<label>{lab('보유 인증 (쉼표로)','Certifications (comma-separated)')}<input name="certs"></label>
<fieldset><legend>{lab('알림 받는 방법','Alert channels')}</legend>
<label class="chk"><input type="checkbox" name="alert_email" checked> {lab('이메일 (새 기회·마감 D-7/D-3)','Email (new opportunities, D-7/D-3 deadlines)')}</label>
<p class="note">{lab('유료 회원은 매주 월요일 관심 나라 요약과 마감 임박 입찰을 이메일로 받습니다. 카카오톡·Slack 알림은 준비 중입니다.','Paid members get a Monday email with their countries and tenders closing soon. KakaoTalk and Slack alerts are coming later.')}</p>
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
    for f in ("wmm-logo-white.png", "wmm-logo.png", "gcsme-logo.jpg", "emblem.png", "og.jpg", "spot.jpg", "paper.jpg", "logo-h.webp", "logo-h-lg.webp", "logo-v.webp", "mark.png"): shutil.copy(os.path.join(SRC, f), OUT + "/assets/" + f)
    for f in glob.glob(os.path.join(ROOT, "web", "*")): shutil.copy(f, OUT + "/assets/")
    os.makedirs(OUT + "/embed/gateway", exist_ok=True); shutil.copy(os.path.join(SRC, "gateway.html"), OUT + "/embed/gateway/index.html")
    os.makedirs(OUT + "/assets/fonts", exist_ok=True)
    for fn in ("NEXON Lv1 Gothic OTF Light", "NEXON Lv1 Gothic OTF", "NEXON Lv1 Gothic OTF Bold"):
        dst = OUT + "/assets/fonts/" + fn.replace(" ", "") + ".woff"; loc = os.path.join(SRC, "fonts", fn.replace(" ", "") + ".woff")
        if os.path.exists(loc): shutil.copy(loc, dst); continue
        try:
            import urllib.request, urllib.parse
            urllib.request.urlretrieve("https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_20-04@2.1/" + urllib.parse.quote(fn) + ".woff", dst)
        except Exception as ex: print("font download skipped (CDN fallback used):", fn, ex)
    W = lambda p, s: (os.makedirs(os.path.dirname(OUT + p), exist_ok=True), open(OUT + p, "w", encoding="utf8").write(s))
    urls = []
    for L in LANGS:
        W(f"/{L}/index.html", home(L)); urls.append((f"/{L}/", {l: f"/{l}/" for l in LANGS}))
        W(f"/{L}/mdb/index.html", mdb_page(L)); urls.append((f"/{L}/mdb/", {l: f"/{l}/mdb/" for l in LANGS}))
        W(f"/{L}/conflict/index.html", conflict_page(L)); urls.append((f"/{L}/conflict/", {l: f"/{l}/conflict/" for l in LANGS}))
        W(f"/{L}/verify/index.html", verify_page(L));
        for _k in P2.LEGAL_ORDER:
            W(f"/{L}/legal/{_k}/index.html", P2.legal_page(L, _k, head, foot, e, LANGS)); urls.append((f"/{L}/legal/{_k}/", {l: f"/{l}/legal/{_k}/" for l in LANGS}))
        W(f"/{L}/consortium/index.html", P2.consortium_page(L, head, foot, e, LANGS)); urls.append((f"/{L}/consortium/", {l: f"/{l}/consortium/" for l in LANGS}))
        W(f"/{L}/consortium/thanks/index.html", P2.thanks_page(L, head, foot, e, LANGS))
        W(f"/{L}/thanks/index.html", P3.thanks2_page(L, C3()))
        W(f"/{L}/member/index.html", P3.member_page(L, C3()))
        W(f"/{L}/how/index.html", P3.how_page(L, C3())); urls.append((f"/{L}/how/", {l: f"/{l}/how/" for l in LANGS}))
        W(f"/{L}/sample/index.html", P3.sample_page(L, C3())); urls.append((f"/{L}/sample/", {l: f"/{l}/sample/" for l in LANGS}))
        W(f"/{L}/unlock/index.html", P3.unlock_page(L, C3())); urls.append((f"/{L}/unlock/", {l: f"/{l}/unlock/" for l in LANGS}))
        W(f"/{L}/gcsme/index.html", P3.gcsme_page(L, C3())); urls.append((f"/{L}/gcsme/", {l: f"/{l}/gcsme/" for l in LANGS}))
        W(f"/{L}/partners/index.html", P3.partners_page(L, C3())); urls.append((f"/{L}/partners/", {l: f"/{l}/partners/" for l in LANGS}))
        W(f"/{L}/individuals/index.html", P3.individuals_page(L, C3())); urls.append((f"/{L}/individuals/", {l: f"/{l}/individuals/" for l in LANGS}))
        W(f"/{L}/notices/index.html", P3.notices_page(L, C3())); urls.append((f"/{L}/notices/", {l: f"/{l}/notices/" for l in LANGS}))
        W(f"/{L}/solutions/index.html", P3.solutions_page(L, C3())); urls.append((f"/{L}/solutions/", {l: f"/{l}/solutions/" for l in LANGS}))
        W(f"/{L}/pricing/index.html", P3.pricing_page(L, C3(), PLANS, PLAN_NOTE)); urls.append((f"/{L}/pricing/", {l: f"/{l}/pricing/" for l in LANGS}))
        W(f"/{L}/projects/index.html", P2.projects_page(L, head, foot, e, LANGS, flag, vbh)); urls.append((f"/{L}/projects/", {l: f"/{l}/projects/" for l in LANGS}))
        W(f"/{L}/experts/index.html", P2.experts_page(L, head, foot, e, LANGS)); urls.append((f"/{L}/experts/", {l: f"/{l}/experts/" for l in LANGS}))
        # ON HOLD (2026-10-31): talent-demand page kept in pages2.talent_page; re-enable when the owner says so
        # W(f"/{L}/talent/index.html", P2.talent_page(L, head, foot, e, LANGS)); urls.append((f"/{L}/talent/", {l: f"/{l}/talent/" for l in LANGS}))
        W(f"/{L}/contracts/index.html", P2.contracts_page(L, head, foot, e, LANGS)); urls.append((f"/{L}/contracts/", {l: f"/{l}/contracts/" for l in LANGS}))
        urls.append((f"/{L}/verify/", {l: f"/{l}/verify/" for l in LANGS}))
        for _g in GUIDES:
            if _g in BY:
                W(f"/{L}/{BY[_g]['slug']}/guide/index.html", guide_page(_g, L)); urls.append((f"{url(L,_g)}guide/", {l: f"{url(l,_g)}guide/" for l in LANGS}))
        W(f"/{L}/about/index.html", about_page(L)); urls.append((f"/{L}/about/", {l: f"/{l}/about/" for l in LANGS}))
        W(f"/{L}/prepare/index.html", stock_page(L)); urls.append((f"/{L}/prepare/", {l: f"/{l}/prepare/" for l in LANGS}))
        W(f"/{L}/feeds/index.html", feeds_page(L)); W(f"/{L}/embed/index.html", embed_page(L)); W(f"/{L}/account/index.html", account_page(L))
        for c in META:
            W(f"/{L}/{c['slug']}/index.html", country_page(c["iso"], L))
            urls.append((url(L, c["iso"]), {l: url(l, c["iso"]) for l in LANGS}))
        for x in REGS:
            W(f"/{L}/{BY[x['iso']]['slug']}/index.html", country_page(x["iso"], L))
            urls.append((url(L, x["iso"]), {l: url(l, x["iso"]) for l in LANGS}))
    for L in ("ko", "en"):
        W(f"/feeds/{L}/all.xml", rss(L))
        for k in INDUSTRIES: W(f"/feeds/{L}/{k}.xml", rss(L, k))
    # data for map, search, widget
    cj = [{"iso": c["iso"], "slug": c["slug"], "r": c["r"], "done": done(c["iso"]), "risk": lvl(c["iso"]), "names": NAMES[c["iso"]]} for c in META]
    W("/data/countries.json", json.dumps(cj, ensure_ascii=False))
    W("/data/regions.json", json.dumps([{"code": x["iso"], "parent": x["parent"], "type": x["type"], "slug": BY[x["iso"]]["slug"], "done": done(x["iso"]), "ko": x["ko"], "en": x["en"]} for x in REGS], ensure_ascii=False))
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
                oi.append({"iso": iso, "slug": BY[iso]["slug"], "kind": kind, "ko": x.get("title"), "en": xe.get("title") or x.get("title"), "deadline": x.get("deadline", ""), "ind": ind, "names": NAMES[iso], "u": d.get("updated", "")})
    oi.sort(key=lambda x: x["u"], reverse=True)
    W("/data/opps.json", json.dumps({"updated": TODAY, "items": oi}, ensure_ascii=False))
    for iso, d in DATA.items():
        if done(iso):
            def _strip(o):
                if isinstance(o, dict): return {k: _strip(v) for k, v in o.items() if k not in ("why", "target", "basis", "fit", "history", "guide")}
                if isinstance(o, list): return [_strip(v) for v in o]
                return o
            c = _strip(d)
            W(f"/data/c/{iso}.json", json.dumps({"iso": iso, "name": BY[iso]["en"], **c}, ensure_ascii=False))
    # member-only analysis (why-now, target buyers, basis) -> private/m/<L>/<ISO>.json, encrypted later by tools/member.py
    _pm = os.path.join(ROOT, "private", "m")
    for _L in LANGS:
        os.makedirs(os.path.join(_pm, _L), exist_ok=True)
        for iso, d in DATA.items():
            if not done(iso): continue
            _b = [x if isinstance(x, dict) else {"title": x} for x in (G(d, "biz", _L) or [])]
            _o = {"iso": iso, "biz": [{k: x.get(k) for k in ("title", "why", "target", "basis") if x.get(k)} for x in _b]}
            if any(len(x) > 1 for x in _o["biz"]):
                with open(os.path.join(_pm, _L, iso + ".json"), "w", encoding="utf8") as _f: json.dump(_o, _f, ensure_ascii=False)
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
        iso = next((k for k, c in BY.items() if p.endswith("/" + c["slug"] + "/")), None)
        lm = (DATA.get(iso) or {}).get("updated", TODAY) if iso else TODAY
        sm.append(f"<url><loc>{BASE}{p}</loc><lastmod>{lm}</lastmod>" + "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{BASE}{a}"/>' for l, a in alts.items()) + "</url>")
    sm.append("</urlset>"); W("/sitemap.xml", "".join(sm))
    W("/_redirects", "".join(f"/{p}  /ko/{p}/  301\n/{p}/  /ko/{p}/  301\n" for p in ["about","conflict","verify","prepare","mdb","feeds","embed","account","consortium","projects","contracts","experts","solutions","pricing","notices","individuals","unlock","gcsme","partners"]))
    try:
        from PIL import Image
        im = Image.open(os.path.join(OUT, "assets", "mark.png")).convert("RGBA"); im.save(os.path.join(OUT, "favicon.ico"), sizes=[(16,16),(32,32),(48,48)])
    except Exception as ex: print("favicon skipped", ex)
    W("/robots.txt", f"User-agent: *\nAllow: /\nDisallow: /widget/\n\nSitemap: {BASE}/sitemap.xml\n")
    llms = [f"# GOV RADAR (WMM × GCSME)", "", f"> {T['en']['desc_home']}", "", "Publisher: WORLD MAKING MEMBERS Co., Ltd. (Seoul) with Global & Commonwealth SME Club (London). Contact 73036396@naver.com", "", "## Countries (English)"]
    llms += [f"- [{c['en']}]({BASE}{url('en', c['iso'])}): {((DATA.get(c['iso']) or {}).get('en') or {}).get('summary', '')[:160]}" for c in META if done(c["iso"])]
    llms += ["", "## Autonomous & special regions"] + [f"- [{x['en']}]({BASE}{url('en', x['iso'])}) — {BY[x['parent']]['en']}: {((DATA.get(x['iso']) or {}).get('en') or {}).get('summary', '')[:160]}" for x in REGS]
    llms += ["", "## 국가 (한국어)"] + [f"- [{c['ko']}]({BASE}{url('ko', c['iso'])})" for c in META if done(c["iso"])]
    W("/llms.txt", "\n".join(llms) + "\n")
    W("/_headers", "/assets/*\n  Cache-Control: public, max-age=604800\n/data/*\n  Cache-Control: public, max-age=3600\n  X-Robots-Tag: noindex\n/widget/*\n  Content-Security-Policy: frame-ancestors *\n/embed/*\n  Content-Security-Policy: frame-ancestors *\n/*\n  X-Content-Type-Options: nosniff\n")
    # UI strings for es/fr/ar/vi/id: exact text-node replacement from English (src/i18n_ui/<L>_*.json)
    import html as _h
    for _L in ("es", "fr", "ar", "vi", "id"):
        mp = {}
        for f in sorted(glob.glob(os.path.join(SRC, "i18n_ui", _L + "_u*.json"))):
            try: mp.update({k: v for k, v in json.load(open(f, encoding="utf8")).items() if isinstance(v, str) and v.strip()})
            except Exception: pass
        if not mp: continue
        def _tn(m):
            raw = m.group(1); s = _h.unescape(raw).strip()
            v = mp.get(s)
            if not v: return m.group(0)
            lead = raw[:len(raw) - len(raw.lstrip())]; tail = raw[len(raw.rstrip()):]
            return ">" + lead + _h.escape(v, quote=False) + tail + "<"
        def _at(m):
            s = _h.unescape(m.group(2)).strip(); v = mp.get(s)
            return f'{m.group(1)}="{_h.escape(v)}"' if v else m.group(0)
        for dp, _, fs in os.walk(os.path.join(OUT, _L)):
            for fn in fs:
                if not fn.endswith(".html"): continue
                fp = os.path.join(dp, fn); h = open(fp, encoding="utf-8").read()
                parts = re.split(r"(<script\b.*?</script>|<style\b.*?</style>)", h, flags=re.S)
                for i in range(0, len(parts), 2):
                    parts[i] = re.sub(r">([^<>]+)<", _tn, parts[i])
                    parts[i] = re.sub(r'\b(placeholder|aria-label|title)="([^"]+)"', _at, parts[i])
                h2 = "".join(parts)
                if h2 != h: open(fp, "w", encoding="utf-8").write(h2)
    # cache-busting: /assets/* is cached 7 days, so stamp CSS/JS links with a content hash
    import hashlib
    ver = {}
    for f in ["site.css", "site.js", "hotmap.js", "auth.js", "config.js"]:
        fp = os.path.join(OUT, "assets", f)
        if os.path.exists(fp): ver[f] = hashlib.md5(open(fp, "rb").read()).hexdigest()[:8]
    for dp, _, fs in os.walk(OUT):
        for fn in fs:
            if not fn.endswith(".html"): continue
            fp = os.path.join(dp, fn); h = open(fp, encoding="utf-8").read(); h2 = h
            for f, v in ver.items(): h2 = h2.replace(f'/assets/{f}"', f'/assets/{f}?v={v}"')
            if h2 != h: open(fp, "w", encoding="utf-8").write(h2)
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"built {n} files · {sum(done(i) for i in BY if not is_reg(i))} researched countries · {sum(done(x["iso"]) for x in REGS)} regions · {len(oi)} opportunities · base {BASE}")

if __name__ == "__main__": build()
