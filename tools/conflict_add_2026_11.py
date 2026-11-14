#!/usr/bin/env python3
"""One-off: add Saudi Arabia and all other current conflicts / unrest (as of 2026-11-15) to src/conflict.json.
Detailed cards come first (Saudi Arabia leads), then a full list of ongoing armed conflicts and a list of riots/unrest."""
import json, os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "conflict.json")
C = json.load(open(P, encoding="utf-8"))
S = C["sources"]
def src(t, u, tier):
    for i, s in enumerate(S):
        if s["u"] == u: return i
    S.append({"t": t, "u": u, "tier": tier}); return len(S) - 1

W = lambda name, slug: src(f"Wikipedia — {name} (for reference; check the original footnotes)", "https://en.wikipedia.org/wiki/" + slug, 3)
LIST = W("List of ongoing armed conflicts (as of 2026-11-14)", "List_of_ongoing_armed_conflicts")

# ---------- detailed cards ----------
sa = dict(id="saudi", iso="SA", level="war", ko="사우디아라비아 (이란 전쟁·후티 공격)", en="Saudi Arabia (Iran war, Houthi attacks)",
  status_ko="이란·후티의 미사일·드론 공격 대상 · 예멘에서 연합군 공습 지휘", status_en="Target of Iranian and Houthi missiles and drones · leads coalition air strikes in Yemen",
  facts=[
   dict(ko="2026년 2월 28일 이란 전쟁이 시작된 뒤 이란 미사일·드론이 사우디 정유시설을 공격했고, 아람코는 라스타누라 정유소 가동을 멈췄다.", en="After the Iran war began on 28 Feb 2026, Iranian missiles and drones hit Saudi refineries; Aramco shut the Ras Tanura refinery.", v="ok",
        src=[src("Rigzone (Reuters wire) — Saudis pulled deeper into war after new Iranian strikes (2026-03-02)", "https://www.rigzone.com/news/wire/saudis_pulled_deeper_into_war_after_new_iranian_strikes-02-mar-2026-183098-article/", 2),
             src("Offshore Technology — Iranian attacks prompt Aramco to shut Ras Tanura refinery", "https://www.offshore-technology.com/newsletters/iranian-attacks-prompt-aramco-shut-ras-tanura-refinery", 2)]),
   dict(ko="4월 미·이란 휴전 발표 직후 동서 송유관 펌프장이 공격받아 하루 70만 배럴이 줄었다(사우디 관리). 이란은 관여를 부인했다.", en="Right after the April US–Iran ceasefire, an attack on an East–West pipeline pumping station cut flows by 700,000 bpd (Saudi official). Iran denied involvement.", v="ok",
        src=[src("The New Arab — Mapping the attacks on the Gulf since the US-Iran ceasefire (2026-04-10)", "https://www.newarab.com/news/mapping-attacks-gulf-us-iran-ceasefire", 2),
             src("Al-Monitor — Attacks cut Saudi oil output and East-West pipeline flow, state news agency says (2026-04)", "https://app.al-monitor.com/originals/2026/04/attacks-cut-saudi-oil-output-and-east-west-pipeline-flow-state-news-agency-says", 2)]),
   dict(ko="사우디·UAE가 이란 안의 드론·미사일 발사 시설을 비밀리에 공격했다고 5월 로이터·AP가 미국 관리를 인용해 보도했다.", en="In May Reuters and AP, citing US officials, reported that Saudi Arabia and the UAE secretly struck drone and missile launch sites inside Iran.", v="ok",
        src=[src("Al-Monitor (Reuters) — Saudi Arabia launched covert attacks on Iran as regional war widened, sources say (2026-05)", "https://www.al-monitor.com/originals/2026/05/saudi-arabia-launched-covert-attacks-iran-regional-war-widened-sources-say", 2),
             src("Philadelphia Inquirer (AP) — Saudi Arabia and UAE carried out secret attacks in Iran, US officials say (2026-05-14)", "https://www.inquirer.com/news/nation-world/saudi-arabia-united-arab-emirates-secret-attacks-iran-retaliation-us-officials-20260514.html", 2)]),
   dict(ko="10월 초 후티가 아브하·지잔 등 남부 공항을 미사일·드론으로 공격해 3명이 다쳤고(사우디 발표), 연합군은 10월 8일 탄도미사일 3발을 요격했다고 밝혔다.", en="In early October the Houthis hit southern airports such as Abha and Jizan with missiles and drones, wounding three (Saudi statement); on 8 Oct the coalition said it intercepted three ballistic missiles.", v="ok",
        src=[src("Al Jazeera — Saudi Arabia says three people wounded in attacks on southern airports (2026-10-05)", "https://www.aljazeera.com/news/2026/10/5/yemen-forces-claim-to-seize-dhubab-sites-near-bab-al-mandeb-from-houthis", 2),
             src("The National — Saudi airports attacked as Yemen's west coast battle intensifies (2026-10-06)", "https://www.thenationalnews.com/news/mena/2026/10/06/saudi-airports-attacked-as-yemens-west-coast-battle-intensifies/", 2),
             src("Al Jazeera — Saudi-led coalition says it intercepts three Houthi ballistic missiles (2026-10-08)", "https://www.aljazeera.com/news/2026/10/8/saudi-led-coalition-says-it-intercepts-three-houthi-ballistic-missiles", 2)]),
   dict(ko="사우디 주도 연합군은 10월 4일 시작된 예멘 정부군의 '예멘의 새벽' 작전에 전투기 100대로 공중 지원을 했고 후티 목표 324곳을 파괴했다고 발표했다.", en="The Saudi-led coalition said 100 jets gave air support to the Yemeni government's 'Yemen Dawn' offensive launched on 4 Oct and destroyed 324 Houthi targets.", v="official",
        src=[src("The National — Yemeni forces claim Bab Al Mandeb gains as Saudi coalition says 100 jets join Houthi offensive (2026-10-05)", "https://www.thenationalnews.com/news/gulf/2026/10/05/yemen-government-forces-claim-bab-al-mandeb-gains-as-saudi-coalition-says-100-jets-join-houthi-offensive/", 2)]),
  ],
  biz_ko="사우디 동부(정유·석유화학)와 남부(지잔·아브하·나지란) 현장·출장은 안전 계획을 다시 세우고, 홍해·걸프 항로 보험료와 납기를 점검하세요.",
  biz_en="Re-plan safety for sites and trips in the Eastern Province (refining) and the south (Jizan, Abha, Najran); review Red Sea and Gulf shipping insurance and delivery dates.")

yemen = dict(id="yemen", iso="YE", level="war", ko="예멘 내전 / 바브엘만데브 해협", en="Yemen civil war / Bab al-Mandab Strait",
  status_ko="후티 공세(9월)와 정부군 반격(10월) · 해협 통제권 공방", status_en="Houthi offensive (Sept) and government counter-offensive (Oct) · fight over the strait",
  facts=[
   dict(ko="후티는 9월 3일 공세를 시작해 모카항과 홍해 해안, 페림섬을 장악하고 사우디 관련 선박 봉쇄를 선언했다.", en="The Houthis launched an offensive on 3 Sept, took Mokha, the Red Sea coast and Perim Island, and declared a blockade on Saudi-linked shipping.", v="ok",
        src=[W("2026 Yemen offensives", "2026_Yemen_offensives"), src("The National — Yemeni forces claim control of Bab Al Mandeb strait and Mokha (2026-10-05)", "https://www.thenationalnews.com/news/gulf/2026/10/05/yemen-government-forces-claim-bab-al-mandeb-gains-as-saudi-coalition-says-100-jets-join-houthi-offensive/", 2)]),
   dict(ko="정부군은 10월 5일 바브엘만데브·모카를 되찾았다고 주장했으나 후티는 부인했다.", en="Government forces claimed on 5 Oct to have retaken Bab al-Mandab and Mokha; the Houthis denied it.", v="claim",
        src=[src("Al Jazeera — Yemen forces claim key gains near Bab al-Mandeb: What's the latest? (2026-10-06)", "https://www.aljazeera.com/news/2026/10/6/yemen-war-whats-the-latest-on-the-battlefield", 2), src("Euronews — Yemen government forces advance on Bab el-Mandeb (2026-10-06)", "https://www.euronews.com/2026/10/06/yemen-government-forces-advance-on-bab-el-mandeb-in-offensive-against-houthis", 2)]),
   dict(ko="WHO는 8월 6일 이후 사상자 5,000명 이상(사망 959명), 피란민 약 20만 명, 콜레라 의심 환자 급증을 보고했다.", en="WHO reported 5,000+ casualties since 6 Aug (959 deaths), about 200,000 displaced and a surge in suspected cholera.", v="official",
        src=[src("The National — Yemeni forces claim control of Bab Al Mandeb strait and Mokha (2026-10-05)", "https://www.thenationalnews.com/news/gulf/2026/10/05/yemen-government-forces-claim-bab-al-mandeb-gains-as-saudi-coalition-says-100-jets-join-houthi-offensive/", 2)]),
  ], biz_ko="홍해·수에즈 경유 화물은 우회 일정과 전쟁위험 보험료를 반영하세요.", biz_en="Price in detours and war-risk premiums for cargo via the Red Sea and Suez.")

gaza = dict(id="gaza", iso="PS", level="tension", ko="가자지구·서안", en="Gaza Strip and West Bank",
  status_ko="2025년 10월 10일 휴전 유지 중이나 공습 계속 · 서안 정착민 폭력 증가", status_en="Ceasefire of 10 Oct 2025 in place but strikes continue · rising settler violence in the West Bank",
  facts=[
   dict(ko="11월 12일 칸유니스 나세르 병원 공습으로 의사와 어린이를 포함해 최소 6명이 숨졌고, 평화위원회(Board of Peace)는 양측에 민간인 보호를 촉구했다.", en="An Israeli strike on Nasser Hospital in Khan Younis on 12 Nov killed at least six, including a doctor and a child; the Board of Peace urged both sides to protect civilians.", v="ok",
        src=[src("ABC17 (CNN) — Israeli strike on Gaza hospital kills at least 6 (2026-11-12)", "https://abc17news.com/news/national-world/cnn-world/2026/11/12/israeli-strike-on-gaza-hospital-kills-at-least-6-including-doctor-and-child-palestinian-officials-say/", 2),
             src("Radio Pakistan — Board of Peace calls for Gaza peace plan implementation (2026-11-13)", "https://www.radio.gov.pk/13-11-2026/board-of-peace-calls-for-gaza-peace-plan-implementation", 2)]),
   dict(ko="11월 들어서도 이스라엘군의 공격으로 사망자가 이어지고 있다(11월 3일 4명, 14일 드론 공격 2명).", en="Deaths from Israeli fire continue in November (four on 3 Nov, two in a drone strike on 14 Nov).", v="ok",
        src=[src("Al Jazeera — Israeli forces kill four in Gaza as fifth Palestinian dies of wounds (2026-11-03)", "https://www.aljazeera.com/news/2026/11/3/israeli-forces-kill-four-in-gaza-as-fifth-palestinian-dies-of-wounds", 2),
             src("Washington Post (AP) — Israeli drone strike kills 2 Palestinians in Gaza (2026-11-14)", "https://www.washingtonpost.com/national/2026/11/14/mideast-news-israel-gaza-iran-november-14/da5d8e60-e032-11f1-912c-4fbb80d73f7f_story.html", 2)]),
   dict(ko="가자 보건부 집계로 전쟁 이후 사망자는 7만 4천 명을 넘는다.", en="According to Gaza's health ministry, more than 74,000 people have been killed since the war began.", v="single", src=[W("Gaza war", "Gaza_war")]),
  ], biz_ko="가자 재건 사업은 평화위원회·국제기구 조달 공고로 나옵니다. 현장 접근은 아직 제한적입니다.", biz_en="Gaza reconstruction will come through Board of Peace and UN procurement; site access is still limited.")

sudan = dict(id="sudan", iso="SD", level="war", ko="수단 내전 (정부군–RSF)", en="Sudan civil war (army vs RSF)",
  status_ko="정부군이 하르툼, RSF가 다르푸르 장악 · 코르도판이 주전선", status_en="Army holds Khartoum, RSF holds Darfur · Kordofan is the main front",
  facts=[
   dict(ko="정부군은 수도 하르툼과 북부·동부·중부를, RSF는 다르푸르 거의 전역을 장악하고 있다. 정부군은 2025년 10월 엘파셰르를 잃었다.", en="The army holds Khartoum and the north, east and centre; the RSF holds almost all of Darfur. The army lost El Fasher in Oct 2025.", v="ok",
        src=[src("Al Jazeera — The battle for Kordofan, the corridor linking Sudan's east and west (2026-10-01)", "https://www.aljazeera.com/news/2026/10/1/the-battle-for-kordofan-the-corridor-linking-sudans-east-and-west", 2), LIST]),
   dict(ko="IOM은 약 50만 명이 머무는 북코르도판 주도 엘오베이드가 전면 공격 위협을 받고 있다고 경고했다.", en="IOM warns that El Obeid, North Kordofan's capital sheltering about 500,000 people, faces the threat of a full-scale assault.", v="single",
        src=[src("Al Jazeera — The battle for Kordofan (2026-10-01)", "https://www.aljazeera.com/news/2026/10/1/the-battle-for-kordofan-the-corridor-linking-sudans-east-and-west", 2)]),
   dict(ko="UN 집계 국내 피란민은 약 860만 명(2025년 1월 최고 1,160만 명)이다.", en="UN figures put the internally displaced at about 8.6 million (peak 11.6 million in Jan 2025).", v="single",
        src=[src("Al Jazeera — The battle for Kordofan (2026-10-01)", "https://www.aljazeera.com/news/2026/10/1/the-battle-for-kordofan-the-corridor-linking-sudans-east-and-west", 2)]),
  ], biz_ko="수단·차드·남수단 인도지원 조달(식량·물·의료)이 이어집니다. 현장 사업은 보류하세요.", biz_en="Humanitarian procurement (food, water, health) continues for Sudan, Chad and South Sudan; hold field projects.")

eth = dict(id="ethiopia", iso="ET", level="war", ko="에티오피아 (티그라이 전쟁 재발·에리트레아 개입)", en="Ethiopia (Tigray war resumes, Eritrea involved)",
  status_ko="9월 23일 반군 연합 공세 · 정부군 메켈레 장악 · 에리트레아군 진입", status_en="Rebel coalition offensive from 23 Sept · federal army takes Mekelle · Eritrean troops enter",
  facts=[
   dict(ko="9월 23일 TPLF 등 반군 연합이 티그라이·아파르·암하라에서 공세를 시작했고, 정부군은 10월 초 티그라이 주도 메켈레를 장악했다.", en="On 23 Sept a rebel coalition including the TPLF launched an offensive in Tigray, Afar and Amhara; the federal army took the Tigray capital Mekelle in early October.", v="ok",
        src=[src("Al Jazeera — Ethiopia and Eritrea accuse one another of launching war (2026-10-09)", "https://www.aljazeera.com/news/2026/10/9/ethiopia-and-eritrea-accuse-one-another-of-launching-war", 2), W("2026 Ethiopian offensive", "2026_Ethiopian_offensive")]),
   dict(ko="에티오피아는 에리트레아군의 티그라이 진입을 '전면 침공'이라며 UN 안보리에 서한을 보냈고, 에리트레아는 이를 부인하고 국교를 끊었다.", en="Ethiopia told the UN Security Council that Eritrea's entry into Tigray was an 'all-out invasion'; Eritrea denied it and cut diplomatic ties.", v="ok",
        src=[src("Al Jazeera — Ethiopia and Eritrea accuse one another of launching war (2026-10-09)", "https://www.aljazeera.com/news/2026/10/9/ethiopia-and-eritrea-accuse-one-another-of-launching-war", 2), src("Chatham House — War has returned to Tigray. This time it may not stay in Ethiopia (2026-10)", "https://www.chathamhouse.org/2026/10/war-has-returned-tigray-time-it-may-not-stay-ethiopia", 2)]),
  ], biz_ko="에티오피아 북부·에리트레아 국경 일대 사업은 중단하고, 아디스아바바 사업은 일정 지연을 반영하세요.", biz_en="Pause work near northern Ethiopia and the Eritrean border; allow for delays in Addis Ababa projects.")

afpak = dict(id="afpak", iso="PK", level="war", ko="파키스탄–아프가니스탄 전쟁", en="Pakistan–Afghanistan war",
  status_ko="2월부터 국경 공습·포격 · 9월 다시 격화", status_en="Cross-border air and artillery strikes since February · flared again in September",
  facts=[
   dict(ko="2월 파키스탄의 아프간 동부 공습으로 시작돼 국방장관이 '공개 전쟁'이라 부를 만큼 커졌다. 두 차례 명절 휴전은 전쟁을 끝내지 못했다.", en="It began with Pakistani air strikes in eastern Afghanistan in February and grew into what the defence minister called 'open war'; two holiday ceasefires did not end it.", v="ok",
        src=[W("2026 Afghanistan–Pakistan war", "2026_Afghanistan%E2%80%93Pakistan_war"), src("FDD Long War Journal — Pakistan conducts airstrikes in eastern Afghanistan in retaliation for terrorist attacks (2026-09-21)", "https://www.longwarjournal.org/archives/2026/09/pakistan-conducts-airstrikes-in-eastern-afghanistan-in-retaliation-for-terrorist-attacks.php", 2)]),
   dict(ko="9월 코하트 대형 테러 이후 다시 격화해 교전이 2주 넘게 이어졌다.", en="Fighting flared again after a mass-casualty attack in Kohat in September and lasted more than two weeks.", v="ok",
        src=[src("FDD Long War Journal — Fighting between Pakistan and the Taliban persists into second week (2026-09-28)", "https://www.longwarjournal.org/archives/2026/09/fighting-between-pakistan-and-the-taliban-persists-into-second-week.php", 2), W("2026 Afghanistan–Pakistan war", "2026_Afghanistan%E2%80%93Pakistan_war")]),
  ], biz_ko="카이베르파크툰크와·발루치스탄 현장은 이동 제한을 확인하세요. 중앙아시아 육로 물류 일정에 여유를 두세요.", biz_en="Check movement limits in Khyber Pakhtunkhwa and Balochistan; allow slack in Central Asia overland logistics.")

mm = dict(id="myanmar", iso="MM", level="war", ko="미얀마 내전", en="Myanmar civil war",
  status_ko="군정 공세와 저항군 교전 계속 · 2026년 사망 9,600여 명(집계)", status_en="Junta offensives and resistance fighting continue · 9,600+ deaths in 2026 (tally)",
  facts=[
   dict(ko="2026년 들어 집계된 교전 사망자는 9,678명이다.", en="Recorded combat deaths in 2026 stand at 9,678.", v="single", src=[LIST]),
   dict(ko="국영매체는 11월 군이 저항군 핵심 본부와 기지 10곳을 장악했다고 발표했다.", en="State media said in November that the army seized a key resistance headquarters and 10 bases.", v="claim",
        src=[src("Khaosod English (AP) — Myanmar army seizes key resistance headquarters and 10 bases, state media says (2026-11-10)", "https://www.khaosodenglish.com/news/international/2026/11/10/myanmar-army-seizes-key-resistance-headquarters-and-10-bases-held-by-opposition-state-media-says/", 2)]),
  ], biz_ko="미얀마 사업은 제재·안전 점검이 먼저입니다. 태국·방글라데시 국경 물류 지연을 반영하세요.", biz_en="Screen sanctions and safety first; allow for delays on Thai and Bangladeshi border logistics.")

drc = dict(id="drc", iso="CD", level="war", ko="콩고민주공화국 동부 (M23)", en="Eastern DR Congo (M23)",
  status_ko="워싱턴 평화협정 뒤에도 교전 · 2026년 사망 약 4천 명(집계)", status_en="Fighting continues despite the Washington accord · about 4,000 deaths in 2026 (tally)",
  facts=[
   dict(ko="M23은 2025년 12월 미국 중재 평화협정 직후 우비라에 들어갔고, 2026년 1월 철수해 정부군이 다시 들어왔다.", en="M23 entered Uvira in Dec 2025 right after the US-brokered peace deal and withdrew in Jan 2026, when government troops returned.", v="ok",
        src=[src("Washington Times (AP) — Congolese soldiers reenter key eastern city after M23 withdrawal (2026-01-19)", "https://www.washingtontimes.com/news/2026/jan/19/congolese-soldiers-reenter-key-eastern-city-m23-rebels-withdrawal/", 2),
             src("SCMP — Rwanda-backed rebels enter strategic DR Congo town as Trump peace deal crumbles (2025-12)", "https://www.scmp.com/news/world/africa/article/3335966/rwanda-backed-rebels-enter-strategic-dr-congo-town-trump-peace-deal-crumbles", 2)]),
   dict(ko="콩고 분쟁 전체의 2026년 집계 사망자는 3,991명이다.", en="Recorded 2026 deaths across the Congolese conflicts stand at 3,991.", v="single", src=[LIST]),
  ], biz_ko="광물(코발트·구리·주석) 공급망은 원산지 실사를 강화하세요.", biz_en="Tighten origin due diligence on minerals (cobalt, copper, tin).")

sahel = dict(id="sahel", iso="ML", level="war", ko="사헬 (말리·부르키나파소·니제르) 무장세력", en="Sahel jihadist insurgency (Mali, Burkina Faso, Niger)",
  status_ko="JNIM의 말리 연료 봉쇄 · 2026년 사망 2만 1천여 명(지역 전체 집계)", status_en="JNIM fuel blockade of Mali · 21,000+ deaths in 2026 (region-wide tally)",
  facts=[
   dict(ko="알카에다 연계 JNIM은 2025년 9월부터 말리 남부 도시에 연료 봉쇄를 하고 있으며, 2026년 4월 28일 수도 바마코 전면 봉쇄를 선언했다.", en="Al-Qaeda-linked JNIM has blockaded fuel to southern Malian cities since Sept 2025 and declared a full blockade of Bamako on 28 Apr 2026.", v="ok",
        src=[W("Mali fuel blockade", "Mali_fuel_blockade"), src("ISS Africa — JNIM's blockade tactics threaten West Africa's trade corridors (2026-06)", "https://issafrica.org/iss-today/jnim-s-blockade-tactics-threaten-west-africa-s-trade-corridors", 2)]),
   dict(ko="마그레브·사헬 이슬람 무장봉기의 2026년 집계 사망자는 21,049명으로 세계 최대 수준이다.", en="Recorded 2026 deaths in the Maghreb–Sahel insurgencies stand at 21,049, among the highest in the world.", v="single", src=[LIST]),
  ], biz_ko="말리·부르키나파소·니제르 현지 사업은 보류하고, 세네갈·코트디부아르 경유 물류 위험을 점검하세요.", biz_en="Hold field work in Mali, Burkina Faso and Niger; review risks on routes via Senegal and Côte d'Ivoire.")

ven = dict(id="venezuela", iso="VE", level="tension", ko="베네수엘라 (미국 개입)", en="Venezuela (US intervention)",
  status_ko="1월 미군 작전으로 마두로 체포 · 로드리게스 권한대행 체제", status_en="Maduro captured in a US raid in January · Rodríguez acting president",
  facts=[
   dict(ko="미국은 1월 3일 카라카스를 공습하고 마두로 대통령 부부를 체포해 뉴욕으로 이송했다. 이 과정에서 약 80명이 숨졌다.", en="On 3 Jan the US struck Caracas and captured President Maduro and his wife, flying them to New York; about 80 people died.", v="ok",
        src=[src("FDD Long War Journal — United States strikes Venezuela, captures President Maduro (2026-01)", "https://www.longwarjournal.org/archives/2026/01/united-states-strikes-venezuela-captures-president-maduro.php", 2), W("2026 United States intervention in Venezuela", "2026_United_States_intervention_in_Venezuela")]),
   dict(ko="델시 로드리게스 부통령이 1월 5일 대통령 권한대행에 취임했다. 카리브해 마약 운반선 공습(남부의 창 작전)은 계속되고 있다.", en="Vice-president Delcy Rodríguez was sworn in as acting president on 5 Jan; US strikes on alleged drug boats in the Caribbean (Operation Southern Spear) continue.", v="ok",
        src=[W("2026 United States intervention in Venezuela", "2026_United_States_intervention_in_Venezuela"), src("Just Security — Timeline of boat strikes and related actions", "https://www.justsecurity.org/124002/timeline-vessel-strikes-related-actions/", 2)]),
  ], biz_ko="베네수엘라 거래는 미국 제재 변동을 매주 확인하세요.", biz_en="Check US sanctions changes weekly before any Venezuela deal.")

new_cards = [sa, yemen, gaza, sudan, eth, afpak, mm, drc, sahel, ven]
ids = {h["id"] for h in C["hotspots"]}
old = [h for h in C["hotspots"] if h["id"] not in {c["id"] for c in new_cards}]
C["hotspots"] = [sa] + old + [c for c in new_cards if c is not sa]

# ---------- full list of ongoing armed conflicts ----------
# [level, ko, en, iso list, start, deaths 2025, deaths 2026]
AL = [
 ["war","아랍–이스라엘·이란 대리전 (가자·서안·레바논·시리아·이란)","Arab–Israeli and Iran–Israel proxy wars (Gaza, West Bank, Lebanon, Syria, Iran)",["PS","IL","LB","SY","IR","SA"],"1948","28,111","11,914"],
 ["war","미얀마 내전","Myanmar civil war",["MM"],"1948","15,917","9,678"],
 ["war","수단·남수단 내전","Sudanese civil wars (Sudan, South Sudan)",["SD","SS"],"1955","21,994–80,000+","12,443"],
 ["war","콩고민주공화국 분쟁 (M23 등)","Congolese conflicts (incl. M23)",["CD","RW"],"1960","7,737–10,000+","3,991"],
 ["war","소말리아 내전 (알샤바브)","Somali civil war (al-Shabaab)",["SO","KE"],"1978","10,788","6,580"],
 ["war","마그레브·사헬 이슬람 무장봉기 (말리·부르키나파소·니제르·보코하람)","Islamist insurgencies in the Maghreb and Sahel (Mali, Burkina Faso, Niger, Boko Haram)",["ML","BF","NE","NG","TD"],"2002","24,046","21,049"],
 ["war","멕시코 마약 전쟁","Mexican drug war",["MX"],"2006","8,973–10,767","6,466"],
 ["war","예멘 내전 (후티–사우디 연합, 바브엘만데브)","Yemeni civil war (Houthis vs Saudi-led coalition, Bab al-Mandab)",["YE","SA","AE"],"2011","2,940","10,495"],
 ["war","러시아–우크라이나 전쟁","Russia–Ukraine war",["UA","RU"],"2014","80,245","49,078"],
 ["minor","이란 내 무장봉기 (쿠르드·발루치 등, 이란 전쟁 중)","Insurgencies in Iran (Kurdish, Baloch and others, during the Iran war)",["IR"],"1918","63","7,060+"],
 ["minor","파키스탄 무장봉기 (발루치스탄·카이베르파크툰크와)","Insurgencies in Pakistan (Balochistan, Khyber Pakhtunkhwa)",["PK"],"1948","985","1,440"],
 ["minor","에티오피아 내전 (티그라이·암하라·오로모, 에리트레아 개입)","Ethiopian civil wars (Tigray, Amhara, Oromia; Eritrea involved)",["ET","ER"],"1961","6,332","6,656"],
 ["minor","콜롬비아 무력분쟁","Colombian conflict",["CO"],"1964","2,293","1,799"],
 ["minor","아프가니스탄 분쟁 (파키스탄과의 전쟁 포함)","Afghanistan conflicts (incl. war with Pakistan)",["AF","PK"],"1978","4,409","6,171"],
 ["minor","에콰도르 분쟁 (마약 조직)","Ecuadorian conflict (drug gangs)",["EC"],"1993","4,073","3,280"],
 ["minor","나이지리아 내부 분쟁 (보코하람·무장강도·유목민 충돌)","Civil conflicts in Nigeria (Boko Haram, bandits, herder–farmer clashes)",["NG"],"1998","3,200","3,620"],
 ["minor","베네수엘라 분쟁 (미국 개입 포함)","Venezuelan conflict (incl. US intervention)",["VE"],"2010","2,602","409"],
 ["minor","시리아 내전 이후 충돌 (이스라엘 개입·드루즈·IS)","Aftermath of the Syrian civil war (Israeli intervention, Druze, ISIS)",["SY"],"2011","8,837","1,766"],
 ["minor","카메룬 분쟁 (영어권 위기·보코하람)","Cameroonian conflicts (Anglophone crisis, Boko Haram)",["CM"],"2012","1,966","1,684"],
 ["minor","중앙아프리카공화국 내전","Central African Republic civil war",["CF"],"2012","1,276","539"],
 ["minor","아이티 갱단 분쟁","Haitian gang conflict",["HT"],"2018","4,828","2,903"],
 ["conflict","쿠르드 민족 분쟁 (이란·이라크·시리아·튀르키예)","Kurdish nationalist conflicts (Iran, Iraq, Syria, Türkiye)",["IQ","IR","SY","TR"],"1918","300","40+"],
 ["conflict","튀르키예 무장봉기","Insurgencies in Türkiye",["TR"],"1921","300","5"],
 ["conflict","자메이카 정치 폭력","Jamaican political violence",["JM"],"1943","297","243"],
 ["conflict","카슈미르 분쟁 (인도–파키스탄)","Kashmir conflict (India–Pakistan)",["IN","PK"],"1947","975","290"],
 ["conflict","인도 동북부 무장봉기 (마니푸르 등)","Insurgencies in Northeast India (incl. Manipur)",["IN"],"1954","980","559"],
 ["conflict","파푸아 분쟁 (인도네시아)","Papua conflict (Indonesia)",["ID"],"1962","259","299"],
 ["conflict","필리핀 내부 분쟁 (신인민군·IS)","Civil conflict in the Philippines (NPA, ISIS)",["PH"],"1969","537","380"],
 ["conflict","방글라데시 무장봉기","Insurgencies in Bangladesh",["BD"],"1972","369","318"],
 ["conflict","카빈다 분쟁 (앙골라)","Cabinda conflict (Angola)",["AO"],"1975","200","25"],
 ["conflict","파푸아뉴기니 부족 폭력","Ethnic violence in Papua New Guinea",["PG"],"1988","142","204"],
 ["conflict","브라질 마약 전쟁","Brazilian drug war",["BR"],"1992","130+","12+"],
 ["conflict","이라크 분쟁 (IS 잔존 세력·쿠르드)","Iraqi conflict (ISIS remnants, Kurdish issues)",["IQ"],"2003","575","461"],
 ["conflict","리비아 위기","Libyan crisis",["LY"],"2011","282","201"],
 ["conflict","카보델가두 무장봉기 (모잠비크)","Cabo Delgado insurgency (Mozambique)",["MZ"],"2017","824","519"],
 ["conflict","온두라스 갱단 단속","Honduran gang crackdown",["HN"],"2022","561","609"],
 ["skirmish","보쿠 분쟁 (가나)","Bawku conflict (Ghana)",["GH"],"1957","0+","10"],
 ["skirmish","사바 국경 공격 (말레이시아–필리핀)","Cross-border attacks in Sabah (Malaysia–Philippines)",["MY","PH"],"1962","3–6","3+"],
 ["skirmish","서사하라 분쟁","Western Sahara conflict",["MA"],"1970","54","6"],
 ["skirmish","라오스 무장봉기","Insurgency in Laos",["LA"],"1975","5–75","1"],
 ["skirmish","페루 분쟁","Peruvian conflict",["PE"],"1980","47","39"],
 ["skirmish","카사망스 분쟁 (세네갈)","Casamance conflict (Senegal)",["SN","GM"],"1982","6","5"],
 ["skirmish","아르메니아–아제르바이잔 국경","Armenia–Azerbaijan border",["AM","AZ"],"1988","8","2"],
 ["skirmish","북캅카스 분쟁 (러시아)","North Caucasus conflict (Russia)",["RU"],"1991","9","3"],
 ["skirmish","태국 남부 무장봉기","South Thailand insurgency",["TH"],"2004","51","48"],
 ["skirmish","파라과이 무장봉기","Insurgency in Paraguay",["PY"],"2005","2","1"],
 ["skirmish","이집트 이슬람 무장봉기 (시나이)","Islamist insurgency in Egypt (Sinai)",["EG"],"2013","53","17"],
 ["skirmish","엘살바도르 갱단 단속","Salvadoran gang crackdown",["SV"],"2022","10","9"],
 ["skirmish","스리랑카 마약 전쟁","Sri Lankan drug war",["LK"],"2023","40+","38"],
]
C["all_conflicts"] = {"asof": "2026-11-14", "src": LIST,
  "note_ko": "교전 사망자 수는 위키백과 '진행 중인 무력분쟁 목록'(UCDP·ACLED 등 각주 기반)의 집계이며 기관마다 차이가 큽니다. 순위가 아니라 규모를 가늠하는 참고 수치입니다.",
  "note_en": "Combat-death figures are from Wikipedia's 'List of ongoing armed conflicts' (footnoted to UCDP, ACLED and others) and vary widely between sources. Use them to gauge scale, not as a ranking.",
  "items": [dict(level=a[0], ko=a[1], en=a[2], iso=a[3], start=a[4], d25=a[5], d26=a[6]) for a in AL]}

# ---------- riots / mass unrest ----------
U = [
 ("FR","프랑스 전국 시위·폭동","France: nationwide protests and riots","2026년 9월~","Since Sept 2026",
  "유가·생활비·교육 문제로 시작돼 10월 17일 전국 110곳 행진에 55만 명(내무부)이 모였고, 이후 약탈·방화로 번졌다.","Began over fuel, living costs and schools; on 17 Oct 550,000 marched in 110 places (Interior Ministry) and violence, looting and arson followed.",
  [W("17 October French riots", "17_October_French_riots"), W("2026 French civil unrest", "2026_French_civil_unrest")]),
 ("IT","이탈리아 소요","Italy: unrest","2026년 10월 16일~","Since 16 Oct 2026",
  "학생·노조가 생활비·유가·교육 정책에 항의하며 시위·파업·충돌이 이어지고 있다.","Students and unions protest living costs, fuel prices and education policy, with strikes and clashes.",
  [W("2026 Italian unrest", "2026_Italian_unrest")]),
 ("BE","유럽 전역 생활비 시위 (Z세대 주도)","Europe-wide cost-of-living protests (led by Gen Z)","2026년 9월~","Since Sept 2026",
  "알바니아·벨기에·체코·독일·포르투갈·세르비아·스페인 등에서 대규모 시위. 호르무즈·바브엘만데브 봉쇄에 따른 유가 급등이 공통 배경이다.","Large protests in Albania, Belgium, Czechia, Germany, Portugal, Serbia, Spain and others; fuel prices driven by the Hormuz and Bab al-Mandab closures are a shared cause.",
  [W("2026 European unrest", "2026_European_unrest"), W("Fuel protests in 2026", "Fuel_protests_in_2026")]),
 ("MU","모리셔스 폭동","Mauritius riots","2026년 10월 7일~","From 7 Oct 2026",
  "물 부족·생활비 시위가 경찰 총격 사건 뒤 전국 폭동으로 번졌다.","Protests over water shortages and living costs turned into nationwide riots after a police shooting.",
  [W("2026 Mauritian riots", "2026_Mauritian_riots")]),
 ("BD","방글라데시 봉제 노동자 시위","Bangladesh garment workers' protests","2026년 8월~","Since Aug 2026",
  "최저임금 인상(1만 2,500→3만 타카)을 요구하며 10월 말~11월 초 아슐리아·가지푸르·다카에서 격화했다.","Workers demanding a minimum wage rise (Tk12,500 to Tk30,000) escalated protests in Ashulia, Gazipur and Dhaka in late Oct–early Nov.",
  [W("2026 Bangladesh garment workers protests", "2026_Bangladesh_garment_workers_protests")]),
 ("IR","이란 반정부 시위와 유혈 진압","Iran: anti-government protests and crackdown","2025년 12월 28일~","Since 28 Dec 2025",
  "경제 위기로 200여 도시에 번진 1979년 이후 최대 규모 시위. 실탄 진압으로 수천 명이 숨졌다는 보고가 있다.","The largest uprising since 1979, spreading to 200+ cities over the economic crisis; live-fire crackdowns are reported to have killed thousands.",
  [W("2025–2026 Iranian protests", "2025%E2%80%932026_Iranian_protests")]),
 ("TR","튀르키예 야권 탄압 항의 시위","Türkiye: protests over arrests of opposition figures","2025년 3월~","Since Mar 2025",
  "이스탄불 시장 이마모을루 체포 이후 전국 시위가 이어지고 있다.","Nationwide protests continue since the arrest of Istanbul mayor İmamoğlu.",
  [W("2025–2026 Turkish protests", "2025%E2%80%932026_Turkish_protests")]),
 ("PK","파키스탄령 카슈미르 시위","Azad Kashmir (Pakistan) protests","2026년 6월 7일~","Since 7 Jun 2026",
  "의석 배분 등 38개 요구를 내건 시위·파업·충돌로 시위대와 경찰 사상자가 나왔다.","Protests, strikes and clashes over a 38-point charter including assembly seats; protesters and police have been killed and injured.",
  [W("2026 Azad Kashmir protests", "2026_Azad_Kashmir_protests")]),
 ("IN","인도 마니푸르 종족 분쟁","India: Manipur ethnic conflict","2023년 5월~","Since May 2023",
  "메이테이–쿠키족 충돌로 정부 집계 306명 사망, 6만 명 피란(2026년 9월 기준).","Meitei–Kuki clashes: 306 killed and 60,000 displaced by government count (Sept 2026).",
  [W("Manipur conflict (2023–present)", "Manipur_conflict_(2023%E2%80%93present)")]),
 ("CU","쿠바 생활고 시위","Cuba: protests over shortages","2024년 3월~","Since Mar 2024",
  "식량 부족과 정전에 항의하는 시위가 이어지고 있다.","Protests over food shortages and power cuts continue.",
  [W("2024–2026 Cuban protests", "2024%E2%80%932026_Cuban_protests")]),
 ("GB","영국 북아일랜드 폭동 (반이민)","UK: Northern Ireland riots (anti-immigrant)","2026년 6월","June 2026",
  "벨파스트에서 시작된 폭동이 스코틀랜드·잉글랜드 일부로 번졌고 이민자 거주 주택이 방화됐다.","Riots that began in Belfast spread to parts of Scotland and England; homes of immigrants were set alight.",
  [W("2026 Northern Ireland riots", "2026_Northern_Ireland_riots")]),
 ("RS","세르비아 반부패 시위 (10월 종료)","Serbia anti-corruption protests (ended in October)","2024년 11월~2026년 10월","Nov 2024–Oct 2026",
  "부치치 대통령이 사임하고 10월 25일 총선에서 학생 명단이 과반을 얻으면서 시위가 끝났다.","Ended after President Vučić resigned and the student list won a majority in the 25 Oct election.",
  [W("2024–2026 Serbian anti-corruption protests", "2024%E2%80%932026_Serbian_anti-corruption_protests")]),
]
C["unrest"] = {"asof": "2026-11-14",
  "note_ko": "폭동·대규모 시위는 위키백과 정리(3등급 출처)를 바탕으로 했습니다. 각 링크의 원문 각주로 확인하세요.",
  "note_en": "Riots and mass protests are based on Wikipedia summaries (tier-3 sources). Check the original footnotes behind each link.",
  "items": [dict(iso=u[0], ko=u[1], en=u[2], when_ko=u[3], when_en=u[4], text_ko=u[5], text_en=u[6], src=u[7]) for u in U]}

C["updated"] = "2026-11-15"
C["summary_ko"] = ("지금 진행 중인 큰 전쟁은 미국·이스라엘–이란 전쟁(2026년 2월 28일 시작), 러시아–우크라이나 전쟁, 수단·미얀마·예멘·사헬·콩고 내전입니다. "
  "사우디아라비아는 이란과 후티의 미사일·드론 공격을 받고 있고, 예멘에서는 9월부터 바브엘만데브 해협을 둘러싼 공방이 벌어지고 있습니다. "
  "9월에는 에티오피아 티그라이 전쟁이 다시 시작됐고, 파키스탄–아프가니스탄 국경 전쟁도 이어지고 있습니다. 유럽에서는 유가·생활비 시위가 폭동으로 번진 곳이 있습니다.")
C["summary_en"] = ("Major wars now under way: the US–Israel vs Iran war (from 28 Feb 2026), Russia–Ukraine, and civil wars in Sudan, Myanmar, Yemen, the Sahel and DR Congo. "
  "Saudi Arabia is under Iranian and Houthi missile and drone attack, and since September Yemen has seen fighting over the Bab al-Mandab Strait. "
  "The Tigray war in Ethiopia resumed in September, and the Pakistan–Afghanistan border war continues. In Europe, some fuel and cost-of-living protests have turned into riots.")
json.dump(C, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("hotspots", len(C["hotspots"]), [h["id"] for h in C["hotspots"]], "all", len(AL), "unrest", len(U), "sources", len(S))
