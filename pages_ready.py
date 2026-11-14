"""재난 대비센터 page renderer (/ko/ready/, /en/ready/; other languages get the English body with a note).
Everything personal (household, stock, contact card) stays in the visitor's browser (localStorage); nothing is sent
except the optional consultation form."""
import html
import ready_art as ART
import ready_content as RC

e = lambda s: html.escape(str(s), quote=True)
NOTE_OTHER = {"es": "Este centro está disponible por ahora en coreano e inglés; esta es la versión en inglés.",
              "fr": "Ce centre est pour l'instant disponible en coréen et en anglais ; voici la version anglaise.",
              "ar": "هذا المركز متاح حاليًا بالكورية والإنجليزية؛ هذه هي النسخة الإنجليزية.",
              "vi": "Trung tâm hiện có tiếng Hàn và tiếng Anh; đây là bản tiếng Anh.",
              "id": "Pusat ini sementara tersedia dalam bahasa Korea dan Inggris; ini versi bahasa Inggris."}

def body(L):
    ko = L == "ko"; t = (lambda k, en: k if ko else en)
    src = lambda ids: " ".join(f'<a class="ref" href="{e(RC.SRC[i][2])}" target="_blank" rel="noopener">[{i}] {e(RC.SRC[i][0] if ko else RC.SRC[i][1])}</a>' for i in ids)
    vid = f"/assets/ready-{'ko' if ko else 'en'}.mp4"
    nav = [("now", "지금 위험할 때", "If danger is now"), ("setup", "내 상황", "My situation"), ("plan", "맞춤 계획", "My plan"), ("calc", "준비량 계산", "Quantities"),
           ("stock", "재고·교체", "Stock & expiry"), ("card", "대피·연락카드", "Contact card"), ("hazards", "재난별 안내", "By hazard"), ("help", "상담 요청", "Get help")]
    out = []
    if L not in ("ko", "en"): out.append(f'<p class="rd-lang">{e(NOTE_OTHER.get(L, ""))}</p>')
    out.append(f'''<section class="rd-hero"><div class="rd-in rd-hero-g">
<div class="rd-hero-t"><p class="crumb"><a href="/{L}/">GOV RADAR</a> · <a href="/{L}/conflict/">{t("세계 상황판", "World watch")}</a></p>
<h1>{t("재난 대비센터", "Preparedness centre")}</h1>
<p class="rd-lede">{t("우리 집·우리 단체가 무엇을 준비하고, 얼마나 필요하며, 어디로 가고, 부족한 것은 어떻게 채우는지 한 곳에서 정리합니다. 공식기관 지침만 근거로 썼습니다.", "What to prepare, how much you need, where to go and how to fill the gaps — for your household or organisation, in one place. Built only on official guidance.")}</p>
<div class="rd-doors">
<a class="rd-door urgent" href="#now"><b>{t("지금 위험한 상황입니다", "I am in danger now")}</b><span>{t("재난별 즉시 행동과 공식 연락처", "Immediate actions and official contacts")}</span></a>
<a class="rd-door" href="#setup"><b>{t("우리 집을 미리 준비하고 싶습니다", "I want to prepare my home")}</b><span>{t("가족 맞춤 계획, 부족한 물품, 예산", "Family plan, shortages, budget")}</span></a>
<a class="rd-door" href="#org"><b>{t("우리 단체·시설을 준비하고 싶습니다", "I want to prepare my organisation")}</b><span>{t("회사·학교·교회·복지시설·기관", "Companies, schools, churches, care facilities, public bodies")}</span></a>
</div></div>
<div class="rd-hero-a">{ART.hero()}</div></div></section>''')
    out.append(f'<nav class="rd-nav" aria-label="{t("대비센터 화면", "Centre sections")}"><div class="rd-in">' + "".join(f'<a href="#{a}">{e(k if ko else n)}</a>' for a, k, n in nav) + '</div></nav>')
    # video
    out.append(f'''<section class="rd-sec rd-video"><div class="rd-in rd-two">
<div><h2>{t("30초로 보는 준비 순서", "The order of preparation in 30 seconds")}</h2>
<p>{t("오늘 30분이면 시작할 수 있습니다. 연락카드와 대피처 확인부터, 3일 가방, 14일·30일 비축, 60·90일·1년 점검까지 순서대로 늘려 갑니다.", "You can start today in 30 minutes: contact card and shelters first, then a 3-day bag, 14- and 30-day stock, and 60/90-day and yearly checks.")}</p>
<p class="note">{t("WMM이 직접 만든 안내 영상입니다. 공식기관 영상은", "An explainer made by WMM. Official agency videos:")} <a href="https://www.ready.gov/videos" target="_blank" rel="noopener">Ready.gov (FEMA)</a> · <a href="https://www.safekorea.go.kr" target="_blank" rel="noopener">{t("국민재난안전포털", "Korea Safety Portal")}</a></p></div>
<video controls muted playsinline preload="metadata" poster="/assets/ready-poster-{'ko' if ko else 'en'}.jpg"><source src="{vid}" type="video/mp4"></video></div></section>''')
    # NOW
    rows = "".join(f'<tr><th>{e(s[0] if ko else s[1])}</th><td>{e(d[0] if ko else d[1])}</td><td class="rd-avoid">{e(a[0] if ko else a[1])}</td><td class="rd-src">{src(ids)}</td></tr>' for s, d, a, ids in RC.NOW)
    out.append(f'''<section class="rd-sec rd-now" id="now"><div class="rd-in">
<h2>{t("지금 위험할 때 먼저 할 일", "What to do first when danger is now")}</h2>
<p class="rd-alert">{t("이 페이지는 실시간 경보가 아닙니다. 지금 위험하면 거주지 당국의 경보와 대피 지시를 먼저 따르세요. 한국: 화재·구조·응급 119, 범죄 112, 재난문자와", "This page is not a live alert. If you are in danger, follow your local authority's alerts and evacuation orders first. In Korea: fire, rescue and ambulance 119, police 112, and")} <a href="https://www.safekorea.go.kr" target="_blank" rel="noopener">{t("국민재난안전포털", "the Korea Safety Portal")}</a>{t(". 다른 나라는 그 나라 공식 재난기관 안내를 따르세요.", ". In other countries, follow that country's official disaster agency.")}</p>
<div class="rd-tw"><table class="rd-t"><thead><tr><th>{t("상황", "Situation")}</th><th>{t("먼저 할 행동", "Do first")}</th><th>{t("피해야 할 판단", "Avoid")}</th><th>{t("근거", "Source")}</th></tr></thead><tbody>{rows}</tbody></table></div>
<p><a class="rd-link" href="/{L}/conflict/">{t("지금 세계에서 확인된 전쟁·재해·감염병 보기 →", "See confirmed wars, disasters and outbreaks worldwide →")}</a></p></div></section>''')
    # SETUP
    fld = lambda k, lab, typ="number", v="", extra="": f'<label>{e(lab)}<input data-k="{k}" type="{typ}" value="{v}" {extra}></label>'
    out.append(f'''<section class="rd-sec rd-alt" id="setup"><div class="rd-in">
<h2>{t("내 상황 설정", "My situation")}</h2>
<p>{t("입력한 내용은 이 브라우저에만 저장되고 서버로 보내지 않습니다. 건강 정보는 적지 않아도 계획을 만들 수 있습니다.", "What you enter stays in this browser and is never sent to a server. You can build a plan without any health details.")}</p>
<form class="rd-form" id="rd-setup" onsubmit="return false">
<div class="rd-g3">{fld("region", t("나라·도시", "Country and city"), "text", "", 'placeholder="' + t("예: 대한민국 서울", "e.g. Seoul, Korea") + '"')}
<label>{t("주거 형태", "Home type")}<select data-k="home"><option value="apt">{t("아파트·고층", "Apartment, high-rise")}</option><option value="house">{t("단독·저층", "House, low-rise")}</option><option value="other">{t("기타", "Other")}</option></select></label>
<label>{t("주변 위험 (해당 시 선택)", "Nearby risks (if any)")}<select data-k="risk"><option value="">{t("모름·해당 없음", "Unknown / none")}</option><option value="coast">{t("해안 가까움", "Near the coast")}</option><option value="forest">{t("산림 가까움", "Near forest")}</option><option value="river">{t("하천·침수 지역", "River, flood area")}</option><option value="volcano">{t("화산 지역", "Volcanic area")}</option></select></label></div>
<div class="rd-g4">{fld("adults", t("성인", "Adults"), v="2", extra='min="0"')}{fld("kids", t("어린이", "Children"), v="0", extra='min="0"')}{fld("infants", t("영아", "Infants"), v="0", extra='min="0"')}{fld("seniors", t("고령자·돌봄 필요", "Older / needs care"), v="0", extra='min="0"')}</div>
<div class="rd-g4">{fld("pets", t("반려동물", "Pets"), v="0", extra='min="0"')}
<label>{t("목표 기간", "Target period")}<select data-k="days"><option>30</option><option>60</option><option>90</option><option value="365">365</option></select></label>
{fld("budget", t("이번 달 준비 예산(원)" , "This month's budget"), v="100000", extra='min="0" step="10000"')}
{fld("check", t("마지막 점검일", "Last check"), "date")}</div>
<p class="rd-actions"><a class="rd-btn" href="#plan">{t("내 계획 보기", "See my plan")}</a></p>
</form></div></section>''')
    # PLAN (status + timeline + periods)
    tl = "".join(f'<li><label><input type="checkbox" data-tl="{i}"><span class="rd-when">{e(w if ko else we)}</span><span class="rd-task">{e(tk if ko else te)}<small>{t("완료 증거: ", "Proof: ")}{e(pk if ko else pe)}</small></span></label></li>' for i, (w, we, tk, te, pk, pe) in enumerate(RC.TL))
    per = [("30", "30일 기본 준비", "30-day basics", "아직 아무 준비가 없을 때: 이동 가방, 가정 재고, 가족 연락·대피, 우선 구매와 예산", "Starting from zero: go-bag, home stock, family contact and evacuation, first purchases and budget"),
           ("60", "60일 공급 중단 대비", "60-day supply disruption", "다시 구하기 어려울 때: 대체 급수·식품 공급, 처방 지속, 임시 숙소, 돌봄·생활비", "When resupply is hard: backup water and food sources, steady prescriptions, temporary lodging, care and living costs"),
           ("90", "90일 생활 유지", "90-day continuity", "단절이 길어질 때: 재고 순환, 영양·위생, 진료·교육·근무, 전원·통신 대안", "When disruption lasts: stock rotation, nutrition and hygiene, care, school and work, power and contact options"),
           ("365", "1년 지속 관리", "1-year upkeep", "사놓고 잊지 않으려면: 계절별 점검, 교체 일정, 가족 변화 반영, 훈련, 연간 예산·복구계획", "So nothing is forgotten: seasonal checks, replacement dates, family changes, drills, yearly budget and recovery plan")]
    pcards = "".join(f'<div class="rd-per" data-per="{d}"><b>{e(a if ko else b)}</b><p>{e(c if ko else dd)}</p></div>' for d, a, b, c, dd in per)
    out.append(f'''<section class="rd-sec" id="plan"><div class="rd-in">
<div class="rd-head"><h2>{t("내 준비현황과 맞춤 계획", "My status and plan")}</h2><button class="rd-btn ghost" onclick="window.print()">{t("인쇄 / PDF 저장", "Print / save PDF")}</button></div>
<div class="rd-status" id="rd-status">
<div><span>{t("오늘 먼저 할 일", "Do first today")}</span><b id="st-todo">—</b></div>
<div><span>{t("부족한 물품", "Short on")}</span><b id="st-short">—</b></div>
<div><span>{t("이번 달 예산", "This month's budget")}</span><b id="st-budget">—</b></div>
<div><span>{t("연락·대피계획", "Contact & evacuation plan")}</span><b id="st-card">—</b></div>
<div><span>{t("다음 점검일", "Next check")}</span><b id="st-next">—</b></div></div>
<p class="note">{t("완료율은 준비 항목을 기록한 비율일 뿐, 생존 확률이나 안전 점수가 아닙니다.", "Progress shows only what you have recorded. It is not a survival or safety score.")}</p>
<h3>{t("오늘부터 1년까지 준비 일정", "From today to one year")}</h3><ol class="rd-tl">{tl}</ol>
<h3>{t("기간별로 달라지는 준비", "What changes by period")}</h3><div class="rd-pers">{pcards}</div>
<p class="note">{t("한국 비상대비 안내는 30일분 식량·식수와 2~3일분 이동용 생존배낭을 안내합니다. 60·90일·1년 일정은 WMM의 계획 예시이며, 오래 고립되라는 뜻이 아닙니다.", "Korea's guidance suggests 30 days of food and water and a 2–3 day go-bag. The 60/90-day and 1-year steps are WMM planning examples, not advice to isolate.")} {src([1, 3])}</p>
</div></section>''')
    # CALC + go-bag
    out.append(f'''<section class="rd-sec rd-alt" id="calc"><div class="rd-in">
<h2>{t("준비량·부족량 계산", "Quantities and shortfalls")}</h2>
<div class="rd-two">
<form class="rd-form" onsubmit="return false">
<div class="rd-g2">{fld("lpd", t("1인 하루 물(L)", "Water per person per day (L)"), v="4", extra='step="0.5" min="0"')}{fld("kcal", t("1인 하루 열량(kcal)", "Calories per person per day"), v="2100", extra='step="50" min="0"')}</div>
<div class="rd-g2">{fld("haveW", t("지금 있는 안전한 물(L)", "Safe water you have (L)"), v="0", extra='min="0"')}{fld("haveK", t("지금 있는 보관식 열량(kcal)", "Stored food you have (kcal)"), v="0", extra='min="0" step="1000"')}</div>
<p class="note">{t("물 4L는 CDC 최소 기준(1인 1일 약 3.8L)을 계산하기 쉽게 올린 값입니다. 목욕·세탁·더위·질환·반려동물 수요는 포함하지 않습니다. 2,100kcal는 성인 예시이며 영양 처방이 아닙니다. 영아는 성인 배수로 계산하지 마세요.", "4 L rounds up CDC's minimum (about 3.8 L per person per day). It excludes bathing, laundry, heat, illness and pets. 2,100 kcal is an adult example, not a prescription. Do not scale infants from adults.")} {src([3])}</p>
</form>
<div class="rd-tw"><table class="rd-t rd-calc"><thead><tr><th></th><th>30</th><th>60</th><th>90</th><th>365</th></tr></thead><tbody id="rd-calc"></tbody></table>
<p class="note" id="rd-weight"></p></div></div>
<h3>{t("전원 계산", "Power needs")}</h3>
<div class="rd-two"><div><table class="rd-t" id="rd-pw"><thead><tr><th>{t("기기", "Device")}</th><th>W</th><th>{t("하루 사용 시간", "Hours per day")}</th><th></th></tr></thead><tbody></tbody></table>
<p><button class="rd-btn ghost" id="pw-add" type="button">{t("기기 추가", "Add device")}</button></p></div>
<div><p class="rd-big" id="pw-out">—</p><p class="note">{t("필요 전력량(Wh) = 소비전력(W) × 사용시간(h). 배터리 변환 손실을 감안해 사용 가능 비율 80%로 나눈 예시이며 제품 보증값이 아닙니다. 의료기기는 제조사·의료진과 따로 확인하세요. 발전기는 실외에서 건물로부터 약 6m 이상 떨어뜨립니다.", "Wh = watts × hours. Divided by 80% usable capacity as an example, not a product rating. Check medical devices with the maker and clinician. Run generators outdoors, about 6 m from buildings.")} {src([18])}</p></div></div>
<div class="rd-bag"><div class="rd-bag-a">{ART.gobag()}</div><div><h3>{t("집 비축과 따로 챙기는 이동 가방", "The go-bag, separate from home stock")}</h3>
<p>{t("성인 1명 기준의 시작 예시입니다. 무게는 실제로 들고 10~20분 걸어본 뒤 정하세요. 약·물·신분증·연락수단이 먼저입니다.", "A starting example for one adult. Decide the weight after walking 10–20 minutes with it. Medicine, water, ID and a way to communicate come first.")}</p>
<ul class="rd-check">{"".join(f'<li><label><input type="checkbox" data-bag="{i}"> {e(a if ko else b)}</label></li>' for i, (a, b) in enumerate(RC.BAG))}</ul>
<p class="note">{src([2, 6, 23])} · <a href="/{L}/prepare/">{t("실제 제품 구성은 가정 비축 키트에서 →", "Product examples in the home stockpile kit →")}</a></p></div></div>
</div></section>''')
    # STOCK
    out.append(f'''<section class="rd-sec" id="stock"><div class="rd-in">
<div class="rd-head"><h2>{t("내 재고와 교체 일정", "My stock and replacement dates")}</h2><button class="rd-btn ghost" id="st-csv" type="button">{t("CSV로 내려받기", "Download CSV")}</button></div>
<p>{t("기한이 빠른 순서로 보입니다. 30일 안에 교체할 물품은 강조됩니다. 남은 사용일수가 '조달에 걸리는 날 + 여유일' 이하가 되면 보충하세요.", "Sorted by expiry; items due within 30 days are highlighted. Restock when days of use left fall to 'days to resupply + buffer days'.")}</p>
<form class="rd-form rd-stock-f" id="st-f" onsubmit="return false"><div class="rd-g6">
<label>{t("물품", "Item")}<input name="n" required></label><label>{t("수량", "Qty")}<input name="q" type="number" min="0" value="1"></label><label>{t("단가", "Unit price")}<input name="p" type="number" min="0" value="0"></label>
<label>{t("기한", "Expiry")}<input name="x" type="date"></label><label>{t("보관 위치", "Location")}<input name="w"></label><label>&nbsp;<button class="rd-btn" type="submit">{t("추가", "Add")}</button></label></div></form>
<div class="rd-tw"><table class="rd-t"><thead><tr><th>{t("물품", "Item")}</th><th>{t("수량", "Qty")}</th><th>{t("금액", "Amount")}</th><th>{t("기한", "Expiry")}</th><th>{t("위치", "Location")}</th><th></th></tr></thead><tbody id="st-body"></tbody></table></div>
<p class="note">{t("정전된 냉장고는 문을 닫아 두면 약 4시간, 가득 찬 냉동고는 48시간, 절반은 24시간이 기준입니다. 직접 받은 물은 6개월마다 바꿉니다.", "A closed fridge keeps food about 4 hours in an outage; a full freezer 48 hours, half-full 24. Replace self-stored water every 6 months.")} {src([3, 5])}</p>
</div></section>''')
    # CARD
    cf = lambda k, lab: f'<label>{e(lab)}<input data-c="{k}"></label>'
    out.append(f'''<section class="rd-sec rd-alt" id="card"><div class="rd-in rd-two">
<div><h2>{t("가족 대피·연락카드", "Family evacuation and contact card")}</h2>
<p>{t("통신이 끊겨도 쓸 수 있게 종이로 출력해 가방과 지갑에 넣으세요. 아이 카드에는 꼭 필요한 연락처만 적습니다.", "Print it so it works without a network; keep copies in bags and wallets. Children's cards should hold only the contacts they need.")}</p>
<form class="rd-form" onsubmit="return false">{cf("family", t("가족 이름(성)", "Family name"))}{cf("near", t("가까운 만남 장소", "Nearby meeting place"))}{cf("far", t("먼 만남 장소", "Distant meeting place"))}{cf("shelter", t("대피소 / 높은 곳", "Shelter / high ground"))}{cf("out", t("다른 지역 연락인 (이름·연락처)", "Out-of-area contact (name, number)"))}{cf("care", t("아이 인계·돌봄 대리인", "Child pick-up / care backup"))}{cf("med", t("꼭 필요한 약·의료 메모", "Essential medicine / medical note"))}</form></div>
<div class="rd-cardp" id="rd-cardp"><p class="rd-card-h">{t("비상 연락카드", "Emergency contact card")}</p><dl id="rd-cardl"></dl><p class="rd-card-f">{t("한국 119 · 112 · 공식 경보 우선", "Official alerts first · Korea 119 / 112")}</p>
<button class="rd-btn ghost" type="button" onclick="document.body.classList.add('print-card');window.print();document.body.classList.remove('print-card')">{t("카드만 인쇄", "Print card only")}</button></div>
</div></section>''')
    # HAZARDS
    tabs = "".join(f'<button role="tab" data-hz="{h[0]}"{" class=on" if i == 0 else ""}>{e(h[1] if ko else h[2])}</button>' for i, h in enumerate(RC.HZ))
    panes = ""
    for i, (hid, nk, ne, ik, ie, ak, ae, pk, pe, ck, ce, ids) in enumerate(RC.HZ):
        plan = "".join(f'<tr><th>{p}</th><td>{e(x)}</td></tr>' for p, x in zip([t("30일", "30 days"), t("60일", "60 days"), t("90일", "90 days"), t("1년", "1 year")], pk if ko else pe))
        panes += f'''<article class="rd-hz" data-hz="{hid}"{"" if i == 0 else " hidden"}><div class="rd-hz-a">{ART.scene(hid)}</div><div class="rd-hz-t"><h3>{e(nk if ko else ne)}</h3><p class="rd-lede2">{e(ik if ko else ie)}</p>
<ul class="rd-check">{"".join(f'<li><label><input type="checkbox" data-hzc="{hid}-{j}"> {e(x)}</label></li>' for j, x in enumerate(ak if ko else ae))}</ul>
<table class="rd-t rd-mini">{plan}</table><p class="rd-caution">{e(ck if ko else ce)}</p><p class="note">{src(ids)}</p></div></article>'''
    out.append(f'''<section class="rd-sec" id="hazards"><div class="rd-in">
<h2>{t("재난별 행동과 준비", "Actions and preparation by hazard")}</h2>
<div class="rd-tabs" role="tablist">{tabs}</div>{panes}
<p class="note">{t("영아·고령자·장애·만성질환·반려동물은 개인별 준비가 따로 필요합니다. 처방약 여분과 냉장약 보관, 전기의료기기 예비전원은 의료진과 상의하세요.", "Infants, older people, disability, chronic illness and pets need individual plans. Discuss spare prescriptions, cold-chain medicines and backup power for medical devices with a clinician.")} {src([6, 7, 8])}</p>
</div></section>''')
    # ORG
    orows = "".join(f'<tr><th>{e(a if ko else b)}</th><td>{e(c if ko else d)}</td></tr>' for a, b, c, d in RC.ORG)
    out.append(f'''<section class="rd-sec rd-dark" id="org"><div class="rd-in rd-two">
<div><h2>{t("단체·시설은 인원수만 곱해서 준비하지 않습니다", "Organisations need more than personal plans multiplied")}</h2>
<p>{t("방문객, 교대근무, 이동 약자, 건물 구조 때문에 역할 분담·인계 절차·훈련 기록이 따로 필요합니다. WMM이 현황 진단부터 계획서·교육 자료·훈련 운영까지 함께 만듭니다.", "Visitors, shifts, people with limited mobility and building layout call for roles, hand-over steps and drill records. WMM builds them with you, from assessment to plan, training materials and drills.")}</p>
<p><a class="rd-btn light" href="#help" data-prod="org">{t("기관 서비스 견적 받기", "Request a quote")}</a></p>
<p class="note">{t("공식 경보 발령이나 자원 배분 기능은 관련 권한과 협약이 있을 때만 다룹니다. 처음에는 공개 정보·준비·교육·업무 관리 범위로 진행합니다.", "Issuing official alerts or allocating resources requires authority and agreements; we start with public information, preparation, training and task management.")}</p></div>
<table class="rd-t rd-org">{orows}</table></div></section>''')
    # HELP (consultation form -> existing Netlify 'order' form fields)
    out.append(f'''<section class="rd-sec" id="help"><div class="rd-in rd-two">
<div><h2>{t("혼자 준비하기 어렵다면", "If preparing alone is hard")}</h2>
<p>{t("상담을 신청하면 요청 내용을 확인해 1영업일 안에 이메일로 답변 일정과 범위를 알려드립니다. 긴급 상황에는 이 양식 대신 119·112와 현지 당국에 연락하세요.", "Send a request and we reply by email within one business day with scope and timing. In an emergency, call local emergency services instead of using this form.")}</p>
<ul class="rd-free"><li><b>{t("누구나 무료", "Free for everyone")}</b> {t("즉시 행동, 공식기관 연결, 계산기, 재고표, 연락카드, 인쇄", "Immediate actions, official links, calculators, stock sheet, contact card, printing")}</li>
<li><b>{t("한국 회원 (준비 중)", "Korean members (coming)")}</b> {t("가족 공유, 교체 알림, 한국 주거·지역 맞춤 상세 계획, 상담", "Family sharing, replacement reminders, detailed plans for Korean homes and regions, consultation")}</li>
<li><b>{t("단체·기관", "Organisations")}</b> {t("여러 시설·인원 관리, 역할 배정, 교육·훈련, 기관용 보고서 — 견적 후 진행", "Multiple sites and staff, roles, training and drills, reports — by quote")}</li></ul>
<p class="note">{t("긴급 대피·응급 행동과 공식 경보는 결제 뒤에 숨기지 않습니다.", "Emergency actions and official alerts are never behind a paywall.")}</p></div>
<form class="cform rd-form" name="order" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/thanks/"><input type="hidden" name="form-name" value="order"><p hidden><input name="hp"></p><input type="hidden" name="lang" value="{L}">
<label>{t("상담 종류", "Request type")}<select name="product" id="rd-prod"><option value="재난대비 상담 (개인·가족)">{t("개인·가족 준비 상담", "Household preparedness consultation")}</option><option value="재난대비 기관 서비스 견적">{t("단체·기관 서비스 견적", "Organisation service quote")}</option></select></label>
<div class="rd-g2"><label>{t("이름", "Name")}<input name="name" required></label><label>{t("이메일", "Email")}<input name="email" type="email" required></label></div>
<div class="rd-g2"><label>{t("단체·기관명 (개인은 비워 두세요)", "Organisation (leave blank if personal)")}<input name="org"></label><label>{t("나라·지역", "Country / region")}<input name="countries" required></label></div>
<label>{t("대상 (예: 4인 가족, 초등학교 300명, 요양시설)", "Who (e.g. family of 4, school of 300, care home)")}<input name="field"></label>
<label>{t("도움이 필요한 내용 (건강 정보는 적지 마세요)", "What you need (please do not include health details)")}<textarea name="need" rows="4" maxlength="2000"></textarea></label>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> <span>{f'<a href="/{L}/legal/privacy/" target="_blank">개인정보 처리방침</a>에 동의합니다 (필수)' if ko else f'I agree to the <a href="/{L}/legal/privacy/" target="_blank">Privacy Policy</a> (required)'}</span></label>
<p class="note">{t("만 19세 미만은 상담 신청 없이 자료만 볼 수 있습니다.", "Under-19s may read the materials but not submit requests.")}</p>
<button class="rd-btn" type="submit">{t("상담 신청 보내기", "Send request")}</button></form></div></section>''')
    # SOURCES
    out.append(f'''<section class="rd-sec rd-alt" id="sources"><div class="rd-in">
<h2>{t("공식 출처와 적용 범위", "Official sources and scope")}</h2>
<p>{t("조사 기준 2026년 11월 14일. 해외 자료는 일반 준비의 근거이며, 실제 행동은 거주지 당국 지침과 맞는지 확인하세요. 수량 예시·확장 일정·계산기·화면 구성은 WMM의 설계이며 공식기관이 승인한 서비스나 개인 의료 판단이 아닙니다. 그림은 WMM이 직접 그린 일러스트입니다.", "Checked on 14 November 2026. Foreign sources support general preparation; always check against your local authority. Quantity examples, extended schedules, calculators and layout are WMM's design, not an officially endorsed service or medical advice. Illustrations are original WMM artwork.")}</p>
<ol class="rd-srcl">{"".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(k if ko else n)}</a></li>' for i, (k, n, u) in sorted(RC.SRC.items()))}</ol></div></section>''')
    return "\n".join(out) + JS.replace("__L__", L)

JS = r'''<script>(function(){
var L="__L__",ko=L==="ko",S=function(k,v){try{if(v===undefined)return JSON.parse(localStorage.getItem("gvr_"+k)||"null");localStorage.setItem("gvr_"+k,JSON.stringify(v))}catch(e){return null}};
var $=function(s,r){return(r||document).querySelector(s)},$$=function(s,r){return[].slice.call((r||document).querySelectorAll(s))};
var fmt=function(n){return Math.round(n).toLocaleString(ko?"ko-KR":"en-US")};
var T=function(k,e){return ko?k:e};
/* setup + calc fields */
var st=S("setup")||{};$$("[data-k]").forEach(function(i){if(st[i.dataset.k]!=null)i.value=st[i.dataset.k];i.addEventListener("input",function(){st[i.dataset.k]=i.value;S("setup",st);calc();status()})});
function num(k,d){var v=parseFloat(st[k]);if(isNaN(v)){var el=$('[data-k="'+k+'"]');v=el?parseFloat(el.value):NaN}return isNaN(v)?d:v}
function people(){return num("adults",2)+num("kids",0)+num("seniors",0)}
function calc(){var p=people(),l=num("lpd",4),k=num("kcal",2100),hw=num("haveW",0),hk=num("haveK",0),D=[30,60,90,365],r="";
r+="<tr><th>"+T("물 총수요(L)","Water needed (L)")+"</th>"+D.map(function(d){return"<td>"+fmt(p*l*d)+"</td>"}).join("")+"</tr>";
r+="<tr><th>"+T("물 부족(L)","Water short (L)")+"</th>"+D.map(function(d){var s=p*l*d-hw;return"<td class='"+(s>0?"rd-neg":"")+"'>"+(s>0?fmt(s):"0")+"</td>"}).join("")+"</tr>";
r+="<tr><th>"+T("열량 총수요(kcal)","Calories needed")+"</th>"+D.map(function(d){return"<td>"+fmt(p*k*d)+"</td>"}).join("")+"</tr>";
r+="<tr><th>"+T("열량 부족(kcal)","Calories short")+"</th>"+D.map(function(d){var s=p*k*d-hk;return"<td class='"+(s>0?"rd-neg":"")+"'>"+(s>0?fmt(s):"0")+"</td>"}).join("")+"</tr>";
r+="<tr><th>"+T("끼니(하루 3끼)","Meals (3 a day)")+"</th>"+D.map(function(d){return"<td>"+fmt(p*3*d)+"</td>"}).join("")+"</tr>";
var b=$("#rd-calc");if(b)b.innerHTML=r;var w=$("#rd-weight");if(w)w.textContent=T("1년 물 계산값은 "+fmt(p*l*365)+"L, 무게만 약 "+(p*l*365/1000).toFixed(1)+"톤입니다. 한곳에 쌓기보다 초기 3~14일분과 검증된 급수·운반·보충 경로를 함께 확보하세요.","One year of water is "+fmt(p*l*365)+" L, about "+(p*l*365/1000).toFixed(1)+" tonnes. Rather than storing it all, keep 3–14 days at home plus verified ways to get and carry more.");}
/* power */
var pw=S("pw")||[{n:T("조명","Light"),w:5,h:4},{n:T("휴대폰 충전","Phone charging"),w:10,h:3}];
function pwr(){var b=$("#rd-pw tbody");if(!b)return;b.innerHTML=pw.map(function(x,i){return"<tr><td><input data-pi='"+i+"' data-f='n' value='"+String(x.n).replace(/'/g,"&#39;")+"'></td><td><input type='number' min='0' data-pi='"+i+"' data-f='w' value='"+x.w+"'></td><td><input type='number' min='0' step='0.5' data-pi='"+i+"' data-f='h' value='"+x.h+"'></td><td><button type='button' data-pd='"+i+"'>×</button></td></tr>"}).join("");
var wh=pw.reduce(function(a,x){return a+(parseFloat(x.w)||0)*(parseFloat(x.h)||0)},0),d=parseFloat($('[data-k="days"]')&&$('[data-k="days"]').value)||30;
$("#pw-out").innerHTML=T("하루 ","Per day ")+fmt(wh)+" Wh · "+T("배터리 예시 ","battery example ")+fmt(wh/0.8)+" Wh<br><small>"+T("3일이면 약 ","3 days ≈ ")+fmt(wh*3/0.8)+" Wh</small>";S("pw",pw)}
document.addEventListener("input",function(ev){var t=ev.target;if(t.dataset&&t.dataset.pi!=null){pw[+t.dataset.pi][t.dataset.f]=t.value;var wh=pw.reduce(function(a,x){return a+(parseFloat(x.w)||0)*(parseFloat(x.h)||0)},0);$("#pw-out").innerHTML=T("하루 ","Per day ")+fmt(wh)+" Wh · "+T("배터리 예시 ","battery example ")+fmt(wh/0.8)+" Wh<br><small>"+T("3일이면 약 ","3 days ≈ ")+fmt(wh*3/0.8)+" Wh</small>";S("pw",pw)}});
document.addEventListener("click",function(ev){var t=ev.target;if(t.dataset&&t.dataset.pd!=null){pw.splice(+t.dataset.pd,1);pwr()}if(t.dataset&&t.dataset.sd!=null){stk.splice(+t.dataset.sd,1);S("stock",stk);stock();status()}if(t.dataset&&t.dataset.prod==="org"){var s=$("#rd-prod");if(s)s.selectedIndex=1}});
var pa=$("#pw-add");if(pa)pa.addEventListener("click",function(){pw.push({n:T("기기","Device"),w:0,h:1});pwr()});
/* checkboxes */
var ck=S("checks")||{};$$('input[type=checkbox][data-tl],input[type=checkbox][data-bag],input[type=checkbox][data-hzc]').forEach(function(c){var k=c.dataset.tl!=null?"tl"+c.dataset.tl:c.dataset.bag!=null?"bag"+c.dataset.bag:"hz"+c.dataset.hzc;c.checked=!!ck[k];c.addEventListener("change",function(){ck[k]=c.checked;S("checks",ck);status()})});
/* stock */
var stk=S("stock")||[];function dleft(x){if(!x)return 1e9;var t=new Date();t.setHours(0,0,0,0);return Math.round((new Date(x+"T00:00:00")-t)/864e5)}
function stock(){stk.sort(function(a,b){return(a.x||"9999")<(b.x||"9999")?-1:1});var b=$("#st-body");if(!b)return;b.innerHTML=stk.length?stk.map(function(x,i){var d=dleft(x.x);return"<tr class='"+(d<=30?"rd-soon":"")+"'><td>"+esc(x.n)+"</td><td>"+fmt(x.q||0)+"</td><td>"+fmt((x.q||0)*(x.p||0))+"</td><td>"+(x.x||"—")+(d<=30&&x.x?" <small>("+(d<0?T("지남","past"):"D-"+d)+")</small>":"")+"</td><td>"+esc(x.w||"")+"</td><td><button type='button' data-sd='"+i+"'>×</button></td></tr>"}).join(""):"<tr><td colspan='6' class='note'>"+T("아직 등록한 물품이 없습니다.","No items yet.")+"</td></tr>"}
function esc(s){return String(s||"").replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
var sf=$("#st-f");if(sf)sf.addEventListener("submit",function(){var f=new FormData(sf);stk.push({n:f.get("n"),q:+f.get("q")||0,p:+f.get("p")||0,x:f.get("x")||"",w:f.get("w")||""});S("stock",stk);sf.reset();stock();status()});
var sc=$("#st-csv");if(sc)sc.addEventListener("click",function(){var c="﻿"+[T("물품,수량,단가,기한,위치","item,qty,unit_price,expiry,location")].concat(stk.map(function(x){return[x.n,x.q,x.p,x.x,x.w].map(function(v){return'"'+String(v==null?"":v).replace(/"/g,'""')+'"'}).join(",")})).join("\n");var a=document.createElement("a");a.href=URL.createObjectURL(new Blob([c],{type:"text/csv"}));a.download="stock.csv";a.click()});
/* card */
var cd=S("card")||{},CL={family:T("가족","Family"),near:T("가까운 만남 장소","Nearby meeting place"),far:T("먼 만남 장소","Distant meeting place"),shelter:T("대피소·높은 곳","Shelter / high ground"),out:T("다른 지역 연락인","Out-of-area contact"),care:T("아이 인계·돌봄","Child pick-up / care"),med:T("약·의료","Medicine / medical")};
function card(){var l=$("#rd-cardl");if(!l)return;l.innerHTML=Object.keys(CL).map(function(k){return"<dt>"+CL[k]+"</dt><dd>"+(esc(cd[k])||"<span class='note'>—</span>")+"</dd>"}).join("")}
$$("[data-c]").forEach(function(i){i.value=cd[i.dataset.c]||"";i.addEventListener("input",function(){cd[i.dataset.c]=i.value;S("card",cd);card();status()})});
/* status */
function status(){var i,todo=null;for(i=0;i<9;i++){if(!ck["tl"+i]){todo=$$(".rd-tl li")[i];break}}
$("#st-todo").textContent=todo?todo.querySelector(".rd-task").firstChild.textContent:T("일정 완료 — 계절 점검을 이어가세요","Schedule done — keep seasonal checks");
var p=people(),d=num("days",30),sw=p*num("lpd",4)*d-num("haveW",0),sk=p*num("kcal",2100)*d-num("haveK",0),sh=[];if(sw>0)sh.push(T("물 ","water ")+fmt(sw)+"L");if(sk>0)sh.push(T("식량 ","food ")+fmt(sk)+"kcal");
$("#st-short").textContent=sh.length?sh.join(" · ")+" ("+d+T("일 기준",  "-day target")+")":T("목표 기간 기준 부족 없음","Nothing short for the target period");
var used=stk.reduce(function(a,x){return a+(x.q||0)*(x.p||0)},0),bud=num("budget",0);$("#st-budget").textContent=fmt(bud)+(ko?"원":"")+T(" 중 기록 "," · recorded ")+fmt(used)+(ko?"원":"");
var filled=["near","shelter","out"].filter(function(k){return cd[k]}).length;$("#st-card").textContent=filled===3?T("작성 완료 — 인쇄해 두세요","Done — print it"):T("미작성 항목 ","Missing ")+(3-filled)+T("개 (만남 장소·대피소·다른 지역 연락인)"," (meeting place, shelter, out-of-area contact)");
var exp=stk.filter(function(x){return x.x}).map(function(x){return x.x}).sort()[0],lc=st.check,nx=null;if(lc){var t=new Date(lc+"T00:00:00");t.setMonth(t.getMonth()+1);nx=t.toISOString().slice(0,10)}var c=[exp,nx].filter(Boolean).sort()[0];
$("#st-next").textContent=c?c+(c===exp?T(" (기한 임박 물품)"," (item expiring)"):T(" (월간 점검)"," (monthly check)")):T("마지막 점검일을 넣어 주세요","Add your last check date");
$$(".rd-per").forEach(function(x){x.classList.toggle("on",x.dataset.per==String(d))})}
/* hazard tabs */
$$(".rd-tabs button").forEach(function(b){b.addEventListener("click",function(){$$(".rd-tabs button").forEach(function(x){x.classList.toggle("on",x===b)});$$(".rd-hz").forEach(function(a){a.hidden=a.dataset.hz!==b.dataset.hz})})});
var hz=(location.hash.match(/^#hz-(\w+)/)||[])[1];if(hz){var tb=$('.rd-tabs button[data-hz="'+hz+'"]');if(tb){tb.click();document.getElementById("hazards").scrollIntoView()}}
calc();pwr();stock();card();status();
})();</script>'''

CSS = r'''
/* ---- preparedness centre ---- */
.rd-in{max-width:1180px;margin:0 auto;padding:0 24px}
.rd-lang{background:#f3efe6;margin:0;padding:10px 24px;font-size:14px}
.rd-hero{background:#1d2b4f;color:#fff}
.rd-hero-g{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:40px;align-items:center;padding-top:40px;padding-bottom:0}
.rd-hero .crumb a{color:#c9d3e3}
.rd-hero h1{font-size:clamp(34px,5vw,56px);font-weight:700;line-height:1.15;margin:12px 0 16px;color:#fff}
.rd-lede{font-size:18px;line-height:1.65;color:#e9edf5;font-weight:400;max-width:34em}
.rd-doors{display:grid;gap:10px;margin:26px 0 40px}
.rd-door{display:block;background:#26375f;color:#fff;text-decoration:none;padding:16px 18px;border-radius:6px}
.rd-door b{display:block;font-size:18px;font-weight:700}.rd-door span{display:block;font-size:14px;color:#c9d3e3;margin-top:2px;font-weight:300}
.rd-door:hover{background:#2f4372}.rd-door.urgent{background:#e4572e}.rd-door.urgent span{color:#fff}.rd-door.urgent:hover{background:#cf4720}
.rd-hero-a{align-self:end;line-height:0}.rd-hero-a svg{width:100%;height:auto;display:block}
.rd-nav{position:sticky;top:0;z-index:20;background:#fff;box-shadow:0 1px 0 #e3e6ec}
.rd-nav .rd-in{display:flex;gap:4px;overflow-x:auto;padding-top:8px;padding-bottom:8px;scrollbar-width:none}
.rd-nav a{white-space:nowrap;padding:8px 12px;border-radius:6px;color:#1d2b4f;text-decoration:none;font-size:15px}.rd-nav a:hover{background:#f0f2f6}
.rd-sec{padding:88px 0}.rd-alt{background:#f3efe6}.rd-dark{background:#1d2b4f;color:#fff}.rd-dark .note{color:#c9d3e3}
.rd-sec h2{font-size:clamp(26px,3.2vw,36px);font-weight:700;line-height:1.25;margin:0 0 14px;color:inherit}
.rd-sec h3{font-size:21px;font-weight:700;margin:40px 0 12px}
.rd-sec p{font-size:17px;line-height:1.7}
.rd-two{display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:start}
.rd-video video{width:100%;border-radius:6px;background:#0f1a33;display:block;aspect-ratio:16/9}
.rd-alert{background:#fff4ef;border-left:4px solid #e4572e;padding:14px 16px;font-size:16px}
.rd-tw{overflow-x:auto}
.rd-t{width:100%;border-collapse:collapse;font-size:15px;background:#fff}
.rd-t th,.rd-t td{padding:12px 12px;text-align:left;vertical-align:top;border-bottom:1px solid #edf0f4}
.rd-t thead th{background:#1d2b4f;color:#fff;font-weight:700}
.rd-t tbody th{font-weight:700;color:#1d2b4f;width:22%}
.rd-avoid{color:#8a2a12}.rd-src{font-size:13px}.rd-src a,.rd-sec .ref{color:#3a5a9a;font-size:13px;margin-right:6px}
.rd-link{font-weight:700;color:#1d2b4f}
.rd-form label{display:block;font-size:14px;font-weight:700;color:#1d2b4f;margin:0 0 12px}
.rd-form input,.rd-form select,.rd-form textarea{display:block;width:100%;margin-top:6px;padding:10px 12px;border:1px solid #c9d3e3;border-radius:6px;font-size:16px;background:#fff;font-weight:400;box-sizing:border-box}
.rd-g2,.rd-g3,.rd-g4,.rd-g6{display:grid;gap:14px}.rd-g2{grid-template-columns:repeat(2,1fr)}.rd-g3{grid-template-columns:repeat(3,1fr)}.rd-g4{grid-template-columns:repeat(4,1fr)}.rd-g6{grid-template-columns:2fr 1fr 1fr 1.3fr 1.3fr auto;align-items:end}
.rd-btn{display:inline-block;background:#e4572e;color:#fff;border:0;border-radius:6px;padding:12px 20px;font-size:16px;font-weight:700;text-decoration:none;cursor:pointer}
.rd-btn.ghost{background:#fff;color:#1d2b4f;box-shadow:inset 0 0 0 2px #1d2b4f}.rd-btn.light{background:#fff;color:#1d2b4f}
.rd-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.rd-status{display:grid;grid-template-columns:repeat(5,1fr);gap:2px;background:#1d2b4f;border-radius:8px;overflow:hidden;margin:18px 0 8px}
.rd-status div{background:#1d2b4f;color:#fff;padding:18px 16px}.rd-status div:nth-child(odd){background:#22335c}
.rd-status span{display:block;font-size:13px;color:#c9d3e3;font-weight:300}.rd-status b{display:block;font-size:16px;line-height:1.45;margin-top:6px}
.rd-tl{list-style:none;padding:0;margin:0}.rd-tl li{border-bottom:1px solid #edf0f4}
.rd-tl label{display:grid;grid-template-columns:28px 110px 1fr;gap:12px;padding:14px 4px;cursor:pointer;align-items:start}
.rd-tl input{width:20px;height:20px;margin-top:3px}.rd-when{font-weight:700;color:#e4572e}.rd-task{font-size:16px;line-height:1.55}.rd-task small{display:block;color:#5b6577;font-size:13px;margin-top:2px}
.rd-tl input:checked~.rd-task{color:#8a93a3;text-decoration:line-through}
.rd-pers{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.rd-per{background:#f3efe6;padding:18px;border-radius:6px}.rd-per b{font-size:17px}.rd-per p{font-size:15px;margin:8px 0 0}
.rd-per.on{background:#1d2b4f;color:#fff}
.rd-calc td{text-align:right;font-variant-numeric:tabular-nums}.rd-calc thead th{text-align:right}.rd-calc thead th:first-child{text-align:left}.rd-neg{color:#c62828;font-weight:700}
#rd-pw input{width:100%;padding:6px 8px;border:1px solid #c9d3e3;border-radius:4px;font-size:15px;box-sizing:border-box}#rd-pw button,#st-body button{border:0;background:none;font-size:20px;cursor:pointer;color:#8a2a12}
.rd-big{font-size:28px;font-weight:700;color:#1d2b4f;line-height:1.3}
.rd-bag{display:grid;grid-template-columns:5fr 6fr;gap:40px;align-items:center;margin-top:56px}.rd-bag-a svg{width:100%;height:auto;border-radius:8px;display:block}
.rd-check{list-style:none;padding:0;margin:12px 0}.rd-check li{padding:7px 0;font-size:16px;line-height:1.5}.rd-check input{width:18px;height:18px;margin-right:8px;vertical-align:-3px}
.rd-soon td{background:#fff4ef}.rd-soon td:first-child{box-shadow:inset 3px 0 0 #e4572e}
.rd-cardp{background:#fff;border-radius:8px;padding:24px;box-shadow:0 6px 24px rgba(15,26,51,.12)}
.rd-card-h{font-size:20px;font-weight:700;color:#1d2b4f;margin:0 0 12px}.rd-cardp dl{display:grid;grid-template-columns:140px 1fr;gap:8px 12px;margin:0 0 14px}.rd-cardp dt{font-weight:700;color:#5b6577;font-size:14px}.rd-cardp dd{margin:0;font-size:16px}
.rd-card-f{font-size:13px;color:#8a2a12;margin:0 0 14px}
.rd-tabs{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 24px}.rd-tabs button{border:0;background:#f0f2f6;color:#1d2b4f;padding:10px 14px;border-radius:6px;font-size:15px;cursor:pointer;font-weight:400}
.rd-tabs button.on{background:#1d2b4f;color:#fff;font-weight:700}
.rd-hz{display:grid;grid-template-columns:6fr 5fr;gap:40px;align-items:start}.rd-hz-a svg{width:100%;height:auto;border-radius:8px;display:block}
.rd-hz h3{margin-top:0;font-size:26px}.rd-lede2{font-size:17px}.rd-mini th{width:80px}.rd-caution{background:#fff4ef;padding:12px 14px;font-size:15px!important;border-left:4px solid #e4572e}
.rd-org th{width:34%}.rd-dark .rd-t{background:#22335c;color:#fff}.rd-dark .rd-t th,.rd-dark .rd-t td{border-color:#2f4372}.rd-dark .rd-t tbody th{color:#fff}
.rd-free{list-style:none;padding:0}.rd-free li{padding:10px 0;font-size:16px;line-height:1.55;border-bottom:1px solid #edf0f4}.rd-free b{display:block}
.rd-srcl{columns:2;font-size:14px;line-height:1.9;padding-left:20px}.rd-srcl a{color:#1d2b4f}
@media (max-width:900px){.rd-hero-g,.rd-two,.rd-bag,.rd-hz{grid-template-columns:1fr}.rd-hero-g{gap:8px}.rd-status{grid-template-columns:1fr 1fr}.rd-pers{grid-template-columns:1fr 1fr}.rd-g3,.rd-g4{grid-template-columns:1fr 1fr}.rd-g6{grid-template-columns:1fr 1fr}.rd-srcl{columns:1}.rd-sec{padding:64px 0}}
@media (max-width:560px){.rd-in{padding:0 16px}.rd-status,.rd-pers,.rd-g2,.rd-g3,.rd-g4{grid-template-columns:1fr}.rd-tl label{grid-template-columns:24px 1fr}.rd-when{grid-column:2}.rd-task{grid-column:2}.rd-cardp dl{grid-template-columns:1fr}.rd-t{font-size:14px}}
@media print{header,footer,.rd-nav,.rd-hero,.rd-video,#setup,#calc,#stock form,#hazards,#org,#help,#sources,.prepbar,.rd-btn,#now{display:none!important}.rd-sec{padding:16px 0}body.print-card main>*:not(#card){display:none!important}body.print-card #card form,body.print-card #card .rd-two>div:first-child{display:none!important}}
'''
