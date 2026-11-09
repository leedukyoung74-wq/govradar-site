// 회원가입·로그인 요청을 Netlify Identity로 그대로 전달 (같은 주소에서 동작하도록)
const ORIGIN = "https://wmm-govradar.netlify.app/.netlify/identity/";
export async function onRequest({ request, params }) {
  const u = new URL(request.url);
  const p = Array.isArray(params.path) ? params.path.join("/") : (params.path || "");
  const h = new Headers(request.headers);
  ["host", "cf-connecting-ip", "cf-ipcountry", "cf-ray", "cf-visitor", "x-forwarded-proto", "x-real-ip"].forEach(k => h.delete(k));
  const hasBody = !["GET", "HEAD"].includes(request.method);
  const r = await fetch(ORIGIN + p + u.search, { method: request.method, headers: h, body: hasBody ? await request.arrayBuffer() : undefined, redirect: "manual" });
  const out = new Headers(r.headers);
  out.delete("access-control-allow-origin");
  return new Response(r.body, { status: r.status, headers: out });
}
