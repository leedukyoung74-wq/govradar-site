# Second menu bar (always directly under the top bar) + shared header for the stand-alone pages (/hazards/, /signals/).
import json, html as _h

def _e(s): return _h.escape(str(s), quote=True)

LBL = {
 "map":       {"ko":"세계 지도","en":"World map","es":"Mapa mundial","fr":"Carte du monde","ar":"خريطة العالم","vi":"Bản đồ thế giới","id":"Peta dunia"},
 "list":      {"ko":"전체 국가","en":"All countries","es":"Todos los países","fr":"Tous les pays","ar":"كل الدول","vi":"Tất cả quốc gia","id":"Semua negara"},
 "mdb":       {"ko":"입찰·사업","en":"Tenders","es":"Licitaciones","fr":"Appels d'offres","ar":"المناقصات","vi":"Đấu thầu","id":"Tender"},
 "projects":  {"ko":"프로젝트 랩","en":"Project lab","es":"Laboratorio de proyectos","fr":"Labo projets","ar":"مختبر المشاريع","vi":"Phòng dự án","id":"Lab proyek"},
 "consortium":{"ko":"컨소시엄","en":"Consortium","es":"Consorcio","fr":"Consortium","ar":"الاتحاد","vi":"Liên danh","id":"Konsorsium"},
 "experts":   {"ko":"전문가 참여","en":"Experts","es":"Expertos","fr":"Experts","ar":"الخبراء","vi":"Chuyên gia","id":"Pakar"},
 "partners":  {"ko":"협력 참여","en":"Partners","es":"Socios","fr":"Partenaires","ar":"الشركاء","vi":"Đối tác","id":"Mitra"},
 "notices":   {"ko":"공지","en":"Notices","es":"Avisos","fr":"Annonces","ar":"إعلانات","vi":"Thông báo","id":"Pengumuman"},
 "solutions": {"ko":"진출 지원","en":"Go global","es":"Expansión","fr":"S'implanter","ar":"التوسع","vi":"Mở rộng","id":"Ekspansi"},
 "gcsme":     {"ko":"GCSME","en":"GCSME","es":"GCSME","fr":"GCSME","ar":"GCSME","vi":"GCSME","id":"GCSME"},
 "request":   {"ko":"분석 의뢰","en":"Request analysis","es":"Solicitar análisis","fr":"Demander une analyse","ar":"طلب تحليل","vi":"Yêu cầu phân tích","id":"Minta analisis"},
 "sample":    {"ko":"결과물 샘플","en":"Samples","es":"Ejemplos","fr":"Exemples","ar":"نماذج","vi":"Mẫu","id":"Contoh"},
 "contracts": {"ko":"계약서","en":"Contracts","es":"Contratos","fr":"Contrats","ar":"العقود","vi":"Hợp đồng","id":"Kontrak"},
 "conflict":  {"ko":"세계 상황","en":"World watch","es":"Situación mundial","fr":"Veille mondiale","ar":"الوضع العالمي","vi":"Tình hình thế giới","id":"Situasi dunia"},
 "hazards":   {"ko":"재난 지도","en":"Hazard map","es":"Mapa de riesgos","fr":"Carte des risques","ar":"خريطة المخاطر","vi":"Bản đồ hiểm họa","id":"Peta bahaya"},
 "ready":     {"ko":"재난 대비","en":"Preparedness","es":"Preparación","fr":"Préparation","ar":"الاستعداد","vi":"Phòng bị","id":"Kesiapsiagaan"},
 "prepare":   {"ko":"비축 키트","en":"Stockpile kit","es":"Kit de reservas","fr":"Kit de réserves","ar":"حقيبة الطوارئ","vi":"Bộ dự trữ","id":"Kit persediaan"},
 "signals":   {"ko":"표지·풍자","en":"","es":"","fr":"","ar":"","vi":"","id":""},
 "pricing":   {"ko":"요금·회원","en":"Pricing","es":"Precios","fr":"Tarifs","ar":"الأسعار","vi":"Bảng giá","id":"Harga"},
 "member":    {"ko":"회원 자료","en":"Member area","es":"Área de socios","fr":"Espace membre","ar":"منطقة الأعضاء","vi":"Khu thành viên","id":"Area anggota"},
 "account":   {"ko":"내 계정","en":"My account","es":"Mi cuenta","fr":"Mon compte","ar":"حسابي","vi":"Tài khoản","id":"Akun saya"},
 "about":     {"ko":"회사 소개","en":"About","es":"Acerca de","fr":"À propos","ar":"من نحن","vi":"Giới thiệu","id":"Tentang"},
 "legal":     {"ko":"약관·정책","en":"Terms & policy","es":"Términos","fr":"Conditions","ar":"الشروط","vi":"Điều khoản","id":"Ketentuan"},
}
GROUPS = {
 "map":    ["map", "list", "sample", "request", "notices"],
 "biz":    ["mdb", "projects", "consortium", "experts", "partners", "notices"],
 "go":     ["solutions", "gcsme", "request", "sample", "contracts"],
 "world":  ["conflict", "hazards", "ready", "prepare", "signals"],
 "member": ["pricing", "member", "account", "request", "about", "legal"],
}
SEG2G = {"mdb":"biz","projects":"biz","consortium":"biz","experts":"biz","partners":"biz","notices":"biz",
         "solutions":"go","gcsme":"go","request":"go","sample":"go","contracts":"go",
         "conflict":"world","ready":"world","prepare":"world",
         "pricing":"member","member":"member","account":"member","about":"member","legal":"member"}

def href(L, k):
    if k == "map": return f"/{L}/#map"
    if k == "list": return f"/{L}/#gwrap"
    if k == "hazards": return "/hazards/" if L == "ko" else f"/hazards/?l={L}"
    if k == "signals": return "/signals/"
    if k == "legal": return f"/{L}/legal/terms/"
    return f"/{L}/{k}/"

def items(L, g):
    return [(k, href(L, k), LBL[k][L]) for k in GROUPS[g] if LBL[k].get(L)]

def group_of(path):
    seg = (path.strip("/").split("/") + ["", ""])[1]
    return SEG2G.get(seg, "map"), seg

def subnav(L, path, group=None, active=None):
    g, seg = group_of(path)
    g = group or g; act = active or (seg if seg in LBL else ("map" if g == "map" else ""))
    a = "".join(f'<a href="{_e(h)}"{" aria-current=\"page\"" if k == act else ""}>{_e(t)}</a>' for k, h, t in items(L, g))
    return f'<nav class="subnav" aria-label="sub"><div class="in">{a}</div></nav>'

def gvhdr_js(NAV, LANG_NAME, LANG_SHORT, AT, MENU):
    data = {"nav": {}, "sub": {}, "lang": LANG_NAME, "short": LANG_SHORT,
            "login": {L: AT[L]["login"] for L in LANG_NAME}, "menu": MENU}
    for L in LANG_NAME:
        data["nav"][L] = [[("/hazards/" if L == "ko" else f"/hazards/?l={L}") if p == "@hazards" else "/signals/" if p == "@signals" else f"/{L}/{p}", lbl, p] for p, lbl in NAV[L]]
        data["sub"][L] = {g: [[k, h, t] for k, h, t in items(L, g)] for g in GROUPS}
    css = r"""
.gvh,.gvh *{box-sizing:border-box}
.gvh{--gb:#F5F5F2;--gp:#fff;--gi:#0B0B0B;--gm:#5C5C5A;--gl:#D7D7D3;position:sticky;top:0;z-index:60;font:400 15px/1.5 "WMM Nexon","NEXON Lv1 Gothic OTF","Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:var(--gi)}
@media (prefers-color-scheme:dark){.gvh{--gb:#0A0A0A;--gp:#141414;--gi:#F2F2EF;--gm:#9A9A96;--gl:#2B2B2A}}
.gvh .gin{max-width:1200px;margin:0 auto;padding:0 max(16px,env(safe-area-inset-left))}
.gvh .gtop{background:var(--gb);border-bottom:1px solid var(--gl)}
.gvh .gtop .gin{display:flex;align-items:center;gap:14px;height:60px}
.gvh .gbrand{flex:0 0 auto;display:flex}.gvh .gbrand img{height:40px;width:120px;object-fit:contain;display:block}
.gvh .glinks{flex:1 1 auto;display:flex;justify-content:center;min-width:0}
.gvh .glinks a{white-space:nowrap;font-size:14px;padding:8px 11px;color:var(--gm);text-decoration:none;border-radius:6px}
.gvh .glinks a:hover,.gvh .glinks a[aria-current]{color:var(--gi);background:color-mix(in srgb,var(--gi) 7%,transparent)}
.gvh .gr{display:flex;align-items:center;gap:8px;flex:0 0 auto}
.gvh select{font:inherit;font-size:13px;padding:6px 8px;border:1px solid var(--gl);border-radius:6px;background:var(--gp);color:var(--gi);max-width:132px}
.gvh .glog{display:inline-flex;align-items:center;border:1px solid var(--gi);background:var(--gp);color:var(--gi);border-radius:8px;padding:6px 12px;font-family:inherit;font-weight:700;font-size:13px;text-decoration:none;white-space:nowrap}
.gvh .gbur{display:none;width:40px;height:40px;border:1px solid var(--gl);border-radius:8px;background:var(--gp);padding:10px 9px;flex-direction:column;justify-content:space-between;cursor:pointer}
.gvh .gbur span{display:block;height:2px;background:var(--gi);border-radius:2px}
.gvh .subnav{background:#0b0b0b;border-bottom:1px solid #2a2a28}
@media (max-width:1080px){.gvh .glinks a{padding:8px 7px;font-size:13.5px}}
@media (max-width:920px){.gvh .glinks{display:none;position:fixed;top:60px;left:0;right:0;flex-direction:column;background:var(--gb);border-bottom:1px solid var(--gl);padding:8px 16px 16px;box-shadow:0 18px 30px rgba(0,0,0,.18)}
 .gvh .glinks.open{display:flex}.gvh .glinks a{font-size:16px;padding:13px 6px;border-bottom:1px solid var(--gl);border-radius:0;color:var(--gi)}
 .gvh .gbur{display:flex}.gvh select{max-width:96px}.gvh .gr{margin-left:auto}}
"""
    js = r"""(function(){var D=__DATA__;
var s=document.currentScript,L=s.getAttribute("data-l")||"ko";if(L==="auto")L=new URLSearchParams(location.search).get("l")||"ko";var G=s.getAttribute("data-g")||"world",A=s.getAttribute("data-a")||"";
if(!D.nav[L])L="en";
function e(t){return String(t).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
var st=document.createElement("style");st.textContent=__CSS__+__SUBCSS__;document.head.appendChild(st);
var nav=D.nav[L].map(function(x){var cur=(A==="hazards"&&x[2]==="@hazards")||(A==="signals"&&x[2]==="@signals")||(G==="world"&&x[2]==="conflict/"&&!A);return'<a href="'+e(x[0])+'"'+(cur?' aria-current="page"':'')+'>'+e(x[1])+'</a>'}).join("");
var CS=window.GVH_SUB?window.GVH_SUB(L):null;var sub=CS?CS.map(function(x){return'<a href="'+e(x[0])+'">'+e(x[1])+'</a>'}).join(""):(D.sub[L][G]||[]).map(function(x){return'<a href="'+e(x[1])+'"'+(x[0]===A?' aria-current="page"':'')+'>'+e(x[2])+'</a>'}).join("");
var opts=Object.keys(D.lang).map(function(l){return'<option value="'+l+'"'+(l===L?' selected':'')+'>'+e(D.lang[l])+'</option>'}).join("");
var h='<div class="gvh" id="gvh"><div class="gtop"><div class="gin"><a class="gbrand" href="/'+L+'/"><img src="/assets/logo-h.webp" alt="GOV RADAR" width="120" height="40"></a><nav class="glinks" id="gvhl">'+nav+'</nav><div class="gr"><select aria-label="Language" id="gvhs">'+opts+'</select><a class="glog" href="/'+L+'/account/">'+e(D.login[L])+'</a><button class="gbur" id="gvhb" aria-label="'+e(D.menu[L])+'" aria-expanded="false"><span></span><span></span><span></span></button></div></div></div><nav class="subnav'+(CS?' toc':'')+'"><div class="in">'+sub+'</div></nav></div>';
document.write(h);
document.getElementById("gvhs").onchange=function(){var l=this.value,u=window.GVH_LANG_URL?window.GVH_LANG_URL(l):("/"+l+"/");location.href=u};
var b=document.getElementById("gvhb"),n=document.getElementById("gvhl");b.onclick=function(){var o=n.classList.toggle("open");b.setAttribute("aria-expanded",o)};
})();
__SPY__"""
    return js.replace("__SPY__", SPYJS).replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__CSS__", json.dumps(css)).replace("__SUBCSS__", json.dumps(SUBCSS))

SPYJS = '(function(){function spy(){var n=document.querySelector(".subnav.toc");if(!n)return;var box=n.querySelector(".in")||n,A=[].slice.call(n.querySelectorAll(\'a[href^="#"]\'));if(!A.length)return;\nvar S=A.map(function(a){return document.getElementById(decodeURIComponent(a.getAttribute("href").slice(1)))}),cur=-1,lock=0,vis={};\nfunction mark(k){if(k===cur)return;cur=k;A.forEach(function(a,i){if(i===k)a.setAttribute("aria-current","true");else a.removeAttribute("aria-current")});var a=A[k];if(a){var l=a.offsetLeft-(box.clientWidth-a.offsetWidth)/2;box.scrollTo({left:Math.max(0,l),behavior:"smooth"})}}\nA.forEach(function(a,i){a.addEventListener("click",function(ev){var s=S[i];if(!s||s.offsetParent===null)return;ev.preventDefault();lock=Date.now()+900;mark(i);var y=s.getBoundingClientRect().top+scrollY-118;scrollTo({top:y,behavior:"smooth"});try{history.replaceState(null,"",a.getAttribute("href"))}catch(e){}})});\nif(!("IntersectionObserver" in window))return;var io=new IntersectionObserver(function(es){es.forEach(function(e){vis[S.indexOf(e.target)]=e.isIntersecting});if(Date.now()<lock)return;var k=-1;for(var i=0;i<S.length;i++)if(vis[i]){k=i;break}if(k<0){var y=scrollY+130;S.forEach(function(s,i){if(s&&s.getBoundingClientRect().top+scrollY<=y)k=i})}if(k>=0)mark(k)},{rootMargin:"-118px 0px -55% 0px"});S.forEach(function(s){if(s)io.observe(s)});}\nif(document.readyState==="loading")document.addEventListener("DOMContentLoaded",spy);else spy();})();'
SUBCSS = """.subnav{position:sticky;top:60px;z-index:19;background:#0b0b0b;border-bottom:1px solid #2a2a28}
.subnav .in{display:flex;gap:4px;height:44px;align-items:center;overflow-x:auto;scrollbar-width:none;max-width:1200px;margin:0 auto;padding:0 max(16px,env(safe-area-inset-left))}
.subnav .in::-webkit-scrollbar{display:none}
.subnav a{flex:0 0 auto;white-space:nowrap;color:#bdbdb8;text-decoration:none;font-size:13.5px;padding:7px 12px;border-radius:999px;font-family:"WMM Nexon","NEXON Lv1 Gothic OTF","Apple SD Gothic Neo","Malgun Gothic",sans-serif}
.subnav a:hover{color:#fff;background:#1c1c1a}
.subnav a[aria-current]{color:#0b0b0b;background:#E3CC96;font-weight:700}
.gvh .subnav{position:static}
"""

# ---- in-page table of contents as the second bar -------------------------------------------
import re as _re
SHORT = {
 "나라를 누르면 그 나라 정부의 모든 것이 열립니다": "세계 지도", "돈을 내기 전에, 받게 될 결과물을 먼저 보세요": "결과물 샘플",
 "AI에게 물어보는 것과 무엇이 다른가": "AI와 다른 점", "무엇을 어디까지 볼 수 있나": "이용 범위", "이런 분들이 여기서 사업을 만듭니다": "이용 고객",
 "재난·분쟁 16가지를 움직이는 지도로": "재난 16가지", "전시회·무역사절단 일정": "행사 일정", "마감이 다가오는 입찰": "마감 입찰",
 "지금 제안할 수 있는 사업": "제안할 사업", "마감일 순 열린 입찰": "열린 입찰", "지난 입찰과 여러 나라 반복 수요": "지난 입찰·반복 수요",
 "개발은행·국제기구": "개발은행·국제기구", "기관별 조달 포털": "조달 포털", "레이더에 잡힌 분야별 사업": "분야별 사업", "함께 일하는 방법": "함께 일하는 방법",
 "출처가 달린 상세 내용": "상세 내용", "국가별 대비 시나리오 (가정)": "대비 시나리오", "각국 대비 정책 — 사실 확인": "각국 대비 정책",
 "떠도는 주장 판정": "주장 판정", "무료·분석 회원·파트너십 비교": "회원 비교", "지금 주문할 수 있는 것": "주문 상품", "주문하면 이렇게 진행됩니다": "진행 순서",
}
def _short(t):
    t = _re.sub(r"<[^>]+>", "", t); t = _h.unescape(t).replace("⌛", "").strip()
    if t in SHORT: return SHORT[t]
    if t.endswith(" 한눈에 보기"): return "한눈에 보기"
    if t.lower().endswith(" at a glance"): return "At a glance"
    t = _re.sub(r"\s*\(\d+\)\s*$", "", t)
    for sep in (" — ", " – ", ": ", " · "):
        if sep in t and len(t) > 16: t = t.split(sep)[0]
    t = _re.sub(r"\s*\(.*?\)\s*$", "", t)
    return t if len(t) <= 22 else t[:21].rstrip() + "…"

def toc_post(html):
    """Replace the sibling sub bar with this page's own headings (2+), adding ids to h2 that lack one."""
    a = html.find("<!--SUBNAV-->"); b = html.find("<!--/SUBNAV-->")
    if a < 0 or b < 0: return html
    m0 = html.find("<main>"); body = html[m0:] if m0 >= 0 else ""
    rd = _re.search(r'<nav class="rd-nav"[^>]*><div class="rd-in">(.*?)</div></nav>', body, _re.S)
    links = []
    if rd:
        links = [(h_, _h.unescape(_re.sub("<[^>]+>", "", t))) for h_, t in _re.findall(r'<a href="(#[^"]+)">(.*?)</a>', rd.group(1))]
    else:
        n = [0]
        def addid(m):
            tag, inner = m.group(1), m.group(2)
            idm = _re.search(r'\bid="([^"]+)"', tag)
            if idm: hid = idm.group(1)
            else:
                n[0] += 1; hid = f"s{n[0]}"; tag = tag[:-1] + f' id="{hid}">'
            if "data-notoc" not in tag and _re.sub(r"<[^>]+>", "", inner).strip():
                links.append(("#" + hid, _short(inner)))
            return tag + inner + "</h2>"
        body2 = _re.sub(r"(<h2\b[^>]*>)(.*?)</h2>", addid, body, flags=_re.S)
        if len(links) >= 2: html = html[:m0] + body2
        a = html.find("<!--SUBNAV-->"); b = html.find("<!--/SUBNAV-->")
    if len(links) < 2:
        return html.replace("<!--SUBNAV-->", "").replace("<!--/SUBNAV-->", "")
    nav = '<nav class="subnav toc" aria-label="contents"><div class="in">' + "".join(f'<a href="{_e(h_)}">{_e(t)}</a>' for h_, t in links) + "</div></nav>"
    return html[:a] + nav + html[b + len("<!--/SUBNAV-->"):]
