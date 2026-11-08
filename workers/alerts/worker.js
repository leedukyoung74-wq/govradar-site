// Cloudflare Worker (cron) — automatic alerts for members, so Korean tech companies see matching
// tenders, ODA projects and events without visiting the site.
// Triggers: "17 0 * * *" (daily 09:17 KST). Bindings: KV namespace STATE.
// Env: SITE (https://radar.wmm-hoa.com), SUPABASE_URL, SUPABASE_SERVICE_KEY,
//      RESEND_API_KEY, MAIL_FROM ("GOV RADAR <radar@wmm-hoa.com>"),
//      SOLAPI_KEY, SOLAPI_SECRET, KAKAO_PFID, KAKAO_TEMPLATE_ID, SENDER_PHONE  (optional, KakaoTalk AlimTalk)
const IND = { "ai-digital": "AI·디지털", infrastructure: "건설·인프라", energy: "에너지·환경", health: "헬스케어", education: "교육·인재", agrifood: "농업·식품", manufacturing: "제조·산업", fintech: "금융·핀테크" };
const PIND = { ai: "ai-digital", con: "infrastructure", ene: "energy", hea: "health", edu: "education", agr: "agrifood", man: "manufacturing", fin: "fintech" };

export default {
  async scheduled(_e, env, ctx) { ctx.waitUntil(run(env)); },
  async fetch(req, env) { if (new URL(req.url).searchParams.get("key") !== env.RUN_KEY) return new Response("no", { status: 403 }); await run(env); return new Response("ok"); }
};

async function run(env) {
  const sb = (path) => fetch(`${env.SUPABASE_URL}/rest/v1/${path}`, { headers: { apikey: env.SUPABASE_SERVICE_KEY, authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}` } }).then(r => r.json());
  const opps = (await (await fetch(`${env.SITE}/data/opps.json`)).json()).items || [];
  const seen = new Set(JSON.parse((await env.STATE.get("seen")) || "[]"));
  const key = o => `${o.iso}|${o.kind}|${o.ko}`;
  const fresh = opps.filter(o => !seen.has(key(o)));
  const [profiles, follows, watch] = await Promise.all([sb("profiles?select=*"), sb("follows?select=user_id,iso"), sb("watch?select=user_id,iso,title,deadline")]);
  const today = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
  const days = d => Math.round((new Date(d + "T00:00:00") - new Date(today + "T00:00:00")) / 864e5);
  for (const p of profiles) {
    const myIso = new Set(follows.filter(f => f.user_id === p.user_id).map(f => f.iso));
    const myInd = new Set((p.industries || []).map(k => PIND[k] || k));
    const hits = fresh.filter(o => myIso.has(o.iso) || (o.ind || []).some(i => myInd.has(i))).slice(0, 12);
    const due = watch.filter(w => w.user_id === p.user_id && w.deadline && [7, 3].includes(days(w.deadline)));
    if (!hits.length && !due.length) continue;
    const ko = (p.lang || "ko") === "ko";
    const lines = [
      ...due.map(w => `${ko ? "[마감 D-" : "[Deadline D-"}${days(w.deadline)}] ${w.title} (${w.iso})`),
      ...hits.map(o => `[${o.names[ko ? "ko" : "en"] || o.iso}] ${ko ? o.ko : o.en}${o.deadline ? " · " + o.deadline : ""} — ${env.SITE}/${ko ? "ko" : "en"}/${o.slug}/#${o.kind}`)
    ];
    const subject = ko ? `[GOV RADAR] 새 기회 ${hits.length}건${due.length ? ` · 마감 임박 ${due.length}건` : ""}` : `[GOV RADAR] ${hits.length} new opportunities${due.length ? ` · ${due.length} deadlines` : ""}`;
    const footer = ko ? "\n\nWORLD MAKING MEMBERS × GCSME · 73036396@naver.com\n알림 설정은 GOV RADAR 내 정보에서 바꿀 수 있습니다." : "\n\nWORLD MAKING MEMBERS × GCSME · 73036396@naver.com\nChange alerts in your GOV RADAR account.";
    const text = lines.join("\n") + footer;
    if (p.alert_email && p.email && env.RESEND_API_KEY)
      await fetch("https://api.resend.com/emails", { method: "POST", headers: { authorization: `Bearer ${env.RESEND_API_KEY}`, "content-type": "application/json" }, body: JSON.stringify({ from: env.MAIL_FROM, to: [p.email], subject, text }) });
    if (p.slack_webhook && /^https:\/\/hooks\.slack\.com\//.test(p.slack_webhook))
      await fetch(p.slack_webhook, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: `*${subject}*\n${lines.join("\n")}` }) });
    if (p.teams_webhook && /^https:\/\/[\w.-]+\.(webhook\.office\.com|logic\.azure\.com)\//.test(p.teams_webhook))
      await fetch(p.teams_webhook, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: `**${subject}**\n\n${lines.join("\n\n")}` }) });
    if (p.alert_kakao && p.kakao_phone && env.SOLAPI_KEY) await kakao(env, p.kakao_phone, subject, lines.slice(0, 3).join("\n"));
  }
  fresh.forEach(o => seen.add(key(o)));
  await env.STATE.put("seen", JSON.stringify([...seen].slice(-20000)));
}

// KakaoTalk AlimTalk via Solapi (template must be approved by Kakao first).
async function kakao(env, to, title, body) {
  const date = new Date().toISOString(), salt = crypto.randomUUID();
  const sig = await hmac(env.SOLAPI_SECRET, date + salt);
  await fetch("https://api.solapi.com/messages/v4/send", { method: "POST",
    headers: { "content-type": "application/json", authorization: `HMAC-SHA256 apiKey=${env.SOLAPI_KEY}, date=${date}, salt=${salt}, signature=${sig}` },
    body: JSON.stringify({ message: { to, from: env.SENDER_PHONE, kakaoOptions: { pfId: env.KAKAO_PFID, templateId: env.KAKAO_TEMPLATE_ID, variables: { "#{제목}": title, "#{내용}": body.slice(0, 900) } } } }) });
}
async function hmac(secret, msg) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return [...new Uint8Array(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(msg)))].map(b => b.toString(16).padStart(2, "0")).join("");
}
