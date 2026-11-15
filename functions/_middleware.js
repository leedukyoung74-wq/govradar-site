// 구글 로그인 등 Netlify Identity 외부 로그인의 되돌아오는 경로(/.netlify/identity/*)를 Netlify로 전달
const ORIGIN = "https://wmm-govradar.netlify.app";
export async function onRequest(ctx) {
  const u = new URL(ctx.request.url);
  if (!u.pathname.startsWith("/.netlify/identity/")) return ctx.next();
  const h = new Headers(ctx.request.headers);
  ["host", "cf-connecting-ip", "cf-ipcountry", "cf-ray", "cf-visitor", "x-forwarded-proto", "x-real-ip"].forEach(k => h.delete(k));
  const hasBody = !["GET", "HEAD"].includes(ctx.request.method);
  const r = await fetch(ORIGIN + u.pathname + u.search, { method: ctx.request.method, headers: h, body: hasBody ? await ctx.request.arrayBuffer() : undefined, redirect: "manual" });
  const out = new Headers(r.headers);
  const loc = out.get("location");
  if (loc) out.set("location", loc.replace("https://wmm-govradar.netlify.app", "https://radar.wmm-hoa.com"));
  return new Response(r.body, { status: r.status, headers: out });
}
