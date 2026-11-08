# New public pages (2026-10-31): legal, consortium hub, project lab, contracts.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
CO = dict(name_ko="월드메이킹멤버스 주식회사", name_en="WORLD MAKING MEMBERS Co., Ltd.", ceo_ko="대표이사 이덕영", ceo_en="CEO Lee Duk-young",
          brn="589-88-01039", mail_order="제2024-서울서초-2185호", email="73036396@naver.com", web="https://www.wmm-hoa.com", site="https://radar.wmm-hoa.com")
UPDATED = "2026-10-31"

def co_block(ko=True):
    if ko:
        return (f'<div class="coinfo"><b>{CO["name_ko"]}</b> · {CO["ceo_ko"]} · 사업자등록번호 {CO["brn"]} · 통신판매업신고 {CO["mail_order"]} · '
                f'이메일 {CO["email"]} · <a href="https://www.ftc.go.kr/bizCommPop.do?wrkr_no=5898801039" target="_blank" rel="noopener">사업자정보확인</a></div>')
    return (f'<div class="coinfo"><b>{CO["name_en"]}</b> · {CO["ceo_en"]} · Business reg. {CO["brn"]} · Mail-order business reg. No. 2024-Seoul Seocho-2185 · '
            f'Email {CO["email"]}</div>')

# ---------------------------------------------------------------- legal
LEGAL = {
 "terms": {
  "ko": ("이용약관", [
   ("제1조 (목적)", "이 약관은 월드메이킹멤버스 주식회사(이하 '회사')가 운영하는 GOV RADAR(radar.wmm-hoa.com, 이하 '서비스')의 이용 조건과 회사·회원의 권리와 의무를 정합니다."),
   ("제2조 (서비스 내용)", "서비스는 각국 정부의 정책·사업·입찰·국제기구 조달·위험 정보를 공개 자료에서 모아 요약·분류해 제공하고, 회원에게 알림, AI 분석, 컨소시엄 연결, 온라인 문서 지원을 제공합니다. 서비스는 정보 제공 서비스이며 투자·법률·세무·안보 자문이 아닙니다."),
   ("제3조 (회원가입)", "만 14세 이상은 이메일로 가입할 수 있습니다. 만 14세 미만은 법정대리인의 동의를 받아 별도로 신청해야 합니다. 허위 정보로 가입하거나 타인의 정보를 쓰면 이용이 제한될 수 있습니다."),
   ("제4조 (요금과 결제)", "무료(FREE)와 유료 서비스(분석 회원, 국가 진출 브리프, 입찰 적합도 검토, 프로젝트 파트너십, 기관·대학 라이선스)가 있으며 가격은 주문·요금 페이지에 표시합니다. 현재 유료 서비스는 견적서에 따라 계좌이체로 미리 내는 이용권이며 자동으로 갱신되지 않습니다. 온라인 정기결제를 열 때는 결제 화면에 금액·결제 주기·다음 결제일·해지 방법을 표시하고 따로 동의를 받습니다. 가격을 바꿀 때는 30일 전에 알립니다."),
   ("제5조 (청약철회와 환불)", "환불은 별도 '환불 정책'과 전자상거래 등에서의 소비자보호에 관한 법률을 따릅니다."),
   ("제6조 (정보의 정확성)", "회사는 공개 자료를 교차검증하고 항목마다 판정과 출처를 표시합니다. 다만 원 자료의 변경·오류, AI 요약의 한계로 일부 내용이 실제와 다를 수 있습니다. 입찰 참여, 계약, 투자, 여행 등 중요한 결정 전에는 반드시 원문(발주처 공고·정부 발표)을 확인해야 합니다."),
   ("제7조 (가정 시나리오)", "서비스의 '대비 시나리오'는 위기 대비를 위한 가정이며 예측이나 사실 확인이 아닙니다."),
   ("제8조 (회원의 의무)", "회원은 서비스 자료를 법령에 맞게 사용해야 하며, 자료를 무단 대량 수집하거나 재판매하거나, 제재 대상과의 거래 등 불법 목적에 쓰면 안 됩니다."),
   ("제8조의2 (자격 진술과 회수)", "회원은 연령·소속 등 자격을 사실대로 밝혀야 합니다. 허위로 밝혀 혜택을 받은 경우 회사는 혜택을 중단하고 정상가와의 차액을 청구하며 계정을 정지할 수 있습니다. 회사는 필요하면 자격을 다시 확인할 수 있습니다."),
   ("제8조의3 (만 19세 미만 회원)", "만 19세 미만 회원은 열람과 무보수 학습 기능만 이용합니다. 결제, 유료 작업, 컨소시엄 등록, 계약 요청, 다른 회원과의 연락 기능은 이용할 수 없습니다. 학습 과제 결과물은 회사의 고객 납품에 쓰지 않습니다."),
   ("제8조의4 (검증원·전문가 작업)", "유료 작업은 만 19세 이상(거주국의 성년 연령이 더 높으면 그 연령 이상)이며, 실력 확인 과제를 통과하고 지급 전 본인 확인을 마친 사람과 결과물 단위의 업무위탁 계약으로 진행합니다. 근무 시간은 지정하지 않으며, 보수는 미리 정한 결과물 단가로 검수 승인 후 지급합니다."),
   ("제9조 (컨소시엄·연결)", "회사는 참여자 사이의 연결과 온라인 협의를 지원합니다. 참여자 사이의 계약은 당사자가 직접 체결하며, 회사는 별도 계약이 없는 한 그 이행을 보증하지 않습니다. 컨소시엄 관심 등록은 법적 구속력이 없는 협력 의향 표시이며, 기관명은 검증과 서면 동의 후에만 공개합니다."),
   ("제10조 (지식재산)", "서비스의 편집물·디자인·소프트웨어의 권리는 회사에 있습니다. 출처 원문의 권리는 각 원저작자에게 있으며 서비스는 짧은 요약과 링크만 제공합니다."),
   ("제11조 (책임의 제한)", "회사는 고의 또는 중대한 과실이 없는 한, 서비스 정보를 이용해 내린 결정으로 생긴 손해에 책임지지 않습니다. 천재지변·통신 장애·외부 사이트 변경으로 인한 서비스 중단도 같습니다."),
   ("제12조 (분쟁 해결)", "분쟁은 먼저 이메일(73036396@naver.com)로 협의합니다. 소송은 대한민국 법을 따르며 민사소송법상 관할 법원에 제기합니다."),
   ("부칙", f"이 약관은 {UPDATED}부터 적용합니다.")]),
  "en": ("Terms of Service", [
   ("1. Purpose", "These terms govern use of GOV RADAR (radar.wmm-hoa.com, the 'Service') operated by WORLD MAKING MEMBERS Co., Ltd. (the 'Company')."),
   ("2. What the Service is", "The Service collects and summarises public information on government policy, projects, tenders, multilateral procurement and risk, and offers members alerts, AI analysis, consortium matching and online document support. It is an information service, not investment, legal, tax or security advice."),
   ("3. Accounts", "Anyone 14 or older may register by email. Under-14s need a parent's consent and apply separately. False or third-party details may lead to suspension."),
   ("4. Fees", "There is a free tier (FREE) and paid services (analysis membership, market-entry briefs, tender fit reviews, project partnerships, institutional and university licences), priced on the Orders & pricing page. Paid services are currently prepaid by bank transfer against a quote and do not renew automatically. When online subscriptions open, the checkout will show the amount, billing cycle, next charge date and how to cancel, and ask for separate consent. Price changes are notified 30 days ahead."),
   ("5. Refunds", "See the separate Refund Policy, which follows Korean consumer-protection law for e-commerce."),
   ("6. Accuracy", "We cross-check public sources and show a verdict and sources for each item, but source changes, errors and AI limitations mean some content may differ from reality. Always check the original notice or government statement before bidding, contracting, investing or travelling."),
   ("7. Scenarios", "'Preparedness scenarios' are hypotheses for planning; they are neither predictions nor verified facts."),
   ("8. Your obligations", "Use the Service lawfully. Do not bulk-scrape, resell, or use it for unlawful purposes such as dealing with sanctioned parties."),
   ("8a. Eligibility statements", "State your age and affiliation truthfully. Benefits obtained by false statements may be stopped, the price difference charged and the account suspended. We may re-verify eligibility."),
   ("8b. Members under 19", "Members under 19 may read and use unpaid learning features only: no payments, paid work, consortium registration, contract requests or member-to-member contact. Learning outputs are never used in client deliverables."),
   ("8c. Verifiers and experts", "Paid work is open to people aged 19+ (or the age of majority where they live, if higher) who pass a skills task and identity check before payout, under deliverable-based service contracts. No working hours are set; fees are fixed per deliverable and paid after acceptance."),
   ("9. Consortium and introductions", "We facilitate introductions and online discussion. Contracts between participants are made directly between them; unless agreed in writing we do not guarantee performance. Consortium registration is a non-binding expression of interest; organisation names are shown only after verification and written consent."),
   ("10. Intellectual property", "Our compilation, design and software belong to the Company. Source content belongs to its owners; we provide short summaries and links only."),
   ("11. Limitation of liability", "Except for intent or gross negligence, we are not liable for decisions made using the Service, or for interruptions caused by force majeure, network failures or third-party sites."),
   ("12. Disputes", "Contact 73036396@naver.com first. Korean law applies; courts with jurisdiction under the Korean Civil Procedure Act."),
   ("Effective", f"From {UPDATED}. The Korean version prevails in case of conflict.")]),
 },
 "privacy": {
  "ko": ("개인정보 처리방침", [
   ("1. 수집 항목", "필수: 이메일, 비밀번호(암호화 저장), 연령대, 약관 동의 일시. 선택: 이름·기관명, 회사 정보(업종·매출 구간·업력·인증), 알림 수단(이메일), 광고성 정보 수신 동의. 컨소시엄·문의 양식: 이름, 기관, 직함, 이메일, 국가, 관심 분야."),
   ("2. 이용 목적", "회원 식별과 로그인, 멤버십 제공, 맞춤 알림, 컨소시엄 연결과 온라인 협의, 문의 응대, 부정 이용 방지, 법령상 의무 이행."),
   ("3. 보유 기간", "회원 탈퇴 시 지체 없이 파기합니다. 다만 전자상거래법에 따라 계약·청약철회 기록 5년, 대금결제·재화 공급 기록 5년, 소비자 불만·분쟁 처리 기록 3년, 통신비밀보호법에 따른 접속 기록 3개월은 보관합니다."),
   ("4. 제3자 제공", "법령에 근거가 있거나 이용자가 동의한 경우 외에는 제3자에게 제공하지 않습니다. 컨소시엄 연결은 양측이 동의한 범위의 정보만 상대방에게 전달합니다."),
   ("5. 처리 위탁과 국외 이전", "회원 인증·웹 호스팅·양식 저장: Netlify, Inc.(미국) — 서비스 이용 시 암호화 통신으로 전송, 회원 탈퇴 또는 위탁 종료 시까지 보관. 결제 대행(도입 시): 국내 전자결제대행사. 이전을 원하지 않으면 가입하지 않거나 탈퇴할 수 있으나 이 경우 회원 기능을 쓸 수 없습니다."),
   ("6. 만 14세 미만", "만 14세 미만 아동의 개인정보는 법정대리인 동의를 받은 경우에만 처리합니다."),
   ("7. 이용자의 권리", "언제든 열람·정정·삭제·처리정지·동의 철회를 요청할 수 있습니다. '내 정보'에서 직접 고치거나 73036396@naver.com으로 요청하면 10일 안에 처리합니다."),
   ("8. 안전성 확보 조치", "비밀번호 암호화, 전송 구간 암호화(HTTPS), 접근 권한 최소화, 접속 기록 보관."),
   ("9. 쿠키와 저장소", "로그인 유지를 위해 브라우저 저장소에 인증 토큰을 저장합니다. 광고 추적 쿠키는 쓰지 않습니다."),
   ("10. 개인정보 보호책임자", "월드메이킹멤버스 주식회사 대표이사 이덕영 · 73036396@naver.com. 침해 신고: 개인정보침해신고센터(privacy.kisa.or.kr, 118), 개인정보분쟁조정위원회(kopico.go.kr)."),
   ("시행일", f"{UPDATED}")]),
  "en": ("Privacy Policy", [
   ("1. What we collect", "Required: email, password (stored hashed), age group, time of consent. Optional: name or organisation, company details, alert channels (email, mobile for KakaoTalk, Slack/Teams webhooks), marketing consent. Consortium/contact forms: name, organisation, title, email, country, interests."),
   ("2. Why", "Sign-in, memberships, tailored alerts, consortium introductions and online discussion, support, abuse prevention, legal obligations."),
   ("3. Retention", "Deleted on account closure, except records Korean law requires us to keep (contracts and payments 5 years, complaints 3 years, access logs 3 months)."),
   ("4. Sharing", "Not shared except by law or with your consent. Consortium introductions share only what both sides agreed to."),
   ("5. Processors and transfers abroad", "Authentication, hosting and form storage: Netlify, Inc. (USA), over encrypted connections, kept until account closure or end of service. Payment processor (when introduced): a licensed Korean PG."),
   ("6. Children", "Data of under-14s is processed only with a parent's consent."),
   ("7. Your rights", "Access, correct, delete, restrict or withdraw consent at any time via My account or 73036396@naver.com (answered within 10 days)."),
   ("8. Security", "Hashed passwords, HTTPS, least-privilege access, access logs."),
   ("9. Cookies and storage", "A sign-in token is kept in your browser storage. No advertising trackers."),
   ("10. Privacy officer", "Lee Duk-young, CEO · 73036396@naver.com. The Korean version prevails."),
   ("Effective", UPDATED)]),
 },
 "refund": {
  "ko": ("환불 정책", [
   ("청약철회 (7일)", "유료 멤버십은 결제일로부터 7일 안에, 유료 기능(알림 설정 외의 유료 자료 열람·AI 생성·다운로드)을 쓰지 않았다면 전액 환불합니다."),
   ("이용 후 해지", "이용을 시작한 뒤에는 다음 결제일 전까지 해지할 수 있고, 남은 기간까지 이용할 수 있습니다. 연간 요금은 이용한 달을 월 요금으로 계산해 뺀 금액을 환불합니다."),
   ("디지털 자료", "이미 받은 보고서·계약서 서식 등 디지털 자료는 열람 또는 다운로드 후에는 청약철회가 제한됩니다(전자상거래법 제17조 제2항). 회사는 구매 전에 이 사실을 표시합니다."),
   ("맞춤 보고서·검토", "국가 진출 브리프·입찰 적합도 검토 같은 맞춤 작업은 작업을 시작하기 전까지 전액 환불하고, 작업을 시작한 뒤에는 진행한 만큼을 뺀 금액을 환불합니다. 완성본을 받은 뒤에는 디지털 자료 규정을 따릅니다."),
   ("서비스 문제", "회사 사정으로 서비스를 연속 72시간 이상 쓰지 못했다면 그 기간만큼 이용 기간을 연장하거나 환불합니다."),
   ("신청 방법", "73036396@naver.com으로 가입 이메일과 결제일을 보내 주세요. 영업일 3일 안에 처리합니다.")]),
  "en": ("Refund Policy", [
   ("7-day withdrawal", "Full refund within 7 days of payment if paid features (premium content, AI generation, downloads) were not used."),
   ("Cancelling after use", "Cancel any time before the next billing date and keep access until then. Annual plans are refunded minus used months at the monthly rate."),
   ("Digital materials", "Reports and templates already opened or downloaded cannot be withdrawn (Korean E-Commerce Act Art. 17(2)); this is shown before purchase."),
   ("Custom reports and reviews", "Custom work such as market-entry briefs and tender fit reviews is fully refundable until work starts; after that, we refund the balance minus work done. Once delivered, the digital-materials rule applies."),
   ("Outages", "If the Service is unavailable for 72+ consecutive hours due to us, we extend or refund that period."),
   ("How", "Email 73036396@naver.com with your account email and payment date; handled within 3 business days.")]),
 },
 "disclaimer": {
  "ko": ("정보 이용 안내와 면책", [
   ("정보 제공 목적", "GOV RADAR의 모든 내용은 공개 자료를 모아 요약한 정보이며 투자·법률·세무·안보·의료 자문이 아닙니다."),
   ("검증 배지", "항목마다 '확인됨·공식 발표·당사자 주장·단일 출처' 등의 판정을 붙입니다. '확인됨'도 원 자료가 바뀌면 달라질 수 있습니다."),
   ("AI 요약", "요약과 번역에 AI를 씁니다. 원문 링크를 함께 두니 중요한 결정 전에는 원문을 확인하세요."),
   ("가정 시나리오", "'대비 시나리오'는 위기 대비 연습용 가정이며 특정 사건이 일어난다는 예측이 아닙니다."),
   ("외부 링크", "외부 사이트의 내용과 가용성은 회사가 통제하지 않습니다."),
   ("안전 정보", "실제 재난·공습 상황에서는 정부 경보(국민재난안전포털, 안전디딤돌 앱)와 외교부 해외안전여행 공지를 먼저 따르세요."),
   ("문의·정정 요청", "틀린 내용은 73036396@naver.com으로 알려 주세요. 확인 후 고치고 정정 기록을 남깁니다.")]),
  "en": ("Information use and disclaimer", [
   ("Information only", "Everything on GOV RADAR is a summary of public information, not investment, legal, tax, security or medical advice."),
   ("Verification badges", "Each item carries a verdict such as Confirmed, Official statement, Party claim or Single source. Even 'Confirmed' can change if sources change."),
   ("AI summaries", "AI helps summarise and translate. Original links are provided; check them before important decisions."),
   ("Scenarios", "Preparedness scenarios are planning hypotheses, not predictions."),
   ("External links", "We do not control third-party sites."),
   ("Safety", "In a real emergency follow official government alerts and travel advisories first."),
   ("Corrections", "Report errors to 73036396@naver.com; we fix them and log the correction.")]),
 },
}
LEGAL_ORDER = ["terms", "privacy", "refund", "disclaimer"]
LEGAL_NAV = {"ko": {"terms":"이용약관","privacy":"개인정보 처리방침","refund":"환불 정책","disclaimer":"면책 안내"},
             "en": {"terms":"Terms","privacy":"Privacy","refund":"Refunds","disclaimer":"Disclaimer"}}

def legal_page(L, kind, head, foot, e, LANGS):
    k = "ko" if L == "ko" else "en"; title, items = LEGAL[kind][k]
    nav = " · ".join(f'<a href="/{L}/legal/{x}/"{" aria-current=page" if x==kind else ""}>{LEGAL_NAV[k][x]}</a>' for x in LEGAL_ORDER)
    note = "" if L in ("ko", "en") else '<p class="note">This page is provided in English. The Korean version prevails.</p>'
    body = f"""<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a> · {nav}</p><h1>{e(title)}</h1></div></section>
<div class="in stock legal">{note}{''.join(f'<h2>{e(h)}</h2><p>{e(p)}</p>' for h,p in items)}{co_block(k=="ko")}<p class="note">{"최종 갱신" if k=="ko" else "Last updated"} {UPDATED}</p></div>"""
    return head(L, title + " · GOV RADAR", title, f"/{L}/legal/{kind}/", {l: f"/{l}/legal/{kind}/" for l in LANGS}) + body + foot(L)

# ---------------------------------------------------------------- consortium hub
PTYPES = [
 ("uni","대학교·대학원","Universities","공동 연구·ODA 성과평가·현지 교육 사업 공동 제안, 박사진 온라인 검토 참여, 학생 프로젝트 랩"),
 ("res","연구기관·싱크탱크","Research institutes","정책 흐름 분석, 국가별 시나리오 공동 작성, 데이터 검증"),
 ("bank","은행·금융기관","Banks & finance","무역금융·보증·사업 타당성 공동 검토, 수출금융 연계"),
 ("io","국제기구·개발은행","International organisations & MDBs","조달 설명회, 공급자 등록 안내, 공동 웨비나"),
 ("gov","정부·지자체·공공기관","Governments & agencies","정책 수요 공유, 사업 발굴, 공공 조달 정보 협력"),
 ("emb","대사관·무역관","Embassies & trade offices","현지 정책·발주 정보 공유, 사절단·상담회 공동 개최"),
 ("biz","기업","Companies","컨소시엄 주관·참여, 기술·제품 공급, 공동 입찰"),
 ("pro","개인 전문가 (박사·기술사·기술자)","Individual experts (PhDs, engineers)","온라인 자문·검토, 제안서 기술 부분 작성, 강의"),
]
STEPS = [("온라인 신청","Apply online","아래 양식으로 기관·전문 분야를 알려 주세요."),("자격 확인","Verification","기관 이메일·홈페이지·공개 자료로 확인합니다 (영업일 5일 이내)."),
         ("관심 등록","Expression of interest","표준 협력 의향 조건(법적 구속력 없음)에 동의합니다. 기관명은 검증과 서면 동의 후에만 공개합니다."),("공동 프로젝트","Joint projects","프로젝트 랩의 제안 과제에 역할을 정해 참여하고, 성과를 함께 공개합니다.")]
MOU_KO = ["목적: 양 기관은 GOV RADAR를 통해 각국 정부·국제기구 사업 정보를 공유하고 공동 프로젝트를 온라인으로 발굴·추진하는 데 협력한다.",
 "협력 분야: 정책·조달 정보 교류, 공동 연구·제안, 교육·인재 교류, 온라인 원격 검토(박사진 포함), 행사 공동 개최.",
 "운영: 협의는 온라인(화상·문서)을 기본으로 하며, 각 프로젝트의 역할·비용·성과 배분은 별도 개별 계약으로 정한다.",
 "비밀유지: 협의 중 받은 비공개 정보는 상대방 동의 없이 공개하지 않는다.",
 "명칭 사용: 상대방의 명칭·로고는 사전 서면(이메일 포함) 동의를 받아 사용한다.",
 "효력: 이 MOU는 협력 의향을 확인하는 문서로 법적 구속력이 없으며, 어느 쪽이든 이메일 통지로 종료할 수 있다. 유효기간은 1년이며 이의가 없으면 1년씩 연장된다."]
MOU_EN = ["Purpose: the parties cooperate through GOV RADAR to share information on government and multilateral projects and to identify and pursue joint projects online.",
 "Areas: exchange of policy and procurement information, joint research and proposals, education and talent exchange, online remote review (including PhD faculty), joint events.",
 "Operation: discussions are online-first; roles, costs and outcomes of each project are set in separate agreements.",
 "Confidentiality: non-public information received is not disclosed without consent.",
 "Names and logos: used only with prior written (including email) consent.",
 "Effect: this MOU states intent and is not legally binding; either party may end it by email. Valid for one year, renewed annually unless either side objects."]

def consortium_page(L, head, foot, e, LANGS):
    ko = L == "ko"
    cards = "".join(f'<div class="card ptype"><span class="pt-ic">{i+1:02d}</span><h3>{e(a if ko else b)}</h3><p>{e(c) if ko else ""}</p></div>' for i,(k,a,b,c) in enumerate(PTYPES))
    steps = "".join(f'<li><b>{e(a if ko else b)}</b><span>{e(c) if ko else ""}</span></li>' for a,b,c in STEPS)
    opts = "".join(f'<option value="{k}">{e(a if ko else b)}</option>' for k,a,b,c in PTYPES)
    mou = "".join(f"<li>{e(x)}</li>" for x in (MOU_KO if ko else MOU_EN))
    T = (lambda k_, e_: k_ if ko else e_)
    body = f"""<section class="chero img-cons"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{T("GOV RADAR 글로벌 컨소시엄","GOV RADAR Global Consortium")}</h1>
<p class="lede">{T("대학·연구기관·은행·국제기구·정부·대사관·기업·개인 전문가가 온라인에서 함께 정부 사업을 찾고 제안합니다. 현지 국가 대학교와 협의체가 구성되면, 그 대학 박사진과 함께 온라인으로 검토·구축합니다.","Universities, institutes, banks, international organisations, governments, embassies, companies and individual experts find and propose government projects together, online. Where a partner-country university joins, its PhD faculty review and build projects with us online.")}</p></div></section>
<div class="in stock">
<h2>{T("누가 참여하나요","Who takes part")}</h2><div class="cards c4">{cards}</div>
<h2>{T("참여 절차","How it works")}</h2><ol class="steps4">{steps}</ol>
<h2>{T("협력 의향 조건 (요약)","Terms of interest (summary)")}</h2><ol class="mou">{mou}</ol>
<p class="note">{T("전문은 계약서 모음에서 볼 수 있습니다.","Full text in the contracts library.")} <a href="/{L}/contracts/#mou">{T("전문 보기 →","Read the full text →")}</a></p>
<h2 id="apply">{T("컨소시엄 관심 등록","Register your interest")}</h2>
<div class="callout">{T("등록 기관은 '신청 기관'으로만 관리하며, 검증과 서면(이메일) 동의를 마친 뒤에만 '검증된 기관'으로 이름을 공개합니다. 등록은 법적 구속력이 없습니다. 만 19세 이상만 등록할 수 있습니다.","Registrants are kept as 'applicants'; names are shown as 'verified members' only after verification and written (email) consent. Non-binding. 19+ only.")}</div>
<form class="cform" name="consortium" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/consortium/thanks/">
<input type="hidden" name="form-name" value="consortium"><p hidden><label>Do not fill <input name="hp"></label></p><input type="hidden" name="lang" value="{L}">
<div class="two"><label>{T("참여 유형","Type")}<select name="type" required>{opts}</select></label><label>{T("국가","Country")}<input name="country" required></label></div>
<div class="two"><label>{T("기관·회사명 (개인은 소속)","Organisation (or affiliation)")}<input name="org" required></label><label>{T("홈페이지","Website")}<input name="website" type="url" placeholder="https://"></label></div>
<div class="two"><label>{T("담당자 이름","Contact name")}<input name="name" required></label><label>{T("직함 (예: 교수, 박사, 국장)","Title (e.g., Professor, PhD, Director)")}<input name="title"></label></div>
<div class="two"><label>{T("기관 이메일","Work email")}<input name="email" type="email" required></label><label>{T("관심 분야·국가","Interests (sectors, countries)")}<input name="interests"></label></div>
<label>{T("함께 하고 싶은 일","What you would like to do together")}<textarea name="message" rows="4"></textarea></label>
<label class="chk"><input type="checkbox" name="mou_agree" value="yes" required> {T("협력 의향 조건(법적 구속력 없음)에 동의합니다.","I agree to the terms of interest (non-binding).")}</label>
<label class="chk"><input type="checkbox" name="adult" value="yes" required> {T("만 19세 이상입니다.","I am 19 or older.")}</label>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> <span>{T('<a href="/ko/legal/privacy/" target="_blank">개인정보 처리방침</a>에 따라 신청 정보를 수집·이용하는 데 동의합니다. (필수)','I agree to the collection and use of this information under the <a href="/en/legal/privacy/" target="_blank">Privacy Policy</a>. (required)')}</span></label>
<button class="btn pri" type="submit">{T("신청하기","Submit")}</button></form>
<p class="note">{T("신청 후 영업일 5일 안에 이메일로 결과를 알려 드립니다. 문의: 73036396@naver.com","We reply by email within 5 business days. Contact: 73036396@naver.com")}</p>
</div>"""
    jl = '<script type="application/ld+json">' + json.dumps({"@context":"https://schema.org","@type":"WebPage","name":"GOV RADAR Global Consortium","inLanguage":L}, ensure_ascii=False) + '</script>'
    return head(L, T("글로벌 컨소시엄","Global Consortium") + " · GOV RADAR", T("대학·기관·기업·전문가 온라인 컨소시엄","Online consortium for universities, institutions, companies and experts"), f"/{L}/consortium/", {l: f"/{l}/consortium/" for l in LANGS}, jl) + body + foot(L)

def thanks_page(L, head, foot, e, LANGS):
    ko = L == "ko"
    body = f"""<section class="chero"><div class="in"><h1>{"신청을 받았습니다" if ko else "Thank you — application received"}</h1><p class="lede">{"영업일 5일 안에 이메일로 연락드립니다." if ko else "We will reply by email within 5 business days."}</p><p><a class="btn" href="/{L}/projects/">{"프로젝트 랩 보기" if ko else "See the Project Lab"}</a></p></div></section>"""
    return head(L, "GOV RADAR", "thanks", f"/{L}/consortium/thanks/", {l: f"/{l}/consortium/thanks/" for l in LANGS}, '<meta name="robots" content="noindex">') + body + foot(L)

# ---------------------------------------------------------------- project lab
def projects_page(L, head, foot, e, LANGS, flag, vbh):
    ko = L == "ko"; P = json.load(open(os.path.join(HERE, "src", "projects.json"), encoding="utf-8"))
    T = (lambda k_, e_: k_ if ko else e_)
    def card(p):
        fl = " ".join(flag(i) for i in p.get("iso", [])[:6])
        basis = "".join(f'<li>{vbh(b["v"], not ko)}{e(b["ko"] if ko else b["en"])}</li>' for b in p["basis"])
        roles = " · ".join(e(r) for r in (p["roles_ko"] if ko else p["roles_en"]))
        return f"""<article class="card proj"><p class="note">{fl} {e(p["region_ko"] if ko else p["region_en"])} · {e(p["horizon"])}</p><h3>{e(p["title_ko"] if ko else p["title_en"])}</h3>
<p>{e(p["idea_ko"] if ko else p["idea_en"])}</p><h4>{T("근거 (검증 판정)","Basis (verified)")}</h4><ul class="basis">{basis}</ul>
<div class="lockbox sm"><b>{T("필요한 참여자 구성·발주·재원 후보","Participants needed, buyers and funders")}</b> <span class="note">{T("프로젝트 파트너십 상담 고객과 참여 신청자에게 비밀유지 서약 후 공개합니다.","Shared with partnership clients and applicants after a confidentiality pledge.")}</span> <a class="btn sm pri" href="/{L}/pricing/?p=partner#order">{T("프로젝트 파트너십 무료 상담","Free partnership consultation")}</a> <a class="btn sm" href="/{L}/consortium/?p={e(p.get('id',''))}">{T("참여 신청","Apply to join")}</a></div>
<p><a class="btn sm" href="/{L}/consortium/#apply">{T("이 프로젝트에 참여 신청","Join this project")}</a></p></article>"""
    body = f"""<section class="chero img-proj"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{T("프로젝트 랩 — 흐름을 먼저 읽고 사업을 설계합니다","Project Lab — read the trend first, then design the project")}</h1>
<p class="lede">{T("정부 정책, 국제기구 예산, 분쟁·재난 흐름을 AI가 교차검증된 사실로 먼저 읽고, 아직 발주되지 않은 사업을 추론해 제안합니다. 대학·기업·기관이 역할을 나눠 온라인으로 함께 준비합니다.","AI reads government policy, multilateral budgets and conflict and disaster trends from cross-checked facts, then infers projects that have not been tendered yet. Universities, companies and institutions prepare them together online.")}</p></div></section>
<div class="in stock"><div class="callout">{T("아래 제안은 AI 추론이며 발주가 확정된 사업이 아닙니다. 근거마다 검증 판정을 붙였습니다.","These are AI-inferred proposals, not confirmed tenders. Each basis carries a verification verdict.")} · {T("갱신","Updated")} {e(P["updated"])}</div>
<div class="cards c2">{''.join(card(p) for p in P["projects"])}</div>
<p class="note">{T("추론 방법의 세부는 공개하지 않습니다. 모든 근거는 공개 출처의 검증 판정과 함께 표시합니다.","Method details are not published. Every basis is shown with its verification verdict.")}</p></div>"""
    return head(L, T("프로젝트 랩","Project Lab") + " · GOV RADAR", T("정책·국제기구·분쟁 흐름에서 추론한 공동 프로젝트 제안","Joint project proposals inferred from policy, multilateral and conflict trends"), f"/{L}/projects/", {l: f"/{l}/projects/" for l in LANGS}) + body + foot(L)

# ---------------------------------------------------------------- contracts library
def contracts_page(L, head, foot, e, LANGS):
    ko = L == "ko"; C = json.load(open(os.path.join(HERE, "src", "contracts.json"), encoding="utf-8"))
    T = (lambda k_, e_: k_ if ko else e_)
    k = "ko" if ko else "en"
    toc = "".join(f'<a class="chip" href="#{c["id"]}">{e(c["title_"+k])}</a>' for c in C["docs"])
    party = (f"갑(서비스 제공자): {CO['name_ko']} ({CO['ceo_ko']}, 사업자등록번호 {CO['brn']}, 통신판매업신고 {CO['mail_order']}, 이메일 {CO['email']})" if ko else
             f"Provider: {CO['name_en']} ({CO['ceo_en']}, business reg. {CO['brn']}, email {CO['email']})")
    docs = ""
    for c in C["docs"]:
        arts = "".join(f'<h4>{e(a[0])}</h4><p>{e(a[1])}</p>' for a in c["articles_"+k])
        if c["id"] in ("connect", "nda"):
            arts = f'<div class="lockbox sm"><b>{T("전문은 요청 시 보내 드립니다","Full text on request")}</b> <span class="note">{T("업무 범위, 보수 구조, 비밀유지 조항을 담고 있습니다. 아래 양식으로 요청하면 이메일로 보내 드립니다.","Scope, fee structure and confidentiality terms. Request it with the form below and we email it.")}</span> <a class="btn sm" href="#req">{T("전문 요청","Request full text")}</a></div>'
            if c["id"] == "connect":
                arts = f'<p>{T("첫 상담은 무료입니다. 착수금과 성공보수는 첫 상담 뒤 사업 규모에 맞춰 정하며, 성공보수 중심으로 구성합니다(상한 5,000만 원). 정부·국제기구 사업은 반부패·수수료 공개 조항을 적용합니다.","The first consultation is free. The retainer and success fee are agreed after it according to the deal, weighted toward the success fee (cap ₩50M). Government and multilateral deals carry anti-bribery and fee-disclosure clauses.")}</p>' + arts
        docs += f"""<article class="contract" id="{c['id']}"><div class="ch"><h2>{e(c['title_'+k])}</h2><button class="btn sm" onclick="window.print()">{T('인쇄·PDF','Print / PDF')}</button></div>
<p class="note">{e(c['use_'+k])}</p><p class="party">{e(party)}<br>{e(c['party_'+k])}</p>{arts}
<div class="sign"><div><b>{T('갑','Provider')}</b><br>{e(CO['name_ko'] if ko else CO['name_en'])}<br>{e(CO['ceo_ko'] if ko else CO['ceo_en'])} (인)</div><div><b>{T('을','Counterparty')}</b><br>{T('기관·회사명','Organisation')}: ____________<br>{T('대표자','Representative')}: ____________ ({T('인','sign')})</div><div>{T('체결일','Date')}: ____ . __ . __</div></div></article>"""
    body = f"""<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{T('계약서·협력 의향서 표준 서식','Standard contracts & letter of intent')}</h1>
<p class="lede">{T('회사 정보가 들어간 표준 서식입니다. 온라인으로 검토하고, 체결이 필요하면 아래 요청 양식을 보내 주세요. 전자서명 문서로 보내 드립니다.','Standard templates with our company details. Review online; to sign, send the request form and we will send an e-signature copy.')}</p><div class="chips">{toc}</div></div></section>
<div class="in stock"><div class="callout">{T('표준안입니다. 금액·범위는 개별 협의로 정하며, 중요한 계약은 체결 전에 법률 검토를 권합니다.','Templates only. Amounts and scope are agreed case by case; legal review is recommended before signing.')}</div>{docs}
<h2 id="req">{T('계약 체결 요청','Request a contract')}</h2>
<form class="cform" name="contract-request" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/consortium/thanks/"><input type="hidden" name="form-name" value="contract-request"><p hidden><input name="hp"></p>
<div class="two"><label>{T('계약 종류','Contract')}<select name="contract">{''.join(f'<option>{e(c["title_"+k])}</option>' for c in C["docs"])}</select></label><label>{T('기관·회사명','Organisation')}<input name="org" required></label></div>
<div class="two"><label>{T('담당자','Contact')}<input name="name" required></label><label>{T('이메일','Email')}<input name="email" type="email" required></label></div>
<label>{T('요청 내용 (범위·기간·예산)','Details (scope, period, budget)')}<textarea name="message" rows="3"></textarea></label>
<label class="chk"><input type="checkbox" name="adult" value="yes" required> {T('만 19세 이상이며 기관을 대표해 요청합니다.','I am 19+ and request on behalf of my organisation.')}</label>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> {T('개인정보 수집·이용에 동의합니다 (필수)','I agree to the Privacy Policy (required)')}</label>
<button class="btn pri" type="submit">{T('요청 보내기','Send request')}</button></form>{co_block(ko)}</div>"""
    return head(L, T('계약서·MOU','Contracts & MOU') + " · GOV RADAR", T('WMM 표준 계약서와 협력 의향서','WMM standard contracts and letter of intent'), f"/{L}/contracts/", {l: f"/{l}/contracts/" for l in LANGS}) + body + foot(L)

# ---------------------------------------------------------------- verifiers & experts (paid work)
def experts_page(L, head, foot, e, LANGS):
    ko = L == "ko"; T = (lambda k_, e_: k_ if ko else e_)
    steps = [
     ("지원","Apply","아래 양식으로 언어·국가·전문 분야를 알려 주세요. 가입비·교육비·보증금은 없습니다.","Tell us your languages, countries and field. No fees, ever."),
     ("공개 경력 확인","Profile check","대학 교원 페이지·ORCID·LinkedIn·소속 기관 이메일 회신 등 공개 자료로 확인합니다. 신분증 사진은 받지 않습니다.","We check public sources (faculty page, ORCID, LinkedIn, a reply from your institutional email). No ID photos."),
     ("유료 실력 과제","Paid skills task","정답을 아는 실제 형식의 과제 1건을 풀고 보수를 받습니다. 합격 기준을 미리 알려 드립니다.","One paid task with a known answer key; pass criteria are shared in advance."),
     ("계약과 지급 등록","Contract & payout set-up","결과물 단위 업무위탁 계약(비밀유지·저작권 포함)을 온라인으로 맺고, 첫 지급 전에 본인 확인과 제재명단 대조를 합니다.","A deliverable-based service contract (confidentiality, IP) signed online; identity and sanctions check before the first payout."),
     ("작업","Work","AI 직원(Claude·ChatGPT)이 만든 초안을 원문과 대조해 고치고, 판정과 근거를 남깁니다. 근무 시간은 정하지 않습니다.","You check AI drafts (Claude, ChatGPT) against originals and record verdicts and evidence. No fixed hours."),
     ("검수와 지급","Review & pay","첫 5건은 전부, 그 뒤는 5~10%를 다른 사람이 다시 확인합니다. 승인된 결과물은 정해진 단가로 지급합니다.","Your first 5 tasks are fully re-checked; after that, a 5–10% sample is re-checked. Accepted work is paid at the fixed rate."),
    ]
    rates = [("정부 정보 검증 1건 (원문 대조·판정)","Verify one government item (source check, verdict)","10,000원부터","from ₩10,000"),
             ("현지어 번역 감수 A4 1쪽","Local-language review, one A4 page","15,000원부터","from ₩15,000"),
             ("국가 리포트 전문가 검토 1건 (박사·실무 전문가)","Expert review of a country report (PhD / practitioner)","150,000~300,000원","₩150,000–300,000"),
             ("화상 자문 1시간 (협약 대학 박사진)","One-hour video consultation (partner-university PhDs)","100,000원부터","from ₩100,000")]
    pay = [("한국 거주 개인 (작업자)","Korea-resident individuals (workers)","계좌이체. 사업소득 3.3% 원천징수 후 지급, 지급명세서 신고","Bank transfer, 3.3% business-income withholding, reported to the tax office"),
           ("한국 거주 전문가 (일시 자문·강의)","Korea-resident experts (occasional advice)","계좌이체. 기타소득 8.8% 원천징수","Bank transfer, 8.8% other-income withholding"),
           ("해외 거주자","Residents abroad","해외 송금 (은행·국제 송금 서비스). 송금 수수료는 WMM 부담, 세금 처리는 거주국·조세조약 기준","International transfer; WMM pays transfer fees; tax handled under your country of residence and any tax treaty"),
           ("지급 시기","When","승인된 결과물을 매월 말 합산해 다음 달 10일까지 지급","Accepted work is totalled monthly and paid by the 10th of the following month")]
    st = "".join(f'<li><b>{e(a if ko else b)}</b><span>{e(c if ko else d)}</span></li>' for a,b,c,d in steps)
    rt = "".join(f'<tr><td>{e(a if ko else b)}</td><td><b>{e(c if ko else d)}</b></td></tr>' for a,b,c,d in rates)
    pt = "".join(f'<tr><td>{e(a if ko else b)}</td><td>{e(c if ko else d)}</td></tr>' for a,b,c,d in pay)
    body = f"""<section class="chero img-cons"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{T("검증원·전문가로 함께 일하기","Work with us as a verifier or expert")}</h1>
<p class="lede">{T("AI가 만든 정부·국제기구 정보를 현지 언어와 전문 지식으로 확인하는 일입니다. 실력으로 참여하고, 결과물마다 정해진 보수를 받습니다. 협약 대학이 있는 나라는 그 대학 박사진과 함께 검토합니다.","Check AI-drafted government and multilateral information with your language and expertise. You are selected on skill and paid a fixed fee per deliverable. In countries with a partner university, its PhD faculty also review the work.")}</p></div></section>
<div class="in stock"><div class="callout">{T("일감은 고객 주문이 있을 때만 엽니다. 지금 등록하시면 실력 과제 순서대로 연락드립니다. '가입하면 돈을 번다'는 약속은 하지 않습니다. 만 19세 이상(거주국 성년 연령이 더 높으면 그 연령)만 참여할 수 있습니다.","Work becomes available only when clients place orders. Applicants are contacted in turn for the skills task. We never promise income for signing up. 19+ only (or the local age of majority, if higher).")}</div>
<h2>{T("참여 절차","How it works")}</h2><ol class="steps4 s6">{st}</ol>
<h2>{T("보수 기준 (예시, 확정 전)","Rates (indicative)")}</h2><table class="qt">{rt}</table>
<p class="note">{T("단가는 실효 시급이 최저임금 이상이 되도록 작업 시간을 재서 정합니다. 국적과 관계없이 같은 일에는 같은 단가를 지급합니다.","Rates are set from timed tasks so the effective hourly rate is at least minimum wage. Same work, same rate, regardless of nationality.")}</p>
<h2>{T("지급 방법","How you are paid")}</h2><table class="qt">{pt}</table>
<p class="note">{T("제재 대상 국가·개인에게는 지급할 수 없습니다. 세금 처리는 세무 전문가 확인을 거쳐 확정합니다.","We cannot pay sanctioned countries or persons. Tax handling is confirmed with a tax adviser.")}</p>
<h2 id="apply">{T("지원하기","Apply")}</h2>
<form class="cform" name="expert-apply" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/consortium/thanks/"><input type="hidden" name="form-name" value="expert-apply"><p hidden><input name="hp"></p><input type="hidden" name="lang" value="{L}">
<div class="two"><label>{T("이름","Name")}<input name="name" required></label><label>{T("이메일","Email")}<input name="email" type="email" required></label></div>
<div class="two"><label>{T("거주 국가","Country of residence")}<input name="country" required></label><label>{T("사용 언어 (능숙한 순)","Languages (strongest first)")}<input name="languages" required></label></div>
<div class="two"><label>{T("참여 형태","Role")}<select name="role"><option>{T("검증원 (정보 확인)","Verifier")}</option><option>{T("번역 감수","Language reviewer")}</option><option>{T("전문가 (박사·기술사·실무자)","Expert (PhD, engineer, practitioner)")}</option></select></label><label>{T("전문 분야·국가","Field and countries")}<input name="field"></label></div>
<label>{T("공개 경력 링크 (대학 페이지·ORCID·LinkedIn 등)","Public profile link (faculty page, ORCID, LinkedIn)")}<input name="profile" type="url" placeholder="https://"></label>
<label>{T("추천 기관 (선택: GCSME 회원사·대학·NGO)","Referred by (optional: GCSME member, university, NGO)")}<input name="referral"></label>
<label class="chk"><input type="checkbox" name="adult" value="yes" required> {T("만 19세 이상(거주국 성년 연령 이상)입니다.","I am 19 or over (and an adult where I live).")}</label>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> <span>{T('<a href="/ko/legal/privacy/" target="_blank">개인정보 처리방침</a>에 동의합니다 (필수)','I agree to the <a href="/en/legal/privacy/" target="_blank">Privacy Policy</a> (required)')}</span></label>
<button class="btn pri" type="submit">{T("지원하기","Apply")}</button></form></div>"""
    return head(L, T("검증원·전문가","Verifiers & experts") + " · GOV RADAR", T("현지 언어와 전문 지식으로 정부 정보를 검증하고 결과물마다 보수를 받습니다","Verify government information with your language and expertise; paid per deliverable"), f"/{L}/experts/", {l: f"/{l}/experts/" for l in LANGS}) + body + foot(L)

# ---------------------------------------------------------------- overseas talent demand intake (information only, no placement)
def talent_page(L, head, foot, e, LANGS):
    ko = L == "ko"; T = (lambda k_, e_: k_ if ko else e_)
    roles = [("엔지니어·기술자","Engineers / technicians"),("IT·개발","IT / software"),("연구원·박사","Researchers / PhDs"),("영업·현지 사업개발","Sales / business development"),("통역·현지 코디네이터","Interpreters / coordinators"),("의료·보건","Healthcare"),("건설·현장 인력","Construction / site"),("기타","Other")]
    sizes = [("1~5명","1–5"),("6~20명","6–20"),("21~50명","21–50"),("51명 이상","51+"),("아직 모름","Not sure yet")]
    when = [("3개월 이내","Within 3 months"),("3~6개월","3–6 months"),("6~12개월","6–12 months"),("검토 단계","Just exploring")]
    ro = "".join(f'<label class="chk"><input type="checkbox" name="roles" value="{e(b)}"> {e(a if ko else b)}</label>' for a,b in roles)
    so = "".join(f'<option value="{e(b)}">{e(a if ko else b)}</option>' for a,b in sizes)
    wo = "".join(f'<option value="{e(b)}">{e(a if ko else b)}</option>' for a,b in when)
    body = f"""<section class="chero img-cons"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{T("해외 인력 수요 등록","Overseas talent demand")}</h1>
<p class="lede">{T("어느 나라에서 어떤 인력이 필요한지 알려 주세요. 모인 수요는 국가별 인력 시장 정보와 진출 준비 자료를 만드는 데 씁니다.","Tell us which country and what kind of people you need. We use the demand we collect to build country talent-market information and market-entry material.")}</p></div></section>
<div class="in stock"><div class="callout">{T("이 양식은 수요 조사입니다. WMM은 현재 인재 추천·채용 알선·인력 파견을 하지 않으며, 등록이나 결과에 대해 어떤 비용도 받지 않습니다. 필요하시면 해당 국가 정보와, 면허를 가진 전문기관을 안내해 드립니다.","This form is a demand survey. WMM does not currently recommend candidates, broker hiring or supply staff, and charges nothing for registering. Where useful, we share country information and point you to licensed providers.")}</div>
<h2>{T("등록 후 받는 것","What you get")}</h2>
<ol class="steps4"><li><b>{T("확인 메일","Confirmation")}</b><span>{T("영업일 2일 안에 접수 확인을 보내 드립니다.","We confirm receipt within 2 business days.")}</span></li>
<li><b>{T("국가 정보","Country brief")}</b><span>{T("해당 국가의 노동·비자·채용 관련 공개 정보 요약(출처 표시)을 보내 드립니다.","A sourced summary of public labour, visa and hiring information for that country.")}</span></li>
<li><b>{T("수요 리포트","Demand report")}</b><span>{T("비슷한 수요가 모이면 국가·직무별 요약을 등록 기업에 공유합니다(기업명 비공개).","When similar demand builds up, registrants receive a country/role summary (company names withheld).")}</span></li>
<li><b>{T("서비스 출시 알림","Launch notice")}</b><span>{T("관련 서비스를 정식으로 열면 가장 먼저 알려 드립니다.","You hear first if we launch a related service.")}</span></li></ol>
<h2 id="form">{T("수요 등록","Register demand")}</h2>
<form class="cform" name="talent-demand" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/consortium/thanks/"><input type="hidden" name="form-name" value="talent-demand"><p hidden><input name="hp"></p><input type="hidden" name="lang" value="{L}">
<div class="two"><label>{T("회사·기관명","Company / organisation")}<input name="org" required></label><label>{T("담당자 이름","Contact name")}<input name="name" required></label></div>
<div class="two"><label>{T("업무용 이메일","Work email")}<input name="email" type="email" required></label><label>{T("회사 소재 국가","Company country")}<input name="org_country"></label></div>
<div class="two"><label>{T("인력이 필요한 국가 (여러 곳 가능)","Country where you need people (several OK)")}<input name="target_country" required placeholder="{T('예: 베트남, UAE','e.g. Vietnam, UAE')}"></label><label>{T("근무 형태","Work arrangement")}<select name="arrangement"><option value="on-site">{T("현지 근무","On site in that country")}</option><option value="remote">{T("원격 근무","Remote")}</option><option value="to-korea">{T("한국으로 초청","Bring to Korea")}</option><option value="unsure">{T("미정","Not sure")}</option></select></label></div>
<fieldset class="chks"><legend>{T("필요한 직무 (복수 선택)","Roles needed (choose any)")}</legend>{ro}</fieldset>
<div class="two"><label>{T("필요 인원","Headcount")}<select name="headcount">{so}</select></label><label>{T("필요 시기","Timing")}<select name="timing">{wo}</select></label></div>
<label>{T("필요한 기술·언어·자격 (간단히)","Skills, languages, qualifications (brief)")}<textarea name="detail" rows="4" maxlength="1500"></textarea></label>
<label>{T("지금 겪는 어려움 (선택)","Main difficulty so far (optional)")}<input name="pain" placeholder="{T('예: 비자 절차, 현지 급여 수준, 후보자 부족','e.g. visas, local pay levels, few candidates')}"></label>
<p class="note">{T("개인 이력서나 후보자 개인정보는 보내지 마세요. 회사의 수요만 받습니다.","Please do not send CVs or candidates' personal data. We only collect your company's demand.")}</p>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> <span>{T('<a href="/ko/legal/privacy/" target="_blank">개인정보 처리방침</a>에 동의합니다 (필수)','I agree to the <a href="/en/legal/privacy/" target="_blank">Privacy Policy</a> (required)')}</span></label>
<label class="chk"><input type="checkbox" name="understand" value="yes" required> {T("수요 조사이며 인재 추천·채용 알선 서비스가 아님을 이해합니다.","I understand this is a demand survey, not a recruitment or placement service.")}</label>
<button class="btn pri" type="submit">{T("수요 등록하기","Register demand")}</button></form></div>"""
    return head(L, T("해외 인력 수요 등록","Overseas talent demand") + " · GOV RADAR", T("어느 나라에 어떤 인력이 필요한지 등록하는 수요 조사","A demand survey: which country, what kind of people"), f"/{L}/talent/", {l: f"/{l}/talent/" for l in LANGS}) + body + foot(L)
