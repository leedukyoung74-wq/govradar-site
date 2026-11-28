const defaultCanonical = 'https://radar.wmm-hoa.com';
const identityUser = 'https://wmm-govradar.netlify.app/.netlify/identity/user';
const cookieName = '__Host-govradar-member';
const cookieFlags = 'Path=/; Secure; HttpOnly; SameSite=Lax';
const tokenFormat = /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/;
const languages = '(?:ko|en|es|fr|ar|vi|id)';
const siteLanguage = new RegExp(`^/(${languages})(?:/|$)`);
const legal = new RegExp(`^/${languages}/legal/(?:terms|privacy|refund|disclaimer)/$`);
const welcome = new RegExp(`^/welcome/(?:${languages}/)?(?:about/|services/|membership/|country/)?$`);
const welcomeLogin = new RegExp(`^/welcome/(?:(${languages})/)?login/$`);
const access = new RegExp(`^/access/${languages}/$`);
const publicAccessScripts = new Set(['/access/member.js', '/access/entry.js']);
const introAndBrand = new Set([
  '/intro/', '/intro/gov-radar-intro.mp4', '/intro/poster.jpg',
  '/assets/mark.png', '/assets/logo-h.webp', '/assets/logo-h-lg.webp', '/assets/site.css',
  '/assets/og-govradar.jpg', '/assets/c-sa.webp', '/assets/wmm-logo-white.png', '/assets/wmm-logo.png',
  '/assets/gcsme-logo.jpg', '/assets/gcsme-club.webp', '/assets/og.jpg', '/robots.txt',
  '/assets/fonts/NEXONLv1GothicOTFLight.woff', '/assets/fonts/NEXONLv1GothicOTF.woff',
  '/assets/fonts/NEXONLv1GothicOTFBold.woff',
]);
const browserIdentityMethods = {
  authorize: ['GET'], callback: ['GET', 'POST'], settings: ['GET'],
  token: ['POST'], signup: ['POST'], verify: ['POST'], recover: ['POST'], logout: ['POST'],
  user: ['GET', 'PUT'],
};

function privateHeaders(input) {
  const headers = new Headers(input);
  headers.set('cache-control', 'private, no-store');
  headers.set('cdn-cache-control', 'no-store');
  headers.set('cloudflare-cdn-cache-control', 'no-store');
  return headers;
}

function reply(status, error, extra) {
  const headers = privateHeaders(extra);
  if (!error) return new Response(null, { status, headers });
  headers.set('content-type', 'application/json; charset=utf-8');
  return new Response(JSON.stringify({ error }), { status, headers });
}

function redirectTo(path, status = 303) {
  return reply(status, null, { location: path });
}

function secureCookie(token, seconds) {
  return `${cookieName}=${token}; Max-Age=${seconds}; ${cookieFlags}`;
}

function acceptedToken(value) {
  return value?.length <= 3600 && tokenFormat.test(value) ? value : null;
}

function cookieToken(headers) {
  const values = (headers.get('cookie') || '').split(';')
    .map(part => part.trim())
    .filter(part => part.startsWith(`${cookieName}=`));
  return values.length === 1 ? acceptedToken(values[0].slice(cookieName.length + 1)) : null;
}

function languageFor(request, url) {
  const explicit = siteLanguage.exec(url.pathname)?.[1];
  if (explicit) return explicit;
  const browser = (request.headers.get('accept-language') || '').toLowerCase();
  return new RegExp(`^(${languages})(?:[-,;]|$)`).exec(browser)?.[1] || 'ko';
}

function isHtml(path, request) {
  return (request.headers.get('accept') || '').includes('text/html') ||
    (/^\/(?:ko|en|es|fr|ar|vi|id)(?:\/|$)/.test(path) && (
      path.endsWith('.html') || !/\.[a-z0-9]+$/i.test(path)
    ));
}

function requestedMode(url) {
  const mode = url.searchParams.get('auth');
  return mode === 'signup' || mode === 'reset' ? `?mode=${mode}` : '';
}

export function createMembershipGate(fetchUser = fetch, canonical = defaultCanonical) {
  async function verify(token) {
    if (!token) return 401;
    try {
      const current = await fetchUser(identityUser, {
        headers: { authorization: `Bearer ${token}` },
        redirect: 'error',
        signal: AbortSignal.timeout(4000),
      });
      if ([400, 401, 403, 404].includes(current.status)) return 401;
      if (!current.ok) return 503;
      const user = await current.json();
      const confirmed = user?.confirmed_at || user?.confirmedAt;
      return typeof user?.id === 'string' && user.id && typeof confirmed === 'string' &&
        Number.isFinite(Date.parse(confirmed)) ? 200 : 401;
    } catch {
      return 503;
    }
  }

  return async function gate(context) {
    const { request } = context;
    const url = new URL(request.url);
    const path = url.pathname;
    const read = request.method === 'GET' || request.method === 'HEAD';
    if (url.origin !== canonical) {
      return read ? redirectTo(canonical + path + url.search, 308) : reply(421, 'wrong_host');
    }
    if (/(?:^|\/)private(?:\/|$)/i.test(path)) return reply(404, 'not_found');

    if (path === '/gate/session' || path === '/gate/logout') {
      if (request.method !== 'POST') return reply(405, 'method_not_allowed', { allow: 'POST' });
      if (request.headers.get('origin') !== canonical) return reply(403, 'invalid_origin');
      if (path === '/gate/logout') return reply(204, null, { 'set-cookie': secureCookie('', 0) });
      const token = acceptedToken(/^Bearer ([^ ]+)$/i.exec(request.headers.get('authorization') || '')?.[1]);
      const status = await verify(token);
      if (status !== 200) return reply(status, status === 401 ? 'membership_required' : 'identity_unavailable');
      return reply(204, null, { 'set-cookie': secureCookie(token, 3600) });
    }

    const idPath = /^\/(?:\.netlify\/identity|nfid)\/([^/]+)\/?$/.exec(path);
    if (path.startsWith('/.netlify/') || path.startsWith('/nfid/')) {
      if (!idPath || !Object.hasOwn(browserIdentityMethods, idPath[1]) ||
          !browserIdentityMethods[idPath[1]].includes(request.method)) return reply(404, 'not_found');
      return context.next();
    }

    const login = welcomeLogin.exec(path);
    if (read && login) return redirectTo(`/access/${login[1] || 'ko'}/${requestedMode(url)}`);
    if (read && publicAccessScripts.has(path)) {
      const response = await context.next();
      return new Response(response.body, { status: response.status, headers: privateHeaders(response.headers) });
    }
    if (read && (introAndBrand.has(path) || welcome.test(path) || legal.test(path) || access.test(path))) {
      return context.next();
    }

    const status = await verify(cookieToken(request.headers));
    if (status === 503) return reply(503, 'identity_unavailable');
    if (status === 200) {
      const response = await context.next();
      return new Response(response.body, { status: response.status, headers: privateHeaders(response.headers) });
    }

    const language = languageFor(request, url);
    if (read && (path === '/' || path === '/index.html')) {
      const welcomePath = `/welcome/${language === 'ko' ? '' : language + '/'}`;
      const intro = `/intro/?to=${encodeURIComponent(welcomePath)}&amp;replay=1`;
      const html = `<!doctype html><html lang="${language}"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GOV RADAR</title><a id="intro" href="${intro}">GOV RADAR</a><script src="/access/entry.js" defer></script>`;
      const headers = privateHeaders({ 'content-type': 'text/html; charset=utf-8', 'referrer-policy': 'no-referrer', 'content-security-policy': "default-src 'none'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'" });
      return new Response(request.method === 'HEAD' ? null : html, { headers });
    }
    if (read && isHtml(path, request)) return redirectTo(`/access/${language}/${requestedMode(url)}`);
    return reply(401, 'membership_required');
  };
}
