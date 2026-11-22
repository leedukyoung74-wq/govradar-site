"use strict";
const languageSelect=document.getElementById('world-language');
document.getElementById('translate-page').addEventListener('click',()=>{
 const language=languageSelect.value;if(!language){languageSelect.focus();return;}
 const url=new URL('https://translate.google.com/translate');
 url.searchParams.set('sl','en');url.searchParams.set('tl',language==='other'?'en':language);
 url.searchParams.set('u','https://www.wmm-hoa.com/business-studio/en.html');
 location.href=url.href;
});
