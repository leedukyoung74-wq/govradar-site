import { createMembershipGate } from './membership.js';
import { renderAccess } from './access-view.js';

const identityOrigin = 'https://wmm-govradar.netlify.app';
const productionOrigin = 'https://radar.wmm-hoa.com';

async function proxyIdentity(request, canonical) {
  const source = new URL(request.url);
  const endpoint = source.pathname.replace(/^\/nfid\//, '/.netlify/identity/');
  const headers = new Headers(request.headers);
  for (const key of ['host', 'cf-connecting-ip', 'cf-ipcountry', 'cf-ray', 'cf-visitor', 'x-forwarded-proto', 'x-real-ip']) {
    headers.delete(key);
  }
  const cookies = headers.get('cookie')?.split(';').filter(part => !part.trim().startsWith('__Host-govradar-member='));
  if (cookies?.some(part => part.trim())) headers.set('cookie', cookies.join(';'));
  else headers.delete('cookie');
  const options = { method: request.method, headers, redirect: 'manual' };
  if (request.method !== 'GET' && request.method !== 'HEAD') options.body = await request.arrayBuffer();
  try {
    const response = await fetch(identityOrigin + endpoint + source.search, options);
    const outgoing = new Headers(response.headers);
    outgoing.delete('access-control-allow-origin');
    outgoing.delete('access-control-allow-credentials');
    outgoing.set('cache-control', 'no-store');
    const location = outgoing.get('location');
    if (location) {
      const target = new URL(location, identityOrigin);
      if (target.origin === identityOrigin) outgoing.set('location', canonical + target.pathname + target.search + target.hash);
    }
    return new Response(response.body, { status: response.status, headers: outgoing });
  } catch {
    return Response.json({ error: 'identity_unavailable' }, { status: 503, headers: { 'cache-control': 'no-store' } });
  }
}

export async function onRequest(context) {
  const canonical = context.env.GOV_RADAR_CANONICAL_ORIGIN || productionOrigin;
  const path = new URL(context.request.url).pathname;
  const providerPath = path.startsWith('/.netlify/identity/') || path.startsWith('/nfid/');
  const access = /^\/access\/(ko|en|es|fr|ar|vi|id)\/$/.exec(path);
  return createMembershipGate(fetch, canonical)({
    request: context.request,
    next: () => {
      if (providerPath) return proxyIdentity(context.request, canonical);
      if (access) return renderAccess(context.request, access[1]);
      return context.next();
    },
  });
}
