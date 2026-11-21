import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createMembershipGate } from '../functions/membership.js';
import { renderAccess } from '../functions/access-view.js';

const main = 'https://radar.wmm-hoa.com';
const identity = 'https://wmm-govradar.netlify.app/.netlify/identity/user';
const token = 'mock-auth.token.value';
const cookie = `__Host-govradar-member=${token}`;

function mockProvider({ confirmed = true, outage = false, status } = {}) {
  const calls = [];
  const gate = createMembershipGate(async (url, options) => {
    calls.push({ url, options });
    if (outage) throw new Error('outage');
    if (status) return new Response(null, { status });
    return options.headers.authorization === `Bearer ${token}`
      ? Response.json({ id: 'mock-user', confirmed_at: confirmed ? '2026-01-01T00:00:00Z' : null })
      : new Response(null, { status: 401 });
  });
  return { gate, calls };
}

function context(path, options = {}, origin = main) {
  let calls = 0;
  return {
    request: new Request(origin + path, options),
    next: async () => {
      calls++;
      return new Response('upstream payload', { headers: { 'cache-control': 'public, max-age=999' } });
    },
    get calls() { return calls; },
  };
}

test('all Pages requests run middleware, with no static route exclusions', async () => {
  const routing = JSON.parse(await readFile(new URL('../public/_routes.json', import.meta.url), 'utf8'));
  assert.deepEqual(routing, { version: 1, include: ['/*'], exclude: [] });
});

test('explicitly public rotating intro, welcome, and auth-only destinations pass through', async () => {
  const { gate, calls } = mockProvider();
  for (const path of ['/intro/?replay=1', '/intro/gov-radar-intro.mp4', '/intro/poster.jpg', '/welcome/', '/welcome/en/', '/access/ko/', '/access/en/', '/ko/legal/privacy/']) {
    const ctx = context(path);
    assert.equal((await gate(ctx)).status, 200, path);
    assert.equal(ctx.calls, 1, path);
  }
  assert.equal(calls.length, 0);
});

test('existing login and signup links reach independent access pages', async () => {
  const { gate } = mockProvider();
  for (const [path, route] of [['/welcome/login/', '/access/ko/'], ['/welcome/en/login/', '/access/en/'], ['/en/?auth=signup', '/access/en/?mode=signup'], ['/ko/?auth=reset', '/access/ko/?mode=reset']]) {
    const ctx = context(path);
    const response = await gate(ctx);
    assert.equal(response.status, 303);
    assert.equal(response.headers.get('location'), route);
    assert.equal(ctx.calls, 0);
  }
});

test('public root serves only the intro handoff and preserves supported identity callbacks', async () => {
  const { gate } = mockProvider();
  const ctx = context('/', { headers: { 'accept-language': 'en-US' } });
  const response = await gate(ctx);
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /intro\/\?to=%2Fwelcome%2Fen%2F&amp;replay=1/);
  assert.match(html, /\/access\/entry\.js/);
  assert.equal(ctx.calls, 0);
});

test('signed-out direct dashboard visits and HTML file routes redirect before loading content', async () => {
  const { gate } = mockProvider();
  for (const [path, lang] of [['/ko/south-korea/', 'ko'], ['/en/south-korea/index.html', 'en'], ['/fr/', 'fr']]) {
    const ctx = context(path, { method: 'HEAD' });
    const response = await gate(ctx);
    assert.equal(response.status, 303, path);
    assert.equal(response.headers.get('location'), `/access/${lang}/`);
    assert.match(response.headers.get('cache-control'), /no-store/);
    assert.equal(ctx.calls, 0);
  }
});

test('data, static payloads, feeds and API requests require a member without a content response', async () => {
  const { gate } = mockProvider();
  for (const path of ['/data/countries.json', '/data/regions.json', '/feeds/en/all.xml', '/assets/country-payload.js', '/api/req', '/mkey']) {
    const ctx = context(path);
    const response = await gate(ctx);
    assert.equal(response.status, 401, path);
    assert.deepEqual(await response.json(), { error: 'membership_required' });
    assert.equal(ctx.calls, 0);
  }
});

test('private source assets are never served to browser sessions', async () => {
  const { gate, calls } = mockProvider();
  const ctx = context('/private/m/en/KR.json', { headers: { cookie } });
  assert.equal((await gate(ctx)).status, 404);
  assert.equal(calls.length, 0);
  assert.equal(ctx.calls, 0);
});

test('public signup HTML contains no dashboard content and covers signup requirements', async () => {
  for (const language of ['ko', 'en']) {
    const response = renderAccess(new Request(`${main}/access/${language}/?mode=signup`), language);
    const html = await response.text();
    assert.equal(response.status, 200);
    assert.match(html, /name="terms" type="checkbox" required/);
    assert.match(html, /name="age" required/);
    assert.match(html, /src="\/access\/member\.js"/);
    assert.match(html, /data-mode="signup"/);
    assert.doesNotMatch(html, /data\/countries\.json|stay=1/);
    assert.match(response.headers.get('cache-control'), /no-store/);
  }
});

test('Pages aliases redirect to the canonical HTTPS origin without serving content', async () => {
  const { gate } = mockProvider();
  for (const origin of ['https://wmm-radar.pages.dev', 'https://branch.wmm-radar.pages.dev', 'http://radar.wmm-hoa.com']) {
    const ctx = context('/ko/south-korea/?lang=ko', {}, origin);
    const response = await gate(ctx);
    assert.equal(response.status, 308);
    assert.equal(response.headers.get('location'), main + '/ko/south-korea/?lang=ko');
    assert.equal(ctx.calls, 0);
    for (const route of ['/gate/session', '/gate/logout']) {
      const post = context(route, { method: 'POST', headers: { origin: main } }, origin);
      assert.equal((await gate(post)).status, 421);
      assert.equal(post.calls, 0);
    }
  }
});

test('expired browser cookie remains blocked and a fresh verified identity can replace it', async () => {
  const { gate, calls } = mockProvider();
  const expired = '__Host-govradar-member=expired.mock.token';
  const denied = context('/ko/', { headers: { cookie: expired } });
  const response = await gate(denied);
  assert.equal(response.status, 303);
  assert.equal(denied.calls, 0);
  const expiredGrant = context('/gate/session', { method: 'POST', headers: { origin: main, cookie: expired, authorization: 'Bearer expired.mock.token' } });
  const expiredResponse = await gate(expiredGrant);
  assert.equal(expiredResponse.status, 401);
  assert.equal(expiredResponse.headers.get('set-cookie'), null);
  const freshGrant = context('/gate/session', { method: 'POST', headers: { origin: main, cookie: expired, authorization: `Bearer ${token}` } });
  const freshResponse = await gate(freshGrant);
  assert.equal(freshResponse.status, 204);
  assert.ok(freshResponse.headers.get('set-cookie').startsWith(`${cookie};`));
  assert.equal(calls.length, 3);
});

test('public access scripts serve without a session and never use shared caching', async () => {
  const { gate, calls } = mockProvider();
  for (const path of ['/access/member.js', '/access/entry.js']) {
    const ctx = context(path);
    const response = await gate(ctx);
    assert.equal(response.status, 200);
    assert.match(response.headers.get('cache-control'), /private, no-store/);
    assert.equal(ctx.calls, 1);
  }
  assert.equal(calls.length, 0);
});

test('issue cookie only for same-origin verified confirmed members, with safe attributes', async () => {
  const { gate, calls } = mockProvider();
  for (const origin of [undefined, 'https://outside.example']) {
    const headers = { authorization: `Bearer ${token}`, ...(origin ? { origin } : {}) };
    const denied = await gate(context('/gate/session', { method: 'POST', headers }));
    assert.equal(denied.status, 403);
    assert.equal(denied.headers.get('set-cookie'), null);
  }
  assert.equal(calls.length, 0);
  const response = await gate(context('/gate/session', { method: 'POST', headers: { origin: main, authorization: `Bearer ${token}` } }));
  assert.equal(response.status, 204);
  assert.equal(response.headers.get('set-cookie'), `${cookie}; Max-Age=3600; Path=/; Secure; HttpOnly; SameSite=Lax`);
  assert.equal(calls[0].url, identity);
  assert.equal(calls[0].options.redirect, 'error');
});

test('verified members reach Cloudflare content with uncacheable response', async () => {
  const { gate, calls } = mockProvider();
  const ctx = context('/data/countries.json', { headers: { cookie } });
  const response = await gate(ctx);
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'upstream payload');
  assert.match(response.headers.get('cache-control'), /private, no-store/);
  assert.equal(calls.length, 1);
  assert.equal(ctx.calls, 1);
});

test('provider rejection, unconfirmed email, and outage keep protected content closed', async () => {
  for (const [options, status] of [[{ confirmed: false }, 401], [{ outage: true }, 503], [{ status: 403 }, 401], [{ status: 429 }, 503]]) {
    const { gate } = mockProvider(options);
    const ctx = context('/data/countries.json', { headers: { cookie } });
    assert.equal((await gate(ctx)).status, status);
    assert.equal(ctx.calls, 0);
  }
});

test('logout clears only the host-only cookie after a same-origin POST', async () => {
  const { gate, calls } = mockProvider();
  const denied = await gate(context('/gate/logout', { method: 'POST', headers: { origin: 'https://outside.example' } }));
  assert.equal(denied.status, 403);
  const response = await gate(context('/gate/logout', { method: 'POST', headers: { origin: main, cookie } }));
  assert.equal(response.status, 204);
  assert.equal(response.headers.get('set-cookie'), '__Host-govradar-member=; Max-Age=0; Path=/; Secure; HttpOnly; SameSite=Lax');
  assert.equal(calls.length, 0);
});

test('Identity browser endpoints are explicitly allowed, provider administration is denied', async () => {
  const { gate } = mockProvider();
  const publicRoute = context('/nfid/signup', { method: 'POST' });
  assert.equal((await gate(publicRoute)).status, 200);
  assert.equal(publicRoute.calls, 1);
  const privateRoute = context('/nfid/admin/users');
  assert.equal((await gate(privateRoute)).status, 404);
  assert.equal(privateRoute.calls, 0);
});
