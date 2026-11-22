/* WMM Business Radar v1.0 — isolated, zero AI calls, no paid calls. */
(()=>{
'use strict';
const root=document.getElementById('wmm-business-radar'); if(!root) return;
if(new URLSearchParams(location.search).get('embed')==='1') document.body.classList.add('wr-embed-mode');
const $=id=>root.querySelector('#'+id);
const E=(tag,cls,text)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=String(text);return x};
const safeUrl=s=>{try{const u=new URL(s);return u.protocol==='https:' && /(^|\.)bizinfo\.go\.kr$/.test(u.hostname)?u.href:null}catch{return null}};
const labels=['서울','경기','인천','강원','충북','충남','세종','대전','전북','전남','광주','경북','대구','경남','울산','부산','제주'];
const markers=[
 ['서울',127.000,37.572,-31,-17],['경기',127.46,37.40,18,7],['인천',126.62,37.45,-39,12],['강원',128.18,37.82,16,-11],
 ['충북',127.67,36.75,18,-10],['충남',126.82,36.52,-37,-10],['세종',127.30,36.48,15,-26],['대전',127.39,36.34,15,17],
 ['전북',127.06,35.74,-33,-6],['전남',126.72,34.82,-32,12],['광주',126.87,35.16,18,-19],['경북',128.68,36.27,18,-5],
 ['대구',128.59,35.87,18,17],['경남',128.20,35.26,21,-3],['울산',129.31,35.52,17,-10],['부산',129.06,35.19,23,19],['제주',126.51,33.49,22,-10]
];
const $state={items:[],source:'verified_snapshot',verifiedAt:'',region:'전체',industry:'전체',target:'전체',status:'all',query:'',bookmarksOnly:false,limit:7,zoom:1,center:[260,315],bookmarks:new Set()};
const requestedRegion=new URLSearchParams(location.search).get('region');if(labels.includes(requestedRegion))$state.region=requestedRegion;
const bookmarkStorageKey='wmm_radar_saved_ids_'+String(window.WMM_AUTH_UID||'local');
try {$state.bookmarks=new Set(JSON.parse(localStorage.getItem(bookmarkStorageKey)||'[]'))}catch{}
const nowKst=()=>{let f=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'});return f.format(new Date())};
const toDate=x=>{const s=String(x||'').replace(/[.\/]/g,'-');if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return '';const d=new Date(s+'T00:00:00Z');return Number.isFinite(+d)&&d.toISOString().slice(0,10)===s?s:'';};
const statusOf=x=>{let today=nowKst(),start=toDate(x.start),end=toDate(x.end);if(!end||!start)return 'unconfirmed';if(start && start>today)return 'scheduled';if(end<today)return 'ended';return 'active'};
const dleft=x=>{if(!x.end)return null; const d=new Date(x.end+'T12:00:00+09:00').getTime()-new Date(nowKst()+'T12:00:00+09:00').getTime();return Math.round(d/86400000)};
const normalize=x=>{
 const id=String(x.id||'').trim();let title=String(x.title||'').trim(), url=safeUrl(x.sourceUrl);
 if(!id||!title||!url)return null;
 return {id,title,sourceUrl:url,region:labels.includes(x.region)?x.region:(x.region==='전국'?'전국':'지역 확인 필요'),industry:String(x.industry||'기타'),target:String(x.target||'대상 확인'),agency:String(x.agency||'공식 원문 확인'),operator:String(x.operator||''),summary:String(x.summary||''),published:toDate(x.published),start:toDate(x.start),end:toDate(x.end),amountText:String(x.amountText||'지원 규모 원문 확인')};
};
const filterData=(ignoreRegion=false)=>$state.items.filter(x=>{
 if(!ignoreRegion&&$state.region!=='전체'&&x.region!==$state.region&&x.region!=='전국')return false;
 if($state.industry!=='전체'&&!x.industry.includes($state.industry))return false;
 if($state.target!=='전체'&&!x.target.includes($state.target))return false;
 if($state.bookmarksOnly&&!$state.bookmarks.has(x.id))return false;
 if($state.status==='active'&&statusOf(x)!=='active')return false;
 if($state.status==='soon'&&!(statusOf(x)==='active'&&dleft(x)>=0&&dleft(x)<=7))return false;
 if($state.status==='planned'&&statusOf(x)!=='unconfirmed')return false;
 if($state.query){let hay=[x.title,x.industry,x.target,x.region,x.agency,x.operator,x.summary].join(' ').toLowerCase();if(!hay.includes($state.query.toLowerCase()))return false}return true
 }).sort((a,b)=>{
 let s={active:0,scheduled:1,unconfirmed:2,ended:3};return s[statusOf(a)]-s[statusOf(b)]||String(a.end||'9999').localeCompare(String(b.end||'9999'))||b.published.localeCompare(a.published)
 });
function dropdown(id,values,anyLabel){let s=$(id),existing=s.value;s.innerHTML='';let o=E('option','',anyLabel);o.value='전체';s.append(o);values.forEach(v=>{let e=E('option','',v);e.value=v;s.append(e)});s.value=values.includes(existing)?existing:'전체'}
function setupDropdowns(){dropdown('wr-region',labels,'전국 · 전체');let inds=[...new Set($state.items.flatMap(x=>x.industry.split('·')))].sort((a,b)=>a.localeCompare(b,'ko'));dropdown('wr-industry',inds,'모든 산업군');let ts=[...new Set($state.items.flatMap(x=>x.target.split('·')))].sort((a,b)=>a.localeCompare(b,'ko'));dropdown('wr-target',ts,'모든 대상')}
const projection=(lat,lon)=>[(lon-125)/5.8*520,(39.2-lat)/6.25*620];
const ns='http://www.w3.org/2000/svg';const SVG=(tag,attrs)=>{let e=document.createElementNS(ns,tag);Object.entries(attrs||{}).forEach(([k,v])=>e.setAttribute(k,String(v)));return e};
function mapView(){let svg=$('wr-svg');let width=520/$state.zoom,height=620/$state.zoom;let cx=$state.center[0],cy=$state.center[1];svg.setAttribute('viewBox',`${Math.max(0,Math.min(520-width,cx-width/2))} ${Math.max(0,Math.min(620-height,cy-height/2))} ${width} ${height}`)}
function drawMap(){let group=$('wr-map-points');group.replaceChildren();let counts={};const mapRows=filterData(true);labels.forEach(n=>counts[n]=mapRows.filter(x=>x.region===n).length);
 markers.forEach(([n,lon,lat,dx,dy])=>{let [x,y]=projection(lat,lon);let count=counts[n]||0, g=SVG('g',{class:'wr-region-dot'+($state.region===n?' wr-active':''),role:'button',tabindex:'0','aria-label':`${n} 지역 한정 공고 ${count}건, 클릭 시 해당 지역과 전국 공고 조회`});
 g.append(SVG('circle',{cx:x,cy:y,r:22,fill:'transparent',stroke:'none',class:'wr-hit'}));let c=SVG('circle',{cx:x,cy:y,r:count?9.8:6.7});g.append(c);
 if(count){let t=SVG('text',{x,y:y+3.4,'text-anchor':'middle',class:'wr-count'});t.textContent=count;g.append(t)}
 let l=SVG('text',{x:x+dx,y:y+dy,'text-anchor':dx<0?'end':'start'});l.textContent=n;g.append(l);
 const select=()=>{ $state.region=$state.region===n?'전체':n;$('wr-region').value=$state.region;$state.limit=7; if($state.region===n){$state.zoom=1.75;$state.center=[x,y]}else{$state.zoom=1;$state.center=[260,310]}render(); };
 g.addEventListener('click',select);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select()}});
 g.addEventListener('mouseenter',()=>showTip(n,count));group.append(g);
 });
 let region=$state.region;if(region!=='전체'){let local=filterData().filter(x=>x.region===region).slice(0,2); if($state.zoom>=1.6 && local.length){let [cx,cy]=projection(markers.find(m=>m[0]===region)[2],markers.find(m=>m[0]===region)[1]);let t=SVG('text',{x:cx+8,y:cy-33,'text-anchor':'middle','font-size':'10','font-weight':'700',fill:'#b18c51',stroke:'#f8f8f8','stroke-width':'3','paint-order':'stroke'});t.textContent=local[0].title.slice(0,15)+'…';group.append(t)}}
 mapView();showTip(region,counts[region]||0);
}
function showTip(region,count){let t=$('wr-map-tooltip');if(region==='전체'){t.replaceChildren(E('strong','','대한민국 전체'),E('div','','17개 시·도 · 지역을 눌러 상세 공고 조회'))}else{t.replaceChildren(E('strong','',region),E('div','',`지역 한정 확인 공고 ${count}건`),E('div','','전국 공고는 별도 후보로 함께 표시됩니다.'))}}
function renderStats(items){let active=items.filter(x=>statusOf(x)==='active');let soon=active.filter(x=>{let d=dleft(x);return d!==null&&d<=7&&d>=0});$('wr-stat-total').textContent=items.length;$('wr-stat-soon').textContent=soon.length;$('wr-stat-local').textContent=items.filter(x=>labels.includes(x.region)).length;$('wr-stat-planned').textContent=items.filter(x=>statusOf(x)==='unconfirmed').length;$('wr-insight-title').textContent=($state.region==='전체'?'전국':$state.region)+' · '+($state.industry==='전체'?'전체 산업':$state.industry);$('wr-insight-desc').textContent=items.length?`선택 조건에 일치하는 ${items.length}건을 찾았습니다. 지역 전용 공고와 전국 대상 후보를 함께 확인하세요.`:'선택 조건에 부합하는 수록 공고가 없습니다. 다른 조건을 선택하거나 공식 포털에서 확인하세요.';let chips=$('wr-selected-chips');chips.replaceChildren();chips.append(E('span','',$state.region==='전체'?'전국':$state.region),E('span','',$state.industry==='전체'?'전체 산업':$state.industry),E('span','',$state.status==='active'?'모집 중':$state.status==='soon'?'마감임박':$state.status==='planned'?'일정 미확인':'전체 상태'));$('wr-results-subtitle').textContent=`선택 조건의 공고 ${items.length}건 · ${['live','cached'].includes($state.source)?'기업마당 API 응답':($state.source==='stale'?'마지막 성공 API 캐시 · 현재 상태 미검증':'2026.11.05 과거 공고 스냅샷')} · 실제 신청 가능 여부는 원문 확인`}
function renderList(items){const list=$('wr-list');list.replaceChildren();if(!items.length){list.append(E('div','wr-empty','표시할 공고가 없습니다. 필터를 바꾸거나 기업마당·K-Startup 공식 사이트에서 다시 검색해 주세요.'));$('wr-more').hidden=true;return}
 const short=items.slice(0,$state.limit);short.forEach(x=>{
 let article=E('article','wr-result'),left=E('div',''),top=E('div','wr-result-top');let st=statusOf(x),statusLabel=['live','cached'].includes($state.source)?{active:'기간상 모집 중',unconfirmed:'일정 원문 확인',scheduled:'접수 예정',ended:'기간상 마감'}[st]:'과거 확인본 · 현재 상태 미검증';let status=E('span','wr-result-status',statusLabel);top.append(status,E('span','',x.region==='전국'?'전국 대상 후보':x.region==='지역 확인 필요'?'지역 미확인':x.region+' 지역 공고'),E('span','',x.industry),E('span','',x.published+' 등록'));left.append(top,E('h3','',x.title),E('p','',x.summary));let due=(x.end||'기한 개별 확인');let meta=E('div','wr-result-meta',`${x.agency} · ${x.operator}  |  마감 ${due}  |  ${x.amountText}`);left.append(meta);
 let actions=E('div','wr-result-actions'),save=E('button','',$state.bookmarks.has(x.id)?'★':'☆');save.type='button';save.setAttribute('aria-label',x.title+' 저장');save.setAttribute('aria-pressed',$state.bookmarks.has(x.id)?'true':'false');save.addEventListener('click',()=>{if($state.bookmarks.has(x.id))$state.bookmarks.delete(x.id);else $state.bookmarks.add(x.id);try{localStorage.setItem(bookmarkStorageKey,JSON.stringify([...$state.bookmarks]))}catch{}render()});let anchor=E('a','','공식 원문 ↗');anchor.href=x.sourceUrl;anchor.target='_blank';anchor.rel='noopener noreferrer';actions.append(save,anchor);article.append(left,actions);list.append(article)
 });$('wr-more').hidden=short.length>=items.length;$('wr-count-note').textContent=`${short.length} / ${items.length}건 표시 · 공식 출처와 제출 자격은 반드시 원문 확인`}
function render(){const u=new URL(location.href);if($state.region==='전체')u.searchParams.delete('region');else u.searchParams.set('region',$state.region);history.replaceState(null,'',u.pathname+u.search);let items=filterData();$('wr-head-count').textContent=$state.items.length;renderStats(items);renderList(items);drawMap();$('wr-only-bookmarks').setAttribute('aria-pressed',$state.bookmarksOnly?'true':'false'); root.dispatchEvent(new CustomEvent('wmm:radar:update',{detail:{region:$state.region,industry:$state.industry,status:$state.status,items:$state.items,filtered:items}}));}
window.WMMRadarBridge={
 getState:()=>({region:$state.region,industry:$state.industry,items:$state.items,filtered:filterData(),mapItems:filterData(true)}),
 selectRegion:n=>{if(!labels.includes(n)&&n!=='전체')return;$state.region=n;$state.zoom=1;$state.center=[260,310];$state.limit=7;$('wr-region').value=n;render();}
};
function bind(){ $('wr-region').addEventListener('change',e=>{$state.region=e.target.value;$state.zoom=1;$state.center=[260,310];$state.limit=7;render()});$('wr-industry').addEventListener('change',e=>{$state.industry=e.target.value;$state.limit=7;render()});$('wr-target').addEventListener('change',e=>{$state.target=e.target.value;$state.limit=7;render()});$('wr-status').addEventListener('change',e=>{$state.status=e.target.value;$state.limit=7;render()});let pending; $('wr-query').addEventListener('input',e=>{clearTimeout(pending);pending=setTimeout(()=>{$state.query=e.target.value.trim();$state.limit=7;render()},180)});
 $('wr-reset').addEventListener('click',()=>{$state.region='전체';$state.industry='전체';$state.target='전체';$state.status='all';$state.query='';$state.limit=7;$state.zoom=1;$state.center=[260,310];$state.bookmarksOnly=false;['wr-region','wr-industry','wr-target'].forEach(id=>$(id).value='전체');$('wr-status').value='all';$('wr-query').value='';render()});
 $('wr-zoomin').addEventListener('click',()=>{$state.zoom=Math.min(3.7,$state.zoom*1.33);render()});$('wr-zoomout').addEventListener('click',()=>{$state.zoom=Math.max(1,$state.zoom/1.33);render()});$('wr-all-regions').addEventListener('click',()=>{$state.region='전체';$state.zoom=1;$state.center=[260,310];$('wr-region').value='전체';render()});$('wr-more').addEventListener('click',()=>{$state.limit+=7;renderList(filterData())});$('wr-only-bookmarks').addEventListener('click',()=>{$state.bookmarksOnly=!$state.bookmarksOnly;$state.limit=7;render()});$('wr-refresh').addEventListener('click',()=>load(true));$('wr-export').addEventListener('click',()=>{let list=filterData(),head=['공고명','지역','분야','지원대상','기관','등록일','접수시작','마감일','지원규모','공식URL'];let rows=[head,...list.map(x=>[x.title,x.region,x.industry,x.target,x.agency,x.published,x.start,x.end,x.amountText,x.sourceUrl])];let csv='\ufeff'+rows.map(r=>r.map(v=>'"'+String(v??'').replace(/^[=+@\-\t\r]/,m=>"'"+m).replaceAll('"','""')+'"').join(',')).join('\r\n');let obj=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8;'}));let a=document.createElement('a');a.href=obj;a.download='WMM_공식공고_필터결과_'+nowKst()+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(obj),1000)});
 }
async function load(force=false){$('wr-fetch-badge').textContent='공식 데이터 확인 중…';let payload=null;if(location.protocol!=='file:')try{let url=(root.getAttribute('data-api')||'/api/wmm/opportunities')+(force?'?refresh=1':'');let ac=new AbortController();let timeout=setTimeout(()=>ac.abort(),9000);let accessToken=typeof window.WMM_AUTH_GET_TOKEN==='function' ? await window.WMM_AUTH_GET_TOKEN() : ''; if(!accessToken){window.dispatchEvent(new Event('wmm:auth-expired'));return;}let res=await fetch(url,{signal:ac.signal,headers:{Authorization:'Bearer '+accessToken},cache:'no-store'});clearTimeout(timeout);if(res.status===401){window.dispatchEvent(new Event('wmm:auth-expired'));return;}if(res.ok){let p=await res.json();if(p&&['live','cached','stale'].includes(p.mode)&&Array.isArray(p.items))payload=p}}catch(e){}
 if(!window.WMM_AUTH_GET_TOKEN)return;
 if(!payload){payload=window.WMM_VERIFIED_SEED||{mode:'verified_snapshot',verifiedAt:'',items:[]};}
 $state.source=payload.mode;$state.verifiedAt=payload.verifiedAt||payload.fetchedAt||'';$state.items=[...new Map((payload.items||[]).map(normalize).filter(Boolean).map(x=>[x.id,x])).values()];
 if(['live','cached'].includes($state.source)){$('wr-fetch-badge').textContent='기업마당 API 응답 수신';$('wr-mode-label').textContent='공식 API 조회 · 마지막 수집 시각 표시';$('wr-disclosure').textContent='기업마당 API에서 최대 180건을 조회하며 캐시는 6시간 유지합니다. API 제공범위·수집시각·신청 자격에 따라 누락이 있을 수 있으며 최종 신청조건은 원문 확인이 필요합니다.';}else if($state.source==='stale'){$('wr-fetch-badge').textContent='갱신 실패 · 마지막 성공 캐시';$('wr-mode-label').textContent='현재 상태 미검증';$('wr-disclosure').textContent='공급자 응답 오류로 이전 응답을 표시합니다. 현재 접수 여부는 원문을 확인하세요.';}else{$('wr-fetch-badge').textContent='2026.11.05 저장본 · 현재 상태 미검증';$('wr-mode-label').textContent='과거 저장본 · 실시간 연동 대기';$('wr-disclosure').textContent='2026-11-05에 저장된 제한된 공고입니다. 이 자료의 현재 모집 여부는 검증하지 않았습니다. 실제 접수 여부는 공식 원문에서 확인해 주세요.'}
 $('wr-updated').textContent='수집/저장 시각: '+($state.verifiedAt||'확인 전');setupDropdowns();$('wr-region').value=$state.region;render();
}
(function init(){bind();load()})();
})();
