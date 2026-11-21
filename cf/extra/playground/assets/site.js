/* WMM PLAYGROUND v30 — public-safe static experience. No external API or payment.
 * Static source: 120 WMM editorial draft ideas. Local data stays in this browser.
 */
(() => {
'use strict';
const PREFIX='wmm.playground.v30.';
const $=(selector,root=document)=>root.querySelector(selector);
const $$=(selector,root=document)=>Array.from(root.querySelectorAll(selector));
const safeJSON=(str,fallback)=>{try{return JSON.parse(str)}catch(_){return fallback}};
const mem={};
const read=(key,fallback)=>{try{const v=localStorage.getItem(PREFIX+key);return v===null?fallback:safeJSON(v,fallback)}catch(_){return Object.prototype.hasOwnProperty.call(mem,key)?mem[key]:fallback}};
const msg=(ko,en)=>document.documentElement.lang==='en'?en:ko;
const write=(key,value)=>{mem[key]=value;try{localStorage.setItem(PREFIX+key,JSON.stringify(value));return true}catch(_){notify(msg('브라우저 저장이 제한되어 있습니다. 파일을 다운로드해 보관하세요.','Browser storage is unavailable. Download the file to keep a copy.'));return false}};
const escapeHTML=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function notify(message){const t=$('#toast');if(!t)return;t.textContent=message;t.hidden=false;clearTimeout(notify.timer);notify.timer=setTimeout(()=>{t.hidden=true},3600)}
function download(filename,text,mime='text/plain;charset=utf-8'){
 const blob=new Blob([text],{type:mime});const url=URL.createObjectURL(blob);
 const a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function copy(text){
 try{if(!navigator.clipboard||!window.isSecureContext)throw Error('Clipboard unavailable');await navigator.clipboard.writeText(text);notify(msg('내용을 복사했습니다.','Copied to clipboard.'));}
 catch(_){download('wmm-playground-copy.txt',text);notify(msg('클립보드 대신 텍스트 파일로 저장했습니다.','Saved a text file because clipboard access is unavailable.'));}
}
function strip(s,max=1000){return String(s??'').trim().slice(0,max)}
function dateStr(){return new Date().toLocaleDateString('en-CA')}
const i18n={
 ko:{preview:'CREATIVEOS 2026 · 공개 미리보기 · 120개 WMM 자체 기획 콘텐츠 · 실제 회원·계약·결제 서비스 아님',start:'지금 시작하기 ↗',nav_0:'홈',nav_1:'120개 탐색',nav_2:'아이디어 스튜디오',nav_3:'7·14일 챌린지',nav_4:'함께하기',nav_5:'WMM 멤버십'},
 en:{preview:'CREATIVEOS 2026 · Public preview · 120 WMM editorial drafts · No live accounts, contracts or payments',start:'Start creating ↗',nav_0:'Home',nav_1:'Explore 120',nav_2:'Idea Studio',nav_3:'Challenges',nav_4:'Collaborate',nav_5:'Membership'}
};
// Original KO text nodes are tracked without HTML injection; locale switches are reversible.
const originalText = new WeakMap();
function translateStaticNodes(lang){
 const dictionary=window.WMM_EN_UI||{};
 const tree=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 let node;
 while((node=tree.nextNode())){
  if(node.parentElement&&['SCRIPT','STYLE','NOSCRIPT','TEXTAREA'].includes(node.parentElement.tagName))continue;
  if(!originalText.has(node))originalText.set(node,node.nodeValue);
  const raw=originalText.get(node),trimmed=raw.trim();
  const koDict=window.WMM_KO_UI||{};
  if(lang==='en'&&Object.prototype.hasOwnProperty.call(dictionary,trimmed)){
    node.nodeValue=raw.replace(trimmed,dictionary[trimmed]);
  }else if(lang!=='en'&&Object.prototype.hasOwnProperty.call(koDict,trimmed)){
    node.nodeValue=raw.replace(trimmed,koDict[trimmed]);
  }else{node.nodeValue=raw}
 }
 const labels=['placeholder','aria-label','title','alt'];
 $$('[placeholder],[aria-label],[title]').forEach(el=>{
  labels.forEach(attr=>{
   if(!el.hasAttribute(attr))return;
   const cache='wmmOriginal'+attr.replace('-','');
   if(!Object.prototype.hasOwnProperty.call(el.dataset,cache))el.dataset[cache]=el.getAttribute(attr);
   const ko=el.dataset[cache];el.setAttribute(attr,lang==='en'?(dictionary[ko]||ko):ko);
  });
 });
}
function localizeCatalogCards(lang){
 const cat=window.WMM_CATALOG||[];
 const byId=new Map(cat.map(x=>[x.id,x]));
 $$('.catalog-card').forEach(card=>{
   const href=card.querySelector('a[href*="template="]')?.getAttribute('href')||'';
   const key=href.split('template=')[1]?.split('&')[0];
   const item=byId.get(key);if(!item)return;
   const en=lang==='en';
   const title=en?item.titleEn:item.title;
   const description=en?item.descriptionEn:item.description;
   const h=card.querySelector('h3'), p=card.querySelector('p');
   if(h)h.textContent=title;
   if(p)p.textContent=description;
   const category=card.querySelector('.catalog-meta .tag');
   if(category)category.textContent=en?item.categoryEn:item.categoryKo;
   card.dataset.title=title;
   card.dataset.search=[item.title,item.description,item.categoryKo,item.titleEn,item.descriptionEn,item.categoryEn].join(' ').toLocaleLowerCase();
 });
}
function localizePrefilledStudio(lang){
 const q=new URLSearchParams(location.search).get('template');
 if(!q)return;
 const item=(window.WMM_CATALOG||[]).find(x=>x.id===q);if(!item)return;
 const key=document.activeElement;
 const pairs=[['#ideaTitle',item.title,item.titleEn],['#ideaProblem',item.description,item.descriptionEn],['#ideaPromise',item.deliverable,item.deliverableEn]];
 for(const [sel,ko,en] of pairs){const el=$(sel);if(el&&el!==key&&(el.value===ko||el.value===en))el.value=lang==='en'?en:ko}
}
function setLang(lang){
 const v=lang==='en'?'en':'ko';document.documentElement.lang=v;
 $$('[data-i18n]').forEach(el=>{const k=el.getAttribute('data-i18n');if(i18n[v][k])el.textContent=i18n[v][k]});
 translateStaticNodes(v);
 localizeCatalogCards(v);
 localizePrefilledStudio(v);
 const toggle=$('#langToggle');if(toggle){toggle.textContent=v==='ko'?'EN':'KO';toggle.setAttribute('aria-label',v==='ko'?'Switch site language to English':'웹사이트 한국어로 변경')};
 write('lang',v);
 document.dispatchEvent(new CustomEvent('wmm:language',{detail:{lang:v}}));
}
function initNavigation(){
 const menu=$('#mobileMenu'),toggle=$('#mobileToggle');
 if(menu&&toggle){const close=()=>{menu.hidden=true;toggle.setAttribute('aria-expanded','false')};toggle.addEventListener('click',()=>{const expanded=toggle.getAttribute('aria-expanded')==='true';menu.hidden=expanded;toggle.setAttribute('aria-expanded',String(!expanded))});$$('a',menu).forEach(a=>a.addEventListener('click',close));document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});}
 const btn=$('#langToggle');const initial=read('lang','ko');setLang(initial);if(btn)btn.addEventListener('click',()=>setLang(document.documentElement.lang==='ko'?'en':'ko'));
 const video=$('.hero-visual video');if(video&&window.matchMedia&&window.matchMedia('(prefers-reduced-motion:reduce)').matches){video.pause();video.removeAttribute('autoplay')}
}
function initCatalog(){
 const grid=$('#catalogGrid');if(!grid)return;
 const search=$('#catalogSearch'),cat=$('#catalogCategory'),sort=$('#catalogSort'),reset=$('#catalogReset'),count=$('#catalogCount'),empty=$('#catalogEmpty');
 const cards=$$('.catalog-card',grid);cards.forEach((el,i)=>el.dataset.origin=String(i));
 const params=new URLSearchParams(location.search);const chosen=params.get('category');
 if(chosen&&$$('option',cat).some(o=>o.value===chosen))cat.value=chosen;
 function render(){const q=(search.value||'').trim().toLocaleLowerCase('ko');const category=cat.value;
  const sorted=cards.slice().sort((a,b)=>{if(sort.value==='short')return +a.dataset.duration-+b.dataset.duration;if(sort.value==='long')return +b.dataset.duration-+a.dataset.duration;if(sort.value==='name')return a.dataset.title.localeCompare(b.dataset.title,document.documentElement.lang==='en'?'en':'ko');return +a.dataset.origin-+b.dataset.origin});
  const fragment=document.createDocumentFragment();sorted.forEach(el=>fragment.appendChild(el));grid.appendChild(fragment);
  let visible=0;sorted.forEach(el=>{const hit=(!q||el.dataset.search.includes(q))&&(category==='all'||el.dataset.category===category);el.hidden=!hit;if(hit)visible++});
  if(empty)empty.hidden=visible!==0;if(count)count.textContent=document.documentElement.lang==='en'?`${visible} / ${cards.length} ideas`:`총 ${visible} / ${cards.length}개 콘텐츠`;
 }
 document.addEventListener('wmm:language',render);[search,cat,sort].forEach(el=>el.addEventListener(el===search?'input':'change',render));reset.addEventListener('click',()=>{search.value='';cat.value='all';sort.value='default';if(location.protocol==='http:'||location.protocol==='https:'){history.replaceState(null,'',location.pathname)}render();search.focus()});render();
}
let latestIdea='';
function initStudio(){const form=$('#studioForm');if(!form)return;
 const cat=window.WMM_CATALOG||[];const q=new URLSearchParams(location.search).get('template');if(q){const item=cat.find(x=>x.id===q);if(item){const english=document.documentElement.lang==='en';$('#ideaTitle').value=english?item.titleEn:item.title;$('#ideaProblem').value=english?item.descriptionEn:item.description;$('#ideaPromise').value=english?item.deliverableEn:item.deliverable;const badge=$('#prefillNote');badge.hidden=false;badge.textContent=english?`Source template: ${item.categoryEn} · WMM editorial draft / unverified`:`원본 템플릿: ${item.categoryKo} · WMM 자체 기획 / 미검증`}}
 const heading=$('#ideaResultHeading'),result=$('#studioResult'),placeholder=$('#studioPlaceholder');
 form.addEventListener('submit',ev=>{ev.preventDefault();if(!form.reportValidity())return;
  const en=document.documentElement.lang==='en';const title=strip($('#ideaTitle').value,100),problem=strip($('#ideaProblem').value),audience=strip($('#ideaAudience').value,180)||(en?'Audience needs confirmation':'대상 고객 또는 참여자를 확인해야 함'),format=$('#ideaFormat').value,promise=strip($('#ideaPromise').value,250)||(en?'Define a measurable outcome':'어떤 변화가 생기는지 구체적인 측정 기준 필요'),caution=strip($('#ideaCaution').value,600)||(en?'Check demand, rights, costs and safety':'실제 사용자 반응, 저작권, 비용, 안전 조건 검증 필요');
  if(title.length<2||problem.length<5){notify(msg('아이디어 이름과 해결할 문제를 조금 더 구체적으로 작성하세요.','Please describe the idea and problem in more detail.'));return}
  const actions=en?['1. Check with 2–3 people whether the problem exists.','2. Build the smallest '+format+' prototype.','3. Record time, cost, and feedback before deciding what to do next.']:['1. 대상 2~3명에게 문제의 실제 존재 여부를 확인한다.','2. '+format+' 형태의 가장 작은 결과물을 만든다.','3. 소요 시간·비용·피드백을 기록하고 계속할지 판단한다.'];
  const now=dateStr();latestIdea=en?`# ${title}\n\nCreated: ${now}\nDocument: WMM PLAYGROUND personal experiment draft (not AI analysis or business approval)\n\n## Problem\n${problem}\n\n## Audience\n${audience}\n\n## Deliverable\n${format}\n\n## Expected outcome\n${promise}\n\n## Assumptions and risks\n${caution}\n\n## Next three actions\n${actions.join('\n')}\n\n---\nWMM PLAYGROUND CreativeOS / offline rules-based brief. Market demand, rights, and safety require independent validation.\n`:`# ${title}\n\n작성일: ${now}\n문서 종류: WMM PLAYGROUND 개인 실험 초안 / 실제 AI 분석·사업 승인 아님\n\n## 해결할 문제\n${problem}\n\n## 대상\n${audience}\n\n## 제작할 결과물\n${format}\n\n## 기대하는 변화\n${promise}\n\n## 확인해야 할 조건\n${caution}\n\n## 다음 세 가지 행동\n${actions.join('\n')}\n\n---\nWMM PLAYGROUND CreativeOS / 오프라인 규칙형 기획서. 시장성·권리·안전성은 별도 검증 필요.\n`;
  heading.textContent=title;$('#resProblem').textContent=problem;$('#resAudience').textContent=audience;$('#resDeliverable').textContent=format;$('#resPromise').textContent=promise;$('#resCaution').textContent=caution;$('#resActions').textContent=actions.join('\n');result.hidden=false;placeholder.hidden=true;notify(en?'Your idea brief is ready.':'아이디어 기획서가 만들어졌습니다.');result.scrollIntoView({behavior:'smooth',block:'nearest'});
 });
 $('#downloadIdea').addEventListener('click',()=>{if(latestIdea)download('WMM_IDEA_'+dateStr()+'.md',latestIdea,'text/markdown;charset=utf-8')});
 $('#copyIdea').addEventListener('click',()=>{if(latestIdea)copy(latestIdea)});
 $('#saveIdea').addEventListener('click',()=>{if(!latestIdea)return;const value=read('ideas',[]);const items=Array.isArray(value)?value:[];const title=strip($('#ideaTitle').value,100);items.unshift({title,createdAt:new Date().toISOString(),content:latestIdea});write('ideas',items.slice(0,30));notify(document.documentElement.lang==='en'?'Saved in this browser. Export JSON before changing devices.':'이 브라우저에 저장했습니다. 기기 변경 전 JSON으로 백업하세요.')});
}
const MISSION_EN={
seven:[
['Define the problem','Write the problem you want to solve in one sentence.'],
['Observe','Collect three examples of when the problem occurs.'],
['Identify the audience','Define the people who need help.'],
['Make a first deliverable','Create a page, video, or prototype with tools you already have.'],
['Collect feedback','Ask two or three stakeholders for candid feedback.'],
['Improve','Change only the parts shown to be useful.'],
['Share and reflect','Record your result, lessons, and one next action.']
],
fourteen:[
['Problem and customer hypothesis','Describe the problem separately from the target customer.'],
['Competitors and alternatives','Research at least three existing solutions.'],
['Rights and safety','Check privacy, copyright, law, and child safeguards.'],
['Success criteria','Define measurable success or stop conditions.'],
['Prototype scope','Pick one core function and exclude the rest.'],
['Create the prototype','Make the smallest demo, proposal, or content piece.'],
['Test and review','Check whether it works on another person’s device.'],
['Recruit test participants','Find a small group who consent to participate.'],
['Observe behavior','Record actual choices instead of only compliments.'],
['Record the numbers','Track time, cost, valid feedback, and inquiries.'],
['Revisit the problem','Adjust or discard hypotheses based on feedback.'],
['Check economics','Review actual price, costs, time, refunds, and legal obligations.'],
['Review collaboration terms','Document authority, roles, agreements, and rights.'],
['Choose the next action','Decide to proceed, revise, or stop, and explain why.']
]};
const MISSIONS={
 seven:[
  ['문제 정의','내가 해결하려는 문제를 한 문장으로 적습니다.'],['관찰','그 문제가 실제로 언제 발생하는지 사례 3개를 모읍니다.'],['대상 확인','도움이 필요한 사람 또는 사용자를 명확히 정합니다.'],['첫 결과물','지금 가진 도구로 1페이지·영상·시안을 만듭니다.'],['피드백','이해관계자 2~3명의 솔직한 피드백을 받습니다.'],['수정','실제로 필요하다고 확인된 부분만 개선합니다.'],['공유와 회고','결과와 배운 점, 다음 주 한 가지 행동을 기록합니다.']
 ],
 fourteen:[
  ['문제·고객 가설','문제와 대상 고객을 분리하여 서술합니다.'],['경쟁·대체 수단','기존에 해결하는 방법을 최소 3가지 조사합니다.'],['권리·안전 점검','개인정보·저작권·법령·미성년자 보호 조건을 확인합니다.'],['성공 기준','측정 가능한 성공/중단 기준을 미리 정합니다.'],['시제품 기획','핵심 기능 하나를 정하고 나머지는 제외합니다.'],['시제품 제작','가장 작은 데모/제안서/콘텐츠를 제작합니다.'],['시연·기술 점검','타인의 기기에서도 실제로 이해되는지 확인합니다.'],['테스트 대상 모집','동의를 받은 소수의 참여자를 찾습니다.'],['행동 관찰','말뿐인 호감보다 실제 선택·행동을 기록합니다.'],['정량 기록','시간·비용·유효 피드백·문의 수를 기록합니다.'],['문제 재정의','피드백을 받아 가설을 수정하거나 폐기합니다.'],['경제성 점검','실제 가격·원가·시간·환불·법적 비용을 검토합니다.'],['협업·계약 검토','권한·역할·계약·저작권을 문서로 확인합니다.'],['결정과 다음 실험','진행·수정·중단 중 하나를 선택하고 근거를 남깁니다.']
 ]
};
function initChallenges(){const list=$('#taskList');if(!list)return;const tab7=$('#tab7'),tab14=$('#tab14');let mode='seven';
 function render(){const english=document.documentElement.lang==='en',data=english?MISSION_EN[mode]:MISSIONS[mode],save=read('tasks_'+mode,{});$('#taskKicker').textContent=english?(mode==='seven'?'7-DAY CHALLENGE':'LAUNCH 14 / EXPERIMENT'):(mode==='seven'?'7일 챌린지':'14일 사업 검증');$('#taskTitle').textContent=english?(mode==='seven'?'Seven days of small steps':'LAUNCH 14 · Business experiment'):(mode==='seven'?'7일, 작은 시작의 기록':'LAUNCH 14 · 사업 검증 로드맵');$('#taskDesc').textContent=english?(mode==='seven'?'Complete one small action each day.':'Separate market assumptions, prototypes, feedback, and rights.'): (mode==='seven'?'매일 하나의 행동으로 실행하는 7일 미션입니다.':'시장 가설·시제품·고객 반응·권리를 구분하는 14일 실험입니다.');tab7.setAttribute('aria-selected',String(mode==='seven'));tab14.setAttribute('aria-selected',String(mode==='fourteen'));
 list.replaceChildren();data.forEach(([title,desc],i)=>{const label=document.createElement('label');label.className='task';const input=document.createElement('input');input.type='checkbox';input.checked=Boolean(save[i]);input.setAttribute('aria-label',`DAY ${i+1} ${title} ${english?'done':'완료'}`);input.addEventListener('change',()=>{const copy=read('tasks_'+mode,{});copy[i]=input.checked;write('tasks_'+mode,copy);updateProgress()});const text=document.createElement('span');const strong=document.createElement('b');strong.textContent=`DAY ${String(i+1).padStart(2,'0')} · ${title}`;const small=document.createElement('small');small.textContent=desc;text.append(strong,small);label.append(input,text);list.append(label)});updateProgress();}
 function updateProgress(){const checked=$$('input:checked',list).length,max=MISSIONS[mode].length,percent=Math.round(checked/max*100);$('#taskProgress').textContent=document.documentElement.lang==='en'?`${checked} / ${max} complete · ${percent}%`:`${checked} / ${max} 완료 · ${percent}%`;$('#progressFill').style.width=percent+'%';$('#progressBar').setAttribute('aria-valuenow',percent);}
 tab7.addEventListener('click',()=>{mode='seven';render()});tab14.addEventListener('click',()=>{mode='fourteen';render()});
 document.addEventListener('wmm:language',render);$('#downloadTasks').addEventListener('click',()=>{const done=read('tasks_'+mode,{});const en=document.documentElement.lang==='en';const data=en?MISSION_EN[mode]:MISSIONS[mode];const text=`# WMM PLAYGROUND ${mode==='seven'?(en?'7-day challenge':'7일 챌린지'):'LAUNCH14'} ${en?'personal checklist':'개인 작업표'}\n날짜: ${dateStr()}\n개인 실행 기록/비공개 시연\n\n`+data.map(([title,desc],i)=>`- [${done[i]?'x':' '}] DAY ${i+1} ${title} — ${desc}`).join('\n')+'\n';download('WMM_'+(mode==='seven'?'7DAY':'14DAY')+'_'+dateStr()+'.md',text,'text/markdown;charset=utf-8')});
 $('#resetTasks').addEventListener('click',()=>{if(!confirm(msg('이 프로그램의 진행 상태만 초기화할까요?','Reset progress for this challenge only?')))return;write('tasks_'+mode,{});render();notify(msg('선택한 프로그램의 기록을 초기화했습니다.','Challenge progress was reset.'))});render();}
let latestCollab='';
function initCollaboration(){const form=$('#collabForm');if(!form)return;form.addEventListener('submit',e=>{e.preventDefault();if(!form.reportValidity())return;
 const title=strip($('#collabTitle').value,100),goal=strip($('#collabGoal').value),roles=strip($('#collabRoles').value,280)||(document.documentElement.lang==='en'?'To be discussed':'추가 논의 필요'),duration=$('#collabDuration').value,scope=$('#collabScope').value,rights=strip($('#collabRights').value,700)||(document.documentElement.lang==='en'?'Agree in writing before starting':'협업 시작 전 서면 합의 필요');if(title.length<2||goal.length<5){notify(msg('프로젝트 명칭과 목표를 구체적으로 작성하세요.','Please describe the project name and goal in more detail.'));return}
 latestCollab=document.documentElement.lang==='en'?`# ${title} / WMM Collaboration proposal (draft)\n\nCreated: ${dateStr()}\nNOT a live recruitment or contract\n\n## Objective\n${goal}\n\n## Needed roles\n${roles}\n\n## Duration\n${duration}\n\n## Collaboration mode\n${scope}\n\n## Rights, permission and compensation\n${rights}\n\n## Checklist before collaboration\n- Verify identity and authority\n- Confirm image, music and code rights\n- Agree on budget, payment, refunds and liability\n- Review privacy and local law\n- Agree on acceptance and exit terms\n\n*Personal local draft only; not sent to WMM or third parties.*\n`:`# ${title} / WMM 협업 제안서 초안\n\n작성일: ${dateStr()}\n현재 실제 계약·모집 아님\n\n## 목표 / 필요성\n${goal}\n\n## 필요한 역할\n${roles}\n\n## 기간\n${duration}\n\n## 방식\n${scope}\n\n## 저작권·이용권·보상 원칙\n${rights}\n\n## 협업 전 확인 항목\n- 대표권 및 본인 확인\n- 사진·음악·소스코드 권리\n- 예산·지급·환불·책임분담\n- 개인정보·국가별 규정\n- 결과물 인수/종료 조건\n\n*이 문서는 개인 로컬 초안입니다. WMM/제3자에게 제출되지 않습니다.*\n`;
 $('#collabPreview').textContent=latestCollab;$('#collabResult').hidden=false;notify(document.documentElement.lang==='en'?'Collaboration brief created.':'협업 제안서 초안이 만들어졌습니다.');$('#collabResult').scrollIntoView({behavior:'smooth',block:'nearest'});
 });$('#downloadCollab').addEventListener('click',()=>{if(latestCollab)download('WMM_COLLAB_'+dateStr()+'.md',latestCollab,'text/markdown;charset=utf-8')});$('#copyCollab').addEventListener('click',()=>{if(latestCollab)copy(latestCollab)});}
function initDataControls(){const out=$('#storageSummary');if(!out)return;function update(){const data=read('ideas',[]);const a=Array.isArray(data)?data.length:0;const p7=read('tasks_seven',{}),p14=read('tasks_fourteen',{});const c7=Object.values(p7).filter(Boolean).length,c14=Object.values(p14).filter(Boolean).length;out.textContent=document.documentElement.lang==='en'?`Saved on this device: ${a} ideas, 7-day tasks ${c7}/7, LAUNCH14 ${c14}/14. No cloud backup is available.`:`이 기기의 저장 기록: 아이디어 ${a}건, 7일 미션 ${c7}/7, LAUNCH14 ${c14}/14. 자동 클라우드 백업은 지원하지 않습니다.`}
 document.addEventListener('wmm:language',update);$('#exportLocalData').addEventListener('click',()=>{const data={format:'wmm.playground.v30.local_backup',exportedAt:new Date().toISOString(),ideas:read('ideas',[]),tasks_seven:read('tasks_seven',{}),tasks_fourteen:read('tasks_fourteen',{})};download('WMM_PLAYGROUND_MY_DATA_'+dateStr()+'.json',JSON.stringify(data,null,2),'application/json;charset=utf-8');notify(msg('내 기록을 JSON 파일로 다운로드했습니다.','Your local backup was downloaded as JSON.'))});
 $('#clearLocalData').addEventListener('click',()=>{if(!confirm(msg('WMM PLAYGROUND 로컬 기록을 모두 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.','Delete all local WMM PLAYGROUND data? This cannot be undone.')))return;try{Object.keys(localStorage).filter(k=>k.startsWith(PREFIX)).forEach(k=>localStorage.removeItem(k))}catch(_){ }Object.keys(mem).forEach(k=>delete mem[k]);update();notify(msg('WMM PLAYGROUND 로컬 기록을 삭제했습니다.','WMM PLAYGROUND local data was deleted.'))});update();}
function initWorkspace(){
 const list=$('#workspaceItems');if(!list)return;
 let current=-1;
 const count=$('#workspaceCount'), heading=$('#workspaceTitle'), detail=$('#workspaceSelected'),empty=$('#workspaceEmpty'),pre=$('#workspaceText');
 const items=()=>{const x=read('ideas',[]);return Array.isArray(x)?x.filter(a=>a&&typeof a==='object'&&typeof a.title==='string'&&typeof a.content==='string').slice(0,30):[]};
 function render(){const data=items();count.textContent=String(data.length);list.replaceChildren();
  if(!data.length){const m=document.createElement('p');m.className='muted';m.textContent=document.documentElement.lang==='en'?'No saved ideas yet. Create one in the Idea Studio.':'저장된 아이디어가 없습니다. 스튜디오에서 첫 기획서를 만들어 보세요.';list.appendChild(m);current=-1;heading.textContent=document.documentElement.lang==='en'?'Select a saved draft.':'저장된 기획서를 선택해 주세요.';empty.hidden=false;detail.hidden=true;return}
  if(current>=data.length)current=-1;
  data.forEach((d,i)=>{const button=document.createElement('button');button.type='button';button.className='workspace-entry';button.setAttribute('aria-selected',String(current===i));const name=document.createElement('span');name.textContent=d.title;const time=document.createElement('small');time.textContent=String(d.createdAt||'').slice(0,10);button.append(name,time);button.addEventListener('click',()=>{current=i;render()});list.append(button)});
  if(current<0){heading.textContent=document.documentElement.lang==='en'?'Select a saved idea.':'저장된 아이디어를 선택해 주세요.';empty.hidden=false;detail.hidden=true;return}
  const chosen=data[current];heading.textContent=chosen.title;pre.textContent=chosen.content;empty.hidden=true;detail.hidden=false;
 }
 $('#workspaceDownload').addEventListener('click',()=>{const a=items()[current];if(a)download('WMM_SAVED_IDEA_'+dateStr()+'.md',a.content,'text/markdown;charset=utf-8')});
 $('#workspaceDelete').addEventListener('click',()=>{const a=items()[current];if(!a)return;if(!confirm(msg('선택한 아이디어를 삭제할까요? 이 작업은 되돌릴 수 없습니다.','Delete the selected draft? This cannot be undone.')))return;const next=items();next.splice(current,1);write('ideas',next);current=-1;render();notify(msg('선택한 아이디어가 삭제되었습니다.','The selected draft was deleted.'))});document.addEventListener('wmm:language',render);render();
}
function initLocalDataRestore(){const upload=$('#importLocalData');if(!upload)return;
 upload.addEventListener('change',async()=>{const file=upload.files&&upload.files[0];if(!file)return;
  try{
    if(file.size>300000)throw Error('백업 파일이 300KB를 초과합니다.');
    const data=JSON.parse(await file.text());
    if(!data||data.format!=='wmm.playground.v30.local_backup')throw Error('이 프로그램에서 생성한 백업 파일이 아닙니다.');
    if(!Array.isArray(data.ideas)||data.ideas.length>30)throw Error('아이디어 목록 개수가 잘못되었습니다.');
    const ideas=data.ideas.map(x=>{if(!x||typeof x.title!=='string'||typeof x.content!=='string'||x.title.length>100||x.content.length>15000)throw Error('기획서 항목 형식이 잘못되었습니다.');return {title:x.title,content:x.content,createdAt:String(x.createdAt||'').slice(0,35)}});
    const validateTasks=(value,limit)=>{if(!value||Array.isArray(value)||typeof value!=='object')throw Error('체크리스트 형식이 잘못되었습니다.');const out={};Object.entries(value).forEach(([k,v])=>{if(!/^(0|[1-9][0-9]*)$/.test(k)||+k>=limit||typeof v!=='boolean')throw Error('체크리스트 데이터가 올바르지 않습니다.');out[k]=v});return out};
    const seven=validateTasks(data.tasks_seven,7),fourteen=validateTasks(data.tasks_fourteen,14);
    if(!confirm(msg('현재 WMM PLAYGROUND 로컬 기록을 선택한 백업 파일로 대체하시겠습니까?','Replace current WMM PLAYGROUND local data with the selected backup?')))return;
    write('ideas',ideas);write('tasks_seven',seven);write('tasks_fourteen',fourteen);
    const info=$('#storageSummary');if(info){const done7=Object.values(seven).filter(Boolean).length,done14=Object.values(fourteen).filter(Boolean).length;info.textContent=`백업 복원 완료: 아이디어 ${ideas.length}건, 7일 미션 ${done7}/7, LAUNCH14 ${done14}/14. 다른 기기에는 자동 동기화되지 않습니다.`;}
    notify(msg('백업 기록을 복원했습니다.','Local backup was restored.'));
  }catch(err){notify(msg('복원 실패: ','Restore failed: ')+String(err.message||msg('파일 형식 오류','Invalid file format')).slice(0,115))}finally{upload.value=''}
 });
}

function init(){initNavigation();initCatalog();initStudio();initChallenges();initCollaboration();initDataControls();initWorkspace();initLocalDataRestore()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
