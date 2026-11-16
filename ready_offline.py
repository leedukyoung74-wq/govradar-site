"""재난 대비센터 — "인터넷·통신이 끊겼을 때 쓰는 도구" section (/ko/ready/#offline, /en/ready/#offline).
Facts checked 2026-11-17 against the sources listed in SRC. Illustrations are drawn by WMM in this file (inline SVG):
no third-party logos, app screenshots or Instagram images are used."""
import html
e = lambda s: html.escape(str(s), quote=True)
G, K, W, M = "#b8954a", "#111111", "#ffffff", "#8a8a8a"   # restrained gold, black, white, grey

def _svg(inner, label):
    return (f'<svg viewBox="0 0 240 160" role="img" aria-label="{e(label)}" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="240" height="160" rx="14" fill="{K}"/>{inner}</svg>')

ART = {
 "maps": lambda: _svg(f'''<path d="M40 40l50-14 60 14 50-14v94l-50 14-60-14-50 14z" fill="none" stroke="{W}" stroke-width="3" stroke-linejoin="round"/>
<path d="M90 26v94M150 40v94" stroke="{M}" stroke-width="2"/>
<path d="M58 104c18-6 22-30 44-34s30 18 50 10 20-22 34-26" fill="none" stroke="{G}" stroke-width="4" stroke-linecap="round" stroke-dasharray="2 9"/>
<path d="M186 34c-9 0-15 7-15 15 0 11 15 24 15 24s15-13 15-24c0-8-6-15-15-15z" fill="{G}"/><circle cx="186" cy="49" r="5" fill="{K}"/>
<circle cx="58" cy="104" r="6" fill="{W}"/>''', "offline map with a route"),
 "briar": lambda: _svg(f'''<rect x="38" y="34" width="52" height="92" rx="9" fill="none" stroke="{W}" stroke-width="3"/>
<rect x="150" y="34" width="52" height="92" rx="9" fill="none" stroke="{W}" stroke-width="3"/>
<rect x="48" y="52" width="32" height="12" rx="4" fill="{G}"/><rect x="160" y="74" width="32" height="12" rx="4" fill="{W}"/>
<path d="M104 70q16 10 0 20M114 62q28 18 0 36M124 54q40 26 0 52" fill="none" stroke="{G}" stroke-width="3" stroke-linecap="round"/>
<text x="120" y="146" fill="{M}" font-size="11" text-anchor="middle" font-family="sans-serif">&lt; 100 m</text>''', "two phones messaging at short range"),
 "kiwix": lambda: _svg(f'''<path d="M44 46c26-8 50-8 76 4 26-12 50-12 76-4v76c-26-8-50-8-76 4-26-12-50-12-76-4z" fill="none" stroke="{W}" stroke-width="3" stroke-linejoin="round"/>
<path d="M120 50v76" stroke="{W}" stroke-width="3"/>
<path d="M60 66h40M60 80h40M60 94h30M140 66h40M140 80h40M140 94h26" stroke="{M}" stroke-width="3" stroke-linecap="round"/>
<path d="M120 14v22m-10-10l10 10 10-10" fill="none" stroke="{G}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>''', "library downloaded for offline reading"),
 "mesh": lambda: _svg(f'''<rect x="30" y="70" width="40" height="54" rx="6" fill="none" stroke="{W}" stroke-width="3"/><path d="M50 70V36" stroke="{W}" stroke-width="3" stroke-linecap="round"/>
<rect x="170" y="70" width="40" height="54" rx="6" fill="none" stroke="{W}" stroke-width="3"/><path d="M190 70V36" stroke="{W}" stroke-width="3" stroke-linecap="round"/>
<circle cx="120" cy="96" r="5" fill="{G}"/><path d="M70 96h40M130 96h40" stroke="{G}" stroke-width="3" stroke-dasharray="6 6"/>
<path d="M36 40q14-12 28 0M36 48q14-6 28 0M176 40q14-12 28 0M176 48q14-6 28 0" fill="none" stroke="{G}" stroke-width="2.5"/>
<text x="120" y="146" fill="{M}" font-size="11" text-anchor="middle" font-family="sans-serif">LoRa · KR 920–923 MHz</text>''', "two LoRa radios relaying messages"),
 "ollama": lambda: _svg(f'''<rect x="54" y="38" width="132" height="80" rx="8" fill="none" stroke="{W}" stroke-width="3"/><path d="M40 126h160" stroke="{W}" stroke-width="3" stroke-linecap="round"/>
<rect x="100" y="58" width="40" height="40" rx="6" fill="none" stroke="{G}" stroke-width="3"/><path d="M108 58v-6M120 58v-6M132 58v-6M108 104v-6M120 104v-6M132 104v-6" stroke="{G}" stroke-width="3"/>
<path d="M176 30c0-8 10-12 15-6 4-7 16-4 15 5 7 0 8 11 0 11h-28c-6 0-7-10-2-10z" fill="none" stroke="{M}" stroke-width="2.5"/><path d="M176 22l34 26" stroke="{G}" stroke-width="3" stroke-linecap="round"/>''', "laptop running a local model with cloud switched off"),
}

SRC = {  # [n]: (ko, en, url)
 1: ("Organic Maps 공식 사이트", "Organic Maps official site", "https://organicmaps.app/"),
 2: ("OpenStreetMap 위키 — Organic Maps (지원 기기·라이선스)", "OpenStreetMap Wiki — Organic Maps", "https://wiki.openstreetmap.org/wiki/Organic_Maps"),
 3: ("Briar 공식 사이트", "Briar official site", "https://briarproject.org/"),
 4: ("위키백과 — Briar (지원 기기·통신 방식·보안 감사)", "Wikipedia — Briar (software)", "https://en.wikipedia.org/wiki/Briar_(software)"),
 5: ("카스퍼스키 — 오프라인 메시 메신저 (거리·배터리)", "Kaspersky — offline mesh messengers (range, battery)", "https://www.kaspersky.com/blog/mesh-messengers/54192/"),
 6: ("Kiwix 공식 사이트", "Kiwix official site", "https://kiwix.org/"),
 7: ("위키백과 — Kiwix (지원 기기·자료 용량)", "Wikipedia — Kiwix", "https://en.wikipedia.org/wiki/Kiwix"),
 8: ("Meshtastic 공식 사이트", "Meshtastic official site", "https://meshtastic.org/"),
 9: ("Meshtastic 문서 — LoRa 지역 설정(한국 KR 920–923MHz)", "Meshtastic docs — LoRa regions (KR 920–923 MHz)", "https://meshtastic.org/docs/configuration/radio/lora/"),
 10: ("Ollama 공식 사이트", "Ollama official site", "https://ollama.com/"),
 11: ("Ollama 공식 문서 — 클라우드 모델과 로컬 전용 사용", "Ollama docs — cloud models and local-only use", "https://docs.ollama.com/cloud"),
}

# (key, art, name, url, ko{...}, en{...}, sources)
TOOLS = [
 ("maps", "Organic Maps", "https://organicmaps.app/",
  dict(what="인터넷 없이 쓰는 지도와 길 안내", dev="안드로이드 · 아이폰(iOS 15 이상) · Mac · Linux — Windows 없음", need="휴대폰과 미리 내려받은 지역 지도",
       before=["앱을 설치하고 사는 곳과 이동할 지역의 지도를 내려받습니다.", "집 · 직장 · 학교 · 가까운 대피소를 즐겨찾기에 저장합니다.", "비행기 모드에서 집 → 대피소 길찾기를 한 번 해 봅니다."],
       ok="GPS 위치(위성 신호 — 실내·지하에서는 약함), 내려받은 지역의 장소 검색, 도보·차량 길찾기",
       no="새 지역 지도 받기·지도 갱신, 실시간 교통·도로 통제, 대피소가 지금 열려 있는지",
       rng="거리 제한 없음(내려받은 지역 안)", bat="길 안내 중 GPS·화면이 배터리를 많이 씁니다 — 보조배터리 필수", cost="무료 · 오픈소스(Apache-2.0) · 지도는 OpenStreetMap"),
  dict(what="Maps and directions without the internet", dev="Android · iPhone (iOS 15+) · Mac · Linux — no Windows", need="A phone and maps downloaded in advance",
       before=["Install the app and download the maps for where you live and may need to go.", "Save home, work, school and the nearest shelter as bookmarks.", "In airplane mode, route once from home to the shelter."],
       ok="GPS position (satellite — weak indoors and underground), search within downloaded areas, walking and driving routes",
       no="Downloading new areas or updates, live traffic or road closures, whether a shelter is open right now",
       rng="No range limit (inside downloaded areas)", bat="Navigation uses GPS and screen heavily — carry a power bank", cost="Free · open source (Apache-2.0) · OpenStreetMap data"),
  [1, 2]),
 ("briar", "Briar", "https://briarproject.org/",
  dict(what="인터넷 없이 가까운 사람과 주고받는 문자 메시지", dev="안드로이드 · Windows/Mac/Linux 데스크톱판 — 아이폰 없음", need="양쪽 모두 Briar 설치, 서로 미리 연락처 등록",
       before=["가족·동료와 직접 만나 앱에서 서로 연락처를 추가합니다(멀리서는 추가가 어렵습니다).", "블루투스·Wi-Fi 전송을 켜고 같은 방, 벽 너머에서 각각 시험해 봅니다.", "아이폰 사용자가 있으면 다른 연락 수단을 따로 정합니다."],
       ok="가까이 있는 등록된 연락처와 암호화된 문자 주고받기(블루투스·같은 Wi-Fi)",
       no="멀리 있는 사람(인터넷·Tor 필요), 아이폰 사용자, 등록하지 않은 사람, 음성 통화",
       rng="블루투스 범위 안 — 대개 수십 m 이내, 트인 곳에서도 100m 이내이며 벽·장애물에 크게 약해집니다", bat="블루투스·Wi-Fi를 계속 켜 두면 배터리가 빨리 닳습니다", cost="무료 · 오픈소스(GPL-3.0) · 2017년 외부 보안 감사"),
  dict(what="Text messages with people nearby, without the internet", dev="Android · desktop for Windows/Mac/Linux — no iPhone", need="Briar on both sides and contacts added in advance",
       before=["Meet family and colleagues in person and add each other in the app (adding from afar is hard).", "Turn on Bluetooth/Wi-Fi sharing and test in the same room and through a wall.", "Agree another channel for anyone using an iPhone."],
       ok="Encrypted texts with added contacts nearby (Bluetooth, same Wi-Fi)",
       no="People far away (needs internet/Tor), iPhone users, anyone not added, voice calls",
       rng="Bluetooth range — usually tens of metres, under 100 m even in the open; walls cut it sharply", bat="Keeping Bluetooth/Wi-Fi on drains the battery faster", cost="Free · open source (GPL-3.0) · external security audit in 2017"),
  [3, 4, 5]),
 ("kiwix", "Kiwix", "https://kiwix.org/",
  dict(what="인터넷 없이 보는 백과사전·안내서", dev="안드로이드 · 아이폰 · Windows · Mac · Linux", need="미리 내려받은 자료 파일(ZIM)과 저장 공간",
       before=["앱을 설치하고 필요한 자료(예: 한국어 위키백과, 의료 위키, 여행 안내)를 내려받습니다.", "저장 공간을 확인합니다 — 영어 위키백과 전체는 사진 포함 약 110GB, 사진 없이 약 57GB(2024년 11월 기준).", "정부 재난 안내서는 따로 인쇄하거나 PDF로 저장해 둡니다."],
       ok="내려받은 자료의 검색과 열람",
       no="내려받은 뒤 바뀐 내용, 새 자료, 공식 재난 지침의 최신판",
       rng="거리와 무관(기기 안 자료)", bat="일반 읽기 수준", cost="무료 · 오픈소스(GPLv3)"),
  dict(what="Encyclopedias and manuals readable without the internet", dev="Android · iPhone · Windows · Mac · Linux", need="Content files (ZIM) downloaded in advance and storage space",
       before=["Install the app and download what you need (e.g. Wikipedia in your language, medical wiki, travel guides).", "Check storage — all of English Wikipedia is about 110 GB with pictures, 57 GB without (November 2024).", "Print or save official emergency guidance as PDF separately."],
       ok="Searching and reading downloaded content",
       no="Anything changed after the download, new content, the latest official guidance",
       rng="Not range-based (content on the device)", bat="Like normal reading", cost="Free · open source (GPLv3)"),
  [6, 7]),
 ("mesh", "Meshtastic", "https://meshtastic.org/",
  dict(what="전용 무선장치로 만드는 문자 통신망 — 앱만으로는 작동하지 않습니다", dev="LoRa 무선장치 + 블루투스로 연결한 휴대폰(안드로이드·아이폰)", need="한 사람당 LoRa 장치 1대, 지역 설정 'KR'(920–923MHz)",
       before=["장치를 사기 전에 국내 전파법상 적합성평가(KC) 대상·인증 여부를 판매처에 확인합니다 — WMM은 아직 확인하지 못했습니다.", "장치마다 지역을 'KR'로 맞추고, 같은 채널 설정으로 짝을 맞춥니다.", "건물 안·밖, 1km 이상 거리에서 실제로 시험합니다."],
       ok="장치가 있는 사람끼리 문자 주고받기, 장치가 많으면 서로 중계해 더 멀리",
       no="장치가 없는 사람, 인터넷 서비스, 119 등 구조 기관 연결",
       rng="트인 곳에서 수 km 가능, 건물·지형에 따라 크게 줄어듭니다", bat="장치 자체 배터리·충전이 필요합니다", cost="소프트웨어 무료 · 장치는 구매 필요(WMM은 구매·추천하지 않음)"),
  dict(what="A text network built with dedicated radios — the app alone does nothing", dev="A LoRa radio + a phone paired by Bluetooth (Android or iPhone)", need="One LoRa device per person, region set to 'KR' (920–923 MHz) in Korea",
       before=["Before buying, ask the seller whether the device has Korean conformity certification (KC) — WMM has not confirmed this.", "Set every device to region 'KR' and the same channel.", "Test indoors, outdoors and over 1 km."],
       ok="Texts between people who have devices; more devices relay messages further",
       no="People without a device, internet services, reaching 119 or other rescue services",
       rng="Several km in open terrain, much less among buildings or hills", bat="The device needs its own battery and charging", cost="Free software · devices must be bought (WMM does not buy or recommend one)"),
  [8, 9]),
]
OLLAMA = ("ollama", "Ollama", "https://ollama.com/",
  dict(what="인터넷 없이 Windows PC에서 돌리는 로컬 AI(보조 도구)", dev="Windows · Mac · Linux PC", need="인터넷이 될 때 미리 설치하고 로컬 모델을 내려받아 둔 PC(모델마다 수 GB)",
       before=["Ollama를 설치하고 로컬 모델을 내려받습니다.", "클라우드 모델을 쓰지 않도록 합니다 — 이름 끝이 '-cloud'인 모델을 쓰지 말고, 설정에서 클라우드 기능을 끕니다.", "인터넷을 끊고 실제로 질문해 봅니다."],
       ok="로컬 모델의 질문·요약·번역 — 질문이 PC 밖으로 나가지 않습니다",
       no="'-cloud' 모델(ollama.com 계정과 인터넷이 필요하고 질문이 외부 서버에서 처리됨), 최신 정보 검색",
       rng="해당 없음(PC 안)", bat="노트북 배터리를 많이 씁니다", cost="로컬 사용 무료 · 클라우드는 별도 요금(WMM은 쓰지 않음)"),
  dict(what="A local AI on a Windows PC without the internet (support tool)", dev="Windows · Mac · Linux PCs", need="A PC with Ollama installed and local models downloaded in advance (several GB each)",
       before=["Install Ollama and download a local model.", "Keep cloud models off: do not use models ending in '-cloud', and disable cloud features in settings.", "Disconnect the internet and ask it something."],
       ok="Questions, summaries and translation with a local model — nothing leaves the PC",
       no="'-cloud' models (need an ollama.com account and internet; prompts are processed on its servers), searching current information",
       rng="Not applicable (on the PC)", bat="Heavy on laptop batteries", cost="Free for local use · cloud is paid separately (WMM does not use it)"),
  [10, 11])

L_ = {
 "ko": dict(h="인터넷·통신이 끊겼을 때 쓰는 도구", first="재난이 오기 <b>전에</b> 설치하고, 내려받고, 한 번 시험해 두어야 합니다. 통신이 끊긴 뒤에는 앱도 지도도 받을 수 없습니다.",
            notsub="이 도구들은 119·112 같은 긴급 구조 연락이나 재난문자·안전디딤돌 같은 공식 재난 경보를 대신하지 않습니다. 공식 경보와 당국의 대피 지시를 먼저 따르세요.",
            th=("무엇", "지원 기기", "필요한 것", "끊겨도 되는 것", "끊기면 안 되는 것", "거리", "배터리", "비용"), before="재난 전에 할 일", site="공식 사이트",
            aih="보조 기능 — 인터넷 없는 로컬 AI", aip="AI 답은 틀릴 수 있습니다. 응급처치·대피 판단에는 쓰지 말고, 인쇄해 둔 공식 지침과 119를 우선하세요.",
            pick="WMM 추천", picks={"maps": "높음", "briar": "높음 · 사전 설정 필수", "kiwix": "높음", "mesh": "조건부 · 장비·전파 인증 확인 전 보류", "ollama": "보조 · PC가 있을 때"},
            img="그림: WMM 자체 제작(기관 로고·앱 화면이 아닙니다)", src="근거", checked="2026년 11월 17일 확인. 앱 기능은 바뀔 수 있으니 설치 전 공식 사이트를 확인하세요.",
            card="통신 대비 체크: 지도 받기 · 연락처 미리 등록 · 자료 내려받기 · 보조배터리 · 건전지 라디오 · 종이 연락카드"),
 "en": dict(h="Tools for when the internet and phone networks fail", first="Install, download and test these <b>before</b> a disaster. Once networks are down you cannot download apps or maps.",
            notsub="These tools do not replace emergency services (119/112 in Korea, your local number elsewhere) or official alerts. Follow official alerts and evacuation orders first.",
            th=("What", "Devices", "You need", "Works offline", "Does not work offline", "Range", "Battery", "Cost"), before="Before a disaster", site="Official site",
            aih="Support tool — local AI without the internet", aip="AI answers can be wrong. Do not use them for first aid or evacuation decisions; rely on printed official guidance and emergency services.",
            pick="WMM rating", picks={"maps": "High", "briar": "High · set up in advance", "kiwix": "High", "mesh": "Conditional · on hold until device and radio certification are checked", "ollama": "Support · if you have a PC"},
            img="Illustrations made by WMM (not organisation logos or app screenshots)", src="Sources", checked="Checked 17 November 2026. Apps change; check the official site before installing.",
            card="Comms checklist: download maps · add contacts in advance · download reference content · power bank · battery radio · paper contact card"),
}

def _card(t, L, s):
    key, name, url, ko, en, ids = t; d = ko if L == "ko" else en
    rows = "".join(f'<tr><th>{e(h)}</th><td>{e(v)}</td></tr>' for h, v in zip(s["th"], (d["what"], d["dev"], d["need"], d["ok"], d["no"], d["rng"], d["bat"], d["cost"])))
    refs = " ".join(f'<a class="ref" href="{e(SRC[i][2])}" target="_blank" rel="noopener">[{i}] {e(SRC[i][0] if L == "ko" else SRC[i][1])}</a>' for i in ids)
    return f'''<article class="ro-card" id="ro-{key}"><figure class="ro-art">{ART[key]()}</figure>
<div class="ro-body"><h3>{e(name)} <span class="ro-pick">{e(s["pick"])}: {e(s["picks"][key])}</span></h3>
<table class="ro-t">{rows}</table>
<p class="ro-bh">{e(s["before"])}</p><ol class="ro-steps">{"".join(f"<li>{e(x)}</li>" for x in d["before"])}</ol>
<p class="ro-links"><a class="ro-site" href="{e(url)}" target="_blank" rel="noopener">{e(s["site"])} ↗</a> <span class="note">{refs}</span></p></div></article>'''

def section(L):
    s = L_["ko" if L == "ko" else "en"]
    cards = "".join(_card(t, L, s) for t in TOOLS)
    return f'''<section class="rd-sec ro" id="offline"><div class="rd-in">
<h2>{e(s["h"])}</h2>
<p class="ro-first">{s["first"]}</p>
<p class="ro-not">{e(s["notsub"])}</p>
<div class="ro-grid">{cards}</div>
<h3 class="ro-aih">{e(s["aih"])}</h3><p class="ro-not">{e(s["aip"])}</p>
<div class="ro-grid ro-one">{_card(OLLAMA, L, s)}</div>
<p class="ro-check">{e(s["card"])}</p>
<p class="note">{e(s["img"])} · {e(s["checked"])}</p>
</div></section>
<style>
.ro{{background:#fff;color:#111}}.ro h2{{font-size:clamp(26px,4vw,40px)}}
.ro-first{{font-size:18px;line-height:1.6;border-left:4px solid #b8954a;padding:12px 16px;background:#faf7f0;margin:18px 0 10px}}
.ro-not{{font-size:15px;line-height:1.6;color:#333}}
.ro-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:22px 0}}.ro-one{{grid-template-columns:1fr}}
.ro-card{{border:1px solid #e6e2d8;border-radius:14px;overflow:hidden;background:#fff;display:flex;flex-direction:column}}
.ro-one .ro-card{{flex-direction:row}}.ro-one .ro-art{{flex:0 0 36%}}
.ro-art{{margin:0;background:#111;line-height:0}}.ro-art svg{{width:100%;height:auto;display:block}}
.ro-body{{padding:16px 18px 18px}}.ro-body h3{{margin:0 0 10px;font-size:22px}}
.ro-pick{{display:block;font-size:13px;font-weight:400;color:#7a5e1f;margin-top:4px}}
.ro-t{{width:100%;border-collapse:collapse;font-size:14px;line-height:1.5}}.ro-t th{{text-align:left;width:31%;color:#555;font-weight:700;padding:6px 8px 6px 0;vertical-align:top}}
.ro-t td{{padding:6px 0}}.ro-t tr+tr{{border-top:1px solid #f0ece3}}
.ro-bh{{font-weight:700;margin:14px 0 4px}}.ro-steps{{margin:0;padding-left:20px;font-size:14px;line-height:1.55}}
.ro-links{{margin-top:12px;font-size:13px}}.ro-site{{display:inline-block;background:#111;color:#fff!important;text-decoration:none;padding:7px 14px;border-radius:999px;font-weight:700;margin-right:6px}}
.ro-links .ref{{color:#555;margin-right:6px}}
.ro-check{{font-weight:700;border:1px dashed #b8954a;border-radius:10px;padding:12px 14px}}
@media(max-width:760px){{.ro-grid{{grid-template-columns:1fr;gap:14px}}.ro-one .ro-card{{flex-direction:column}}.ro-t th{{width:36%}}.ro-first{{font-size:16px}}}}
</style>'''
