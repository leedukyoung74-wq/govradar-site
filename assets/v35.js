/* v35: 고정 탭 위치·현재 섹션 표시 (서버 호출 없음) */
(()=>{'use strict';
function ready(f){document.readyState==='loading'?document.addEventListener('DOMContentLoaded',f):f();}
ready(()=>{
  const tabs=document.querySelector('.px-tabs');if(!tabs)return;
  const head=document.querySelector('.header');
  const setTop=()=>{const h=head?head.getBoundingClientRect().height:64;document.documentElement.style.setProperty('--px-tabs-top',Math.round(h)+'px');};
  setTop();addEventListener('resize',setTop);
  const links=[...tabs.querySelectorAll('a[href^="#"]')];
  const secs=links.map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
  if(!('IntersectionObserver' in window)||!secs.length)return;
  const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){links.forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id));}});},{rootMargin:'-40% 0px -55% 0px'});
  secs.forEach(s=>io.observe(s));
});
})();
/* v35.1: 영상 재생 버튼·스크롤 등장 효과(움직임 최소화 설정 존중) */
(()=>{'use strict';
function ready(f){document.readyState==='loading'?document.addEventListener('DOMContentLoaded',f):f();}
ready(()=>{
  const rm=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  const v=document.getElementById('pxFilm'),b=document.getElementById('pxFilmBtn');
  if(v&&b){
    const sync=()=>{const paused=v.paused;b.setAttribute('aria-pressed',String(paused));
      b.querySelector('[data-locale="ko"]').textContent=paused?'재생':'일시정지';b.querySelector('[data-locale="en"]').textContent=paused?'Play':'Pause';};
    if(rm){v.removeAttribute('autoplay');v.pause();}
    b.addEventListener('click',()=>{v.paused?v.play().catch(()=>{}):v.pause();});
    v.addEventListener('play',sync);v.addEventListener('pause',sync);sync();
  }
  if(rm||!('IntersectionObserver' in window))return;
  const els=document.querySelectorAll('.px-row,.px-bubble,.px-step,.px-film-frame');
  const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}}),{rootMargin:'0px 0px -8% 0px'});
  els.forEach(el=>{const r=el.getBoundingClientRect();if(r.top<innerHeight)return;el.classList.add('px-reveal');io.observe(el);});
});
})();
/* v38: 첫 화면 영상 멈춤 버튼, 14일 탭 바로가기 */
(()=>{'use strict';
function ready(f){document.readyState==='loading'?document.addEventListener('DOMContentLoaded',f):f();}
ready(()=>{
  const v=document.getElementById('pxHeroVideo'),b=document.getElementById('pxHeroPause');
  if(v&&b){
    const rm=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
    const lab=()=>{const p=v.paused;b.setAttribute('aria-pressed',String(p));b.querySelector('[data-locale="ko"]').textContent=p?'움직임 재생':'움직임 멈춤';b.querySelector('[data-locale="en"]').textContent=p?'Play motion':'Pause motion';};
    if(rm){v.removeAttribute('autoplay');v.pause();}
    b.addEventListener('click',()=>{v.paused?v.play().catch(()=>{}):v.pause();});
    v.addEventListener('play',lab);v.addEventListener('pause',lab);lab();
  }
  if(location.hash==='#launch14'){const t=document.getElementById('tab14');if(t)setTimeout(()=>{t.click();t.scrollIntoView({block:'start'});},50);}
});
})();
/* v39.1: 씨앗 슬라이드 — 화면에 들어오면 반듯하게 */
(()=>{'use strict';
function ready(f){document.readyState==='loading'?document.addEventListener('DOMContentLoaded',f):f();}
ready(()=>{
  const s=document.querySelectorAll('.seed-slide');if(!s.length)return;
  if(!('IntersectionObserver' in window)){s.forEach(x=>x.classList.add('flat'));return;}
  const io=new IntersectionObserver(es=>es.forEach(e=>e.target.classList.toggle('flat',e.isIntersecting&&e.intersectionRatio>0.45)),{threshold:[0,.45,.7]});
  s.forEach(x=>io.observe(x));
});
})();
