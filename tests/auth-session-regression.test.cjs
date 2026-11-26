// Regression tests for Cloudflare Pages + Netlify Identity session handling.
// Run: node --test tests/auth-session-regression.test.cjs
'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const locations = [
  path.join(__dirname, '..', 'public', 'assets', 'auth.js'),
  path.join(__dirname, '..', 'web', 'auth.js')
];
const file = locations.find(p => fs.existsSync(p));
if (!file) throw new Error('Cannot find auth implementation');
const code = fs.readFileSync(file, 'utf8');

function setup(status, hostname = 'radar.wmm-hoa.com') {
  const key = 'wmm.auth.v1';
  const saved = { access_token: 'expired', refresh_token: 'refresh-123',
    expires_at: Date.now() - 60000,
    user: { id: 'user1', email: 'member@example.invalid', app_metadata: { roles: ['m1'] } } };
  const storage = new Map([[key, JSON.stringify(saved)]]);
  const calls = [];
  const user = saved.user;
  const sandbox = {
    window: { RADAR_LANG: 'ko', RADAR_AT: {} },
    document: { querySelector: () => null, addEventListener: () => {},
      documentElement: { dataset: {} } },
    localStorage: { getItem: k => storage.get(k) || null,
      setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k) },
    sessionStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
    location: { hostname, origin: 'https://' + hostname,
      pathname: '/ko/account/', search: '', hash: '' },
    fetch: async (url) => {
      calls.push(url);
      if (url.endsWith('/token')) return {
        ok: status === 200, status,
        text: async () => JSON.stringify(status === 200
          ? { access_token: 'fresh', refresh_token: 'refresh-456', expires_in: 3600 }
          : { msg: status === 503 ? 'temporarily unavailable' : 'invalid_grant' })
      };
      if (url.endsWith('/user')) return { ok: true, status: 200,
        text: async () => JSON.stringify(user) };
      throw new Error('Unexpected endpoint ' + url);
    },
    Date, URL, URLSearchParams, setTimeout: () => 0,
    history: { replaceState: () => {} }
  };
  vm.runInNewContext(code, sandbox, { filename: file });
  return { auth: sandbox.window.WMMAuth, storage, calls, key };
}

test('transient Netlify 503 retains refresh credentials but refuses membership', async () => {
  const s = setup(503);
  assert.equal(await s.auth.token(), null);
  assert.notEqual(s.storage.get(s.key), undefined);
  assert.equal(s.auth.tier(), null);
  assert.equal(s.calls.filter(u => u.endsWith('/token')).length, 1);
  assert.ok(s.calls[0].startsWith('/nfid/'));
});
test('explicitly invalid 400 refresh clears the saved session', async () => {
  const s = setup(400);
  assert.equal(await s.auth.token(), null);
  assert.equal(s.storage.has(s.key), false);
});
test('valid refresh validates the identity and restores member tier', async () => {
  const s = setup(200);
  assert.equal(await s.auth.token(), 'fresh');
  assert.equal(s.auth.tier(), 'm1');
  assert.equal(s.calls.length, 2);
});
test('Netlify preview uses the native Identity endpoint', async () => {
  const s = setup(503, 'preview.netlify.app');
  assert.equal(await s.auth.token(), null);
  assert.ok(s.calls[0].startsWith('/.netlify/identity/'));
});
