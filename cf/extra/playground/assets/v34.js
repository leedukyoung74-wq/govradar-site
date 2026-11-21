/* WMM PLAYGROUND v34 — 작은 구동 개선 (서버 호출·추적·저장 키 변경 없음) */
(()=>{'use strict';
function ready(fn){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',fn);else fn();}
ready(()=>{
  // 솔루션 찾기: 처음 열었을 때 기본 조건 추천을 미리 보여 준다(화면 위치는 그대로).
  const form=document.getElementById('matchForm'),res=document.getElementById('matchResults');
  if(form&&res&&!res.children.length&&!location.hash){
    const y=window.scrollY;
    setTimeout(()=>{
      if(res.children.length)return;
      try{form.requestSubmit?form.requestSubmit():form.dispatchEvent(new Event('submit',{cancelable:true,bubbles:true}));}catch(e){return;}
      window.scrollTo(0,y);
      if(document.activeElement&&document.activeElement!==document.body)document.activeElement.blur();    },0);
  }
  // 외부로 나가는 링크는 항상 새 창 + 참조자 정보 차단
  document.querySelectorAll('a[href^="http"]').forEach(a=>{
    if(a.host!==location.host){a.target='_blank';a.rel='noopener noreferrer';}
  });
});
})();
