const language = document.documentElement.dataset.language;
const ko = language === 'ko';
const form = document.querySelector('#member');
const passwordForm = document.querySelector('#new-password');
const message = document.querySelector('#message');
const google = document.querySelector('#google');
const text = {
  wait: ko ? '확인 중입니다.' : 'Checking your request.',
  error: ko ? '요청이 완료되지 않았습니다. 입력과 이메일 인증 상태를 확인하고 다시 시도하세요.' : 'The request did not complete. Check your details and email verification, then try again.',
  verify: ko ? '가입 확인 메일을 확인하세요.' : 'Check your email for a verification link.',
  reset: ko ? '등록된 이메일이라면 재설정 링크가 발송됩니다.' : 'If this email is registered, you will receive a reset link.',
  password: ko ? '새 비밀번호를 입력하세요.' : 'Enter your new password.',
};

async function identity(path, options) {
  const response = await fetch(`/.netlify/identity${path}`, options);
  if (!response.ok) throw new Error('identity');
  const value = await response.text();
  return value ? JSON.parse(value) : null;
}

function json(method, data, extra) {
  return { method, headers: { 'content-type': 'application/json', ...extra }, body: JSON.stringify(data) };
}

async function enter(tokens) {
  if (!tokens?.access_token) throw new Error('session');
  const headers = { authorization: `Bearer ${tokens.access_token}` };
  const user = await identity('/user', { headers });
  const response = await fetch('/gate/session', { method: 'POST', headers });
  if (!response.ok) throw new Error('session');
  try {
    localStorage.setItem('wmm.auth.v1', JSON.stringify({
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      expires_at: Date.now() + (Number(tokens.expires_in) || 3600) * 1000,
      user,
    }));
  } catch { /* browser storage is optional for the server gate */ }
  location.replace(`/${language}/?stay=1`);
}

function signIn(email, password) {
  return identity('/token', {
    method: 'POST',
    body: new URLSearchParams({ grant_type: 'password', username: email, password }),
  });
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = form.querySelector('button');
  const fields = new FormData(form);
  const email = fields.get('email').trim();
  const password = fields.get('password');
  button.disabled = true;
  message.textContent = text.wait;
  try {
    if (form.dataset.mode === 'login') {
      await enter(await signIn(email, password));
    } else if (form.dataset.mode === 'signup') {
      const age = fields.get('age');
      if (!fields.get('terms') || !['adult', 'teen'].includes(age)) throw new Error('signup');
      const timestamp = new Date().toISOString();
      const user = await identity('/signup', json('POST', {
        email, password, data: { full_name: fields.get('name').trim(), lang: language, age_band: age, terms_at: timestamp, marketing: false, marketing_at: null, marketing_decision_at: timestamp },
      }));
      if (user?.confirmed_at) await enter(await signIn(email, password));
      else message.textContent = text.verify;
    } else {
      await identity('/recover', json('POST', { email }));
      message.textContent = text.reset;
    }
  } catch {
    message.textContent = text.error;
  } finally {
    button.disabled = false;
  }
});

function promptForPassword(changePassword) {
  form.hidden = true;
  passwordForm.hidden = false;
  if (google) google.hidden = true;
  message.textContent = text.password;
  passwordForm.addEventListener('submit', async event => {
    event.preventDefault();
    const button = passwordForm.querySelector('button');
    button.disabled = true;
    try { await changePassword(new FormData(passwordForm).get('password')); }
    catch { message.textContent = text.error; }
    finally { button.disabled = false; }
  });
  passwordForm.querySelector('input').focus();
}

async function processCallback() {
  if (!location.hash) return;
  const values = new URLSearchParams(location.hash.slice(1));
  history.replaceState(null, '', location.pathname + location.search);
  const confirmation = values.get('confirmation_token');
  const recovery = values.get('recovery_token');
  const invitation = values.get('invite_token');
  const access = values.get('access_token');
  if (confirmation) {
    await enter(await identity('/verify', json('POST', { type: 'signup', token: confirmation })));
  } else if (recovery) {
    const tokens = await identity('/verify', json('POST', { type: 'recovery', token: recovery }));
    promptForPassword(async password => {
      await identity('/user', json('PUT', { password }, { authorization: `Bearer ${tokens.access_token}` }));
      await enter(tokens);
    });
  } else if (invitation) {
    promptForPassword(async password => enter(await identity('/verify', json('POST', { type: 'signup', token: invitation, password }))));
  } else if (access) {
    const initiated = sessionStorage.getItem('govradar.oauth.language');
    sessionStorage.removeItem('govradar.oauth.language');
    if (!initiated || initiated !== language) throw new Error('oauth');
    await enter({ access_token: access, refresh_token: values.get('refresh_token'), expires_in: values.get('expires_in') });
  } else if (values.has('error_description')) {
    throw new Error('identity');
  }
}

form.querySelector('button').disabled = false;
processCallback().catch(() => { message.textContent = text.error; });
if (google) {
  identity('/settings').then(settings => { google.hidden = form.hidden || !settings?.external?.google; }).catch(() => {});
  google.addEventListener('click', () => {
    try {
      sessionStorage.setItem('govradar.oauth.language', language);
      location.href = '/.netlify/identity/authorize?provider=google';
    } catch { message.textContent = text.error; }
  });
}
