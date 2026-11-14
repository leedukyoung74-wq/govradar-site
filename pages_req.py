"""Member analysis requests (doc 2026-11-14 §2–3): four fixed-scope requests.
Flow: pick a request → see output, limit and handling rule before sending → fill only what is needed →
request number issued, double submit blocked → lands in the Netlify "order" form (same inbox and Gmail-draft alert).
Copy is Korean and English; the other five languages show the English copy."""
from html import escape as e

K = {
 "ko": dict(
  t="회원 분석 의뢰", lede="결과물의 범위가 정해진 네 가지 의뢰부터 받습니다. 보내기 전에 받게 될 결과물, 한도 차감, 처리 기준을 먼저 보여 드립니다.",
  who="대상: 분석 회원(월 19,800원). 매달 2건까지 포함됩니다. 회원이 아니거나 2건을 넘으면 건당 견적을 먼저 이메일로 보내 드리고, 동의하신 뒤에 시작합니다.",
  pick="1. 의뢰 고르기", fill="2. 필요한 정보만 입력", send="3. 확인하고 보내기",
  out="받는 결과물", need="필요한 정보", rule="처리 기준",
  limit="한도: 분석 회원은 매달 2건(매월 1일 새로 시작). 결과는 접수 확인 후 5영업일 안에 이메일로 보내고, 같은 의뢰에 대한 보완 질문 1회는 추가 차감 없이 답합니다. 요금표의 '입찰 적합도 판정(건당 10만 원)'은 서류 목록·컨소시엄 구성안·참여자 구성까지 들어가는 상세판이고, 여기의 회원 의뢰는 참가 가능 여부와 부족한 조건을 정리하는 빠른 검토입니다.",
  rule_all="접수 확인은 1영업일 안에 이메일로 보냅니다. 결과물에는 결론·근거·확인하지 못한 점·다음 할 일을 함께 적습니다. 분석이 실패하면 무한히 다시 돌리지 않고, 실패 사유를 알려 드리며 그 의뢰는 한도에서 빼지 않습니다.",
  email="이메일", name="이름 또는 담당자", org="회사·단체명 (선택)", country="관심 국가", code="회원 코드 (있으면)",
  agree="개인정보 수집·이용(의뢰 처리 목적, 처리 후 1년 보관)에 동의합니다", btn="의뢰 보내기", sending="보내는 중…",
  done="접수되었습니다. 요청번호", dup="같은 내용을 방금 보내셨습니다. 요청번호", mine="이 브라우저에서 보낸 의뢰", mine_n="아직 보낸 의뢰가 없습니다.",
  st="접수됨 — 확인 메일을 기다려 주세요", req="필수 항목을 채워 주세요.",
  types=[
   ("tender", "이 입찰에 우리 회사가 참여할 수 있는지 검토", "참가 자격·필요 서류·부족한 조건을 정리한 참가 조건표와 참여 권고(예·조건부·아니오)", "공고 링크 또는 제목, 업종, 연 매출, 공공·해외 실적, 보유 인증",
    [("tender", "공고 링크 또는 제목", "text", True), ("industry", "업종·주력 제품", "text", True), ("revenue", "연 매출 (억 원)", "number", False), ("record", "공공·해외 실적 (간단히)", "textarea", False), ("certs", "보유 인증", "text", False)]),
   ("country", "관심 국가의 사업 기회 정리", "그 나라 정부 과제·예산 사업·진행 중 입찰·ODA 중 우리 업종과 맞는 기회 5~10건과 접근 순서", "국가, 업종·제품, 원하는 진출 방식",
    [("industry", "업종·주력 제품", "text", True), ("mode", "원하는 방식 (수출·현지 파트너·입찰·투자 등)", "text", False), ("goal", "알고 싶은 것", "textarea", False)]),
   ("family", "우리 가족 재난 준비계획 작성", "우리 지역 위험에 맞춘 30일 준비계획: 비축 목록·수량, 연락·대피 계획, 점검 일정", "지역(시·군 단위), 가족 수, 영유아·고령자·반려동물 여부",
    [("area", "사는 지역 (시·군 단위까지만)", "text", True), ("people", "가족 수", "number", True), ("care", "영유아·고령자·반려동물 (해당하는 것만)", "text", False), ("note", "특별히 챙길 점 (선택, 건강 정보는 꼭 필요한 만큼만)", "textarea", False)]),
   ("partner", "내가 찾는 파트너와 지원 경로 정리", "찾는 상대의 유형·후보를 찾는 경로, 정부·기관 지원 사업, 첫 연락 방법", "찾는 상대, 내 제품·기술, 지역",
    [("seek", "찾는 상대 (바이어·제조사·현지 대리인 등)", "text", True), ("offer", "우리 제품·기술", "text", True), ("note", "조건·일정 (선택)", "textarea", False)]),
  ]),
 "en": dict(
  t="Member analysis requests", lede="We start with four requests whose output is fixed in advance. Before you send, you see what you will receive, how it counts against your limit, and how it is handled.",
  who="For analysis members (KRW 19,800 a month): two requests a month are included. Non-members and extra requests get a quote by email first, and we start only after you agree.",
  pick="1. Choose a request", fill="2. Give only what is needed", send="3. Check and send",
  out="You receive", need="We need", rule="Handling",
  limit="Limit: two requests a month for analysis members (resets on the 1st). Results arrive by email within five business days of confirmation, and one follow-up question on the same request is answered at no extra count. The per-tender 'fit assessment' (KRW 100,000) on the pricing page is the detailed version with document list, consortium plan and team; member requests are a quick check of eligibility and gaps.",
  rule_all="We confirm receipt by email within one business day. Every result states the conclusion, the evidence, what could not be confirmed and the next step. A failed analysis is not retried endlessly; we tell you why and it does not count against your limit.",
  email="Email", name="Name or contact person", org="Company or organisation (optional)", country="Country of interest", code="Member code (if any)",
  agree="I agree to the collection and use of my details to handle this request (kept for one year)", btn="Send request", sending="Sending…",
  done="Received. Request number", dup="You just sent the same request. Request number", mine="Requests sent from this browser", mine_n="No requests yet.",
  st="Received — watch for our confirmation email", req="Please fill in the required fields.",
  types=[
   ("tender", "Can our company bid on this tender?", "An entry-conditions table (eligibility, documents, gaps) and a recommendation: yes, conditional or no", "Notice link or title, industry, annual revenue, public or overseas record, certifications",
    [("tender", "Notice link or title", "text", True), ("industry", "Industry and main product", "text", True), ("revenue", "Annual revenue (USD)", "text", False), ("record", "Public or overseas record (brief)", "textarea", False), ("certs", "Certifications", "text", False)]),
   ("country", "Business opportunities in a country", "5–10 matching opportunities from government priorities, funded projects, open tenders and ODA, with an order of approach", "Country, industry or product, preferred way in",
    [("industry", "Industry and main product", "text", True), ("mode", "Preferred way in (export, local partner, tender, investment…)", "text", False), ("goal", "What you want to know", "textarea", False)]),
   ("family", "A preparedness plan for my family", "A 30-day plan for your area's risks: supplies and quantities, contact and evacuation plan, check-up schedule", "Area (city or district only), household size, infants, elderly or pets",
    [("area", "Where you live (city or district only)", "text", True), ("people", "Household size", "number", True), ("care", "Infants, elderly, pets (only what applies)", "text", False), ("note", "Anything special (optional; health details only as needed)", "textarea", False)]),
   ("partner", "Partners and support routes for what I need", "Types of partner and where to find candidates, public support programmes, how to make first contact", "Who you seek, your product or technology, region",
    [("seek", "Who you seek (buyer, manufacturer, local agent…)", "text", True), ("offer", "Your product or technology", "text", True), ("note", "Conditions or timing (optional)", "textarea", False)]),
  ]),
}


def request_page(L, head, foot, LANGS):
    k = K.get(L) or K["en"]
    ko = L == "ko"
    cards = "".join(f'''<label class="rq-c"><input type="radio" name="rqt" value="{tid}"{" checked" if i == 0 else ""}><b>{e(tt)}</b>
<span><i>{e(k["out"])}</i> {e(out)}</span><span><i>{e(k["need"])}</i> {e(nd)}</span></label>''' for i, (tid, tt, out, nd, _) in enumerate(k["types"]))
    fields = "".join(f'<div class="rq-f" data-t="{tid}"' + ("" if i == 0 else " hidden") + ">" + "".join(
        (f'<label>{e(lb)}{" *" if rq else ""}<textarea data-k="{fk}" rows="3"{" data-req" if rq else ""}></textarea></label>' if ty == "textarea"
         else f'<label>{e(lb)}{" *" if rq else ""}<input data-k="{fk}" type="{ty}"{" data-req" if rq else ""}></label>')
        for fk, lb, ty, rq in fl) + "</div>" for i, (tid, _, _, _, fl) in enumerate(k["types"]))
    names = {tid: tt for tid, tt, *_ in k["types"]}
    import json
    body = f'''<section class="chero"><div class="in"><p class="crumb"><a href="/{L}/">GOV RADAR</a></p><h1>{e(k["t"])}</h1><p class="lede">{e(k["lede"])}</p><p style="font-size:14px;color:#d8d8d4;margin:10px 0 0">{e(k["who"])}</p></div></section>
<section class="band"><div class="in rq">
<h2>{e(k["pick"])}</h2><div class="rq-g">{cards}</div>
<div class="rq-rule"><p><b>{e(k["rule"])}</b> · {e(k["rule_all"])}</p><p>{e(k["limit"])}</p></div>
<h2>{e(k["fill"])}</h2>
<form class="cform rq-form" name="order" method="POST" data-netlify="true" netlify-honeypot="hp" action="/{L}/thanks/">
<input type="hidden" name="form-name" value="order"><input type="hidden" name="lang" value="{L}"><input type="hidden" name="product"><input type="hidden" name="need"><input type="hidden" name="field">
<p hidden><label>hp<input name="hp"></label></p>
{fields}
<div class="two"><label>{e(k["email"])} *<input name="email" type="email" required></label><label>{e(k["name"])} *<input name="name" required></label></div>
<div class="two"><label>{e(k["org"])}<input name="org"></label><label>{e(k["country"])}<input name="countries"></label></div>
<label>{e(k["code"])}<input data-k="code" autocomplete="off"></label>
<h2>{e(k["send"])}</h2>
<label class="chk"><input type="checkbox" name="privacy_agree" value="yes" required> {e(k["agree"])}</label>
<p><button class="btn pri" type="submit">{e(k["btn"])}</button> <span class="rq-msg note" role="status"></span></p>
</form>
<h3>{e(k["mine"])}</h3><ul class="rq-mine"></ul>
</div></section>
<script>(function(){{var K={json.dumps({"names": names, "done": k["done"], "dup": k["dup"], "st": k["st"], "none": k["mine_n"], "req": k["req"], "sending": k["sending"]}, ensure_ascii=False)};
var f=document.querySelector(".rq-form"),msg=f.querySelector(".rq-msg"),btn=f.querySelector("button[type=submit]");
function cur(){{return (document.querySelector("input[name=rqt]:checked")||{{}}).value}}
document.querySelectorAll("input[name=rqt]").forEach(function(r){{r.addEventListener("change",function(){{f.querySelectorAll(".rq-f").forEach(function(d){{d.hidden=d.dataset.t!==cur()}})}})}});
function load(){{try{{return JSON.parse(localStorage.getItem("gv_rq")||"[]")}}catch(e){{return []}}}}
function save(a){{try{{localStorage.setItem("gv_rq",JSON.stringify(a.slice(0,30)))}}catch(e){{}}}}
function paint(){{var a=load(),u=document.querySelector(".rq-mine");u.innerHTML=a.length?a.map(function(x){{return "<li><b>"+x.id+"</b> · "+(K.names[x.t]||x.t)+" <small class=note>"+x.at+" · "+K.st+"</small></li>"}}).join(""):"<li class=note>"+K.none+"</li>"}}
function hash(s){{var h=0;for(var i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))|0;return String(h)}}
f.addEventListener("submit",function(ev){{var t=cur(),box=f.querySelector('.rq-f[data-t="'+t+'"]'),lines=[],ok=true;
box.querySelectorAll("[data-k]").forEach(function(i){{var v=(i.value||"").trim();if(i.hasAttribute("data-req")&&!v)ok=false;if(v)lines.push(i.parentNode.firstChild.textContent.replace(" *","")+": "+v)}});
var code=(f.querySelector('[data-k=code]').value||"").trim();if(code)lines.push("member code: "+code);
if(!ok){{ev.preventDefault();msg.textContent=K.req;return}}
var h=hash(t+lines.join("|")+f.email.value),a=load(),prev=a.filter(function(x){{return x.h===h&&Date.now()-x.ts<6e5}})[0];
if(prev){{ev.preventDefault();msg.textContent=K.dup+" "+prev.id;return}}
var d=new Date(),id="RQ-"+String(d.getFullYear()).slice(2)+("0"+(d.getMonth()+1)).slice(-2)+("0"+d.getDate()).slice(-2)+"-"+Math.random().toString(36).slice(2,6).toUpperCase();
f.product.value="request:"+t+" "+id;f.field.value=t;f.need.value="["+id+"] "+(K.names[t]||t)+"\\n"+lines.join("\\n");
a.unshift({{id:id,t:t,h:h,ts:Date.now(),at:d.toISOString().slice(0,10)}});save(a);btn.disabled=true;btn.textContent=K.sending;msg.textContent=K.done+" "+id}});
paint()}})();</script>'''
    t_ = k["t"]
    return head(L, t_ + " · GOV RADAR", k["lede"][:150], f"/{L}/request/", {l: f"/{l}/request/" for l in LANGS}) + body + foot(L)
