import {safeReturnPath} from './navigation.mjs';
import {authErrorMessage} from './auth-errors.mjs';
/** WMM Google-only login gate. No pseudo-login, no email/password form.
 * User must complete Google OAuth and Sites server token verification before map scripts load.
 */
const qs=new URLSearchParams(location.search), byCode=Object.keys(window.WMMRegions).find(n=>window.WMMRegions[n]===qs.get('code'));
const currentRegion=byCode||qs.get('region');
const validRegion='서울 경기 인천 강원 충북 충남 세종 대전 전북 전남 광주 경북 대구 경남 울산 부산 제주'.split(' ').includes(currentRegion);
const full=document.querySelector('.wr-auth-fallback');full.target='_top';const fullQuery=new URLSearchParams(location.search);fullQuery.delete('embed');full.href='/support-map/'+(fullQuery.size?'?'+fullQuery:'');
if(validRegion){fullQuery.set('region',currentRegion);fullQuery.set('code',window.WMMRegions[currentRegion]);full.href='/support-map/?'+fullQuery;document.querySelector('.wr-auth-eyebrow').textContent=currentRegion+' · 지역별 사업지원';}
if(validRegion&&document.querySelector('#public-return'))document.querySelector('#public-return').href='/support-map/?region='+encodeURIComponent(currentRegion);
let config = {};
try {
 const response=await fetch('/api/wmm/config',{cache:'no-store',signal:AbortSignal.timeout(10000)});
 if(response.ok)config=await response.json();
} catch {}
window.WMM_LOGIN_CONFIG=config;
const gate = document.getElementById('wmm-auth-gate');
const content = document.getElementById('wmm-business-radar');
const status = document.getElementById('wmm-auth-status');
const button = document.getElementById('wmm-google-signin');
const consent = document.getElementById('wmm-auth-consent');
const userBar = document.getElementById('wmm-userbar');
const userIdentity = document.getElementById('wmm-user-identity');
const signout = document.getElementById('wmm-google-signout');
const setStatus = (message,error=false) => { status.textContent=message;status.classList.toggle('is-error',error); };

const project = config.firebase || {};
const validConfig = Boolean(config.enabled && project.apiKey && project.projectId && project.authDomain && project.appId && location.protocol==='https:');
let auth, sdk, signedInUser, loadedUid, appLoaded=false;

async function loadMapAfterVerifiedLogin(user){
  window.WMM_AUTH_GET_TOKEN = async () => signedInUser?.getIdToken() || '';
  gate.hidden=true;content.hidden=false;content.classList.remove('wr-auth-locked');
  userIdentity.textContent = `${user.displayName||'Google 사용자'} · ${user.email||''}`;
  userBar.hidden=false;
  if(appLoaded){gate.hidden=true;content.hidden=false;content.classList.remove('wr-auth-locked');return;}
  const response=await fetch('/api/wmm/map-config',{headers:{Authorization:'Bearer '+await user.getIdToken()},cache:'no-store',signal:AbortSignal.timeout(12000)});
  if(response.status===401)throw Error('인증이 만료됐습니다. 다시 로그인해 주세요.');
  window.WMM_RUNTIME_MAP_CONFIG=response.ok?await response.json():{enabled:false};
  const scripts=['map-config.js','seed.js','app.js','vworld-satellite.js','earth-premium.js'];
  for(const name of scripts){
    await new Promise((resolve,reject)=>{
      const el=document.createElement('script');el.src=`assets/${name}`;el.async=false;
      const timer=setTimeout(()=>{el.remove();reject(Error('지도 로딩 시간이 초과되었습니다. 새로고침하거나 홈페이지로 돌아가세요.'));},15000);
      el.onload=()=>{clearTimeout(timer);resolve()};el.onerror=()=>{clearTimeout(timer);el.remove();reject(Error('지도 파일을 불러오지 못했습니다. 새로고침해 주세요.'))};document.body.append(el);
    });
  }
  appLoaded=true;gate.hidden=true;content.hidden=false;content.classList.remove('wr-auth-locked');
}
function lock(){
  window.dispatchEvent(new Event('wmm:auth-locked'));
  signedInUser=null;
  content.hidden=true;content.classList.add('wr-auth-locked');
  userBar.hidden=true;gate.hidden=false;
  window.WMM_AUTH_GET_TOKEN=undefined;
}
async function validateOnServer(user){
  const token=await user.getIdToken();
  const response=await fetch('/api/wmm/session',{headers:{Authorization:`Bearer ${token}`},cache:'no-store',signal:AbortSignal.timeout(12000)});
  if(!response.ok)throw Error(response.status===503 ? '서버 인증 설정을 확인해 주세요.' : '로그인 검증에 실패했습니다. 다시 로그인해 주세요.');
  const data=await response.json();
  if(!data.authenticated)throw Error('로그인이 확인되지 않았습니다.');
  if(loadedUid && loadedUid!==user.uid){location.reload();return;}
  loadedUid=user.uid;signedInUser=user;window.WMM_AUTH_UID=user.uid;
  window.WMM_BOOKMARK_KEY='wmm_radar_saved_'+user.uid;
  const back=safeReturnPath(qs.get('returnTo'),location.origin);
  if(back){location.assign(back);return;}
  await loadMapAfterVerifiedLogin(user);
}

window.addEventListener('wmm:auth-expired',async()=>{content.hidden=true;window.WMM_AUTH_GET_TOKEN=undefined;try{if(auth&&sdk)await sdk.signOut(auth)}finally{lock();setStatus('로그인 시간이 만료됐습니다. 다시 로그인해 주세요.',true)}});
if(!validConfig){
  lock();setStatus('관리자 설정 대기: Google 로그인 기능이 아직 연결되지 않았습니다.');
}else{
  try{
    const [{initializeApp},{getAuth,GoogleAuthProvider,signInWithPopup,onIdTokenChanged,signOut,browserLocalPersistence,setPersistence}]=await Promise.all([
      import('https://www.gstatic.com/firebasejs/12.0.0/firebase-app.js'),
      import('https://www.gstatic.com/firebasejs/12.0.0/firebase-auth.js')
    ]);
    const app=initializeApp(project);
    auth=getAuth(app);await setPersistence(auth,browserLocalPersistence);
    sdk={GoogleAuthProvider,signInWithPopup,signOut};
    setStatus('동의 확인 후 Google 계정으로 로그인하세요.');
    consent.addEventListener('change',()=>{button.disabled=!consent.checked});
    button.disabled=!consent.checked;
    button.addEventListener('click',async()=>{
      if(!consent.checked)return;
      button.disabled=true;setStatus('Google 계정 인증 중…');
      try{await signInWithPopup(auth,new GoogleAuthProvider());}
      catch(e){setStatus(authErrorMessage(e.code,qs.get('lang')==='en'),true)}
      finally{button.disabled=!consent.checked}
    });
    onIdTokenChanged(auth,async(user)=>{
      if(!user){lock();setStatus('동의 확인 후 Google 계정으로 로그인하세요.');return;}
      try{setStatus('서버에서 로그인 권한을 확인하고 있습니다…');await validateOnServer(user)}
      catch(e){lock();setStatus(e.message||'로그인 확인 실패',true)}
    },()=>{lock();setStatus('Google 로그인 상태를 확인할 수 없습니다.',true)});
    signout.addEventListener('click',async()=>{try{await signOut(auth)}finally{location.reload()}});
  }catch(e){lock();setStatus(authErrorMessage(e.code||'auth/module-load-failed',qs.get('lang')==='en'),true)}
}
