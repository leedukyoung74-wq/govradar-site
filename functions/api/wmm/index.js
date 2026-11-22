import { verify, json } from "../../_lib/common.js";
// /api/wmm?resource=grants|community|session|projects|ledger  (WMM start app)
async function grants() {
  const cache = caches.default, ck = new Request("https://cache.wmm/grants");
  const hit = await cache.match(ck);
  if (hit) { const o = await hit.json(); o.cached = true; return o; }
  const src = "https://mss.go.kr/rss/smba/board/310.do";
  const r = await fetch(src, { headers: { "user-agent": "WMM-www/1.0 (73036396@naver.com)" } });
  const xml = await r.text();
  const pick = (s, t) => { const m = s.match(new RegExp("<" + t + ">(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?</" + t + ">")); return m ? m[1].trim() : ""; };
  const REG = "서울 경기 인천 강원 충북 충남 세종 대전 전북 전남 광주 경북 대구 경남 울산 부산 제주".split(" ");
  const items = (xml.match(/<item>[\s\S]*?<\/item>/g) || []).slice(0, 40).map((it) => {
    const title = pick(it, "title"), d = new Date(pick(it, "pubDate"));
    const ts = isNaN(d) ? "" : new Date(d.getTime() + 9 * 3600e3).toISOString().replace(/[-:T]/g, "").slice(0, 14);
    return { title, url: pick(it, "link"), summary: "", publishedAt: ts, regions: REG.filter((x) => title.includes(x)), deadline: "원문에서 확인", source: "중소벤처기업부" };
  });
  const out = { items, checkedAt: new Date().toISOString(), source: src, coverage: "중소벤처기업부 사업공고 RSS. 모든 지원금이 포함되지는 않아요.", stale: false, cached: false };
  if (items.length) await cache.put(ck, new Response(JSON.stringify(out), { headers: { "cache-control": "max-age=3600" } }));
  return out;
}
export const onRequest = async ({ request, env }) => {
  const res = new URL(request.url).searchParams.get("resource") || "";
  const user = await verify(request);
  if (res === "session") return json({ signedIn: !!user, aiConnected: false });
  if (res === "grants") { try { return json(await grants()); } catch { return json({ items: [], checkedAt: new Date().toISOString(), stale: true, error: "source_unavailable" }); } }
  if (res === "community" && request.method === "GET") {
    const list = env.WMM_KV ? JSON.parse((await env.WMM_KV.get("community")) || "[]") : [];
    return json({ items: list, checkedAt: new Date().toISOString() });
  }
  if (!user) return json({ error: "내 기록을 보려면 먼저 로그인해 주세요." }, 401);
  if (!env.WMM_KV) return json({ error: "저장 기능을 옮기는 중입니다. 잠시 뒤 다시 이용해 주세요." }, 503);
  const key = res + ":" + user.sub;
  if (res === "projects" || res === "ledger") {
    if (request.method === "GET") return json({ items: JSON.parse((await env.WMM_KV.get(key)) || "[]") });
    const body = await request.json().catch(() => null);
    if (!body || typeof body !== "object") return json({ error: "invalid_body" }, 400);
    const list = JSON.parse((await env.WMM_KV.get(key)) || "[]");
    list.unshift({ ...body, id: crypto.randomUUID(), createdAt: new Date().toISOString() });
    await env.WMM_KV.put(key, JSON.stringify(list.slice(0, 200)));
    return json({ ok: true, items: list.slice(0, 200) });
  }
  if (res === "community" && request.method === "POST") {
    const body = await request.json().catch(() => null);
    if (!body || typeof body !== "object") return json({ error: "invalid_body" }, 400);
    const list = JSON.parse((await env.WMM_KV.get("community")) || "[]");
    list.unshift({ ...body, uid: user.sub, id: crypto.randomUUID(), createdAt: new Date().toISOString() });
    await env.WMM_KV.put("community", JSON.stringify(list.slice(0, 300)));
    return json({ ok: true });
  }
  return json({ error: "unknown_resource" }, 400);
};
