"""Tender win centre (/L/win/): seven steps from finding a tender to delivering it, a pre-tender pipeline radar,
contract-award and competitor analysis, and a 90-day action plan. Pipeline and award data come from the daily
no-AI feeds (tools/feed_intel.py) on the data branch; the page shows a build-time snapshot and refreshes in the browser."""
import json, os
ROOT = os.path.dirname(os.path.abspath(__file__))
FEED = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/"

def _load(name):
    try: return json.load(open(os.path.join(ROOT, "data_branch", "feeds", name), encoding="utf-8"))
    except Exception: return {}

T = {
 "ko": dict(
  title="입찰 수주 센터 — 공고 전 사업부터 낙찰까지 · GOV RADAR",
  desc="입찰을 찾는 데서 끝나지 않고 이기기까지: 입찰 전 사업 레이더, 낙찰·경쟁사 분석, 수주 7단계 실행 방법과 90일 계획.",
  h1="입찰 수주 센터", lead="입찰은 찾는 것보다 이기는 것이 어렵습니다. 공고가 나오기 전 사업부터 누가 얼마에 따냈는지까지, 수주에 필요한 단계를 한곳에서 준비합니다.",
  s1="열린 입찰", s1b="매일 갱신", s2="입찰 전 사업", s2b="세계은행 승인 전", s3="최근 낙찰 공고", s3b="그중 한국 기업",
  j=[("steps", "수주 7단계"), ("pipe", "입찰 전 사업"), ("awards", "낙찰·경쟁사"), ("plan", "90일 실행 계획"), ("order", "주문하기")],
  sh="수주까지 7단계 — 직접 하는 방법과 우리가 돕는 것", sl="각 단계에서 회사가 직접 할 일과, 공짜로 쓸 수 있는 공식 창구, GOV RADAR·WMM이 대신하거나 함께하는 일을 나눠 적었습니다.",
  do="직접 하는 방법", we="GOV RADAR·WMM이 돕는 것",
  ph="입찰 전 사업 레이더 — 공고가 나오기 전에 먼저 보기", pl="세계은행 이사회 승인을 기다리는 사업입니다. 승인 뒤 실행기관이 조달계획을 세우고 입찰을 내기까지 시간이 걸리므로, 지금 분야가 맞는 사업을 골라 실행기관·현지 파트너와 먼저 관계를 만들면 앞설 수 있습니다.",
  pc=["나라", "사업", "규모(미화)", "분야"], pnote="규모는 세계은행이 밝힌 사업 총액이며 하나의 입찰 금액이 아닙니다. 승인 전이라 바뀔 수 있습니다.",
  ah="낙찰·경쟁사 분석 — 누가 얼마에 따냈나", al="세계은행 사업의 최근 낙찰 공고를 모았습니다. 우리 분야에서 어느 나라 기업이 이기는지, 계약 규모가 어느 정도인지 보고 입찰가와 파트너 전략을 정하세요.",
  abc="낙찰 업체 국적 상위", akr="한국 기업 낙찰", ac=["날짜", "발주국", "계약", "낙찰 업체(국적)", "금액"], anote="금액은 서명된 계약 금액이며, '약 US$'는 참고용 환산입니다. 현지 통화 단위가 커 보여도 미화로는 작을 수 있습니다.",
  ains="최근 낙찰 {n}건 가운데 한국 기업은 {k}건입니다. 대부분은 현지 기업이 이깁니다 — 현지 파트너와 함께 들어가는 이유입니다.",
  q="분야·나라·업체 이름으로 찾기", all="전체", more="회원은 전체 목록과 필터를 봅니다", moreb="분석 회원으로 전체 보기",
  plh="90일 실행 계획 — 첫 입찰을 내기까지", pll="해외 조달이 처음인 회사가 90일 안에 첫 입찰 또는 관심표명서(EOI)를 내는 순서입니다.",
  oh="지금 주문할 수 있는 것", ol="공고 1건 검토부터 수주까지 함께하는 파트너십까지, 필요한 만큼만 고르세요.",
  upd="갱신", src="출처: 세계은행 조달 공고·사업 API(공개 데이터), 매일 자동 수집", type={"CW": "공사", "GO": "물품", "CS": "컨설팅", "NC": "일반 용역"}),
 "en": dict(
  title="Tender win centre — from pre-tender projects to contract awards · GOV RADAR",
  desc="Go beyond finding tenders: a pre-tender pipeline radar, contract-award and competitor analysis, seven practical steps to win and a 90-day plan.",
  h1="Tender win centre", lead="Finding a tender is the easy part; winning it is hard. From projects that have not reached tender yet to who won and for how much, prepare every step in one place.",
  s1="Open tenders", s1b="updated daily", s2="Pre-tender projects", s2b="awaiting World Bank approval", s3="Recent contract awards", s3b="won by Korean firms",
  j=[("steps", "7 steps"), ("pipe", "Pre-tender projects"), ("awards", "Awards & competitors"), ("plan", "90-day plan"), ("order", "Order")],
  sh="Seven steps to a contract — what you can do and how we help", sl="For each step: what your company does itself, the free official channels to use, and what GOV RADAR and WMM do for you or with you.",
  do="What you do", we="How GOV RADAR and WMM help",
  ph="Pre-tender radar — see projects before the notice", pl="Projects waiting for World Bank Board approval. After approval the implementing agency plans procurement before tenders appear, so picking the projects in your field now and building ties with the agency and local partners puts you ahead.",
  pc=["Country", "Project", "Size (US$)", "Field"], pnote="Size is the World Bank's total project amount, not a single tender. Projects not yet approved can change.",
  ah="Awards and competitors — who won, for how much", al="Recent contract awards on World Bank projects. See which countries' firms win in your field and how large contracts are, then set your price and partner strategy.",
  abc="Top winner nationalities", akr="Won by Korean firms", ac=["Date", "Country", "Contract", "Winner (nationality)", "Amount"], anote="Amounts are signed contract prices; 'about US$' is an approximate conversion.",
  ains="Of {n} recent awards, {k} went to Korean firms. Most are won by local companies — which is why you go in with a local partner.",
  q="Search by field, country or company", all="All", more="Members see the full list and filters", moreb="See everything as an analysis member",
  plh="90-day plan — to your first bid", pll="The order in which a company new to international procurement can submit its first bid or expression of interest within 90 days.",
  oh="What you can order now", ol="From a review of one notice to a partnership through delivery — pick only what you need.",
  upd="Updated", src="Source: World Bank procurement notices and projects API (open data), collected daily", type={"CW": "Works", "GO": "Goods", "CS": "Consulting", "NC": "Non-consulting"}),
}

STEPS = [
 ("find", ("찾기", "Find"), ("관심 국가 3곳과 분야 1개를 정하고, 국제기구 조달 포털에 회사를 등록해 공고 알림을 받습니다.", "Choose three target countries and one field, register on the multilateral procurement portals and switch on notice alerts."),
  [("UNGM(유엔 조달 포털) 공급업체 등록", "UNGM supplier registration", "https://www.ungm.org"), ("세계은행 컨설턴트 등록(eConsultant2)", "World Bank eConsultant2 (consultants)", "https://wbgeconsult2.worldbank.org"), ("ADB 컨설턴트 관리 시스템", "ADB Consultant Management System", "https://cms.adb.org")],
  ("입찰·마감 보드가 193개국 공고를 매일 모으고, 나라를 저장하면 분석 회원에게 주간 메일로 마감 임박 공고를 보냅니다.", "The tender board collects notices for 193 countries every day; save countries and analysis members get closing-soon notices by weekly email."),
  [("입찰·마감 보드", "Tender board", "mdb/#deadlines")]),
 ("early", ("미리 알기", "See it early"), ("공고가 나오기 전 단계의 사업을 찾아 사업 문서에서 조달계획을 확인하고, 실행기관(PIU)에 회사를 소개합니다.", "Find projects before their notices, check the procurement plan in the project documents, and introduce your company to the implementing agency (PIU)."),
  [("세계은행 사업 검색", "World Bank projects search", "https://projects.worldbank.org")],
  ("아래 '입찰 전 사업 레이더'가 승인 전 사업을 규모·분야별로 보여 줍니다.", "The pre-tender radar below lists projects awaiting approval by size and field."),
  [("입찰 전 사업 보기", "See pre-tender projects", "#pipe")]),
 ("fit", ("이길 수 있는지 판단", "Decide if you can win"), ("자격 요건(유사 실적·매출·인력·장비)을 회사 자료와 한 줄씩 대조하고, 같은 분야 과거 낙찰자와 낙찰가를 확인합니다.", "Check each eligibility requirement (similar experience, turnover, staff, equipment) against your records, and look up past winners and prices in the same field."),
  [],
  ("입찰 적합도 검토(상담 후 견적)로 참여 여부·부족한 자격·보완 방법을 판정해 드립니다. 아래 낙찰 분석으로 경쟁사를 미리 봅니다.", "A tender fit review (by quote) gives a go/no-go, the gaps and how to close them. The award analysis below shows competitors."),
  [("적합도 검토 주문", "Order a fit review", "pricing/?p=fit#order"), ("낙찰·경쟁사 보기", "See awards", "#awards")]),
 ("docs", ("서류·제안서", "Documents and proposal"), ("입찰보증서, 실적증명, 최근 3년 재무제표, 인증서를 영문으로 준비하고 기술제안서를 평가 기준 순서대로 씁니다.", "Prepare the bid security, experience certificates, three years of financial statements and certificates in English, and write the technical proposal in the order of the evaluation criteria."),
  [],
  ("프로젝트 파트너십으로 제안서 구성 검수와 영문화를 함께합니다(견적).", "Through a project partnership we review the proposal structure and the English version with you (by quote)."),
  [("파트너십 상담", "Partnership consultation", "pricing/?p=partner#order")]),
 ("partner", ("현지 파트너·컨소시엄", "Local partner and consortium"), ("공사·대형 사업은 현지 등록업체와 공동수급(JV)이나 하도급을 검토하고, 협력 의향서와 비밀유지계약을 먼저 맺습니다.", "For works and large projects, consider a joint venture or subcontract with a locally registered firm, and sign a letter of intent and an NDA first."),
  [],
  ("CONNECT와 컨소시엄 매칭으로 현지 파트너 후보를 찾고, 협력 의향서·NDA 양식을 바로 쓸 수 있습니다.", "CONNECT and consortium matching find local partner candidates; letter-of-intent and NDA templates are ready to use."),
  [("컨소시엄", "Consortium", "consortium/"), ("계약서 양식", "Contract templates", "contracts/")]),
 ("finance", ("금융·보증", "Finance and guarantees"), ("입찰보증·계약이행보증은 한국무역보험공사 수출보증보험을, 조달 진출 비용은 조달청 해외조달시장 진출 지원사업을 확인합니다. 유상·무상원조(EDCF·KOICA) 사업과 겹치는지도 봅니다.", "For bid and performance bonds, check K-SURE export guarantee insurance; for market-entry costs, the Public Procurement Service's overseas procurement support programme. Also check overlap with Korean aid projects (EDCF, KOICA)."),
  [("한국무역보험공사(K-SURE)", "K-SURE", "https://www.ksure.or.kr"), ("조달청 해외조달 지원", "Public Procurement Service (PPS)", "https://www.pps.go.kr"), ("EDCF(대외경제협력기금)", "EDCF", "https://www.edcfkorea.go.kr"), ("KOICA", "KOICA", "https://www.koica.go.kr")],
  ("나라별 레이더의 '한국 지원' 칸에 그 나라에서 쓸 수 있는 한국 기관 사업을 모아 둡니다.", "Each country radar has a 'Korean support' section with Korean programmes available there."),
  [("나라별 레이더", "Country radars", "#")]),
 ("deliver", ("수주 후 실행", "After the award"), ("계약 조건(대금 지급·지연 배상·보증 기간)을 확인하고, 현지 법인·통관·인증·인력 계획을 세웁니다.", "Check contract terms (payment, delay damages, guarantee periods) and plan the local entity, customs, certification and staffing."),
  [],
  ("프로젝트 파트너십이 실행 계획과 현지 협력을 함께 관리합니다.", "A project partnership manages the delivery plan and local cooperation with you."),
  [("파트너십 상담", "Partnership consultation", "pricing/?p=partner#order")]),
]
PLAN = [
 (("1–2주", "Weeks 1–2"), ("등록과 알림", "Register and get alerts"), ("UNGM·세계은행·ADB 등록, 관심 국가 3곳 저장, 입찰 알림 켜기", "Register on UNGM, World Bank and ADB; save three countries; turn on alerts")),
 (("3–4주", "Weeks 3–4"), ("목표 고르기", "Pick targets"), ("입찰 전 사업에서 분야가 맞는 사업 5건, 열린 입찰 3건 고르기 · 같은 분야 낙찰자 확인", "Pick five pre-tender projects and three open tenders in your field; look up winners in that field")),
 (("5–8주", "Weeks 5–8"), ("회사 자료 영문화와 파트너", "English company file and partners"), ("실적표·인증·재무제표 영문 정리, 현지 파트너 후보 3곳 접촉, 협력 의향서·NDA", "English track record, certificates and financials; contact three local partner candidates; letter of intent and NDA")),
 (("9–12주", "Weeks 9–12"), ("첫 제출", "First submission"), ("적합도 검토로 1건 선택 → 관심표명서(EOI) 또는 입찰서 제출 → 결과와 낙찰가 기록", "Choose one with a fit review → submit an EOI or bid → record the result and the winning price")),
]
ORD = [("fit", ("입찰 적합도 검토", "Tender fit review"), ("공고 1건 · 상담 후 견적", "One notice · by quote")),
       ("brief", ("국가 진출 브리프", "Market-entry brief"), ("나라 1곳 · 견적", "One country · by quote")),
       ("member", ("분석 회원", "Analysis member"), ("월 20,000원 · 전체 목록·알림", "₩20,000/month · full lists and alerts")),
       ("partner", ("프로젝트 파트너십", "Project partnership"), ("첫 상담 무료 · 수주까지", "First consultation free · through delivery"))]

def _usd(v, ko):
    if not v: return "—"
    if v >= 1e9: return (f"{v/1e9:,.1f}십억 달러" if False else f"US${v/1e9:,.1f}B") if not ko else f"{v/1e8:,.0f}억 달러"
    if v >= 1e6: return f"US${v/1e6:,.0f}M" if not ko else f"{v/1e6:,.0f}백만 달러"
    return f"US${v:,.0f}" if not ko else f"{v:,.0f}달러"

CSS = """.wc-hero{background:#0b1f3a;color:#fff;padding:72px 0 56px}.wc-hero h1{font-size:52px;margin:0 0 14px}.wc-hero .lede{color:#d5dce6;max-width:66ch;font-size:18px;line-height:1.7}
.wc-st{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:30px 0 22px}.wc-st div{background:rgba(255,255,255,.06);padding:18px 20px}.wc-st b{display:block;font-size:34px;color:#e9c46a}.wc-st span{font-size:14px;color:#d5dce6}.wc-st small{display:block;color:#9fb0c6;font-size:12.5px;margin-top:4px}
.wc-j{display:flex;flex-wrap:wrap;gap:8px}.wc-j a{border:1px solid rgba(255,255,255,.35);padding:7px 14px;border-radius:18px;font-size:14px;color:#fff}
.wc-steps{display:grid;gap:14px;counter-reset:s}.wc-step{display:grid;grid-template-columns:200px minmax(0,1fr) minmax(0,1fr);gap:22px;background:#fff;border:1px solid #e3e6ea;padding:22px 24px;counter-increment:s}
.wc-step h3{margin:0;font-size:20px}.wc-step h3:before{content:counter(s);display:block;font-size:13px;color:#9a7a36;font-weight:700;margin-bottom:4px}.wc-step h4{margin:0 0 6px;font-size:13px;color:#6b7280;font-weight:700}
.wc-step p{margin:0 0 8px;font-size:15px;line-height:1.65}.wc-step .lk a{display:inline-block;margin:4px 8px 0 0;font-size:13.5px;color:#1e4fb8;border-bottom:1px solid #c6d4f3}.wc-step .we{background:#f4f6fa;padding:14px 16px}
.wc-t{width:100%;border-collapse:collapse;font-size:14.5px}.wc-t th{text-align:left;font-size:12.5px;color:#6b7280;border-bottom:2px solid #0b1f3a;padding:8px}.wc-t td{border-bottom:1px solid #e3e6ea;padding:10px 8px;vertical-align:top}.wc-t td.n{white-space:nowrap;font-weight:700}
.wc-t a{color:#1e4fb8}.wc-f{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px;align-items:center}.wc-f input{flex:1 1 240px;min-width:0;padding:10px 12px;border:1px solid #c5cad3;font:inherit;font-size:15px}
.wc-bars{display:grid;gap:6px;margin:6px 0 18px}.wc-bar{display:grid;grid-template-columns:150px minmax(0,1fr) 44px;gap:10px;align-items:center;font-size:14px}.wc-bar i{display:block;height:12px;background:#0b1f3a}.wc-bar.kr i{background:#c9a45c}
.wc-two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.4fr);gap:28px}.wc-ins{background:#fff7e6;border-left:4px solid #c9a45c;padding:14px 16px;font-size:15.5px;line-height:1.6;margin:0 0 18px}
.wc-plan{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.wc-plan div{background:#0b1f3a;color:#fff;padding:20px}.wc-plan b{color:#e9c46a;font-size:14px}.wc-plan h3{margin:6px 0 8px;font-size:18px}.wc-plan p{margin:0;color:#d5dce6;font-size:14.5px;line-height:1.6}
.wc-ord{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.wc-ord a{display:block;background:#fff;border:1px solid #d5dae2;padding:20px}.wc-ord b{display:block;font-size:17px;margin-bottom:6px;color:#0b1f3a}.wc-ord span{font-size:14px;color:#4b515c}
.wc-more{text-align:center;padding:16px;background:#f4f6fa;margin-top:10px;font-size:14.5px}.wc-more a{color:#1e4fb8;font-weight:700}
.wc-tag{display:inline-block;font-size:12px;padding:2px 7px;background:#eef1f5;margin:2px 4px 0 0}
@media(max-width:900px){.wc-hero h1{font-size:36px}.wc-st{grid-template-columns:1fr}.wc-step{grid-template-columns:1fr;gap:10px}.wc-two{grid-template-columns:1fr}.wc-plan,.wc-ord{grid-template-columns:1fr 1fr}.wc-bar{grid-template-columns:110px minmax(0,1fr) 36px}.wc-t .hm{display:none}}
@media(max-width:520px){.wc-plan,.wc-ord{grid-template-columns:1fr}}"""

def _wt(L):
    p = os.path.join(ROOT, "tools", "tr", f"win_{L}.json")
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return {}
def _tr(v, D):
    if isinstance(v, str): return D.get(v, v)
    if isinstance(v, list): return [_tr(x, D) for x in v]
    if isinstance(v, tuple): return tuple(_tr(x, D) for x in v)
    if isinstance(v, dict): return {k: _tr(x, D) for k, x in v.items()}
    return v

def win_page(L, C):
    ko = L == "ko"; e = C["e"]; i = 0 if ko else 1
    D = {} if L in ("ko", "en") else _wt(L)
    t = T["ko"] if ko else _tr(T["en"], D)
    STEPS_ = STEPS if ko else [(k, (n[0], D.get(n[1], n[1])), (d[0], D.get(d[1], d[1])), [(a, D.get(b, b), u) for a, b, u in ext], (w[0], D.get(w[1], w[1])), [(a, D.get(b, b), u) for a, b, u in our]) for k, n, d, ext, w, our in STEPS]
    PLAN_ = PLAN if ko else [tuple((x[0], D.get(x[1], x[1])) for x in row) for row in PLAN]
    ORD_ = ORD if ko else [(k, (n[0], D.get(n[1], n[1])), (d[0], D.get(d[1], d[1]))) for k, n, d in ORD]
    P = _load("pipeline.json"); A = _load("awards.json"); TD = _load("tenders.json")
    pi = [x for x in P.get("items", []) if 0 < x.get("usd", 0) < 2e10]
    n_kr = len(A.get("korea") or []); n_a = A.get("count", 0)
    stats = (f'<div><b>{TD.get("count", 0):,}</b><span>{e(t["s1"])}</span><small>{e(t["s1b"])}</small></div>'
             f'<div><b>{P.get("count", 0):,}</b><span>{e(t["s2"])}</span><small>{e(t["s2b"])} · {_usd(sum(x["usd"] for x in pi), ko)}</small></div>'
             f'<div><b>{n_a:,}</b><span>{e(t["s3"])}</span><small>{e(t["s3b"])} {n_kr}</small></div>')
    jump = "".join(f'<a href="#{k}">{e(v)}</a>' for k, v in t["j"])
    def lk(h):
        if h.startswith("https://") or h.startswith("#"): return h if h != "#" else f"/{L}/#map"
        return f"/{L}/{h}"
    steps = "".join(f'<article class="wc-step" id="st-{k}"><h3>{e(nm[i])}</h3><div><h4>{e(t["do"])}</h4><p>{e(do[i])}</p><p class="lk">' +
                    "".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(a if ko else b)} ↗</a>' for a, b, u in ext) +
                    f'</p></div><div class="we"><h4>{e(t["we"])}</h4><p>{e(we[i])}</p><p class="lk">' + "".join(f'<a href="{e(lk(u))}">{e(a if ko else b)} →</a>' for a, b, u in our) + '</p></div></article>'
                    for k, nm, do, ext, we, our in STEPS_)
    def sec_name(x):
        import pages3 as P3
        names = {k: (nk if ko else ne) for k, nk, ne, *_ in P3.SECT}
        return " ".join(f'<span class="wc-tag">{e(names[s])}</span>' for s in x.get("sec", []) if s in names)
    def cname(x): return C["nm"](x["iso"], L) if x.get("iso") else x.get("ctry", "")
    prow = "".join(f'<tr><td>{C["flag"](x["iso"]) if x.get("iso") else ""} {e(cname(x))}</td><td><a href="{e(x["url"])}" target="_blank" rel="noopener nofollow">{e(x["title"])}</a></td><td class="n">{_usd(x["usd"], ko)}</td><td class="hm">{sec_name(x)}</td></tr>' for x in pi[:12])
    by = A.get("by_country") or []; mx = max([v for _, v in by[:10]] or [1])
    bars = "".join(f'<div class="wc-bar"><span>{e(k)}</span><i style="width:{max(2, v * 100 // mx)}%"></i><b>{v}</b></div>' for k, v in by[:10])
    krs = A.get("korea") or []
    kr = "".join(f'<li><b>{e(x["winner"])}</b> · {e(x["ctry"])} · {e(x["cur"])} {x["amt"]:,.0f} · {e(x["date"])} <a href="{e(x["url"])}" target="_blank" rel="noopener nofollow">↗</a></li>' for x in krs[:8] if x.get("amt")) or "<li>—</li>"
    def amt(x):
        if not x.get("amt"): return "—"
        s = f'{e(x["cur"])} {x["amt"]:,.0f}'
        return s + (f'<br><small>≈ {_usd(x["usd"], ko)}</small>' if x.get("usd") and x["cur"] != "USD" else "")
    arow = "".join(f'<tr><td>{e(x["date"])}</td><td>{e(cname(x))}</td><td class="hm">{e(x["title"][:110])}</td><td>{e(x["winner"])} <small>({e(x["wctry"])})</small>{" · JV" if x.get("jv") else ""}</td><td class="n">{amt(x)}</td></tr>' for x in (A.get("items") or [])[:12])
    plan = "".join(f'<div><b>{e(w[i])}</b><h3>{e(h[i])}</h3><p>{e(p[i])}</p></div>' for w, h, p in PLAN_)
    order = "".join(f'<a href="/{L}/pricing/?p={k}#order"><b>{e(n[i])}</b><span>{e(d[i])}</span></a>' for k, n, d in ORD_)
    upd = (P.get("updated") or A.get("updated") or "")[:10]
    ins = t["ains"].replace("{n}", f"{n_a:,}").replace("{k}", str(n_kr))
    js = """<script>(function(){var F=%s,L=%s,ko=L==="ko";function es(s){return String(s||"").replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function us(v){if(!v)return"—";if(ko){if(v>=1e8)return Math.round(v/1e8).toLocaleString()+"억 달러";if(v>=1e6)return Math.round(v/1e6).toLocaleString()+"백만 달러";return Math.round(v).toLocaleString()+"달러"}
if(v>=1e9)return"US$"+(v/1e9).toFixed(1)+"B";if(v>=1e6)return"US$"+Math.round(v/1e6)+"M";return"US$"+Math.round(v).toLocaleString()}
function wire(inp,tb,rows,row,lim){function draw(){var q=(inp.value||"").toLowerCase().trim(),n=0,h="";rows.forEach(function(x){if(n>=lim)return;if(q&&JSON.stringify(x).toLowerCase().indexOf(q)<0)return;h+=row(x);n++});tb.innerHTML=h||"<tr><td colspan=5>—</td></tr>"}inp.addEventListener("input",draw);draw()}
fetch(F+"pipeline.json",{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){var it=(j.items||[]).filter(function(x){return x.usd>0&&x.usd<2e10});
wire(document.getElementById("pq"),document.getElementById("pt"),it,function(x){return"<tr><td>"+es(x.n&&x.n[L]||x.ctry)+'</td><td><a href="'+es(x.url)+'" target="_blank" rel="noopener nofollow">'+es(x.title)+'</a></td><td class="n">'+us(x.usd)+'</td><td class="hm">'+es((x.wbsec||[]).slice(0,2).join(", "))+"</td></tr>"},12)}).catch(function(){});
fetch(F+"awards.json",{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){
wire(document.getElementById("aq"),document.getElementById("at"),j.items||[],function(x){var a=x.amt?es(x.cur)+" "+Math.round(x.amt).toLocaleString()+(x.usd&&x.cur!=="USD"?"<br><small>≈ "+us(x.usd)+"</small>":""):"—";
return"<tr><td>"+es(x.date)+"</td><td>"+es(x.ctry)+'</td><td class="hm">'+es((x.title||"").slice(0,110))+"</td><td>"+es(x.winner)+" <small>("+es(x.wctry)+")</small>"+(x.jv?" · JV":"")+'</td><td class="n">'+a+"</td></tr>"},12)}).catch(function(){});
})();</script>""" % (json.dumps(FEED), json.dumps(L))
    body = f'''<style>{CSS}</style>
<section class="wc-hero"><div class="in"><p class="crumb"><a href="/{L}/" style="color:#9fb0c6">GOV RADAR</a> · <a href="/{L}/mdb/" style="color:#9fb0c6">{"입찰·마감 보드" if ko else D.get("Tender board", "Tender board")}</a></p>
<h1>{e(t["h1"])}</h1><p class="lede">{e(t["lead"])}</p><div class="wc-st">{stats}</div><div class="wc-j">{jump}</div></div></section>
<section class="band" id="steps"><div class="in"><h2>{e(t["sh"])}</h2><p class="note">{e(t["sl"])}</p><div class="wc-steps">{steps}</div></div></section>
<section class="band alt" id="pipe"><div class="in"><h2>{e(t["ph"])}</h2><p class="note">{e(t["pl"])}</p>
<div class="wc-f"><input id="pq" type="search" placeholder="{e(t["q"])}" aria-label="{e(t["q"])}"></div>
<table class="wc-t"><thead><tr><th>{e(t["pc"][0])}</th><th>{e(t["pc"][1])}</th><th>{e(t["pc"][2])}</th><th class="hm">{e(t["pc"][3])}</th></tr></thead><tbody id="pt">{prow}</tbody></table>
<p class="note">{e(t["pnote"])}</p><div class="wc-more">{e(t["more"])} · <a href="/{L}/pricing/?p=member#order">{e(t["moreb"])} →</a></div></div></section>
<section class="band" id="awards"><div class="in"><h2>{e(t["ah"])}</h2><p class="note">{e(t["al"])}</p><p class="wc-ins">{e(ins)}</p>
<div class="wc-two"><div><h3>{e(t["abc"])}</h3><div class="wc-bars">{bars}</div><h3>{e(t["akr"])}</h3><ul>{kr}</ul></div>
<div><div class="wc-f"><input id="aq" type="search" placeholder="{e(t["q"])}" aria-label="{e(t["q"])}"></div>
<table class="wc-t"><thead><tr><th>{e(t["ac"][0])}</th><th>{e(t["ac"][1])}</th><th class="hm">{e(t["ac"][2])}</th><th>{e(t["ac"][3])}</th><th>{e(t["ac"][4])}</th></tr></thead><tbody id="at">{arow}</tbody></table>
<p class="note">{e(t["anote"])}</p></div></div><div class="wc-more">{e(t["more"])} · <a href="/{L}/pricing/?p=member#order">{e(t["moreb"])} →</a></div></div></section>
<section class="band alt" id="plan"><div class="in"><h2>{e(t["plh"])}</h2><p class="note">{e(t["pll"])}</p><div class="wc-plan">{plan}</div></div></section>
<section class="band" id="order"><div class="in"><h2>{e(t["oh"])}</h2><p class="note">{e(t["ol"])}</p><div class="wc-ord">{order}</div>
<p class="note" style="margin-top:18px">{e(t["upd"])} {e(upd)} · {e(t["src"])}</p></div></section>{js}'''
    return C["head"](L, t["title"], t["desc"], f"/{L}/win/", {l: f"/{l}/win/" for l in C["LANGS"]}, '<meta name="gv-tr" content="1">' if D else "") + body + C["foot"](L)

BAND = {"ko": ("입찰은 이기는 것이 어렵습니다 — 입찰 수주 센터", "공고가 나오기 전 사업, 누가 얼마에 따냈는지, 입찰마다 준비할 서류와 일정까지 한곳에서 봅니다.",
               ["입찰 전 사업", "최근 낙찰 공고", "그중 한국 기업"], ["입찰 전 사업 레이더", "낙찰·경쟁사 분석", "수주 7단계", "90일 실행 계획"], "수주 센터 열기"),
        "en": ("Winning is the hard part — the tender win centre", "Projects before their notices, who won and for how much, and the documents and schedule each tender needs — in one place.",
               ["Pre-tender projects", "Recent contract awards", "won by Korean firms"], ["Pre-tender radar", "Awards and competitors", "7 steps to win", "90-day plan"], "Open the win centre")}
BAND.update({
 "es": ("Ganar es lo difícil — el centro para ganar licitaciones", "Proyectos antes de su anuncio, quién ganó y por cuánto, y los documentos y plazos de cada licitación, en un solo lugar.",
        ["Proyectos previos a licitación", "Adjudicaciones recientes", "ganadas por empresas coreanas"], ["Radar previo a licitación", "Adjudicaciones y competidores", "7 pasos para ganar", "Plan de 90 días"], "Abrir el centro"),
 "fr": ("Le plus dur, c'est de gagner — le centre pour gagner les appels d'offres", "Les projets avant leur avis, qui a gagné et pour combien, et les documents et délais de chaque appel d'offres, au même endroit.",
        ["Projets avant appel d'offres", "Attributions récentes", "remportées par des entreprises coréennes"], ["Radar avant appel d'offres", "Attributions et concurrents", "7 étapes pour gagner", "Plan de 90 jours"], "Ouvrir le centre"),
 "ar": ("الفوز هو الجزء الصعب — مركز الفوز بالمناقصات", "مشاريع قبل إعلانها، ومن فاز وبكم، والمستندات والمواعيد التي تحتاجها كل مناقصة، في مكان واحد.",
        ["مشاريع قبل المناقصة", "ترسيات حديثة", "فازت بها شركات كورية"], ["رادار ما قبل المناقصة", "الترسيات والمنافسون", "7 خطوات للفوز", "خطة 90 يومًا"], "افتح المركز"),
 "vi": ("Khó nhất là thắng thầu — Trung tâm trúng thầu", "Dự án trước khi mời thầu, ai thắng và giá bao nhiêu, cùng hồ sơ và lịch cho từng gói thầu, tất cả ở một nơi.",
        ["Dự án trước mời thầu", "Kết quả trao thầu gần đây", "do doanh nghiệp Hàn Quốc thắng"], ["Radar trước mời thầu", "Trao thầu và đối thủ", "7 bước để thắng", "Kế hoạch 90 ngày"], "Mở trung tâm"),
 "id": ("Yang sulit adalah menang — pusat menang tender", "Proyek sebelum pengumumannya, siapa yang menang dan berapa nilainya, serta dokumen dan jadwal tiap tender, di satu tempat.",
        ["Proyek pra-tender", "Pemenang kontrak terbaru", "dimenangkan perusahaan Korea"], ["Radar pra-tender", "Pemenang dan pesaing", "7 langkah menang", "Rencana 90 hari"], "Buka pusat")})
def win_band(L, C):
    ko = L == "ko"; e = C["e"]; h, p, st, ch, cta = BAND.get(L) or BAND["en"]
    P = _load("pipeline.json"); A = _load("awards.json"); pi = [x for x in P.get("items", []) if 0 < x.get("usd", 0) < 2e10]
    nums = [f'{P.get("count", 0):,}', f'{A.get("count", 0):,}', str(len(A.get("korea") or []))]
    subs = [_usd(sum(x["usd"] for x in pi), ko), "World Bank", f'/ {A.get("count", 0):,}']
    anc = ["pipe", "awards", "steps", "plan"]
    return (f'<section class="band wband" id="win"><div class="in"><h2>{e(h)}</h2><p class="note">{e(p)}</p><div class="wb-g">' +
            "".join(f'<a href="/{L}/win/#{["pipe","awards","awards"][i]}"><b>{n}</b><span>{e(st[i])}</span><small>{e(subs[i])}</small></a>' for i, n in enumerate(nums)) +
            '</div><div class="wb-c">' + "".join(f'<a href="/{L}/win/#{anc[i]}">{e(c)} →</a>' for i, c in enumerate(ch)) +
            f'</div><p class="cta"><a class="btn pri" href="/{L}/win/">{e(cta)}</a></p></div>'
            '<style>.wband{background:#0b1f3a;color:#fff}.wband h2{color:#fff}.wband .note{color:#c9d3e0}.wb-g{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:18px 0}'
            '.wb-g a{background:rgba(255,255,255,.06);padding:18px 20px;color:#fff}.wb-g b{display:block;font-size:34px;color:#e9c46a}.wb-g span{font-size:14.5px}.wb-g small{display:block;color:#9fb0c6;font-size:12.5px}'
            '.wb-c{display:flex;flex-wrap:wrap;gap:8px}.wb-c a{border:1px solid rgba(255,255,255,.35);padding:7px 14px;border-radius:18px;font-size:14px;color:#fff}.wband .btn.pri{background:#c9a45c;color:#0b1f3a;border-color:#c9a45c}'
            '@media(max-width:700px){.wb-g{grid-template-columns:1fr}}</style></section>')
