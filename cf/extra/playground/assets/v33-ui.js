/* WMM Playground design-shell only. No API calls, localStorage, or account data. */
(()=>{'use strict';
function refresh(){
 const en=document.documentElement.lang==='en';
 const art=document.querySelector('.wmm-story-art');
 if(art)art.setAttribute('aria-label',en?'Original WMM illustration connecting creativity, collaboration and progress':'창작·연결·실행·성장을 상징하는 WMM 오리지널 벡터');
 const path=location.pathname.split('/').pop()||'index.html';
 document.querySelectorAll('.wmm-pathbar a').forEach(a=>{
   if(a.getAttribute('href')===path)a.setAttribute('aria-current','page');
   else a.removeAttribute('aria-current');
 });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refresh);else refresh();
document.addEventListener('wmm:language',refresh);
})();
