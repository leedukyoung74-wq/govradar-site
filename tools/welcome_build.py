#!/usr/bin/env python3
"""Turn the approved design canvas (.dc.html, 2026-11-15) into static pre-login pages under cf/extra/welcome/."""
import os, re, sys
SRC = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "cf", "extra", "welcome")
BLOB = {"45932a1e60acb26b8cb9d8c7a1068147": "/assets/c-sa.webp", "15ae09a07df99accc2bc967cd32134bb": "/assets/c-gb.webp",
        "0a3185fdd5f37b36c854a56a70da6c08": "/assets/c-ae.webp", "53e96e672168b31f532f5eadb5e8d835": "/assets/c-us.webp",
        "203e628655021a3e6c4bf815b81be6f6": "/assets/c-cn.webp", "8433488bba6a583850d93ce69e7e10f1": "/assets/c-jp.webp",
        "13759d37370ccd938f13de2b171be411": "/assets/logo-h-lg.webp", "3ae1c2f4033713764c37d3d1e7fd3973": "/assets/govradar-logo.webp",
        "17772d73b0c95f41e132c5941f9f3447": "/assets/fonts/NEXONLv1GothicOTF.woff", "d2b930c84bc0c9be63dc299af3dfded0": "/assets/fonts/NEXONLv1GothicOTFBold.woff",
        "f29714949d5410921e1a04f19bc8eb7e": "/assets/fonts/NEXONLv1GothicOTFLight.woff"}
PAGES = {"Main": "", "About": "about/", "Services": "services/", "Country": "country/", "Membership": "membership/", "Login": "login/"}
DESC = {"Main": "193개국 정부의 정책·사업·입찰·위험 정보를 한 화면에서 읽고 한국 기업이 먼저 움직일 기회를 찾습니다.",
        "About": "GOV RADAR의 비전, 데이터 원칙, 연혁과 운영 주체.", "Services": "국가 정보, 입찰·사업, 세계 상황판, 재난 대비, CONNECT.",
        "Country": "GOV RADAR 국가 리포트 예시 — 사우디아라비아.", "Membership": "WMM 멤버십 M0–M5 등급과 요금, 고객센터.",
        "Login": "로그인하면 GOV RADAR 전체 화면으로 이동합니다."}
TABS_JS = """<script>(function(){var T=[['국가 정보','193개국 정부의 핵심 아젠다, 지도자, 예산, 정부 사업 폴더를 나라별로 정리합니다. 매주 갱신하고 바뀐 내용은 이력으로 남깁니다.'],['입찰·사업','각국 전자조달과 세계은행·ADB·AfDB·UNGM 공고 중 마감 전 입찰만 모읍니다. 자격 요건과 컨소시엄 가능 여부까지 함께 봅니다.'],['세계 상황판','전쟁·분쟁, 자연재해, 감염병을 USGS·GDACS·WHO 공식 자료로 매일 확인해 나라별 위험 수준을 보여 줍니다.'],['재난 대비','가정·회사가 무엇을 얼마나 비축할지 계산하고, 대피 계획과 비상 연락 카드를 만듭니다.'],['CONNECT','정부 사업과 기업, 기업과 기업을 잇습니다. 양쪽이 동의한 소개만 진행하며 성과를 보장하지 않습니다.']];
var box=document.getElementById('wtabs'),d=document.getElementById('wdesc');function sel(s){[].forEach.call(box.children,function(b,i){var on=i===s;b.setAttribute('aria-selected',on);b.style.background=on?'#0b1f3a':'#fff';b.style.color=on?'#fff':'#1a1d23';b.style.borderColor=on?'#0b1f3a':'#c9cdd3'});d.textContent=T[s][1]}
T.forEach(function(t,i){var b=document.createElement('button');b.type='button';b.setAttribute('role','tab');b.textContent=t[0];b.style.cssText='min-width:160px;min-height:44px;padding:0 22px;font:inherit;font-size:15px;cursor:pointer;border:1px solid #c9cdd3';b.onclick=function(){sel(i)};box.appendChild(b)});sel(0)})();</script>"""
LOGIN_JS = """<script>window.RADAR_LANG="ko";</script><script src="/assets/config.js"></script><script src="/assets/auth.js"></script>
<script>(function(){var f=document.getElementById('wlogin'),m=document.getElementById('wmsg');f.addEventListener('submit',function(e){e.preventDefault();if(!window.WMMAuth){m.textContent='잠시 후 다시 시도해 주세요.';return}m.textContent='확인 중…';
WMMAuth.login(f.email.value.trim(),f.password.value).then(function(){location.href='/ko/'}).catch(function(){m.textContent='이메일 또는 비밀번호를 확인해 주세요.'})})})();</script>"""
GATE = None
os.makedirs(OUT, exist_ok=True)
for name, sub in PAGES.items():
    s = open(os.path.join(SRC, name + ".dc.html"), encoding="utf-8").read()
    s = s.replace('<script src="./support.js"></script>', '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="%s"><link rel="icon" href="/assets/govradar-logo.webp"><link rel="canonical" href="https://radar.wmm-hoa.com/welcome/%s">' % (DESC[name], sub))
    s = re.sub(r'<script type="text/x-dc" data-dc-script.*?</script>\s*', "", s, flags=re.S)
    s = s.replace("<x-dc>", "").replace("</x-dc>", "").replace("<helmet>", "").replace("</helmet>", "")
    for k, v in BLOB.items(): s = s.replace("/_blob/" + k, v)
    for n, p in PAGES.items(): s = s.replace('href="%s.dc.html' % n, 'href="/welcome/%s' % p)
    s = s.replace('<a href="#" style="border: 1px solid rgba(255,255,255,.5); border-radius: 20px; padding: 3px 12px; font-size: 13px">KO</a>', '<a href="/en/" style="border: 1px solid rgba(255,255,255,.5); border-radius: 20px; padding: 3px 12px; font-size: 13px">EN</a>')
    s = s.replace('<a href="#" style="border: 1px solid rgba(255,255,255,.5); border-radius: 20px; padding: 3px 12px">KO</a>', '<a href="/en/" style="border: 1px solid rgba(255,255,255,.5); border-radius: 20px; padding: 3px 12px">EN</a>')
    s = s.replace('<a href="#" aria-label="검색"', '<a href="/ko/?stay=1#map" aria-label="나라 검색"')
    if name == "Main":
        s = re.sub(r'<div role="tablist" aria-label="서비스"([^>]*)>.*?</div>', r'<div role="tablist" aria-label="서비스" id="wtabs"\1></div>', s, count=1, flags=re.S)
        s = s.replace('min-height: 58px">{{desc}}</p>', 'min-height: 58px" id="wdesc"></p>')
        s = s.replace("</body>", TABS_JS + "</body>")
    if name == "Login":
        s = s.replace('<form style="flex: 1 1 420px;', '<form id="wlogin" style="flex: 1 1 420px;')
        s = s.replace('<input type="email" autocomplete="email"', '<input name="email" type="email" required autocomplete="email"')
        s = s.replace('<input type="password" autocomplete="current-password"', '<input name="password" type="password" required autocomplete="current-password"')
        s = s.replace('<button type="button" style="min-height: 52px;', '<button type="submit" style="min-height: 52px;')
        s = s.replace('<a href="#" style="color: #1e4fb8; font-weight: 700">무료 가입(M0)</a> · <a href="#" style="color: #4b515c">비밀번호 찾기</a></p>',
                      '<a href="/ko/?auth=signup" style="color: #1e4fb8; font-weight: 700">무료 가입(M0)</a> · <a href="/ko/?auth=reset" style="color: #4b515c">비밀번호 찾기</a></p><p id="wmsg" role="status" style="margin: 0; font-size: 14px; color: #b3261e"></p>')
        s = s.replace("</body>", LOGIN_JS + "</body>")
    if name == "Membership":
        s = re.sub(r'<form style="flex: 1 1 320px;.*?</form>', '<div style="flex: 1 1 320px; min-width: 0; background: #ffffff; padding: 30px; display: flex; flex-direction: column; gap: 14px"><h3 style="margin: 0; font-size: 20px">문의하기</h3><p style="margin: 0; font-size: 15px; line-height: 1.8; color: #4b515c">회사명과 궁금한 점을 메일로 보내 주세요. 1영업일 안에 답변합니다.</p><a href="mailto:73036396@naver.com?subject=GOV%20RADAR%20%EB%AC%B8%EC%9D%98" style="min-height: 48px; display: flex; align-items: center; justify-content: center; background: #0b1f3a; color: #ffffff; font-size: 15px; font-weight: 700">73036396@naver.com 으로 문의</a></div>', s, count=1, flags=re.S)
    assert "{{" not in s and "/_blob/" not in s and ".dc.html" not in s, (name, re.findall(r"\{\{[^}]*\}\}|/_blob/\w+|\w+\.dc\.html", s)[:5])
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    open(os.path.join(OUT, sub, "index.html"), "w", encoding="utf-8").write(s)
    print("wrote /welcome/" + sub)
