const supported = new Set(['ko', 'en', 'es', 'fr', 'ar', 'vi', 'id']);

export function renderAccess(request, language) {
  if (!supported.has(language)) return new Response(null, { status: 404 });
  const ko = language === 'ko';
  const mode = new URL(request.url).searchParams.get('mode');
  const introTarget = `/welcome/${ko ? '' : language + '/'}`;
  const labels = {
    adult: ko ? '만 19세 이상' : '19 or older',
    teen: ko ? '만 14세 이상 19세 미만' : '14 to under 19',
    name: ko ? '이름 또는 기관명' : 'Name or organisation',
    age: ko ? '연령대' : 'Age group',
    ageSelect: ko ? '선택' : 'Select',
    email: ko ? '이메일' : 'Email',
    password: ko ? '비밀번호' : 'Password',
    newPassword: ko ? '새 비밀번호' : 'New password',
    login: ko ? '로그인' : 'Sign in',
    signup: ko ? '무료 회원가입' : 'Create a free account',
    reset: ko ? '비밀번호 재설정' : 'Reset password',
    submitReset: ko ? '재설정 링크 보내기' : 'Send reset link',
    save: ko ? '저장' : 'Save password',
    goBack: ko ? '레이더 인트로 보기' : 'View radar intro',
    verify: ko ? '회원가입 및 이메일 인증 후 레이더를 열람할 수 있습니다.' : 'Create an account and verify your email to access GOV RADAR.',
  };
  const isSignup = mode === 'signup';
  const isReset = mode === 'reset';
  const title = isSignup ? labels.signup : isReset ? labels.reset : labels.login;
  const terms = ko ? '<a href="/ko/legal/terms/">이용약관</a>과 <a href="/ko/legal/privacy/">개인정보 처리방침</a>에 동의합니다' : `<span>I agree to the <a href="/${language}/legal/terms/">terms</a> and <a href="/${language}/legal/privacy/">privacy policy</a></span>`;
  const fields = [
    `<label>${labels.email}<input type="email" name="email" autocomplete="email" required></label>`,
    !isReset ? `<label>${labels.password}<input type="password" name="password" autocomplete="${isSignup ? 'new-password' : 'current-password'}" ${isSignup ? 'minlength="8"' : ''} required></label>` : '',
    isSignup ? `<label>${labels.name}<input name="name" autocomplete="name" required maxlength="160"></label><label>${labels.age}<select name="age" required><option value="">${labels.ageSelect}</option><option value="adult">${labels.adult}</option><option value="teen">${labels.teen}</option></select></label><label class="check"><input name="terms" type="checkbox" required><span>${terms}</span></label>` : '',
  ].join('');
  const href = `/access/${language}/`;
  const html = `<!doctype html>
<html lang="${ko ? 'ko' : 'en'}" data-language="${language}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow"><title>${title} · GOV RADAR</title>
<link rel="icon" href="/assets/mark.png"><script src="/access/member.js" defer></script>
<style>*,::before,::after{box-sizing:border-box}body{margin:0;background:#0b172b;color:#162039;font:1rem/1.55 system-ui,sans-serif;min-height:100vh;display:grid;place-items:center;padding:2rem 1rem}main{width:min(100%,31rem);background:#fff;border-radius:1rem;padding:clamp(1.5rem,6vw,3rem)}.brand{font-size:.86rem;font-weight:800;letter-spacing:.16em;margin:0;color:#234c99}h1{line-height:1.13;margin:1rem 0 .5rem;font-size:2rem}form{display:grid;gap:1rem;margin-top:1.25rem}label{display:grid;gap:.3rem;font-weight:600}input,select,button{font:inherit}input,select{width:100%;padding:.6rem;border:1px solid #68748b;border-radius:.4rem}button{border:0;border-radius:.4rem;padding:.75rem;color:white;background:#204993;font-weight:750;cursor:pointer}button:disabled{opacity:.6}.check{display:flex;gap:.5rem;align-items:flex-start;font-weight:400}.check input{width:auto;margin-top:.24rem}a{color:#164a9f}nav{display:flex;gap:.75rem 1rem;flex-wrap:wrap;margin-top:.75rem}p[role=status]{min-height:1.5em;color:#83293a}button[hidden],form[hidden]{display:none}</style></head>
<body><main><p class="brand">GOV RADAR</p><h1>${title}</h1><p>${labels.verify}</p>
<form id="member" data-mode="${isSignup ? 'signup' : isReset ? 'reset' : 'login'}">
${fields}<button disabled>${isReset ? labels.submitReset : title}</button></form>
<form id="new-password" hidden><label>${labels.newPassword}<input name="password" type="password" minlength="8" autocomplete="new-password" required></label><button>${labels.save}</button></form>
${isSignup || isReset ? '' : '<p><button type="button" id="google" hidden>Google</button></p>'}
<p id="message" role="status" aria-live="polite"></p><nav aria-label="GOV RADAR"><a href="${href}">${labels.login}</a><a href="${href}?mode=signup">${labels.signup}</a><a href="${href}?mode=reset">${labels.reset}</a><a href="/intro/?to=${encodeURIComponent(introTarget)}&amp;replay=1">${labels.goBack}</a></nav></main></body></html>`;
  return new Response(request.method === 'HEAD' ? null : html, {
    headers: {
      'content-type': 'text/html; charset=utf-8',
      'cache-control': 'private, no-store',
      'referrer-policy': 'no-referrer',
      'content-security-policy': "default-src 'none'; script-src 'self'; img-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'",
    },
  });
}
