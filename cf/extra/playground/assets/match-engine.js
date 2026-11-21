/* WMM PLAYGROUND v32 — deterministic offline editorial guide, not AI or business advice. */
(function (root,factory) {
  'use strict';
  const api=factory();
  if(typeof module==='object' && module.exports) module.exports=api;
  if(root) root.WMM_MATCH=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const GOALS={
  launch:['business','ai','code','design'],
  make:['design','video','music','code'],
  learn:['career','ai','code','music'],
  local:['local','impact','planet','safety'],
  ready:['safety','planet','local','global'],
  connect:['global','impact','career','local']
 };
 const ALLOWED_MINUTES=[15,30,60];
 const MODE=['solo','team','community'];
 const LEVEL=['first','growing','together'];
 const LEVEL_KO={first:'시작하기',growing:'한 단계 더',together:'함께하기'};
 const MODES_BY_CATEGORY={team:['design','video','music','ai','business','code','global'],community:['local','impact','planet','safety','global'],solo:['career','ai','code','design','business','music']};
 function validate(choices){
  if(!choices || !Object.prototype.hasOwnProperty.call(GOALS,choices.goal)) throw Error('Invalid goal');
  const minutes=Number(choices.minutes);
  if(!ALLOWED_MINUTES.includes(minutes)||!MODE.includes(choices.mode)||!LEVEL.includes(choices.level)) throw Error('Invalid selection');
  return {goal:choices.goal,minutes,mode:choices.mode,level:choices.level};
 }
 function rank(items,choices){
  const p=validate(choices);
  if(!Array.isArray(items)||items.length>1000) throw Error('Invalid catalog');
  const priorities=GOALS[p.goal];
  const scored=[];
  for(const x of items){
    if(!x || !/^[a-z]+-[0-9]{2}$/.test(x.id||'') || !Number.isFinite(x.duration) || !x.title || !x.titleEn || x.reviewStatus!=='EDITORIAL_DRAFT'||x.live!==false) continue;
    if(x.duration>p.minutes) continue;
    const priority=priorities.indexOf(x.category);
    let score=priority<0?15:100-priority*16;
    score+=x.duration<=p.minutes/2?12:6;
    if(x.difficulty===LEVEL_KO[p.level])score+=12;
    if((MODES_BY_CATEGORY[p.mode]||[]).includes(x.category))score+=9;
    if(x.duration===15)score+=1;
    scored.push({item:x,score,priority:priority<0?9:priority});
  }
  scored.sort((a,b)=>b.score-a.score||a.priority-b.priority||a.item.id.localeCompare(b.item.id));
  // Avoid the misleading impression that six near-identical templates are six distinct solutions.
  const chosen=[],perCategory=new Map();
  for(const candidate of scored){
   const used=perCategory.get(candidate.item.category)||0;
   if(used>=2)continue;
   chosen.push(candidate);perCategory.set(candidate.item.category,used+1);
   if(chosen.length>=6) break;
  }
  return chosen;
 }
 function buildPlan(item,opts){
  if(!item||item.reviewStatus!=='EDITORIAL_DRAFT'||item.live!==false)throw Error('Source must be a WMM preview editorial draft');
  const en=opts?.lang==='en';
  const title=en?item.titleEn:item.title;
  const description=en?item.descriptionEn:item.description;
  const deliverable=en?item.deliverableEn:item.deliverable;
  const tasks=en?[
   ['State a concrete outcome',`Write one result that would demonstrate success: ${deliverable}.`],
   ['Define what you already know',`List assumptions and unknowns for: ${description}`],
   ['Set boundaries','Define time, money, accessibility, privacy and any permissions before starting.'],
   ['Make a small draft',`Work on this preview idea: ${title}. Keep the first output narrow.`],
   ['Get consent-based feedback','Ask a relevant person for voluntary feedback; do not collect sensitive details.'],
   ['Check feasibility and rights','Verify resources, risks, copyright, source accuracy and applicable rules.'],
   ['Record next action','Write what worked, what failed and one small next experiment.']
  ]:[
   ['구체적인 결과 정하기',`완료를 확인할 수 있는 결과물 하나를 적습니다: ${deliverable}.`],
   ['현재 알고 있는 것 분리하기',`가정과 아직 모르는 것을 구분합니다: ${description}`],
   ['실행 범위 정하기','시간·비용·접근성·개인정보·저작권과 필요한 허가를 확인합니다.'],
   ['작은 초안 만들기',`WMM 기획 주제 '${title}'에서 가장 작은 결과물을 제작합니다.`],
   ['동의받은 피드백 받기','관련 당사자에게 자발적인 의견을 요청하고 민감정보는 기록하지 않습니다.'],
   ['실현 가능성과 권리 점검','필요 자원·위험·출처·저작권·현지 규정을 검토합니다.'],
   ['다음 행동 정하기','성공·실패·배운 점과 다음에 검증할 가설 하나를 적습니다.']
  ];
  return {id:item.id,title,description,deliverable,tasks,lang:en?'en':'ko'};
 }
 function markdown(plan){
  if(!plan||!Array.isArray(plan.tasks)||plan.tasks.length!==7)throw Error('Invalid plan');
  const en=plan.lang==='en';
  return `# WMM PLAYGROUND — ${plan.title}\n\n${en?'Preview editorial exercise, not verified advice or a live project.':'WMM 내부 기획 초안이며 검증된 사업·공식 정보나 실제 프로젝트가 아닙니다.'}\n\n${en?'Goal':'목표'}: ${plan.description}\n${en?'Output':'결과물'}: ${plan.deliverable}\n\n`+plan.tasks.map(([title,detail],i)=>`- [ ] ${en?'Day':'일차'} ${i+1}: ${title}\n  - ${detail}`).join('\n')+`\n\n${en?'Review privacy, rights and safety before public use.':'대외 공개 전 개인정보·권리·안전 사항을 검토하세요.'}\n`;
 }
 return Object.freeze({GOALS,validate,rank,buildPlan,markdown});
});
