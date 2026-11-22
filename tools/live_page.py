#!/usr/bin/env python3
"""GOV RADAR 실시간 세계 상황판 (/live/, /live/<lang>/) — 2026-11-22 대표 요청.

화면 전체를 세계지도 레이더로 쓰고, 빛줄기가 지나갈 때마다 전쟁·분쟁·시위·재난·감염병·사이버 공격 지점이 깜박인다.
그 아래에 모든 항목을 한 페이지에 순서대로 펼쳐 둔다(들어가고 또 들어가는 창 없이).
지진(USGS)과 산불·폭풍·화산(NASA EONET)은 열 때마다 원 기관에서 바로 받아 온다(실패하면 매일 갱신 자료).

Input : src/conflict.json, data_branch/hz/hazards.json, tools/cyber_data.py, src/centroids.json, src/names.json
Output: cf/public/live/{index.html,data.json,<lang>/index.html}
Usage : python3 tools/live_page.py cf/public
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
PUB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "cf", "public")
OUT = os.path.join(PUB, "live")
LANGS = ["ko", "en", "es", "fr", "ar", "vi", "id"]

PREP = {"ko": {"h": "미리 대비하라 — 지금 할 일", "sub": "레이더에 뜬 위험마다, 집과 회사가 오늘 바로 할 수 있는 일입니다. 공식기관 지침(행정안전부 국민재난안전포털, 미국 Ready.gov 등)을 바탕으로 정리했습니다.", "kit": "우리 집 비상 키트 보기", "ctr": "재난 대비센터(맞춤 계획·계산기)", "biz": "회사 대비(사업 연속성) 상담", "c": [["war", "전쟁·무력충돌", ["가까운 민방위 대피소 위치를 미리 확인하세요(안전디딤돌 앱·국민재난안전포털).", "가족이 흩어졌을 때의 연락 방법과 모일 장소를 정해 두세요.", "신분증·여권 사본, 현금 일부, 상비약을 한 가방에 넣어 두세요."]], ["cyber", "대정전·사이버 공격", ["손전등·건전지·보조배터리·휴대용 라디오를 준비하세요.", "중요한 파일은 인터넷과 분리된 곳에 백업하세요.", "업무·금융 계정은 비밀번호를 바꾸고 2단계 인증을 켜세요."]], ["disaster", "지진·해일·화산", ["무거운 가구는 벽에 고정하고, 잠자리 옆에 신발과 손전등을 두세요.", "흔들림이 멈추면 엘리베이터 대신 계단으로 나가세요.", "바닷가에서 강한 흔들림을 느끼면 경보를 기다리지 말고 높은 곳으로 가세요."]], ["disaster", "태풍·홍수·산불", ["재난문자와 기상특보를 켜 두세요.", "지하 공간·하천변·저지대는 피하고, 배수구를 미리 치우세요.", "산불 때는 바람 반대 방향, 큰길 쪽으로 대피하세요."]], ["epidemic", "감염병", ["손 씻기와 마스크를 생활화하고, 증상이 있으면 외출을 줄이세요.", "상비약과 체온계를 준비하고, 질병관리청 공지를 확인하세요.", "재택근무·비대면 업무가 가능한지 미리 점검하세요."]], ["unrest", "경제위기·물가·식량", ["장기 보관 식품을 사서 먹은 만큼 다시 채우는 방식으로 1~2주분을 유지하세요.", "필수 지출과 비상금을 따로 정리해 두세요.", "원자재·물류 의존이 큰 회사는 대체 공급처를 한 곳 이상 확보하세요."]]], "base": "기본 72시간: 물은 한 사람 하루 약 4리터(미국 Ready.gov 기준) 최소 3일분, 조리 없이 먹을 수 있는 음식 3일분, 손전등·라디오·보조배터리·구급약·현금·신분증 사본."}, "en": {"h": "Prepare now — what to do today", "sub": "For each risk on the radar, what a household or company can do today. Based on official guidance (Korea's national disaster safety portal, US Ready.gov and others).", "kit": "See the home emergency kit", "ctr": "Disaster preparedness centre (plans, calculator)", "biz": "Business continuity consultation", "c": [["war", "War and armed conflict", ["Find your nearest public shelter in advance.", "Agree how your family will reach each other and where to meet if separated.", "Keep ID and passport copies, some cash and basic medicines in one bag."]], ["cyber", "Blackouts and cyberattacks", ["Keep a torch, batteries, a power bank and a portable radio.", "Back up important files somewhere disconnected from the internet.", "Change passwords on work and bank accounts and turn on two-step login."]], ["disaster", "Earthquake, tsunami, volcano", ["Fix heavy furniture to walls; keep shoes and a torch by the bed.", "When shaking stops, leave by the stairs, not the lift.", "On the coast, if you feel strong shaking, go to high ground without waiting for a warning."]], ["disaster", "Typhoon, flood, wildfire", ["Turn on emergency alerts and weather warnings.", "Avoid basements, riverbanks and low ground; clear drains in advance.", "In a wildfire, evacuate upwind towards wide roads."]], ["epidemic", "Epidemics", ["Wash hands, wear a mask and stay home when ill.", "Keep basic medicines and a thermometer; follow public-health notices.", "Check in advance that remote work is possible."]], ["unrest", "Economic crisis, prices, food", ["Keep 1–2 weeks of long-life food, eating and replacing it as you go.", "Separate essential spending and an emergency fund.", "Firms reliant on raw materials or shipping should line up at least one alternative supplier."]]], "base": "Basic 72 hours: about 4 litres of water per person per day (US Ready.gov) for at least 3 days, 3 days of food that needs no cooking, torch, radio, power bank, first-aid kit, cash and ID copies."}}

UI = {
 "ko": dict(title="실시간 세계 상황판 — 전쟁·분쟁·재난·감염병·사이버 공격 · GOV RADAR", desc="세계지도 레이더 한 화면에 전쟁·무력분쟁·시위·자연재해·감염병·사이버 공격을 실시간으로 표시하고, 모든 항목을 한 페이지에 순서대로 정리했습니다.",
   live="실시간", h1="지금 세계에서 일어나는 일", sub="전쟁부터 재난·감염병·사이버 공격까지, 레이더가 도는 동안 한 화면에서 봅니다.",
   upd="자료 갱신", feed="지진·산불·폭풍은 열 때마다 원 기관에서 받아 옵니다", tap="점을 누르면 내용이 열립니다",
   L=dict(war="전쟁", conflict="무력분쟁", unrest="시위·폭동", disaster="자연재해", epidemic="감염병", cyber="사이버 공격"),
   S=dict(sum="지금 요약", stat="자료 출처 상태 — 기관별 마지막 수집", statn="각 기관 원문을 자동으로 받아 온 마지막 성공 시각(서울)입니다. 36시간 넘게 새로 받지 못하면 ‘지연’, 실패하면 ‘실패’로 표시합니다.", stth=["출처", "상태", "마지막 성공", "건수"], so="정상", sl="지연", sf="실패", news="실시간 뉴스 — 자동 수집", brief="이번 주 브리프 — 한국 기업에 주는 영향과 할 일", bi="영향", bo="기회", ba="지금 할 일", bc="WMM이 도울 수 있는 것", bl="필요한 솔루션 요청", hot="전쟁·주요 분쟁 현장", all="진행 중인 무력분쟁 전체", unrest="폭동·대규모 시위", dis="자연재해 — 최근", livefeed="지금 들어온 소식 (원 기관 실시간)",
          epi="감염병", cyber="사이버 공격 — 최근 사건", hist="사이버 공격 — 역대 주요 사건", ast="지구에 가까이 오는 천체", kinds="재난·분쟁 21가지 — 움직이는 화면", ctry="나라별 위험", prep="지금 준비할 것", src="출처"),
   th=["분쟁", "시작", "2025 사망", "2026 사망"], more="자세히", since="부터", v=dict(atk="실제 공격", susp="조사 중·의심", no="공격 아님", vuln="취약점", hist="역대"),
   lv=dict(war="전쟁", tension="긴장", high="높음", elevated="주의", watch="관찰", conflict="분쟁", minor="소규모", skirmish="충돌"), go="상세 페이지", nofeed="원 기관 연결이 안 돼 매일 갱신 자료로 보여 줍니다.", utc="UTC", kst="서울",
   note="확인된 사실만 싣습니다. 지점은 나라 중심 위치로 표시하며 정확한 현장 좌표가 아닐 수 있습니다."),
 "en": dict(title="Live world situation board — wars, conflicts, disasters, epidemics, cyberattacks · GOV RADAR", desc="One radar world map showing wars, armed conflicts, unrest, natural disasters, epidemics and cyberattacks live, with every item listed in order on one page.",
   live="LIVE", h1="What is happening in the world now", sub="From wars to disasters, epidemics and cyberattacks — one screen, while the radar turns.",
   upd="Data updated", feed="Earthquakes, wildfires and storms load straight from the source each time", tap="Tap a dot to open it",
   L=dict(war="War", conflict="Armed conflict", unrest="Unrest", disaster="Natural disaster", epidemic="Epidemic", cyber="Cyberattack"),
   S=dict(sum="Summary now", stat="Source status — last successful collection", statn="Last time each agency feed was fetched successfully (Seoul time). Over 36 hours without new data shows Delayed; a failure shows Failed.", stth=["Source", "Status", "Last success", "Items"], so="OK", sl="Delayed", sf="Failed", news="Live news — collected automatically", brief="This week’s brief — what it means for businesses and what to do", bi="Impact", bo="Opportunities", ba="Do now", bc="How WMM can help", bl="Request a solution", hot="Wars and major conflict zones", all="All armed conflicts under way", unrest="Riots and mass protests", dis="Natural disasters — recent", livefeed="Just in (live from the source)",
          epi="Epidemics", cyber="Cyberattacks — recent incidents", hist="Cyberattacks — landmark cases", ast="Objects passing close to Earth", kinds="21 hazards — animated", ctry="Risk by country", prep="What to prepare now", src="Sources"),
   th=["Conflict", "Since", "Deaths 2025", "Deaths 2026"], more="More", since="since", v=dict(atk="Confirmed attack", susp="Under investigation", no="Not an attack", vuln="Vulnerability", hist="Landmark"),
   lv=dict(war="War", tension="Tension", high="High", elevated="Elevated", watch="Watch", conflict="Conflict", minor="Minor", skirmish="Skirmish"), go="Full page", nofeed="Could not reach the source; showing the daily update instead.", utc="UTC", kst="Seoul",
   note="Confirmed facts only. Dots mark the country centre, not the exact site."),
}
for l, n in {"es": ("EN VIVO", "Qué está pasando en el mundo ahora", "Guerra", "Conflicto armado", "Disturbios", "Desastre natural", "Epidemia", "Ciberataque"),
             "fr": ("EN DIRECT", "Ce qui se passe dans le monde", "Guerre", "Conflit armé", "Troubles", "Catastrophe naturelle", "Épidémie", "Cyberattaque"),
             "ar": ("مباشر", "ما يحدث في العالم الآن", "حرب", "نزاع مسلح", "اضطرابات", "كارثة طبيعية", "وباء", "هجوم سيبراني"),
             "vi": ("TRỰC TIẾP", "Thế giới đang diễn ra điều gì", "Chiến tranh", "Xung đột vũ trang", "Bất ổn", "Thiên tai", "Dịch bệnh", "Tấn công mạng"),
             "id": ("LANGSUNG", "Apa yang terjadi di dunia sekarang", "Perang", "Konflik bersenjata", "Kerusuhan", "Bencana alam", "Wabah", "Serangan siber")}.items():
    u = dict(UI["en"]); u["live"], u["h1"] = n[0], n[1]
    u["L"] = dict(war=n[2], conflict=n[3], unrest=n[4], disaster=n[5], epidemic=n[6], cyber=n[7])
    UI[l] = u

GO = {"hot": "conflict/", "all": "conflict/", "unrest": "conflict/", "dis": "@hazards", "kinds": "@hazards", "cyber": "@cyber", "hist": "@cyber", "prep": "ready/"}


def flag(iso):
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in iso) if iso and len(iso) == 2 and iso.isalpha() else "🌐"


def data():
    import cyber_data as C
    cf = json.load(open(os.path.join(ROOT, "src", "conflict.json"), encoding="utf-8"))
    hp = os.path.join(ROOT, "data_branch", "hz", "hazards.json")
    hz = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) else {}
    cen = json.load(open(os.path.join(ROOT, "src", "centroids.json"), encoding="utf-8"))
    names = json.load(open(os.path.join(ROOT, "src", "names.json"), encoding="utf-8"))
    nm = {k: {"ko": v.get("ko") or v.get("en"), "en": v.get("en")} for k, v in names.items() if isinstance(v, dict)}
    pts = []

    def P(iso, layer, ko, en, ref, sev=1):
        if iso in cen:
            la, lo = cen[iso]
            pts.append({"x": lo, "y": la, "l": layer, "ko": ko, "en": en, "r": ref, "s": sev, "i": iso})

    hot = []
    seen = set()
    for h in (hz.get("hotspots") or []) + (cf.get("hotspots") or []):
        key = (h.get("iso"), h.get("ko"))
        if key in seen:
            continue
        seen.add(key)
        facts = [{"ko": f.get("ko"), "en": f.get("en")} for f in (h.get("facts") or [])[:4] if isinstance(f, dict)]
        hot.append({"iso": h.get("iso"), "lv": h.get("level"), "ko": h.get("ko"), "en": h.get("en"), "sko": h.get("status_ko"), "sen": h.get("status_en"), "f": facts})
        P(h.get("iso"), "war" if h.get("level") == "war" else "conflict", h.get("ko"), h.get("en"), "hot-%d" % (len(hot) - 1), 3)
    allc = []
    for n, c in enumerate(cf.get("all_conflicts", {}).get("items") or []):
        allc.append({"lv": c.get("level"), "ko": c.get("ko"), "en": c.get("en"), "iso": c.get("iso") or [], "st": c.get("start"), "d25": c.get("d25"), "d26": c.get("d26")})
        for iso in c.get("iso") or []:
            P(iso, "war" if c.get("level") == "war" else "conflict", c.get("ko"), c.get("en"), "all-%d" % n, 2 if c.get("level") in ("war", "conflict") else 1)
    un = []
    for n, u in enumerate(cf.get("unrest", {}).get("items") or []):
        un.append({"iso": u.get("iso"), "ko": u.get("ko"), "en": u.get("en"), "wko": u.get("when_ko"), "wen": u.get("when_en"), "tko": u.get("text_ko"), "ten": u.get("text_en")})
        P(u.get("iso"), "unrest", u.get("ko"), u.get("en"), "un-%d" % n, 1)
    dis, epi, ast = [], [], []
    for d in hz.get("disasters") or []:
        row = {"k": d.get("kind"), "iso": d.get("iso") or "", "d": d.get("date"), "ko": d.get("ko"), "en": d.get("en"), "u": d.get("url"), "src": d.get("src")}
        if d.get("kind") == "asteroid":
            ast.append(row)
        elif d.get("kind") == "epidemic":
            epi.append(row); P(row["iso"], "epidemic", row["ko"], row["en"], "epi-%d" % (len(epi) - 1), 2)
        else:
            dis.append(row); P(row["iso"], "disaster", row["ko"], row["en"], "dis-%d" % (len(dis) - 1), 2)
    for c in hz.get("countries") or []:
        for t in (c.get("epidemic") or {}).get("ko") or []:
            pass
    ctry = [{"iso": c.get("iso"), "lv": c.get("level"), "ck": (c.get("checked") or ""),
             "c": c.get("conflict") or {}, "d": c.get("disaster") or {}, "e": c.get("epidemic") or {}} for c in (hz.get("countries") or [])]
    cy = []
    for n, r in enumerate(C.REC):
        cy.append({"d": r[0], "w": list(r[1]), "v": r[3], "ko": r[5][0], "en": r[5][1]})
        for lo, la, pk, pe in C.REC_PTS[n]:
            pts.append({"x": lo, "y": la, "l": "cyber", "ko": r[5][0], "en": r[5][1], "r": "cy-%d" % n, "s": 2 if r[3] == "atk" else 1, "i": ""})
    hist = [{"d": h[0], "w": list(h[1]), "v": h[2], "ko": h[4][0], "en": h[4][1]} for h in C.HIST]
    srcs = [{"t": s.get("t"), "u": s.get("u")} for s in (cf.get("sources") or []) if isinstance(s, dict) and s.get("u")]
    return {"upd": hz.get("checked") or hz.get("updated") or cf.get("updated"), "cupd": cf.get("updated"),
            "sum": {"ko": hz.get("summary_ko") or cf.get("summary_ko"), "en": hz.get("summary_en") or cf.get("summary_en")},
            "adv": {"ko": cf.get("advice_ko"), "en": cf.get("advice_en")},
            "hot": hot, "all": allc, "un": un, "dis": dis, "epi": epi, "ast": ast, "ctry": ctry, "cy": cy, "hist": hist, "src": srcs, "pts": pts, "nm": nm, "cen": {k: [round(v[0], 1), round(v[1], 1)] for k, v in cen.items()}}


CSS = r"""
@font-face{font-family:"WMM Nexon";font-weight:300;font-display:swap;src:url("/assets/fonts/NEXONLv1GothicOTFLight.woff") format("woff")}
@font-face{font-family:"WMM Nexon";font-weight:400;font-display:swap;src:url("/assets/fonts/NEXONLv1GothicOTF.woff") format("woff")}
@font-face{font-family:"WMM Nexon";font-weight:700;font-display:swap;src:url("/assets/fonts/NEXONLv1GothicOTFBold.woff") format("woff")}
:root{--f:"WMM Nexon","NEXON Lv1 Gothic OTF","IBM Plex Sans Arabic","Be Vietnam Pro","Apple SD Gothic Neo","Malgun Gothic",sans-serif;--ink:#0B1526;--ink2:#4A5568;--line:#E3E7ED;--bg2:#F5F6F8;
 --war:#FF3B4E;--conflict:#FF8A3D;--unrest:#FFD23F;--disaster:#3FD0FF;--epidemic:#3FE08A;--cyber:#B78CFF;--sea:#050B16;--land:#13233A}
*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--ink);font:400 16px/1.65 var(--f);word-break:keep-all;overflow-wrap:break-word}
a{color:inherit}
/* ---- radar stage ---- */
.stage{position:relative;height:calc(100svh - 105px);min-height:560px;background:radial-gradient(ellipse at 50% 50%,#0B1A30 0%,#050B16 70%);overflow:hidden;color:#E6EEF8;isolation:isolate}
.stage svg.map{position:absolute;inset:0;width:100%;height:100%;z-index:1}
.stage .land{fill:var(--land);stroke:#22395A;stroke-width:.5}
.stage .grat{fill:none;stroke:rgba(90,150,220,.10);stroke-width:.6}
.stage .rings circle{fill:none;stroke:rgba(90,200,255,.13);stroke-width:1}
.stage .axes line{stroke:rgba(90,200,255,.10);stroke-width:1}
.sw{position:absolute;left:50%;top:50%;z-index:2;border-radius:50%;pointer-events:none;transform:translate(-50%,-50%) rotate(0deg);
 background:conic-gradient(from 0deg,rgba(63,208,255,0) 0deg,rgba(63,208,255,0) 290deg,rgba(63,208,255,.06) 320deg,rgba(63,208,255,.22) 352deg,rgba(150,235,255,.55) 359.5deg,rgba(63,208,255,0) 360deg);will-change:transform;backface-visibility:hidden}
.run .sw{animation:sw var(--P) linear infinite}
@keyframes sw{to{transform:translate(-50%,-50%) rotate(360deg)}}
.pts{position:absolute;inset:0;width:100%;height:100%;z-index:3}
.pt{cursor:pointer}
.pt .c{stroke:#050B16;stroke-width:.8}
.pt .g{fill:none;stroke-width:2;opacity:0;transform-box:fill-box;transform-origin:center;will-change:transform,opacity}
.run .pt .g{animation:ping var(--P) ease-out infinite}
@keyframes ping{0%{opacity:.95;transform:scale(.6)}18%{opacity:0;transform:scale(3.4)}100%{opacity:0;transform:scale(3.4)}}
.pt.off{display:none}
.hud{position:absolute;z-index:5;pointer-events:none}
.hud *{pointer-events:auto}
.tl{left:max(16px,env(safe-area-inset-left));top:18px;max-width:min(560px,70vw)}
.tl .lv{display:inline-flex;align-items:center;gap:8px;font-weight:700;font-size:13px;letter-spacing:.12em;color:#FF6B78}
.tl .lv i{width:9px;height:9px;border-radius:50%;background:#FF3B4E;box-shadow:0 0 12px #FF3B4E;animation:blink 1.2s infinite}
@keyframes blink{50%{opacity:.25}}
.tl h1{margin:6px 0 6px;font-size:clamp(24px,3.2vw,42px);line-height:1.15;letter-spacing:-.02em;color:#fff;text-wrap:balance;text-shadow:0 2px 18px rgba(0,0,0,.6)}
.tl p{margin:0;color:#A9BCD4;font-size:15px;max-width:34em;text-shadow:0 1px 10px rgba(0,0,0,.7)}
.tr{right:max(16px,env(safe-area-inset-right));top:18px;text-align:right;font-variant-numeric:tabular-nums}
.tr b{display:block;font-size:22px;color:#fff;letter-spacing:.04em}.tr span{font-size:12px;color:#7F97B5;letter-spacing:.1em}
.tr .u{margin-top:8px;font-size:12px;color:#7F97B5}
.chips{left:max(16px,env(safe-area-inset-left));right:max(16px,env(safe-area-inset-right));bottom:58px;display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;align-items:center;gap:8px;font:700 13.5px/1 var(--f);color:#E6EEF8;background:rgba(8,18,34,.78);border:1px solid rgba(120,170,230,.25);border-radius:999px;padding:9px 13px;cursor:pointer;backdrop-filter:blur(4px)}
.chip i{width:10px;height:10px;border-radius:50%;background:var(--c);box-shadow:0 0 10px var(--c)}
.chip em{font-style:normal;color:#9FB4CF;font-weight:400}
.chip[aria-pressed=false]{opacity:.4}
.tick{left:0;right:0;bottom:0;height:44px;background:rgba(3,8,16,.86);border-top:1px solid rgba(120,170,230,.18);overflow:hidden;display:flex;align-items:center}
.tick .tg{position:relative;z-index:2;flex:none;height:100%;display:flex;align-items:center;padding:0 14px;background:#FF3B4E;color:#fff;font:700 13px/1 var(--f);letter-spacing:.08em}
.tick .rl{white-space:nowrap;display:inline-flex;gap:38px;padding-left:24px;animation:tk 120s linear infinite;font-size:14px;color:#CFDBEA}
.tick .rl b{color:#fff;margin-right:6px}.tick .rl i{font-style:normal;color:var(--c);margin-right:6px}
@keyframes tk{to{transform:translateX(-50%)}}
.tip{position:absolute;z-index:8;max-width:320px;background:#fff;color:var(--ink);border-radius:12px;padding:14px 16px;box-shadow:0 18px 50px rgba(0,0,0,.45);font-size:14.5px;line-height:1.5;display:none}
.tip b{display:block;font-size:15.5px;margin-bottom:4px}.tip small{display:inline-block;font-weight:700;color:#fff;background:var(--c);border-radius:999px;padding:2px 8px;margin-bottom:6px;font-size:12px}
.tip a{display:inline-block;margin-top:8px;font-weight:700;border-bottom:2px solid var(--c);text-decoration:none}
.hint{right:max(16px,env(safe-area-inset-right));bottom:62px;font-size:12px;color:#7F97B5}
[dir=rtl] .hint{right:auto;left:max(16px,env(safe-area-inset-left))}
@media (max-width:760px){.stage{height:auto;min-height:0;display:flex;flex-direction:column}.stage .mapbox{position:relative;height:max(300px,78vw);order:2}
 .tl{position:relative;left:auto;top:auto;padding:20px 16px 6px;max-width:none;order:0}.tr{position:relative;right:auto;top:auto;order:1;text-align:start;display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px;padding:0 16px 6px}.tr b{font-size:16px}.tr .u{margin:0;width:100%}
 .chips{order:3}.tick{order:4}
 .chips{position:relative;left:auto;right:auto;bottom:auto;padding:10px 16px 14px}.hint{display:none}.tick{position:relative}}
@media (min-width:761px){.stage .mapbox{position:absolute;inset:0}}
@media (prefers-reduced-motion:reduce){.run .sw{animation-duration:calc(var(--P)*2)}.tick .rl{animation:none}}

.prep{background:#fff;border-bottom:1px solid var(--line);padding-block:56px}
.prep h2{margin:0 0 8px;font-size:clamp(26px,3vw,38px);letter-spacing:-.02em;display:flex;align-items:center;gap:12px}.prep h2 i{width:12px;height:12px;border-radius:50%;background:#12805C;box-shadow:0 0 0 6px rgba(18,128,92,.15)}
.prep .ps{color:var(--ink2);margin:0 0 22px;max-width:52em}
.pg{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.pc{border:1px solid var(--line);border-top:4px solid var(--c);border-radius:12px;padding:18px 20px;background:#fff;min-width:0}
.pc h3{margin:0 0 8px;font-size:18px}.pc ol{margin:0;padding-inline-start:20px;font-size:15px;line-height:1.6}.pc li{margin:5px 0}
.pbase{margin:18px 0 0;padding:16px 18px;background:#F1F8F4;border-radius:12px;font-size:15.5px}.pbase b{color:#12805C}
.pacts{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}.pacts a{display:inline-flex;align-items:center;gap:6px;font-weight:700;font-size:15px;text-decoration:none;border-radius:999px;padding:12px 20px;border:1.5px solid var(--ink);color:var(--ink)}.pacts a.p1{background:#12805C;border-color:#12805C;color:#fff}.pacts a.p3{background:var(--ink);color:#fff}
.tl .pgo{display:inline-block;margin-top:14px;pointer-events:auto;background:#12805C;color:#fff;font-weight:700;font-size:15px;text-decoration:none;border-radius:999px;padding:11px 18px;box-shadow:0 6px 20px rgba(18,128,92,.45)}
@media (max-width:1000px){.pg{grid-template-columns:1fr 1fr}}@media (max-width:640px){.pg{grid-template-columns:1fr}}
/* ---- list ---- */
.wrap{max-width:1180px;margin:0 auto;padding-inline:max(16px,env(safe-area-inset-left)) max(16px,env(safe-area-inset-right))}
.sec{padding-block:64px;border-bottom:1px solid var(--line)}
.sec:nth-of-type(even){background:var(--bg2)}
.sec h2{margin:0 0 6px;font-size:clamp(24px,2.6vw,34px);letter-spacing:-.02em;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.sec h2 i{width:12px;height:12px;border-radius:50%;background:var(--c,#0B1526);flex:none}
.sec h2 em{font-style:normal;font-size:.55em;color:var(--ink2);font-weight:400}
.sec .gl{margin:0 0 26px;color:var(--ink2)}
.sec .gl a{font-weight:700;border-bottom:2px solid #B7800F;text-decoration:none;margin-left:6px}
.lead{font-size:19px;line-height:1.7;max-width:52em;margin:0}
.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.cd{background:#fff;border:1px solid var(--line);border-left:4px solid var(--c);border-radius:12px;padding:18px 20px;min-width:0;scroll-margin-top:120px}
.cd h3{margin:0 0 4px;font-size:18px;line-height:1.35}.cd .m{font-size:13.5px;color:var(--ink2);margin:0 0 8px}
.cd p{margin:6px 0 0;font-size:15px}.cd ul{margin:8px 0 0;padding-inline-start:18px;font-size:14.5px;color:#2D3748}.cd li{margin:4px 0}
.cd.hl{box-shadow:0 0 0 3px var(--c)}
.rows{display:grid;gap:0;border-top:1px solid var(--line)}
.row{display:grid;grid-template-columns:110px minmax(0,1fr) auto;gap:14px;align-items:baseline;padding:13px 4px;border-bottom:1px solid var(--line);scroll-margin-top:120px}
.row .d{font-variant-numeric:tabular-nums;color:var(--ink2);font-size:14px}.row .t{min-width:0}.row .t a{text-decoration:none}.row .t a:hover{text-decoration:underline}
.row .b{font-size:12.5px;font-weight:700;color:#fff;background:var(--c);border-radius:999px;padding:3px 9px;white-space:nowrap}
.row.hl{background:#FFF7E0}
.tbl{overflow-x:auto}.tbl table{width:100%;border-collapse:collapse;font-size:15px;min-width:640px}
.tbl th{text-align:start;font-size:13px;color:var(--ink2);font-weight:700;padding:10px;border-bottom:2px solid var(--ink)}
.tbl td{padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}.tbl td.n{font-variant-numeric:tabular-nums;text-align:end;white-space:nowrap}
.tbl tr{scroll-margin-top:120px}.tbl tr.hl td{background:#FFF7E0}
.lvb{display:inline-block;font-size:12px;font-weight:700;color:#fff;border-radius:999px;padding:2px 8px;margin-inline-end:6px;background:var(--c)}
.gal{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
.hzc{margin:0;display:flex;flex-direction:column;gap:8px;min-width:0}
.hzc-v{position:relative;aspect-ratio:16/10;border-radius:12px;overflow:hidden;background:radial-gradient(120% 90% at 50% 50%,#14202a 0%,#0a0f14 60%,#06090c 100%);isolation:isolate}
.hzc-bg{position:absolute;inset:0;width:100%;height:100%;z-index:1}
.hzc-sw{position:absolute;z-index:2;left:50%;top:50%;width:260%;aspect-ratio:1;transform:translate(-50%,-50%);border-radius:50%;pointer-events:none}
.hzc-rg{position:absolute;z-index:2;inset:0;pointer-events:none;background:repeating-radial-gradient(circle at 50% 50%,transparent 0 38px,rgba(120,255,200,.12) 39px 40px)}
.hzc-tag{position:absolute;z-index:5;left:8px;top:8px;font:700 12px/1.2 var(--f);color:#fff;background:rgba(0,0,0,.62);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:3px 9px}
.cg{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.cg .cd{border-left-width:4px}
.srcs{columns:2;column-gap:32px;font-size:13.5px;color:var(--ink2);padding-inline-start:18px}.srcs li{break-inside:avoid;margin:4px 0}
.note{font-size:13.5px;color:var(--ink2);margin-top:18px}
@media (max-width:1000px){.gal{grid-template-columns:repeat(3,minmax(0,1fr))}.cg{grid-template-columns:1fr 1fr}}
@media (max-width:760px){.cards,.cg{grid-template-columns:1fr}.gal{grid-template-columns:1fr 1fr}.row{grid-template-columns:78px minmax(0,1fr)}.row .b{grid-column:2;justify-self:start}.srcs{columns:1}.sec{padding-block:44px}}
"""

JS = r"""
(function(){
var L=document.documentElement.lang,U=window.LIVE_UI,LG=(L==="ko")?"ko":"en",P=8;
var COL={war:"#FF3B4E",conflict:"#FF8A3D",unrest:"#FFD23F",disaster:"#3FD0FF",epidemic:"#3FE08A",cyber:"#B78CFF"};
var ORDER=["war","conflict","unrest","disaster","epidemic","cyber"];
function e(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function tx(o,k){return o[k+(LG==="ko"?"ko":"en")]||o[k+"en"]||o[k+"ko"]||""}
function T(o){return o?(o[LG]||o.en||o.ko||""):""}
function fl(iso){return iso&&iso.length===2?String.fromCodePoint.apply(null,iso.split("").map(function(c){return 127397+c.charCodeAt(0)})):"🌐"}
function nm(D,iso){var n=D.nm[iso];return n?(n[LG]||n.en):iso}
document.documentElement.style.setProperty("--P",P+"s");
// clocks
function clk(){var d=new Date(),k=new Date(d.getTime()+9*3600e3);function f(x){return x.toISOString().slice(11,19)}document.getElementById("cu").textContent=f(d);document.getElementById("ck").textContent=f(k)}
clk();setInterval(clk,1000);
var RAW="https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/hz/hazards.json";
Promise.all([fetch("/live/data.json").then(function(r){return r.json()}),fetch("/map/world.json").then(function(r){return r.json()}),fetch(RAW,{cache:"no-store"}).then(function(r){return r.ok?r.json():null}).catch(function(){return null})]).then(function(a){
var D=a[0],W=topojson.feature(a[1],a[1].objects.countries);
// 매일 자동 수집·해설 갱신된 최신 자료(data 브랜치)를 열 때마다 직접 반영 — 사이트를 다시 게시하지 않아도 최신
(function(H){if(!H||!H.hotspots)return;var C=D.cen||{};
 if((H.checked||H.updated||"")<(D.upd||""))return;
 D.upd=H.checked||H.updated;if(H.summary_ko)D.sum={ko:H.summary_ko,en:H.summary_en};
 var hot=H.hotspots.map(function(h){return{iso:h.iso,lv:h.level,ko:h.ko,en:h.en,sko:h.status_ko,sen:h.status_en,f:(h.facts||[]).slice(0,4).map(function(f){return{ko:f.ko,en:f.en}})}}),hs={};hot.forEach(function(h){hs[h.iso]=1});
 D.hot=hot.concat(D.hot.filter(function(h){return !hs[h.iso]}));
 var dis=[],epi=[],ast=[];(H.disasters||[]).forEach(function(d){var r={k:d.kind,iso:d.iso||"",d:d.date,ko:d.ko,en:d.en,u:d.url,src:d.src};(d.kind==="asteroid"?ast:d.kind==="epidemic"?epi:dis).push(r)});
 if(dis.length||epi.length){D.dis=dis;D.epi=epi;D.ast=ast}
 if(H.countries&&H.countries.length)D.ctry=H.countries.map(function(c){return{iso:c.iso,lv:c.level,ck:c.checked||"",c:c.conflict||{},d:c.disaster||{},e:c.epidemic||{}}});
 var keep=D.pts.filter(function(p){return !/^(hot|dis|epi)-/.test(p.r||"")}),np=[];
 function P(iso,l,ko,en,r,s){var c=C[iso];if(c)np.push({x:c[1],y:c[0],l:l,ko:ko,en:en,r:r,s:s,i:iso})}
 D.hot.forEach(function(h,i){P(h.iso,h.lv==="war"?"war":"conflict",h.ko,h.en,"hot-"+i,3)});D.dis.forEach(function(d,i){P(d.iso,"disaster",d.ko,d.en,"dis-"+i,2)});D.epi.forEach(function(d,i){P(d.iso,"epidemic",d.ko,d.en,"epi-"+i,2)});
 D.pts=np.concat(keep)})(a[2]);
document.getElementById("upd").textContent=(D.upd||"").replace("T"," ")+" KST";
// ---------- lists ----------
var S=U.S,html="";
function sec(id,key,col,count,body,go){return '<section class="sec" id="'+id+'" style="--c:'+(col||"#0B1526")+'"><div class="wrap"><h2><i></i>'+e(S[key])+(count!=null?' <em>'+count+'</em>':'')+'</h2>'+(go?'<p class="gl"><a href="'+go+'">'+e(U.go)+' →</a></p>':'<p class="gl"></p>')+body+'</div></section>'}
var GO=window.LIVE_GO;
html+=sec("s-sum","sum",null,null,'<p class="lead">'+e(T(D.sum))+'</p>');
html+='<section class="sec" id="s-brief" style="--c:#B7800F" hidden><div class="wrap"><h2><i></i>'+e(S.brief)+' <em id="bfw"></em></h2><p class="gl" id="bfm"></p><div class="cards" id="bfc"></div></div></section>';
html+=sec("s-news","news","#FF3B4E",null,'<div data-newsbox="tabs:war,cyber,disaster,epidemic,prep" data-n="15" data-nohead></div>');
html+=sec("s-hot","hot",COL.war,D.hot.length,'<div class="cards">'+D.hot.map(function(h,i){return '<article class="cd" id="hot-'+i+'" style="--c:'+(h.lv==="war"?COL.war:COL.conflict)+'"><h3>'+fl(h.iso)+' '+e(tx(h,""))+'</h3><p class="m"><span class="lvb">'+e(U.lv[h.lv]||h.lv)+'</span>'+e(tx(h,"s"))+'</p>'+(h.f.length?'<ul>'+h.f.map(function(f){return '<li>'+e(T(f))+'</li>'}).join("")+'</ul>':'')+'</article>'}).join("")+'</div>',GO.hot);
html+=sec("s-all","all",COL.conflict,D.all.length,'<div class="tbl"><table><thead><tr><th>'+U.th.map(e).join("</th><th>")+'</th></tr></thead><tbody>'+D.all.map(function(c,i){var lc=c.lv==="war"?COL.war:COL.conflict;return '<tr id="all-'+i+'"><td><span class="lvb" style="--c:'+lc+'">'+e(U.lv[c.lv]||c.lv)+'</span>'+e(tx(c,""))+'<br><small>'+c.iso.map(fl).join(" ")+'</small></td><td class="n">'+e(c.st||"")+'</td><td class="n">'+e(c.d25||"–")+'</td><td class="n">'+e(c.d26||"–")+'</td></tr>'}).join("")+'</tbody></table></div>',GO.all);
html+=sec("s-un","unrest",COL.unrest,D.un.length,'<div class="cards">'+D.un.map(function(u,i){return '<article class="cd" id="un-'+i+'" style="--c:'+COL.unrest+'"><h3>'+fl(u.iso)+' '+e(tx(u,""))+'</h3><p class="m">'+e(tx(u,"w"))+'</p><p>'+e(tx(u,"t"))+'</p></article>'}).join("")+'</div>',GO.unrest);
function rows(arr,pre,col,lab){return '<div class="rows">'+arr.map(function(d,i){return '<div class="row" id="'+pre+'-'+i+'" style="--c:'+col+'"><span class="d">'+e(d.d||"")+'</span><span class="t">'+fl(d.iso)+' '+(d.u?'<a href="'+e(d.u)+'" target="_blank" rel="noopener">'+e(tx(d,""))+'</a>':e(tx(d,"")))+'</span><span class="b">'+e(lab(d))+'</span></div>'}).join("")+'</div>'}
html+='<section class="sec" id="s-feed" style="--c:'+COL.disaster+'"><div class="wrap"><h2><i></i>'+e(S.livefeed)+' <em id="fc"></em></h2><p class="gl">'+e(U.feed)+'</p><div class="rows" id="feed"></div></div></section>';
html+=sec("s-dis","dis",COL.disaster,D.dis.length,rows(D.dis,"dis",COL.disaster,function(d){return d.src||""}),GO.dis);
html+=sec("s-epi","epi",COL.epidemic,D.epi.length,rows(D.epi,"epi",COL.epidemic,function(d){return d.src||""}));
html+=sec("s-cy","cyber",COL.cyber,D.cy.length,'<div class="rows">'+D.cy.map(function(c,i){return '<div class="row" id="cy-'+i+'" style="--c:'+COL.cyber+'"><span class="d">'+e(c.d)+'</span><span class="t">'+e(LG==="ko"?c.ko:c.en)+' <small>· '+e(LG==="ko"?c.w[0]:c.w[1])+'</small></span><span class="b">'+e(U.v[c.v]||c.v)+'</span></div>'}).join("")+'</div>',GO.cyber);
html+=sec("s-hist","hist",COL.cyber,D.hist.length,'<div class="rows">'+D.hist.map(function(c){return '<div class="row" style="--c:#6B5BA8"><span class="d">'+e(c.d)+'</span><span class="t">'+e(LG==="ko"?c.ko:c.en)+' <small>· '+e(LG==="ko"?c.w[0]:c.w[1])+'</small></span><span class="b">'+e(U.v[c.v]||c.v)+'</span></div>'}).join("")+'</div>',GO.hist);
html+=sec("s-ast","ast","#8A94A6",D.ast.length,rows(D.ast,"ast","#5A6577",function(d){return d.src||""}));
html+=sec("s-kinds","kinds","#0B1526",21,'<div class="gal" id="gal"></div>',GO.kinds);
html+=sec("s-ctry","ctry","#B7800F",D.ctry.length,'<div class="cg">'+D.ctry.map(function(c){var lc={war:COL.war,high:COL.conflict,elevated:COL.unrest}[c.lv]||"#8A94A6";var it=[].concat(T(c.c)||[],T(c.d)||[],T(c.e)||[]);return '<article class="cd" style="--c:'+lc+'"><h3>'+fl(c.iso)+' '+e(nm(D,c.iso))+'</h3><p class="m"><span class="lvb">'+e(U.lv[c.lv]||c.lv)+'</span>'+e(c.ck)+'</p>'+(it.length?'<ul>'+it.slice(0,3).map(function(t){return '<li>'+e(t)+'</li>'}).join("")+'</ul>':'')+'</article>'}).join("")+'</div>');
html+=sec("s-prep","prep","#12805C",null,'<p class="lead">'+e(T(D.adv))+'</p>',GO.prep);
html+='<section class="sec" id="s-stat" style="--c:#4A5568"><div class="wrap"><h2><i></i>'+e(S.stat)+'</h2><p class="gl">'+e(S.statn)+'</p><div class="tbl"><table><thead><tr><th>'+S.stth.map(e).join("</th><th>")+'</th></tr></thead><tbody id="stb"></tbody></table></div></div></section>';
html+=sec("s-src","src","#4A5568",D.src.length,'<ol class="srcs">'+D.src.map(function(s){return '<li><a href="'+e(s.u)+'" target="_blank" rel="noopener">'+e(s.t)+'</a></li>'}).join("")+'</ol><p class="note">'+e(U.note)+'</p>');
document.getElementById("list").innerHTML=html;(function(){var R="https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/";function k(t){if(!t)return"–";var d=Date.parse(t.length<=16&&t.indexOf("Z")<0?t+"+09:00":t);return isNaN(d)?t:new Date(d+9*3600e3).toISOString().slice(5,16).replace("T"," ")}
 function age(t){var d=Date.parse(t&&t.length<=16&&t.indexOf("Z")<0?t+"+09:00":t);return isNaN(d)?99:(Date.now()-d)/3600e3}
 function st(ok,t){var h=age(t);return ok===false?'<span class="lvb" style="--c:#C7362E">'+e(S.sf)+'</span>':h>36?'<span class="lvb" style="--c:#A86A00">'+e(S.sl)+'</span>':'<span class="lvb" style="--c:#12805C">'+e(S.so)+'</span>'}
 var NM={usgs:"USGS (지진)",gdacs:"GDACS (재난 경보)",eonet:"NASA EONET (산불·폭풍·화산)",who:"WHO (감염병)",cneos:"NASA CNEOS (근접 천체)",swpc:"NOAA SWPC (우주날씨)"};
 Promise.all([fetch(R+"hz/official.json",{cache:"no-store"}).then(function(r){return r.json()}).catch(function(){return null}),fetch(R+"feeds/sources_status.json",{cache:"no-store"}).then(function(r){return r.json()}).catch(function(){return null})]).then(function(a){var rows=[];
  if(a[0]&&a[0].sources)Object.keys(a[0].sources).forEach(function(x){var v=a[0].sources[x];rows.push([LG==="ko"?(NM[x]||x):(NM[x]||x).replace(/ \(.*\)/,""),st(v.ok,v.last_ok),k(v.last_ok),v.n])});
  if(a[1])Object.keys(a[1]).forEach(function(x){var v=a[1][x];rows.push([x+(LG==="ko"?" (입찰)":" (tenders)"),!v.last_success?'<span class="lvb" style="--c:#8A94A6">'+(LG==="ko"?"미연결(키 없음)":"Not connected")+'</span>':st(v.state!=="FAILED"&&!(v.failed>0&&v.state!=="PARTIAL"),v.last_success),k(v.last_success),(v.kept||0)+(v.new_today?" · +"+v.new_today:"")])});
  rows.push([LG==="ko"?"ransomware.live·CISA (사이버, 10분)":"ransomware.live·CISA (cyber, 10 min)",st(true,new Date().toISOString()),LG==="ko"?"열 때마다":"on open","–"]);
  document.getElementById("stb").innerHTML=rows.map(function(r){return'<tr><td>'+e(r[0])+'</td><td>'+r[1]+'</td><td class="n">'+e(r[2])+'</td><td class="n">'+e(r[3])+'</td></tr>'}).join("")})})();fetch("https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/hz/brief.json",{cache:"no-store"}).then(function(r){return r.ok?r.json():null}).then(function(B){if(!B)return;var X=B[LG]||B.en||B.ko;if(!X)return;var K=[["impacts",S.bi],["opps",S.bo],["actions",S.ba]];
 document.getElementById("bfw").textContent=B.week||"";document.getElementById("bfm").innerHTML=e((LG==="ko"?"갱신 ":"Updated ")+(B.updated||""))+(B.src&&B.src.length?' · '+B.src.slice(0,6).map(function(x){return '<a href="'+e(x.u)+'" target="_blank" rel="noopener" style="border:0;font-weight:400">'+e(x.t)+'</a>'}).join(" · "):"");
 document.getElementById("bfc").innerHTML=K.map(function(k){var a=X[k[0]]||[];return a.length?'<article class="cd" style="--c:#B7800F"><h3>'+e(k[1])+'</h3><ul>'+a.map(function(t){return '<li>'+e(t)+'</li>'}).join("")+'</ul></article>':""}).join("")+(X.cta?'<article class="cd" style="--c:#0B1526"><h3>'+e(S.bc)+'</h3><p>'+e(X.cta)+'</p><p><a href="'+(LG==="ko"?"/ko/":"/"+L+"/")+'?stay=1#solutions" style="font-weight:700">'+e(S.bl)+' →</a></p></article>':"");
 document.getElementById("s-brief").hidden=false}).catch(function(){});if(window.NEWSBOX)document.querySelectorAll("#list [data-newsbox]").forEach(window.NEWSBOX);
// 21 animated hazards (reuse the hazard map clips)
var X=window.HZFX;if(X&&X.card){var hl=X.NM[L]?L:"en";document.getElementById("gal").innerHTML=(X.G||X.K).map(function(k){return X.card(k,"none",X.NM[hl][k],X.NM[hl][k],"")}).join("")}
// ---------- radar map ----------
var st=document.getElementById("stage"),box=document.getElementById("mapbox"),svg=d3.select("#map"),gp=d3.select("#pts"),tip=document.getElementById("tip");
var pts=D.pts.slice(),rnd=function(i){var x=Math.sin(i*12.9898)*43758.5453;return x-Math.floor(x)};
// spread dots that share a country
var cnt={};pts.forEach(function(p,i){var k=p.x.toFixed(1)+","+p.y.toFixed(1);var n=cnt[k]=(cnt[k]||0)+1;if(n>1){var a=n*2.4,r=1.1*Math.sqrt(n);p.x+=Math.cos(a)*r;p.y+=Math.sin(a)*r*.7}});
var counts={};ORDER.forEach(function(k){counts[k]=0});
var T0=0,MP=null;
function draw(onlyPts){
 if(!T0)T0=performance.now();var el=(performance.now()-T0)/1000;
 var w=box.clientWidth,h=box.clientHeight,narrow=innerWidth<761;gp.selectAll("*").remove();
 if(onlyPts&&MP){var pr=MP.pr,cx=MP.cx,cy=MP.cy}else{
 svg.attr("viewBox","0 0 "+w+" "+h);gp.attr("viewBox","0 0 "+w+" "+h);svg.selectAll("*").remove();
 var pr=d3.geoNaturalEarth1().fitExtent(narrow?[[6,10],[w-6,h-10]]:[[w*.03,h*.13],[w*.97,h*.86]],W),pa=d3.geoPath(pr);
 svg.append("path").attr("class","grat").attr("d",pa(d3.geoGraticule10()));
 svg.append("g").selectAll("path").data(W.features).join("path").attr("class","land").attr("d",pa);
 var cx=w/2,cy=h/2,R=Math.hypot(w,h)/2,rg=svg.append("g").attr("class","rings");
 for(var i=1;i<=5;i++)rg.append("circle").attr("cx",cx).attr("cy",cy).attr("r",R*i/5.2);
 var ax=svg.append("g").attr("class","axes");ax.append("line").attr("x1",0).attr("x2",w).attr("y1",cy).attr("y2",cy);ax.append("line").attr("y1",0).attr("y2",h).attr("x1",cx).attr("x2",cx);
 var sw=document.getElementById("sw");sw.style.width=sw.style.height=(R*2.05)+"px";MP={pr:pr,cx:cx,cy:cy}}
 ORDER.forEach(function(k){counts[k]=0});
 var g=gp.selectAll("g.pt").data(pts).join("g").attr("class",function(p){return "pt L-"+p.l+(off[p.l]?" off":"")}).each(function(p){
   var xy=pr([p.x,p.y]);if(!xy)return;counts[p.l]++;
   var ang=(Math.atan2(xy[0]-cx,-(xy[1]-cy))*180/Math.PI+360)%360,dl=(((ang/360*P-el)%P+P)%P-P).toFixed(3)+"s",c=COL[p.l],r=(narrow?2.2:3)+p.s*(narrow?.9:1.3);
   var s=d3.select(this).attr("transform","translate("+xy[0].toFixed(1)+","+xy[1].toFixed(1)+")").style("animation-delay",dl);
   s.append("circle").attr("class","g").attr("r",r*1.6).attr("stroke",c).style("animation-delay",dl);
   s.append("circle").attr("class","c").attr("r",r).attr("fill",c);
 }).on("click",function(ev,p){show(ev,p)}).on("mouseenter",function(ev,p){if(!narrow)show(ev,p)});
 ORDER.forEach(function(k){var c=document.querySelector('.chip[data-l="'+k+'"] em');if(c)c.textContent=counts[k]});
 st.classList.add("run");
}
var off={};
function show(ev,p){var r=box.getBoundingClientRect(),x=ev.clientX-r.left,y=ev.clientY-r.top;
 tip.style.setProperty("--c",COL[p.l]);tip.innerHTML='<small>'+e(U.L[p.l])+'</small><b>'+(p.i?fl(p.i)+' ':'')+e(LG==="ko"?p.ko:p.en)+'</b>'+(p.r?'<a href="#'+p.r+'">'+e(U.more)+' ↓</a>':'')+(p.u?'<br><a href="'+e(p.u)+'" target="_blank" rel="noopener">'+e(p.l==="cyber"?"ransomware.live":"USGS / NASA")+' ↗</a>':'');
 tip.style.display="block";var tw=tip.offsetWidth,th=tip.offsetHeight;tip.style.left=Math.min(Math.max(8,x+14),r.width-tw-8)+"px";tip.style.top=Math.min(Math.max(8,y+14),r.height-th-8)+"px"}
box.addEventListener("click",function(ev){if(!ev.target.closest(".pt"))tip.style.display="none"});
tip.addEventListener("click",function(ev){var a=ev.target.closest('a[href^="#"]');if(!a)return;var t=document.getElementById(a.getAttribute("href").slice(1));if(t){document.querySelectorAll(".hl").forEach(function(x){x.classList.remove("hl")});t.classList.add("hl")}});
document.getElementById("chips").innerHTML=ORDER.map(function(k){return '<button class="chip" data-l="'+k+'" aria-pressed="true" style="--c:'+COL[k]+'"><i></i>'+e(U.L[k])+' <em>0</em></button>'}).join("");
document.getElementById("chips").addEventListener("click",function(ev){var b=ev.target.closest(".chip");if(!b)return;var k=b.dataset.l;off[k]=!off[k];b.setAttribute("aria-pressed",!off[k]);document.querySelectorAll(".L-"+k).forEach(function(n){n.classList.toggle("off",!!off[k])})});
// ticker
var tk=[];D.hot.forEach(function(h){tk.push([COL[h.lv==="war"?"war":"conflict"],U.L[h.lv==="war"?"war":"conflict"],fl(h.iso)+" "+tx(h,"")+" — "+tx(h,"s")])});
D.dis.slice(0,8).forEach(function(d){tk.push([COL.disaster,d.d,tx(d,"")])});D.epi.forEach(function(d){tk.push([COL.epidemic,d.d,tx(d,"")])});D.cy.slice(0,6).forEach(function(c){tk.push([COL.cyber,c.d,LG==="ko"?c.ko:c.en])});
var tl=tk.map(function(t){return '<span style="--c:'+t[0]+'"><i>●</i><b>'+e(t[1])+'</b>'+e(t[2])+'</span>'}).join("");document.getElementById("rl").innerHTML=tl+tl;
draw();var rt;addEventListener("resize",function(){clearTimeout(rt);rt=setTimeout(function(){draw()},200)});
// ---------- live feeds straight from the source ----------
var feed=[],ko=LG==="ko";
function addFeed(items){items.forEach(function(it){feed.push(it);pts.push({x:it.x,y:it.y,l:"disaster",ko:it.t,en:it.t,r:"",s:it.s,i:"",u:it.u})});
 feed.sort(function(a,b){return b.ts-a.ts});document.getElementById("fc").textContent=feed.length;
 document.getElementById("feed").innerHTML=feed.slice(0,60).map(function(f){var d=new Date(f.ts+9*3600e3).toISOString().slice(5,16).replace("T"," ");return '<div class="row" style="--c:'+COL.disaster+'"><span class="d">'+d+'</span><span class="t"><a href="'+e(f.u)+'" target="_blank" rel="noopener">'+e(f.t)+'</a></span><span class="b">'+e(f.src)+'</span></div>'}).join("");draw(true)}
var QK=ko?"지진":"Earthquake";
fetch("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson").then(function(r){return r.json()}).then(function(j){addFeed((j.features||[]).map(function(f){var c=f.geometry.coordinates,m=f.properties.mag;return{x:c[0],y:c[1],t:QK+" M"+(m!=null?m.toFixed(1):"?")+" — "+f.properties.place,ts:f.properties.time,u:f.properties.url,src:"USGS",s:m>=6?3:m>=5?2:1}}))}).catch(function(){nf()});
var EC={wildfires:ko?"산불":"Wildfire",severeStorms:ko?"폭풍":"Storm",volcanoes:ko?"화산":"Volcano",floods:ko?"홍수":"Flood",landslides:ko?"산사태":"Landslide"};
fetch("https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=10&limit=80").then(function(r){return r.json()}).then(function(j){addFeed((j.events||[]).filter(function(v){return v.categories&&EC[v.categories[0].id]&&v.geometry&&v.geometry.length}).map(function(v){var g=v.geometry[v.geometry.length-1],c=g.type==="Point"?g.coordinates:(g.coordinates[0]&&g.coordinates[0][0])||[0,0];return{x:c[0],y:c[1],t:EC[v.categories[0].id]+" — "+v.title,ts:Date.parse(g.date)||Date.now(),u:(v.sources&&v.sources[0]&&v.sources[0].url)||"https://eonet.gsfc.nasa.gov/",src:"NASA EONET",s:1}}))}).catch(function(){nf()});
fetch("/api/cyberlive").then(function(r){return r.json()}).then(function(j){var by={};(j.rw||[]).forEach(function(x){if(x.la==null)return;(by[x.c]=by[x.c]||{c:x.c,la:x.la,lo:x.lo,n:0,g:{}}).n++;by[x.c].g[x.g]=1});
 Object.keys(by).forEach(function(k){var q=by[k],gs=Object.keys(q.g).slice(0,3).join(", ");pts.push({x:q.lo+1.2,y:q.la-1,l:"cyber",ko:"랜섬웨어 피해 주장 "+q.n+"건 (최근 7일, 확인 전) · "+gs,en:q.n+" ransomware claims (last 7 days, unverified) · "+gs,r:"",s:Math.min(3,1+Math.floor(q.n/5)),i:q.c,u:"https://www.ransomware.live/"})});if(Object.keys(by).length)draw(true)}).catch(function(){});
var nfn=0;function nf(){if(++nfn===2){document.getElementById("feed").innerHTML='<p class="gl">'+e(U.nofeed)+'</p>'}}
}).catch(function(err){console.log("live",err)});
})();
"""


def page(L, D_js):
    u = UI[L]
    up = lambda k: "/hazards/" + ("" if L == "ko" else "?l=" + L) if k == "@hazards" else ("/cyber/" if L == "ko" else f"/cyber/{L}/") if k == "@cyber" else f"/{L}/{k}"
    go = {k: up(v) for k, v in GO.items()}
    sub = [["#stage", u["live"]], ["#s-prep", (PREP.get(L) or PREP["en"])["h"].split(" — ")[0]], ["#s-brief", u["S"]["brief"]], ["#s-news", u["S"]["news"]], ["#s-hot", u["S"]["hot"]], ["#s-all", u["S"]["all"]], ["#s-un", u["S"]["unrest"]], ["#s-feed", u["S"]["livefeed"]], ["#s-dis", u["S"]["dis"]],
           ["#s-epi", u["S"]["epi"]], ["#s-cy", u["S"]["cyber"]], ["#s-kinds", u["S"]["kinds"]], ["#s-ctry", u["S"]["ctry"]], ["#s-stat", u["S"]["stat"]], ["#s-src", u["S"]["src"]]]
    esc = lambda s: s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    PR = PREP.get(L) or PREP["en"]
    COLP = {"war": "#FF3B4E", "cyber": "#B78CFF", "disaster": "#3FD0FF", "epidemic": "#3FE08A", "unrest": "#FFB238"}
    lk = "/ko/" if L == "ko" else f"/{L}/"
    prep_html = (f'<section class="prep" id="s-prep"><div class="wrap"><h2><i></i>{esc(PR["h"])}</h2><p class="ps">{esc(PR["sub"])}</p><div class="pg">'
                 + "".join(f'<article class="pc" style="--c:{COLP[c[0]]}"><h3>{esc(c[1])}</h3><ol>' + "".join(f"<li>{esc(x)}</li>" for x in c[2]) + "</ol></article>" for c in PR["c"])
                 + f'</div><p class="pbase"><b>✓</b> {esc(PR["base"])}</p><div class="pacts"><a class="p1" href="{lk}prepare/">{esc(PR["kit"])} →</a><a href="{lk}ready/">{esc(PR["ctr"])} →</a><a class="p3" href="{lk}?stay=1#solutions">{esc(PR["biz"])} →</a></div></div></section>')
    alts = "".join(f'<link rel="alternate" hreflang="{l}" href="https://radar.wmm-hoa.com/live/{"" if l == "ko" else l + "/"}">' for l in LANGS)
    return f"""<!doctype html><html lang="{L}" dir="{'rtl' if L == 'ar' else 'ltr'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(u['title'])}</title><meta name="description" content="{esc(u['desc'])}">{alts}
<link rel="canonical" href="https://radar.wmm-hoa.com/live/{'' if L == 'ko' else L + '/'}"><meta property="og:image" content="https://radar.wmm-hoa.com/assets/og.jpg">
{'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;700&display=swap">' if L == 'ar' else ''}{'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;700&display=swap">' if L == 'vi' else ''}
<style>{CSS}</style></head><body>
<script>window.GVH_LANG_URL=function(l){{return l==="ko"?"/live/":"/live/"+l+"/"}};window.GVH_SUB=function(){{return {json.dumps(sub, ensure_ascii=False)}}};</script><script src="/assets/gvhdr.js" data-l="{L}" data-g="world" data-a="live"></script>
<main>
<section class="stage" id="stage" aria-label="{esc(u['h1'])}"><div class="mapbox" id="mapbox"><svg class="map" id="map" aria-hidden="true"></svg><div class="sw" id="sw"></div><svg class="pts" id="pts" role="img" aria-label="{esc(u['h1'])}"></svg><div class="tip" id="tip"></div></div>
<div class="hud tl"><span class="lv"><i></i>{esc(u['live'])} · GOV RADAR</span><h1>{esc(u['h1'])}</h1><p>{esc(u['sub'])}</p><a class="pgo" href="#s-prep">{esc(PR['h'].split(' — ')[0])} ↓</a></div>
<div class="hud tr"><span>{u['utc']}</span><b id="cu">--:--:--</b><span>{esc(u['kst'])}</span><b id="ck">--:--:--</b><div class="u">{esc(u['upd'])} <span id="upd"></span></div></div>
<div class="hud chips" id="chips"></div><div class="hud hint">{esc(u['tap'])}</div>
<div class="hud tick"><span class="tg">{esc(u['live'])}</span><div class="rl" id="rl"></div></div>
</section>
{prep_html}<div id="list"></div>
</main>
<script>window.LIVE_UI={json.dumps(u, ensure_ascii=False)};window.LIVE_GO={json.dumps(go)};</script>
<script src="/map/d3.min.js"></script><script src="/map/topojson.min.js"></script><script src="/hazards/hzfx.js"></script><script src="/hazards/hzfx2.js"></script>
<script>{JS}</script>
</body></html>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    D = data()
    json.dump(D, open(os.path.join(OUT, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for L in LANGS:
        d = OUT if L == "ko" else os.path.join(OUT, L)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page(L, None))
    print(f"live_page: {len(D['pts'])} map points, {len(D['hot'])} hotspots, {len(D['all'])} conflicts, {len(D['un'])} unrest, {len(D['dis'])} disasters, {len(D['epi'])} epidemics, {len(D['cy'])} cyber")


if __name__ == "__main__":
    main()
