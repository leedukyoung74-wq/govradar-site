(function(){
"use strict";
var lang=document.documentElement.lang||"en";
var words={
ko:["공식 입찰 데이터 연결 현황","공식 기관 API 수집 결과","수집 상태","최종 성공","유효 공고","원문 보기","DAPA는 정상 응답이지만 검증된 진행 중 공고가 없습니다.","실시간 수집 상태 확인 불가","최신 미국 공고","원문 기관에서 마감일과 내용을 확인하세요."],
en:["Official procurement sources","Government API collection status","Status","Last success","Valid notices","Official notice","DAPA responded successfully but has no verified open notices.","Live source status unavailable","Recent U.S. tenders","Check each notice and deadline with the source."],
es:["Fuentes oficiales de licitaciones","Estado de datos de organismos oficiales","Estado","Último éxito","Avisos válidos","Aviso oficial","DAPA sin avisos abiertos verificados.","Estado no disponible","Licitaciones de EE. UU.","Verifique el plazo en la fuente."],
fr:["Sources officielles des marchés","État des données officielles","Statut","Dernier succès","Avis valides","Avis officiel","DAPA : aucun avis ouvert vérifié.","État indisponible","Marchés américains récents","Vérifiez les délais auprès de la source."],
ar:["مصادر المناقصات الرسمية","حالة جمع البيانات الرسمية","الحالة","آخر نجاح","إعلانات صالحة","الإعلان الرسمي","لا إعلانات مفتوحة مؤكدة من DAPA.","الحالة غير متاحة","أحدث المناقصات الأمريكية","تحقق من المصدر والموعد."],
vi:["Nguồn đấu thầu chính thức","Trạng thái thu thập dữ liệu","Trạng thái","Lần thành công","Thông báo hợp lệ","Thông báo gốc","DAPA không có thông báo mở được xác minh.","Không có trạng thái","Thông báo Mỹ mới","Kiểm tra hạn tại nguồn."],
id:["Sumber tender resmi","Status pengumpulan data","Status","Keberhasilan terakhir","Tender valid","Tender resmi","DAPA belum memiliki tender terbuka terverifikasi.","Status tidak tersedia","Tender AS terbaru","Periksa tenggat pada sumber."]};
var t=words[lang]||words.en, anchor=document.getElementById("deadlines");
if(!anchor||document.getElementById("official-procurement-status"))return;
var s=document.createElement("section");s.className="band alt";s.id="official-procurement-status";
s.innerHTML='<div class="in" style="padding-top:35px;padding-bottom:35px"><h2></h2><p class="note"></p><div class="wmm-src-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(270px,100%),1fr));gap:14px"></div><h3 class="wmm-recent"></h3><ul class="wmm-src-list" style="list-style:none;padding:0"></ul><p class="note wmm-disclaimer"></p></div>';
anchor.parentNode.insertBefore(s,anchor);
s.querySelector("h2").textContent=t[0];s.querySelector("p.note").textContent=t[1];
s.querySelector(".wmm-recent").textContent=t[8];s.querySelector(".wmm-disclaimer").textContent=t[9];
function addCard(name,url){var box=document.createElement("div");box.style.cssText="border:1px solid #d7e2ed;border-radius:14px;padding:18px;background:white";var h=document.createElement("h3"),p=document.createElement("p"),c=document.createElement("p"),a=document.createElement("a");h.textContent=name;p.textContent=t[7];c.textContent=t[4]+": —";a.textContent=url;a.href="https://"+url+"/";a.target="_blank";a.rel="noopener noreferrer";box.append(h,p,c,a);s.querySelector(".wmm-src-cards").appendChild(box);return {p:p,c:c}}
var sam=addCard("SAM.gov (US)","sam.gov"),dapa=addCard("DAPA (Korea)","www.dapa.go.kr");
var base="https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/";
function get(name){return fetch(base+name,{cache:"no-store",credentials:"omit"}).then(function(r){if(!r.ok)throw Error("API");return r.json()})}
function ok(q){return q&&!q.stale&&q.verify!=="partial"&&q.deadline>=new Date().toISOString().slice(0,10)}
Promise.all([get("sources_status.json"),get("tenders.json")]).then(function(v){
var states=v[0],data=v[1];if(!states||!Array.isArray(data.items))throw Error("bad schema");
function update(card,name){var st=states[name]||{},arr=data.items.filter(function(q){return q.source===name&&ok(q)});card.p.textContent=t[2]+": "+(st.state||"UNKNOWN")+" · "+t[3]+": "+(st.last_success||"—");card.c.textContent=t[4]+": "+arr.length+(name==="DAPA (Korea)"&&arr.length===0&&st.state==="SUCCESS"?" · "+t[6]:"")}
update(sam,"SAM.gov (US)");update(dapa,"DAPA (Korea)");
var list=s.querySelector(".wmm-src-list");data.items.filter(function(q){return q.source==="SAM.gov (US)"&&ok(q)}).slice(0,5).forEach(function(q){
var li=document.createElement("li");li.style.cssText="margin:8px 0;padding:12px;border:1px solid #dae2ef;background:white;border-radius:10px";var b=document.createElement("b"),p=document.createElement("p"),a=document.createElement("a");
b.textContent=String(q.title||"").slice(0,180);p.textContent=(q.deadline||"")+" · "+String(q.buyer||"").slice(0,110);
try{var u=new URL(q.url);if(u.protocol==="https:"&&(u.hostname==="sam.gov"||u.hostname.endsWith(".sam.gov"))){a.href=u.href;a.textContent=t[5];a.target="_blank";a.rel="noopener noreferrer"}}catch(e){}
li.append(b,p,a);list.appendChild(li)})
}).catch(function(){sam.p.textContent=t[7];dapa.p.textContent=t[7]});
})();