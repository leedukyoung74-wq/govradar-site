import test from 'node:test';
import assert from 'node:assert/strict';
import { access, readFile } from 'node:fs/promises';

const stage = new URL('../stage/', import.meta.url);
const origin = 'https://radar.wmm-hoa.com';
const token = 'review.mock.token';
const cookie = `__Host-govradar-member=${token}`;
let ready = true;
try { await access(new URL('public/assets/auth.js', stage)); }
catch { ready = false; }

test('assembled site integrates the server gate with real staged HTML and data', { skip: !ready }, async t => {
  const { onRequest } = await import(new URL('functions/_middleware.js', stage));
  const actualFetch = globalThis.fetch;
  let identityCalls = 0;
  globalThis.fetch = async (url, options) => {
    assert.equal(url, 'https://wmm-govradar.netlify.app/.netlify/identity/user');
    assert.equal(options.headers.authorization, `Bearer ${token}`);
    identityCalls++;
    return Response.json({ id: 'fake-user', confirmed_at: '2026-01-01T00:00:00Z' });
  };
  t.after(() => { globalThis.fetch = actualFetch; });

  async function request(path, options = {}) {
    const incoming = new Request(origin + path, options);
    return onRequest({
      request: incoming,
      env: {},
      next: async () => {
        const url = new URL(incoming.url);
        const file = url.pathname.endsWith('/') ? `${url.pathname}index.html` : url.pathname;
        return new Response(await readFile(new URL('public' + file, stage)));
      },
    });
  }

  const video = await request('/intro/?to=%2Fwelcome%2F&replay=1');
  assert.match(await video.text(), /gov-radar-intro\.mp4/);
  const welcome = await request('/welcome/');
  assert.match(await welcome.text(), /\/welcome\/login\//);
  const login = await request('/welcome/login/');
  assert.equal(login.headers.get('location'), '/access/ko/');
  const signup = await request('/access/ko/?mode=signup');
  assert.match(await signup.text(), /무료 회원가입/);
  for (const [path, signature] of [['/access/member.js', /async function enter/], ['/access/entry.js', /emailOrProvider/]]) {
    const script = await request(path);
    assert.match(await script.text(), signature);
    assert.match(script.headers.get('cache-control'), /no-store/);
  }
  const refused = await request('/ko/south-korea/?stay=1');
  assert.equal(refused.status, 303);
  assert.equal(await refused.text(), '');
  const refusedData = await request('/data/countries.json');
  assert.equal(refusedData.status, 401);
  assert.equal(identityCalls, 0);

  const created = await request('/gate/session', { method: 'POST', headers: { origin, authorization: `Bearer ${token}` } });
  assert.equal(created.status, 204);
  assert.ok(created.headers.get('set-cookie').startsWith(cookie));
  const admitted = await request('/ko/south-korea/', { headers: { cookie } });
  assert.match(await admitted.text(), /대한민국/);
  assert.match(admitted.headers.get('cache-control'), /no-store/);
  const admittedData = await request('/data/countries.json', { headers: { cookie } });
  assert.ok(Object.keys(await admittedData.json()).length > 0);
  assert.equal(identityCalls, 3);

  const auth = await request('/assets/auth.js', { headers: { cookie } });
  assert.match(await auth.text(), /\/gate\/session/);
  const site = await request('/assets/site.js', { headers: { cookie } });
  assert.match(await site.text(), /await window\.WMMAuth\.logout\(\)/);
  const logout = await request('/gate/logout', { method: 'POST', headers: { origin, cookie } });
  assert.match(logout.headers.get('set-cookie'), /Max-Age=0/);
});
