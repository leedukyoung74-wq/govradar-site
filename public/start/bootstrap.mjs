// Reuse a Google login from /support-map/. No automatic OAuth or extra scopes.
try {
 const r=await fetch('/api/wmm/config',{cache:'no-store',signal:AbortSignal.timeout(6000)});
 const config=await r.json();
 if(r.ok&&config.enabled){
  const [{initializeApp},{getAuth,onAuthStateChanged}]=await Promise.all([
   import('https://www.gstatic.com/firebasejs/12.0.0/firebase-app.js'),
   import('https://www.gstatic.com/firebasejs/12.0.0/firebase-auth.js')
  ]);
  const auth=getAuth(initializeApp(config.firebase));
  await new Promise(resolve=>{let stop=()=>{};const timer=setTimeout(()=>{stop();resolve();},6000);stop=onAuthStateChanged(auth,()=>{clearTimeout(timer);stop();resolve();},()=>{clearTimeout(timer);resolve();});});
  window.WMM_START_TOKEN=async()=>auth.currentUser?auth.currentUser.getIdToken():'';
 }
}catch{/* Public calculators and official-source links remain usable. */}
await import('./app.js');
