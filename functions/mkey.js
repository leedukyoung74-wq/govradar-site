// 로그인한 회원의 등급(Netlify Identity app_metadata.roles)을 서버에서 확인하고, M1 이상이면 회원 분석 열람 키를 돌려준다.
// 키는 Cloudflare 비밀 변수 GV_MASTER 에만 있다(코드·저장소에는 없음).
const IDENTITY = "https://wmm-govradar.netlify.app/.netlify/identity/user";
const OK = ["m1", "m2", "m3", "m4", "m5", "admin", "owner"];
const json = (o, s) => new Response(JSON.stringify(o), { status: s || 200, headers: { "content-type": "application/json", "cache-control": "no-store" } });
export async function onRequestGet({ request, env }) {
  const auth = request.headers.get("authorization") || "";
  if (!/^Bearer\s+\S+/.test(auth)) return json({ error: "login" }, 401);
  const r = await fetch(IDENTITY, { headers: { authorization: auth } });
  if (!r.ok) return json({ error: "login" }, 401);
  const u = await r.json();
  const roles = ((u.app_metadata || {}).roles || []).map(x => String(x).toLowerCase());
  const grade = OK.find(g => roles.includes(g));
  if (!grade) return json({ error: "grade", grade: "m0" }, 403);
  if (!env.GV_MASTER) return json({ error: "not_configured", grade }, 503);
  return json({ k: env.GV_MASTER, grade });
}
