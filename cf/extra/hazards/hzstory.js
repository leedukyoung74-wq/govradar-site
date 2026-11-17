/* GOV RADAR — story and explainer for each moving hazard clip (click a clip to open).
   Korean and English; other languages show the English text (site policy). General guidance from official sources only.
   window.HZSTORY.open(kind, lang)   2026-11-17 */
(function () {
  var SK = "https://www.safekorea.go.kr/safekorea-kor/acts/nacts/action-guide.do?category=";
  var D = {
    flood: { ko: { s: "큰비가 짧은 시간에 쏟아지거나 며칠씩 이어지면 하천이 넘치고 배수가 막힌 낮은 땅부터 물이 찹니다. 물은 몇 분 만에 불어나 지하주차장·반지하·지하차도를 먼저 채웁니다. 물이 빠진 뒤에도 감전·오염·붕괴 위험이 남습니다.",
        p: ["호우특보·하천 수위 경보가 나옵니다", "배수구가 역류하고 도로에 물이 고입니다", "하천이 넘치고 저지대·지하 공간이 잠깁니다"], a: ["지하·저지대에서 미리 높은 곳으로 옮깁니다", "물에 잠긴 도로는 걷거나 차로 건너지 않습니다 — 흐르는 물 15cm에 어른이 넘어집니다", "물이 빠져도 당국이 안전을 확인할 때까지 들어가지 않습니다"] },
      en: { s: "When intense rain falls fast or lasts for days, rivers overflow and low ground with blocked drains floods first. Water can rise within minutes, filling underground car parks, basements and underpasses. After it recedes, electric shock, contamination and collapse remain risks.",
        p: ["Heavy-rain and river warnings are issued", "Drains back up and water pools on roads", "Rivers overtop and low or underground spaces flood"], a: ["Move from basements and low ground to higher places early", "Never walk or drive through flood water — 15 cm of fast water can knock an adult over", "Do not go back in until the authorities say it is safe"] },
      src: [["CDC — Flood safety", "https://www.cdc.gov/floods/safety/index.html"], ["NWS — Turn Around Don't Drown", "https://www.weather.gov/safety/flood-turn-around-dont-drown"], ["국민재난안전포털 — 호우", SK + "heavyRain&menuSn=1"]], r: "flood" },
    storm: { ko: { s: "따뜻한 바다 위에서 커진 열대성 저기압(태풍)은 강한 바람과 폭우, 바닷물이 밀려드는 해일을 함께 몰고 옵니다. 진로와 도달 시각은 예보로 미리 알 수 있어, 준비할 시간이 있는 재난입니다.",
        p: ["진로 예보와 태풍 특보가 나옵니다", "바람이 강해지고 비가 거세집니다", "해안에 높은 파도와 해일, 내륙에 홍수·산사태가 이어집니다"], a: ["진로와 도달 시각을 확인해 대피 계획을 세웁니다", "날아갈 물건을 치우고 창문을 보강합니다", "해안·하천·산간에서 미리 벗어납니다"] },
      en: { s: "A tropical cyclone (typhoon or hurricane) grows over warm sea and brings strong wind, heavy rain and storm surge together. Its track and arrival can be forecast, so there is time to prepare.",
        p: ["Track forecasts and storm warnings are issued", "Wind strengthens and rain intensifies", "High waves and surge on the coast; floods and landslides inland"], a: ["Check the track and timing and plan where to go", "Bring in loose objects and secure windows", "Leave coasts, riverbanks and slopes early"] },
      src: [["NOAA National Hurricane Center", "https://www.nhc.noaa.gov/"], ["NWS — Hurricane safety", "https://www.weather.gov/safety/hurricane"], ["국민재난안전포털 — 태풍", SK + "typhoon&menuSn=1"]], r: "flood" },
    quake: { ko: { s: "땅속 판의 경계가 갑자기 미끄러지면 지진파가 퍼져 땅이 흔들립니다. 예고 없이 오고, 큰 지진 뒤에는 여진이 이어집니다. 피해는 주로 무너지는 건물과 떨어지는 물건, 화재에서 생깁니다.",
        p: ["예고 없이 강한 흔들림이 시작됩니다", "가구가 넘어지고 물건이 떨어집니다", "여진이 며칠~몇 주 이어질 수 있습니다"], a: ["흔들리는 동안: 몸을 낮추고 머리를 보호하고 튼튼한 탁자를 잡습니다", "흔들림이 멈추면 가스·전기를 확인하고 계단으로 나갑니다", "평소에 무거운 가구를 고정합니다"] },
      en: { s: "When rock along a fault slips suddenly, seismic waves spread and the ground shakes. Quakes come without warning and big ones are followed by aftershocks. Most harm comes from falling buildings and objects, and fires.",
        p: ["Strong shaking starts without warning", "Furniture tips over and objects fall", "Aftershocks can continue for days or weeks"], a: ["During shaking: drop, cover your head and hold on", "After it stops, check gas and power and leave by the stairs", "Secure heavy furniture in advance"] },
      src: [["CDC — Earthquake safety", "https://www.cdc.gov/earthquakes/safety/index.html"], ["USGS — Latest earthquakes", "https://earthquake.usgs.gov/earthquakes/map/"]], r: "earthquake" },
    tsunami: { ko: { s: "바다 밑 큰 지진이나 화산, 해저 산사태가 바닷물 전체를 밀어 올리면 해일이 생깁니다. 먼 바다에서는 낮지만 해안에 가까워지며 높아지고, 여러 번 밀려옵니다. 첫 파도가 가장 크다는 보장은 없습니다.",
        p: ["해안에서 강하거나 긴 지진을 느낍니다", "바닷물이 갑자기 빠지거나 크게 불어납니다", "높은 물결이 여러 차례 밀려옵니다"], a: ["해안에서 강한 지진을 느끼면 경보를 기다리지 말고 높은 곳·내륙으로 갑니다", "바닷물이 빠지는 것을 구경하러 가지 않습니다", "해제될 때까지 해안으로 돌아오지 않습니다"] },
      en: { s: "A large undersea quake, eruption or landslide can lift the whole water column and create a tsunami. Low in deep water, it grows as it nears shore and comes in several waves; the first is not always the biggest.",
        p: ["A strong or long quake is felt at the coast", "The sea suddenly drains away or surges", "High waves arrive several times"], a: ["If you feel a strong quake at the coast, go to high ground or inland without waiting for an alert", "Never go to look at the receding sea", "Stay away until the all-clear"] },
      src: [["NOAA — During a tsunami", "https://www.weather.gov/safety/tsunami-during"], ["NOAA Tsunami Warning Centers", "https://www.tsunami.gov/"]], r: "tsunami" },
    landslide: { ko: { s: "비가 많이 오거나 땅이 흔들리면 비탈의 흙과 바위가 한꺼번에 쏟아집니다. 산불이 지나간 비탈과 깎아 만든 경사면이 특히 약합니다. 빠르게 내려와 피할 시간이 짧습니다.",
        p: ["비탈에서 물이 솟거나 흙탕물이 흐릅니다", "나무가 기울고 땅에 금이 갑니다", "돌 구르는 소리, 땅 울림이 들립니다"], a: ["큰비 예보 때 비탈 아래·계곡 주변에서 미리 벗어납니다", "징후가 보이면 흐름의 옆 방향으로 피합니다", "옹벽·축대에 금이 있으면 시·군·구청에 신고합니다"] },
      en: { s: "Heavy rain or shaking can send soil and rock down a slope at once. Slopes burned by wildfire and cut slopes are especially weak. Slides move fast and leave little time to escape.",
        p: ["Water springs out or muddy water runs from a slope", "Trees tilt and cracks open in the ground", "Rumbling or falling rocks are heard"], a: ["Leave the foot of slopes and valleys when heavy rain is forecast", "If you see signs, move sideways out of the path", "Report cracked retaining walls to the local authority"] },
      src: [["USGS — Landslide Hazards Program", "https://www.usgs.gov/programs/landslide-hazards"], ["국민재난안전포털 — 호우", SK + "heavyRain&menuSn=1"]], r: "flood" },
    wildfire: { ko: { s: "마르고 바람 부는 날 작은 불씨가 숲과 풀밭으로 번지면 산불이 됩니다. 불길은 바람을 타고 빠르게 움직이고, 연기는 수백 km 떨어진 곳의 공기까지 나쁘게 합니다.",
        p: ["건조·강풍 특보가 나옵니다", "연기와 재가 보이고 공기질이 나빠집니다", "대피 명령이 내려집니다"], a: ["대피 명령이 나오면 지정 경로로 일찍 떠납니다", "연기가 많으면 창문을 닫고 실내 공기를 걸러 냅니다", "숲 근처에서 불씨를 만들지 않습니다"] },
      en: { s: "On dry, windy days a small spark can spread through forest and grass. Fire moves fast with the wind, and smoke can foul the air hundreds of kilometres away.",
        p: ["Dry-weather and wind warnings are issued", "Smoke and ash appear and air quality drops", "Evacuation orders are given"], a: ["Leave early by the designated route when told to evacuate", "In heavy smoke, close windows and filter indoor air", "Never make sparks near forests"] },
      src: [["AirNow — Be smoke ready", "https://www.airnow.gov/wildfires/be-smoke-ready/"], ["NASA FIRMS — active fires", "https://firms.modaps.eosdis.nasa.gov/map/"]], r: "wildfire" },
    fire: { ko: { s: "건물 화재는 몇 분 만에 연기로 방을 채웁니다. 사람을 가장 많이 다치게 하는 것은 불길보다 유독한 연기입니다. 전기·난방·조리 기구가 흔한 원인입니다.",
        p: ["연기 감지기가 울리거나 탄 냄새가 납니다", "연기가 천장부터 아래로 내려옵니다", "불길과 열로 출구가 막힙니다"], a: ["불이야 외치고 119에 신고한 뒤 낮은 자세로 나갑니다", "문손잡이가 뜨거우면 열지 않고 다른 길을 찾습니다", "집에 연기 감지기와 소화기를 두고 대피로를 정해 둡니다"] },
      en: { s: "A building fire can fill rooms with smoke in minutes. Toxic smoke, more than flames, causes most injuries. Electrical, heating and cooking equipment are common causes.",
        p: ["The smoke alarm sounds or there is a burning smell", "Smoke fills the room from the ceiling down", "Heat and flames block exits"], a: ["Shout, call emergency services and get out low", "If a door handle is hot, do not open it; use another way", "Keep smoke alarms and an extinguisher, and agree an escape route"] },
      src: [["U.S. Fire Administration — Home fires", "https://www.usfa.fema.gov/prevention/home-fires/"]], r: "" },
    drought: { ko: { s: "비가 오랫동안 적게 오면 강과 저수지가 마르고 농사가 망가집니다. 천천히 오지만 오래 가며, 식량·물값과 생계에 큰 영향을 줍니다. 심하면 식량 위기와 이주로 이어집니다.",
        p: ["강수량이 평년보다 적은 날이 이어집니다", "저수지가 줄고 제한 급수가 시작됩니다", "작황이 나빠지고 식량값이 오릅니다"], a: ["물 절약과 비상 식수 비축을 미리 합니다", "제한 급수 일정과 급수 장소를 확인합니다", "식료품 재고를 돌려 쓰며 유지합니다"] },
      en: { s: "When rain stays low for a long time, rivers and reservoirs shrink and crops fail. Drought arrives slowly but lasts, raising food and water costs and hitting livelihoods; severe drought can lead to food crises and migration.",
        p: ["Rainfall stays below normal week after week", "Reservoirs fall and water is rationed", "Harvests fail and food prices rise"], a: ["Save water and keep an emergency supply", "Know rationing times and water points", "Keep a rotating food stock"] },
      src: [["FAO GIEWS — food security", "https://www.fao.org/giews/en/"], ["WFP — understanding famine", "https://www.wfp.org/stories/understanding-famine-what-it-how-you-can-act"]], r: "famine" },
    temp: { ko: { s: "평소보다 훨씬 덥거나 추운 날이 며칠씩 이어지는 현상입니다. 노인·어린이·만성질환자와 야외 노동자에게 특히 위험하고, 전력 수요가 몰려 정전이 겹치기도 합니다.",
        p: ["폭염·한파 특보가 나옵니다", "밤에도 기온이 내려가지 않거나(폭염) 영하가 계속됩니다(한파)", "온열·한랭 질환자가 늘어납니다"], a: ["야외 활동을 줄이고 취약한 이웃의 안부를 확인합니다", "더위엔 물을 자주, 추위엔 겹쳐 입고 실내 온도를 유지합니다", "정전에 대비해 조명과 물을 둡니다"] },
      en: { s: "Days of much hotter or colder weather than usual. Older people, children, people with chronic illness and outdoor workers are most at risk, and demand for power can cause outages at the same time.",
        p: ["Heat or cold warnings are issued", "Nights stay hot (heat) or temperatures stay below freezing (cold)", "Heat or cold illness rises"], a: ["Limit time outdoors and check on vulnerable neighbours", "In heat drink water often; in cold dress in layers and keep rooms warm", "Keep light and water ready for outages"] },
      src: [["NWS — Heat safety", "https://www.weather.gov/safety/heat"], ["CDC — Winter weather", "https://www.cdc.gov/winter-weather/prevention/index.html"]], r: "heat" },
    volcano: { ko: { s: "땅속 마그마가 올라오면 분화가 일어나 용암, 화산재, 화산가스가 나옵니다. 화산재는 바람을 타고 멀리 퍼져 호흡·교통·전기에 피해를 줍니다. 관측기관이 경보 단계를 발표합니다.",
        p: ["화산 경보 단계가 올라갑니다", "지진·가스 증가 등 이상 징후가 관측됩니다", "분화 후 화산재가 바람 방향으로 떨어집니다"], a: ["관측기관의 경보와 대피 구역을 따릅니다", "화산재가 내리면 실내에 머물고 인증된 마스크를 씁니다", "물과 음식을 덮어 재가 들어가지 않게 합니다"] },
      en: { s: "When magma rises, an eruption can release lava, ash and gas. Ash travels far on the wind and harms breathing, transport and power. Observatories issue alert levels.",
        p: ["The volcano alert level rises", "More quakes or gas are measured", "After an eruption, ash falls downwind"], a: ["Follow observatory alerts and evacuation zones", "In ashfall stay indoors and wear a certified mask", "Cover water and food against ash"] },
      src: [["USGS — Volcanic ash protection", "https://volcanoes.usgs.gov/volcanic_ash/personal_protection_equipment.html"], ["USGS — Prepare for volcanic activity", "https://www.usgs.gov/observatories/cvo/prepare-volcanic-activity"]], r: "volcano" },
    impact: { ko: { s: "지구 가까이 오는 소행성·혜성은 NASA 등 관측기관이 미리 찾아 궤도를 계산합니다. 대부분은 안전하게 지나가며, 지구 근접 소식이 곧 충돌 위험을 뜻하지는 않습니다. 큰 위험이 확인되면 공식 발표가 먼저 나옵니다.",
        p: ["관측기관이 새 천체를 발견해 궤도를 계산합니다", "근접 거리와 충돌 확률이 공개됩니다", "위험이 있으면 공식 기관이 발표합니다"], a: ["공식 기관(NASA·ESA) 발표만 믿습니다", "근거 없는 충돌 소문은 퍼뜨리지 않습니다", "일반 재난 준비(물·식량·연락)가 그대로 도움이 됩니다"] },
      en: { s: "Asteroids and comets that come near Earth are found early by observatories such as NASA's, which compute their orbits. Almost all pass safely; a 'close approach' does not mean an impact risk. Any real danger is announced officially first.",
        p: ["Observatories find a new object and compute its orbit", "Approach distance and impact probability are published", "Any risk is announced by the official agencies"], a: ["Trust only official agencies (NASA, ESA)", "Do not spread impact rumours", "General preparedness (water, food, contacts) still helps"] },
      src: [["NASA — Planetary defense", "https://science.nasa.gov/planetary-defense-overview/"], ["NASA CNEOS — close approaches", "https://cneos.jpl.nasa.gov/"]], r: "asteroid" },
    war: { ko: { s: "국가 간 무력 충돌은 공습·포격과 함께 교통·전기·통신·물자 공급을 끊습니다. 직접 피해 지역 밖에서도 물가·에너지·여행에 영향이 큽니다. 개인이 할 수 있는 일은 공식 경보를 따르고 대피·연락 계획을 세워 두는 것입니다.",
        p: ["긴장이 높아지고 여행 경보가 나옵니다", "공습 경보·민방위 경보가 발령됩니다", "교통·통신·공급이 끊기고 피란이 시작됩니다"], a: ["경보를 들으면 지정 대피소나 견고한 실내로 갑니다", "신분증·처방 등 서류 사본과 72시간 가방을 준비합니다", "가족 만남 장소와 다른 지역 연락인을 정합니다"] },
      en: { s: "Armed conflict between states brings air strikes and shelling and cuts transport, power, communications and supplies. Far beyond the front line it moves prices, energy and travel. What individuals can do is follow official alerts and have a shelter and contact plan.",
        p: ["Tension rises and travel advisories are issued", "Air-raid or civil-defence alerts sound", "Transport, communications and supplies break down; people flee"], a: ["On an alert, go to a designated shelter or solid indoor space", "Keep copies of ID and prescriptions and a 72-hour bag", "Agree meeting places and an out-of-area contact"] },
      src: [["국민재난안전포털 — 비상사태 행동요령", "https://www.safekorea.go.kr/safekorea-kor/acts/nacts/action-guide.do?category=stateOfEmergency&menuSn=4"], ["UN OCHA", "https://www.unocha.org/"]], r: "war" },
    ethnic: { ko: { s: "민족·종교·지역 집단 사이의 갈등이 폭력으로 번지는 경우입니다. 마을 단위 습격과 강제 이주가 일어나고, 오랜 기간 반복되기도 합니다. GOV RADAR는 국제 분쟁 감시기관이 확인한 사건만 다룹니다.",
        p: ["혐오 발언과 긴장이 높아집니다", "국지적 충돌·습격이 발생합니다", "주민이 피란하고 인도적 지원이 필요해집니다"], a: ["현지 당국과 자국 대사관 안내를 따릅니다", "확인되지 않은 소문과 영상을 퍼뜨리지 않습니다", "현지 출장·사업은 여행 경보를 먼저 확인합니다"] },
      en: { s: "Conflict between ethnic, religious or regional groups that turns violent, with attacks on communities and forced displacement, sometimes repeating over years. GOV RADAR shows only events confirmed by international conflict monitors.",
        p: ["Hate speech and tension rise", "Local clashes and attacks occur", "People are displaced and need humanitarian aid"], a: ["Follow local authorities and your embassy", "Do not share unverified rumours or videos", "Check travel advisories before trips or business there"] },
      src: [["ACLED — conflict data", "https://acleddata.com/"], ["UN OCHA", "https://www.unocha.org/"]], r: "" },
    protest: { ko: { s: "시민이 정책이나 정부에 반대해 모이는 집회입니다. 대부분 평화롭게 끝나지만, 큰 시위는 교통을 막고 때로 충돌로 번집니다. 사업·여행 일정에 영향을 줄 수 있습니다.",
        p: ["집회 일정과 장소가 알려집니다", "도심 교통이 통제됩니다", "일부 지역에서 경찰과 충돌이 생길 수 있습니다"], a: ["집회 장소와 시간을 피해 이동합니다", "현지 당국·대사관 안내를 확인합니다", "군중 사이에 머물지 않고 출구를 확인합니다"] },
      en: { s: "People gathering against a policy or government. Most protests end peacefully, but large ones block traffic and can turn into clashes, affecting business and travel plans.",
        p: ["Protest dates and places are announced", "City-centre traffic is restricted", "Clashes with police may occur in places"], a: ["Avoid protest sites and times", "Check local authority and embassy guidance", "Do not stay inside crowds; know the exits"] },
      src: [["ACLED — conflict data", "https://acleddata.com/"]], r: "" },
    riot: { ko: { s: "군중이 폭력이나 약탈로 번지는 혼란 상황입니다. 짧은 시간에 넓게 퍼지고, 통행금지나 통신 제한이 함께 내려지기도 합니다.",
        p: ["시위나 사건 뒤 긴장이 급격히 높아집니다", "방화·약탈이 생깁니다", "통행금지·통신 제한이 발령됩니다"], a: ["실내에 머물고 창가를 피합니다", "통행금지와 당국 지시를 따릅니다", "가족·회사와 연락 방법을 미리 정합니다"] },
      en: { s: "Unrest in which crowds turn to violence or looting. Riots can spread widely within hours and may bring curfews or communication limits.",
        p: ["Tension rises sharply after a protest or incident", "Arson and looting occur", "Curfews or communication limits are imposed"], a: ["Stay indoors and away from windows", "Follow curfews and official instructions", "Agree how to reach family and colleagues"] },
      src: [["ACLED — conflict data", "https://acleddata.com/"]], r: "" },
    epidemic: { ko: { s: "감염병이 평소보다 많은 사람에게 빠르게 퍼지는 상황입니다. 새로운 병원체뿐 아니라 알려진 병(콜레라·홍역 등)의 유행도 포함됩니다. WHO와 각국 보건당국이 확인한 소식이 기준입니다.",
        p: ["보건당국이 집단 발생을 알립니다", "환자가 늘고 지역 간 전파가 확인됩니다", "여행·모임 제한 같은 조치가 나올 수 있습니다"], a: ["손 씻기·기침 예절·필요 시 마스크를 지킵니다", "아프면 집에 머물고 의료기관 안내를 따릅니다", "공식 보건당국 정보만 확인합니다"] },
      en: { s: "An infectious disease spreading faster and to more people than usual — new pathogens as well as known diseases such as cholera or measles. GOV RADAR uses news confirmed by WHO and national health authorities.",
        p: ["Health authorities report an outbreak", "Cases rise and spread between areas", "Measures such as travel or gathering limits may follow"], a: ["Wash hands, cover coughs, wear a mask when advised", "Stay home when ill and follow medical advice", "Rely on official health authorities"] },
      src: [["WHO — Disease Outbreak News", "https://www.who.int/emergencies/disease-outbreak-news"], ["CDC — Respiratory virus prevention", "https://www.cdc.gov/respiratory-viruses/prevention/"]], r: "epidemic" },
    cyber: { ko: { s: "해킹·랜섬웨어·디도스 공격은 은행, 병원, 전기, 물류 같은 서비스를 멈출 수 있습니다. 실제 공격과 단순 장애를 구분하는 것이 중요합니다. GOV RADAR 사이버 공격 페이지에 사례와 준비 방법을 정리했습니다.",
        p: ["수상한 메일·문자, 접속 장애가 늘어납니다", "서비스가 멈추거나 자료가 잠깁니다", "기관이 침해 사실과 대응을 발표합니다"], a: ["중요 계정에 2단계 인증을 켜고 백업을 따로 둡니다", "출처를 모르는 링크·첨부파일을 열지 않습니다", "현금·종이 연락처 등 오프라인 대안을 준비합니다"] },
      en: { s: "Hacking, ransomware and DDoS attacks can stop banks, hospitals, power and logistics. Telling real attacks from plain outages matters. GOV RADAR's cyber page lists cases and how to prepare.",
        p: ["Suspicious mail and messages and outages increase", "Services stop or data is locked", "Organisations announce the breach and response"], a: ["Turn on two-step login for key accounts and keep a separate backup", "Do not open links or attachments from unknown senders", "Keep offline backups: some cash, paper contacts"] },
      src: [["KISA 보호나라", "https://www.boho.or.kr/"], ["GOV RADAR — Cyberattacks", "/cyber/"]], r: "" },
    heat: { ko: { s: "숨 막히는 더위가 며칠씩 이어지면 몸이 열을 식히지 못해 열사병 같은 온열질환이 생깁니다. 혼자 사는 어르신과 야외 노동자가 특히 위험합니다. 한국은 일 최고기온 33℃ 이상이 이틀 넘게 이어질 것으로 보이면 폭염주의보가 나옵니다.",
        p: ["폭염특보가 나옵니다", "밤에도 더위가 식지 않습니다", "어지러움·두통·근육경련 같은 증상이 나타납니다"], a: ["오후 2~5시 야외 활동을 피하고 물을 자주 마십니다", "혼자 사는 이웃·가족의 안부를 확인합니다", "의식이 흐려지면 바로 119에 연락합니다"] },
      en: { s: "When dangerous heat lasts for days the body cannot cool down, causing heat illness such as heatstroke. Older people living alone and outdoor workers are most at risk.",
        p: ["Heat warnings are issued", "Nights stay hot", "Dizziness, headache or cramps appear"], a: ["Avoid outdoor activity in the hottest hours and drink water often", "Check on neighbours and relatives who live alone", "If someone becomes confused or faint, call emergency services"] },
      src: [["국민재난안전포털 — 폭염", SK + "heatWave&menuSn=1"], ["NWS — Heat safety", "https://www.weather.gov/safety/heat"]], r: "heat" },
    cold: { ko: { s: "혹한과 폭설이 이어지면 저체온증·동상 위험이 커지고, 수도관이 얼고 길이 막힙니다. 난방 기구를 잘못 쓰면 일산화탄소 중독과 화재도 생깁니다.",
        p: ["한파·대설 특보가 나옵니다", "수도관 동파와 빙판길이 생깁니다", "떨림·말 어눌함 같은 저체온 증상이 나타날 수 있습니다"], a: ["외출을 줄이고 겹쳐 입습니다", "수도 계량기를 보온하고 난방 기구를 점검합니다", "발전기·숯·가스난로는 실내에서 쓰지 않습니다"] },
      en: { s: "Bitter cold and heavy snow raise the risk of hypothermia and frostbite, freeze pipes and block roads. Misused heaters can cause carbon monoxide poisoning and fires.",
        p: ["Cold-wave and heavy-snow warnings are issued", "Pipes freeze and roads ice over", "Shivering or slurred speech can signal hypothermia"], a: ["Go out less and dress in layers", "Insulate water meters and check heaters", "Never use generators, charcoal or gas heaters indoors"] },
      src: [["국민재난안전포털 — 한파", SK + "coldWave&menuSn=1"], ["CDC — Winter weather", "https://www.cdc.gov/winter-weather/prevention/index.html"]], r: "cold" },
    outage: { ko: { s: "폭풍·폭염·설비 고장·사이버 공격으로 전기가 길게 끊기면 조명, 냉장, 난방·냉방, 통신, 엘리베이터, 의료기기가 함께 멈춥니다. 정전 자체보다 그 뒤에 이어지는 문제가 더 위험할 수 있습니다.",
        p: ["넓은 지역의 불이 꺼집니다", "휴대폰 배터리와 통신이 약해집니다", "냉장 식품과 냉장 약이 상하기 시작합니다"], a: ["손전등·보조배터리·라디오를 준비합니다", "닫힌 냉장고는 약 4시간, 가득 찬 냉동고는 약 48시간이 기준입니다", "발전기는 바깥에서만, 창문과 떨어뜨려 씁니다"] },
      en: { s: "When storms, heat, equipment failure or cyberattacks cut power for a long time, lighting, refrigeration, heating and cooling, communications, lifts and medical devices stop together. What follows can be more dangerous than the outage itself.",
        p: ["Lights go out across a wide area", "Phone batteries and networks weaken", "Chilled food and refrigerated medicine start to spoil"], a: ["Keep torches, power banks and a radio", "A closed fridge keeps food about 4 hours, a full freezer about 48", "Run generators only outdoors, away from windows"] },
      src: [["CDC — Food safety after an emergency", "https://www.cdc.gov/food-safety/foods/keep-food-safe-after-emergency.html"], ["CDC — Safety after disasters", "https://www.cdc.gov/natural-disasters/response/index.html"]], r: "outage" },
    water: { ko: { s: "홍수, 하수 넘침, 화학물질 유출, 정수 설비 고장은 마시는 물을 오염시킵니다. 겉으로 깨끗해 보여도 세균이나 화학물질이 들어 있을 수 있어, 당국의 안내가 가장 중요합니다. 오염된 물은 설사병과 감염병 유행으로 이어질 수 있습니다.",
        p: ["수돗물 끓여 마시기·사용 중지 안내가 나옵니다", "물 색·냄새·맛이 달라집니다", "설사·구토 환자가 늘어날 수 있습니다"], a: ["당국의 '끓여 마시기·사용 중지' 안내를 그대로 따릅니다", "끓여 마시라는 안내가 있으면 팔팔 끓인 뒤 1분 이상 더 끓입니다", "평소 1인 하루 약 4L 기준으로 비상 식수를 둡니다"] },
      en: { s: "Floods, sewage overflows, chemical spills and treatment failures can contaminate drinking water. Water that looks clean can still carry germs or chemicals, so official advice matters most. Contaminated water can lead to diarrhoeal disease and outbreaks.",
        p: ["Boil-water or do-not-use notices are issued", "Water changes colour, smell or taste", "Diarrhoea and vomiting cases may rise"], a: ["Follow boil-water or do-not-use notices exactly", "When told to boil, bring water to a rolling boil for at least 1 minute", "Keep an emergency supply of about 4 L per person per day"] },
      src: [["CDC — Safe water in emergencies", "https://www.cdc.gov/water-emergency/about/"], ["WHO — Drinking-water fact sheet", "https://www.who.int/news-room/fact-sheets/detail/drinking-water"]], r: "calc" }
  };
  var UI = { ko: { st: "이렇게 진행됩니다", ac: "지금 할 일", sr: "공식 출처", rd: "재난 대비센터에서 준비하기 →", mp: "세계 지도에서 보기 →", cl: "닫기", note: "일반 안내입니다. 실제 행동은 거주지 당국의 경보와 지시를 따르세요." },
    en: { st: "How it unfolds", ac: "What to do", sr: "Official sources", rd: "Prepare in the preparedness centre →", mp: "See it on the world map →", cl: "Close", note: "General guidance. Always follow your local authority's alerts and instructions." } };
  var css = ".hzst-d{border:0;padding:0;border-radius:16px;max-width:760px;width:calc(100% - 24px);max-height:calc(100% - 24px);overflow:auto;font-family:'WMM Nexon','NEXON Lv1 Gothic','NEXON Lv1 Gothic OTF',sans-serif;color:#111;background:#fff;box-shadow:0 20px 60px rgba(0,0,0,.4)}" +
    ".hzst-d::backdrop{background:rgba(5,9,15,.72)}.hzst-d .hzc-v{aspect-ratio:16/8;border-radius:0}.hzst-b{padding:22px 26px 26px}.hzst-b h2{font-size:26px;margin:0 0 10px}.hzst-b h3{font-size:16px;margin:20px 0 8px}" +
    ".hzst-b p{line-height:1.7;margin:0}.hzst-b ol,.hzst-b ul{margin:0;padding-left:22px;line-height:1.7}.hzst-b .hzst-n{font-size:13px;color:#666;margin-top:16px}.hzst-l{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}" +
    ".hzst-l a{display:inline-block;padding:9px 14px;border-radius:999px;background:#0b1220;color:#fff;text-decoration:none;font-size:14px;font-weight:700}.hzst-l a.alt{background:#eef2f7;color:#0b1220}" +
    ".hzst-x{position:absolute;right:12px;top:12px;z-index:9;width:38px;height:38px;border-radius:50%;border:0;background:rgba(0,0,0,.6);color:#fff;font-size:20px;cursor:pointer}.hzst-src a{color:#1d4ed8}" +
    "[data-hzk]{cursor:pointer}@media(max-width:600px){.hzst-b{padding:18px}.hzst-b h2{font-size:22px}}";
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  var dlg;
  function open(k, lang) {
    var d = D[k]; if (!d) return; var ko = lang === "ko", c = ko ? d.ko : d.en, u = ko ? UI.ko : UI.en, X = window.HZFX, nm = X && (X.NM[lang] || X.NM.en)[k] || k;
    if (!dlg) { var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st); dlg = document.createElement("dialog"); dlg.className = "hzst-d"; document.body.appendChild(dlg);
      dlg.addEventListener("click", function (e) { if (e.target === dlg || e.target.closest(".hzst-x")) dlg.close(); }); }
    var L2 = lang === "ko" ? "ko" : (["en", "es", "fr", "ar", "vi", "id"].indexOf(lang) >= 0 ? lang : "en");
    var links = (d.r ? '<a href="/' + L2 + '/ready/' + (d.r === "calc" ? "#calc" : "#hz-" + d.r) + '">' + u.rd + "</a>" : "") + (k === "cyber" ? "" : '<a class="alt" href="/hazards/' + (lang === "ko" ? "" : "?l=" + lang) + '#map">' + u.mp + "</a>");
    dlg.innerHTML = '<button class="hzst-x" aria-label="' + u.cl + '">×</button><div style="position:relative"><figure class="hzc hz-' + k + '" style="margin:0"><div class="hzc-v v2"><i class="hzc-sw"></i><i class="hzc-rg"></i><canvas class="hzcv" data-k="' + k + '" aria-hidden="true"></canvas><span class="hzc-tag">' + esc(nm) + "</span></div></figure></div>" +
      '<div class="hzst-b" dir="' + (lang === "ar" && !ko ? "ltr" : "auto") + '"><h2>' + esc(nm) + "</h2><p>" + esc(c.s) + "</p><h3>" + u.st + "</h3><ol>" + c.p.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ol><h3>" + u.ac + "</h3><ul>" +
      c.a.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + '</ul><h3>' + u.sr + '</h3><ul class="hzst-src">' + d.src.map(function (s) { return '<li><a href="' + esc(s[1]) + '"' + (s[1].charAt(0) === "/" ? "" : ' target="_blank" rel="noopener"') + ">" + esc(s[0]) + "</a></li>"; }).join("") +
      '</ul><div class="hzst-l">' + links + '</div><p class="hzst-n">' + u.note + "</p></div>";
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
  }
  // any element with data-hzk="kind" opens its story; cards made by HZFX.card carry class hz-<kind>
  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-hzk]"); if (!el || e.target.closest("a,button:not([data-hzk])")) return;
    e.preventDefault(); open(el.getAttribute("data-hzk"), el.getAttribute("data-hzl") || document.documentElement.lang || "ko");
  });
  window.HZSTORY = { open: open, has: function (k) { return !!D[k]; } };
})();
