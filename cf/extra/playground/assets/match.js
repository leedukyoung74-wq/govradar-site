/* WMM PLAYGROUND v32 offline guided discovery; no network requests, no tracking. */
(function(){'use strict';
 const $=s=>document.querySelector(s),create=(tag,className,text)=>{const el=document.createElement(tag);if(className)el.className=className;if(text!==undefined)el.textContent=text;return el};
 let current=null,selected=null;
 function english(){return document.documentElement.lang==='en'}
 function toast(message){const el=$('#toast');if(!el)return;el.textContent=message;el.hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>{el.hidden=true},3500)}
 function saveFile(filename,body){const blob=new Blob([body],{type:'text/markdown;charset=utf-8'}),url=URL.createObjectURL(blob);const a=create('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),800)}
 function humanDuration(n){return english()?`${n} min`:`${n}분`}
 function render(){const list=$('#matchResults'),detail=$('#matchPlan'),feedback=$('#matchFeedback');list.replaceChildren();detail.hidden=true;selected=null;
  if(!current){feedback.textContent=english()?'Choose your goal and time, then find a starting point.':'목표와 시간을 선택하면 시작점을 추천합니다.';return}
  const results=window.WMM_MATCH.rank(window.WMM_CATALOG,current);
  feedback.textContent=english()?`${results.length} editorial ideas matched. No account, AI API or tracking is used.`:`${results.length}개 기획 초안을 찾았습니다. 가입·AI API·추적 없이 추천합니다.`;
  if(!results.length){list.append(create('p','muted',english()?'No match: try a longer time window.':'해당 조건의 콘텐츠가 없습니다. 실행 시간을 늘려보세요.'));return}
  for(const [i,choice] of results.entries()){
   const x=choice.item,card=create('article','match-result'),head=create('div','match-result-head');
   head.append(create('span','match-rank',String(i+1).padStart(2,'0')),create('span','tag',english()?x.categoryEn:x.categoryKo),create('span','tag',humanDuration(x.duration)));
   const title=create('h3','',english()?x.titleEn:x.title),desc=create('p','muted',english()?x.descriptionEn:x.description);
   const note=create('p','match-reason',english()?'Chosen for your goal, available time and way of working; this is an unverified WMM editorial draft.':'선택한 목표·시간·실행 방식과의 관련성을 기준으로 추천한 검증 전 WMM 기획 초안입니다.');
   const btn=create('button','btn outline small',english()?'Make my 7-day plan →':'7일 실행계획 만들기 →');btn.type='button';btn.addEventListener('click',()=>showPlan(x));
   const link=create('a','match-link',english()?'Open idea studio →':'아이디어 스튜디오에서 시작 →');link.href='studio.html?template='+encodeURIComponent(x.id);
   card.append(head,title,desc,note,btn,link);list.append(card)
  }
 }
 function showPlan(x){selected=x;const d=$('#matchPlan'),out=$('#matchPlanContent');const plan=window.WMM_MATCH.buildPlan(x,{lang:english()?'en':'ko'});
  out.replaceChildren();out.append(create('h3','',plan.title),create('p','muted',plan.description));
  const list=create('ol','match-steps');for(const [name,description] of plan.tasks){const li=create('li');li.append(create('b','',name),create('p','',description));list.append(li)}out.append(list);
  d.hidden=false;d.scrollIntoView({behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
 }
 function saveCurrent(){if(!selected){toast(english()?'Choose a plan first.':'먼저 실행계획을 선택하세요.');return}const plan=window.WMM_MATCH.buildPlan(selected,{lang:english()?'en':'ko'}),md=window.WMM_MATCH.markdown(plan);
  let existing=[];try{const old=JSON.parse(localStorage.getItem('wmm.playground.v30.ideas')||'[]');if(Array.isArray(old))existing=old.filter(x=>x&&typeof x.title==='string'&&typeof x.content==='string').slice(0,29)}catch(_){}
  const entry={title:plan.title.slice(0,100),content:md.slice(0,15000),createdAt:new Date().toISOString()};existing.unshift(entry);
  try{localStorage.setItem('wmm.playground.v30.ideas',JSON.stringify(existing));toast(english()?'Saved to My Workspace on this device.':'이 기기의 내 작업함에 저장했습니다.')}catch(_){saveFile('WMM_7DAY_'+selected.id+'.md',md);toast(english()?'Local storage unavailable. Saved a Markdown file instead.':'브라우저 저장이 불가하여 Markdown 파일을 내려받았습니다.')}
 }
 function init(){if(!$('#matchForm'))return;
  $('#matchForm').addEventListener('submit',e=>{e.preventDefault();const form=e.currentTarget;if(!form.reportValidity())return;
   try{current=window.WMM_MATCH.validate({goal:$('#matchGoal').value,minutes:$('#matchMinutes').value,mode:$('#matchMode').value,level:$('#matchLevel').value});render();$('#matchResults').scrollIntoView({behavior:'smooth',block:'start'})}catch(_){toast(english()?'Choose valid options.':'옵션을 다시 선택해주세요.')}});
  $('#matchDownload').addEventListener('click',()=>{if(selected){saveFile('WMM_7DAY_'+selected.id+'_'+(english()?'EN':'KO')+'.md',window.WMM_MATCH.markdown(window.WMM_MATCH.buildPlan(selected,{lang:english()?'en':'ko'})))}});
  $('#matchSave').addEventListener('click',saveCurrent);
  document.addEventListener('wmm:language',()=>{if(current)render()});
  render();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
