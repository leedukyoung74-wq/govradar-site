const CACHE='wmm-app-v6';
const FILES=['./','./index.html','./manifest.json','./icon-192.png','./icon-512.png','./logo-mark.png','./logo-seal.png','./apple-touch-icon.png','/design-system.css?v=20261029','/site-navigation.js?v=20261029','/fonts/NEXONLv1GothicRegular.ttf','/fonts/NEXONLv1GothicBold.ttf'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('wmm-app-')&&k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',e=>{
 const u=new URL(e.request.url);
 if(e.request.method!=='GET'||u.origin!==self.location.origin||!(u.pathname.startsWith('/app/')||FILES.some(f=>new URL(f,self.location.href).href===u.href)))return;
 e.respondWith(fetch(e.request).then(r=>{if(r.ok){const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp)).catch(()=>{});}return r;}).catch(async()=>{const hit=await caches.match(e.request);if(hit)return hit;if(e.request.mode==='navigate')return caches.match('./index.html');return Response.error();}));
});
