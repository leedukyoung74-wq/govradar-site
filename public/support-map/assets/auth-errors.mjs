export function authErrorMessage(code, en=false) {
 const messages={
  'auth/invalid-api-key':['Google이 현재 인증키를 거부했습니다(API_KEY_INVALID). 관리자에게 Firebase 웹 API 키 수정을 요청해 주세요. 반복 로그인으로 해결되지 않습니다.','Google rejected the configured Firebase API key (API_KEY_INVALID). An administrator must correct it.'],
  'auth/api-key-not-valid.-please-pass-a-valid-api-key.':['Google 인증키가 유효하지 않습니다(API_KEY_INVALID). 관리자 설정이 필요합니다.','The Firebase API key is invalid. Administrator action is required.'],
  'auth/unauthorized-domain':['현재 홈페이지 주소가 Google 로그인 승인 도메인에 등록되지 않았습니다. 관리자 확인이 필요합니다.','This website is not an authorized sign-in domain. Contact the administrator.'],
  'auth/operation-not-allowed':['Firebase에서 Google 로그인 제공업체가 비활성화되어 있습니다.','The Google sign-in provider is disabled in Firebase.'],
  'auth/popup-blocked':['팝업이 차단됐습니다. 전체 화면에서 열고 이 사이트의 팝업을 허용한 뒤 다시 시도해 주세요.','The popup was blocked. Open the full page and allow popups for this site.'],
  'auth/popup-closed-by-user':['로그인 창이 닫혔습니다. 다시 시도할 수 있습니다.','The sign-in window was closed. You can try again.'],
  'auth/network-request-failed':['Google 인증 서버에 연결하지 못했습니다. 네트워크를 확인하고 다시 시도해 주세요.','Unable to reach Google authentication. Check your connection and retry.'],
  'auth/web-storage-unsupported':['브라우저 저장소가 차단되어 로그인 상태를 유지할 수 없습니다. 일반 브라우저에서 전체 화면으로 열어 주세요.','Browser storage is blocked. Open the full page in a regular browser.']
 };
 return (messages[code]||['로그인하지 못했습니다. 관리자에게 오류 코드 '+String(code||'auth/unknown').replace(/[^a-zA-Z0-9/_.-]/g,'').slice(0,80)+'를 알려 주세요.','Sign-in failed. Contact the administrator with code '+String(code||'auth/unknown').replace(/[^a-zA-Z0-9/_.-]/g,'').slice(0,80)])[en?1:0];
}
