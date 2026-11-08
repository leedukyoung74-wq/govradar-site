// Cloudflare Pages Function: POST /api/ask  — members only (non-members can only read the site).
// Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, ANTHROPIC_API_KEY, ASK_DAILY_LIMIT (e.g. "20"), ASK_MODEL (e.g. "claude-sonnet-5-5")
export async function onRequestPost({ request, env }) {
  const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json" } });
  const token = (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  if (!token) return json({ error: "sign-in required" }, 401);
  const u = await fetch(`${env.SUPABASE_URL}/auth/v1/user`, { headers: { apikey: env.SUPABASE_SERVICE_KEY, authorization: `Bearer ${token}` } });
  if (!u.ok) return json({ error: "sign-in required" }, 401);
  const user = await u.json();
  const { iso, q, lang } = await request.json().catch(() => ({}));
  if (!q || String(q).length > 1000) return json({ error: "question missing or too long" }, 400);
  // daily limit per member
  const sb = (path, init = {}) => fetch(`${env.SUPABASE_URL}/rest/v1/${path}`, { ...init, headers: { apikey: env.SUPABASE_SERVICE_KEY, authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`, "content-type": "application/json", prefer: "return=representation,resolution=merge-duplicates", ...(init.headers || {}) } });
  const day = new Date().toISOString().slice(0, 10);
  const cur = await (await sb(`ask_usage?user_id=eq.${user.id}&day=eq.${day}&select=n`)).json();
  const n = (cur[0] && cur[0].n) || 0, limit = parseInt(env.ASK_DAILY_LIMIT || "20", 10);
  if (n >= limit) return json({ error: lang === "ko" ? "오늘 질문 한도를 다 썼습니다." : "Daily question limit reached." }, 429);
  await sb("ask_usage", { method: "POST", body: JSON.stringify({ user_id: user.id, day, n: n + 1 }) });
  // country context from the static site
  const origin = new URL(request.url).origin;
  let ctx = "";
  if (/^[A-Z]{2}$/.test(iso || "")) { const r = await fetch(`${origin}/data/c/${iso}.json`); if (r.ok) ctx = (await r.text()).slice(0, 40000); }
  const sys = `You are the GOV RADAR analyst (WORLD MAKING MEMBERS × GCSME). Answer only from the radar data given; say so when it is missing. Be concrete about programmes, buyers, tenders, ODA and risk for a Korean SME. Under 250 words. Reply in ${lang === "ko" ? "Korean" : "the user's language"}. Not investment or legal advice.`;
  const r = await fetch("https://api.anthropic.com/v1/messages", { method: "POST", headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model: env.ASK_MODEL || "claude-sonnet-5-5", max_tokens: 900, system: sys, messages: [{ role: "user", content: `RADAR DATA (${iso || "none"}):\n${ctx}\n\nQUESTION: ${q}` }] }) });
  if (!r.ok) return json({ error: "AI unavailable" }, 502);
  const out = await r.json();
  return json({ answer: (out.content || []).map(c => c.text || "").join("") });
}
