/* WMM GOV RADAR — read-only official source panels.
   Only public NWS and CISA data. No tracking, keys, incident inference or payments. */
(function () {
  "use strict";
  var rootUrl = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/hz/";
  var lang = (document.documentElement.lang || "").toLowerCase();
  var ko = lang.slice(0, 2) === "ko";
  var cyber = location.pathname.indexOf("/cyber") === 0;
  var I = ko ? {
    title:"공식기관 데이터 · 확인된 정보만", intro:"기관 발표 자료와 원문을 확인하세요. 각 기관의 정보는 지역과 목적이 서로 다릅니다.",
    nws:"미국 기상청 NWS · 실제 발효 중인 중대 기상특보", cisa:"미국 CISA KEV · 악용 확인 취약점",
    loading:"공식 자료를 불러오는 중입니다", unavailable:"정보원 확인 불가 — 최신 상황이라고 판단하지 마세요",
    delayed:"갱신 지연 · 기존 자료 표시", okay:"공식 자료 확인", time:"마지막 정상 확인",
    none:"현재 선택 기준에 해당하는 항목 없음", item:"표시 항목", total:"전체 목록",
    nwsNote:"미국 지역 기상특보입니다. 세계 전체의 재난 현황이나 실제 피해를 의미하지 않습니다.",
    cisaNote:"공개된 취약점 우선대응 자료입니다. 현재 공격·침해사고 발생 건수가 아닙니다.",
    bad:"자료 연결에 실패했습니다. 원문을 직접 확인하세요.",
    source:"기관 원문 열기"
  } : {
    title:"Official agency data · verified sources", intro:"Check the original agency records. Each feed has a specific geographic and analytical scope.",
    nws:"US NWS · active severe weather alerts", cisa:"US CISA KEV · known exploited vulnerabilities",
    loading:"Loading official source data", unavailable:"Source unavailable — current status cannot be verified",
    delayed:"Source delayed · showing last known data", okay:"Agency feed confirmed", time:"Last verified fetch",
    none:"No items match the selected criteria", item:"Displayed records", total:"Catalog total",
    nwsNote:"US weather alerts only. This is not a worldwide disaster assessment or proof of impact.",
    cisaNote:"Vulnerability prioritization data, not evidence of a current cyberattack or breach.",
    bad:"Agency feed unavailable. Check the original source directly.",
    source:"View official source"
  };
  var sources = {
    nws: {file:"nws_active.json", title:I.nws, url:"https://www.weather.gov/documentation/services-web-alerts", staleMs:65*60*1000},
    cisa: {file:"cisa_kev.json", title:I.cisa, url:"https://www.cisa.gov/known-exploited-vulnerabilities-catalog", staleMs:30*60*60*1000}
  };
  function el(tag, cls, value) {
    var x=document.createElement(tag);
    if(cls)x.className=cls;
    if(value!=null)x.textContent=String(value);
    return x;
  }
  function clear(n){while(n.firstChild)n.removeChild(n.firstChild);}
  function validLink(input, type) {
    try {
      var u=new URL(String(input));
      if(u.protocol!=="https:")return null;
      var allow=type==="nws" ? ["api.weather.gov","www.weather.gov"] : ["nvd.nist.gov"];
      if(allow.indexOf(u.hostname)<0)return null;
      return u.href;
    }catch(e){return null;}
  }
  function utcText(t) {
    var d=new Date(t);
    return Number.isFinite(d.getTime())?d.toISOString().slice(0,16).replace("T"," ")+" UTC":"—";
  }
  function safeFresh(h, type) {
    if(!h || h.ok!==true || h.stale === true)return false;
    var d=new Date(h.last_ok);
    return Number.isFinite(d.getTime()) && Math.abs(Date.now()-d.getTime()) < sources[type].staleMs;
  }
  function createPanel(type) {
    var s=sources[type], card=el("article","wmm-of-card");
    var title=el("h3","wmm-of-title",s.title);
    var status=el("p","wmm-of-status",I.loading);
    var stats=el("p","wmm-of-count","");
    var ul=el("ul","wmm-of-list");
    var note=el("p","wmm-of-note",type==="nws"?I.nwsNote:I.cisaNote);
    var a=el("a","wmm-of-link",I.source);
    a.href=s.url;a.target="_blank";a.rel="noopener noreferrer";
    card.appendChild(title);card.appendChild(status);card.appendChild(stats);
    card.appendChild(ul);card.appendChild(note);card.appendChild(a);
    s.nodes={status:status,stats:stats,list:ul};
    return card;
  }
  function render(type, d) {
    var n=sources[type].nodes;
    clear(n.list);
    if(!d || !Array.isArray(d.items) || !d.source_health ||
       (type==="cisa" && d.not_realtime_attack_feed !== true)) {
      n.status.textContent=I.unavailable;
      n.stats.textContent=I.bad;
      n.status.className="wmm-of-status wmm-of-delay";
      return;
    }
    var h=d.source_health, okay=safeFresh(h,type);
    n.status.className="wmm-of-status"+(okay?"":" wmm-of-delay");
    n.status.textContent=(okay?I.okay:(h.last_ok?I.delayed:I.unavailable))+
      " · "+I.time+": "+utcText(h.last_ok);
    if(type==="nws"){
      n.stats.textContent=okay ?
        (I.item+": "+Number(d.filtered_count||0)+" / "+(ko?"미국 중대특보":"US severe/extreme alerts")) :
        I.unavailable;
    } else {
      n.stats.textContent=I.total+": "+
        (Number.isFinite(Number(d.total_vulnerabilities)) ? Number(d.total_vulnerabilities).toLocaleString(ko?"ko-KR":"en-US") : "—")+
        " · "+I.item+": "+Math.min(d.items.length,100);
    }
    if(!h.last_ok){return;}
    var rows=d.items.slice(0,8);
    if(!rows.length && okay){n.list.appendChild(el("li","",I.none));return;}
    rows.forEach(function(item){
      if(!item||typeof item!=="object")return;
      var li=el("li","wmm-of-item");
      var desc=type==="nws"
        ? (String(item.severity||"")+" · "+String(item.title||item.event||""))
        : (String(item.cve||"")+" · "+String(item.vendor||"")+" "+String(item.product||""));
      var u=validLink(item.url,type);
      if(u){var a=el("a","",desc.slice(0,180));a.href=u;a.target="_blank";a.rel="noopener noreferrer";li.appendChild(a);}
      else li.appendChild(el("span","",desc.slice(0,180)));
      var sub=type==="nws"?String(item.area||"").slice(0,120):String(item.date_added||"");
      if(sub)li.appendChild(el("small","",sub));
      n.list.appendChild(li);
    });
  }
  function renderFail(type){
    var n=sources[type].nodes;
    n.status.className="wmm-of-status wmm-of-delay";
    n.status.textContent=I.unavailable;
    n.stats.textContent=I.bad;clear(n.list);
  }
  function fetchOne(type) {
    var s=sources[type];
    fetch(rootUrl+s.file,{cache:"no-store"}).then(function(r){
      if(!r.ok)throw new Error("public feed unavailable");
      return r.json();
    }).then(function(d){render(type,d);}).catch(function(){renderFail(type);});
  }
  function init(){
    if(document.getElementById("wmm-official-sources"))return;
    var hero=document.querySelector("section.hero");
    var alt=document.getElementById("trend")||document.querySelector("main");
    if(!hero && !alt)return;
    var style=el("style");
    style.textContent=".wmm-of{max-width:1180px;margin:32px auto;padding:23px 22px;color:#eef3fa;background:#0b111b;border:1px solid #334050;border-radius:14px;font-family:inherit;box-sizing:border-box}.wmm-of *{box-sizing:border-box}.wmm-of h2{font-size:22px;color:#fff;margin:0 0 6px;font-weight:700}.wmm-of .intro{font-size:14px;line-height:1.6;color:#c3cedc;margin:0 0 20px}.wmm-of-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.wmm-of-card{padding:18px;border:1px solid #273244;background:#111927;border-radius:10px;min-width:0}.wmm-of-title{font-size:16px;color:#fff;margin:0 0 10px}.wmm-of-status{font-size:12px;color:#78e3bb;margin:0 0 10px}.wmm-of-delay{color:#f2b24a}.wmm-of-count{font-size:15px;color:#e5edf7;margin:0 0 12px}.wmm-of-list{list-style:none;margin:0;padding:0}.wmm-of-item{border-top:1px solid #263142;padding:9px 0;font-size:14px;line-height:1.5;overflow-wrap:anywhere}.wmm-of-item a{color:#c6eaff;text-decoration:underline;text-underline-offset:3px}.wmm-of-item small{display:block;color:#a1b0c4;font-size:12px;margin-top:2px}.wmm-of-note{font-size:12px;color:#bcc8d6;line-height:1.6;margin:12px 0}.wmm-of-link{font-size:13px;color:#c9a45c;text-decoration:underline}@media(max-width:760px){.wmm-of{margin:20px 12px;padding:18px 14px}.wmm-of-grid{grid-template-columns:1fr}.wmm-of h2{font-size:19px}}";
    document.head.appendChild(style);
    var section=el("section","wmm-of");
    section.id="wmm-official-sources";
    section.setAttribute("aria-label",I.title);
    section.appendChild(el("h2","",I.title));
    section.appendChild(el("p","intro",I.intro));
    var grid=el("div","wmm-of-grid");
    var order=cyber?["cisa","nws"]:["nws","cisa"];
    order.forEach(function(type){grid.appendChild(createPanel(type));});
    section.appendChild(grid);
    if(hero)hero.insertAdjacentElement("afterend",section);
    else alt.parentNode.insertBefore(section,alt);
    order.forEach(fetchOne);
    setInterval(function(){order.forEach(fetchOne);},10*60*1000);
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);
  else init();
})();