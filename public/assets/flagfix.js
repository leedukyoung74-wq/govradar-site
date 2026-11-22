/* GOV RADAR 국기 표시 (2026-11-22): 이모지 국기(🇰🇷)는 윈도우에서 글자(KR)로 보이므로 그림 국기로 바꾼다. 나중에 그려지는 내용도 따라 바꾼다. */
(function(){
var T=/\uD83C[\uDDE6-\uDDFF]\uD83C[\uDDE6-\uDDFF]/,G=/\uD83C[\uDDE6-\uDDFF]\uD83C[\uDDE6-\uDDFF]/g;
function css(){if(!document.querySelector('link[href*="flag-icons"]')){var l=document.createElement("link");l.rel="stylesheet";l.href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css";document.head.appendChild(l)}
 if(!document.getElementById("fxcss")){var s=document.createElement("style");s.id="fxcss";s.textContent=".fx.fi{display:inline-block;width:1.5em;height:1.1em;line-height:1;vertical-align:-.18em;background-size:cover;background-position:center;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.14)}";document.head.appendChild(s)}}
function code(f){return String.fromCharCode(f.codePointAt(0)-127397,f.codePointAt(2)-127397).toLowerCase()}
function skip(p){for(;p&&p!==document.body;p=p.parentNode){if(p.nodeType===1){var n=p.nodeName;if(/^(SCRIPT|STYLE|TEXTAREA|OPTION|SELECT|TITLE|INPUT|CANVAS)$/.test(n)||p.namespaceURI==="http://www.w3.org/2000/svg"||p.isContentEditable)return true}}return false}
function fix(root){if(!root||!document.body)return;var w=document.createTreeWalker(root,4,null),L=[],n;while((n=w.nextNode()))if(T.test(n.nodeValue)&&!skip(n.parentNode))L.push(n);
 L.forEach(function(t){var s=t.nodeValue,f=document.createDocumentFragment(),i=0,m;G.lastIndex=0;while((m=G.exec(s))){if(m.index>i)f.appendChild(document.createTextNode(s.slice(i,m.index)));var c=code(m[0]),sp=document.createElement("span");sp.className="fx fi fi-"+c;sp.setAttribute("role","img");sp.setAttribute("aria-label",c.toUpperCase());f.appendChild(sp);i=m.index+m[0].length}
  if(i<s.length)f.appendChild(document.createTextNode(s.slice(i)));if(t.parentNode)t.parentNode.replaceChild(f,t)})}
function go(){css();fix(document.body);var q=[],tm=0;new MutationObserver(function(ms){ms.forEach(function(m){m.addedNodes.forEach(function(x){q.push(x.nodeType===3?x.parentNode:x)})});clearTimeout(tm);tm=setTimeout(function(){var a=q;q=[];a.forEach(function(x){if(x&&x.isConnected)fix(x)})},60)}).observe(document.body,{childList:true,subtree:true})}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",go);else go();
})();
