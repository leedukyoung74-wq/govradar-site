import { json } from "../../_lib/common.js";
// GDELT DOC 2.0 proxy — free, no key. Returns {fetched, articles:[{title,url,domain,seendate}], stale}.
const TOPIC = {
  all: "", conflict: "(war OR conflict OR attack OR military)", food: "(famine OR hunger OR \"food security\")",
  health: "(outbreak OR epidemic OR cholera OR ebola OR health)", geopolitics: "(sanctions OR tariff OR trade OR diplomacy)", business: "(economy OR investment OR business)",
};
export const onRequestGet = async ({ request }) => {
  const q = new URL(request.url).searchParams;
  const country = (q.get("country") || "").replace(/[^\p{L}\p{N} .'-]/gu, "").slice(0, 60);
  const topic = q.get("topic") || "all";
  if (!country || !(topic in TOPIC)) return json({ error: "invalid_filter" }, 400);
  const query = `"${country}"${TOPIC[topic] ? " " + TOPIC[topic] : ""} sourcelang:english`;
  const u = "https://api.gdeltproject.org/api/v2/doc/doc?mode=artlist&format=json&maxrecords=20&sort=datedesc&timespan=24h&query=" + encodeURIComponent(query);
  const cache = caches.default, ck = new Request("https://cache.wmm/news?" + encodeURIComponent(country + "|" + topic));
  try {
    const r = await fetch(u, { headers: { "user-agent": "WMM-www/1.0 (73036396@naver.com)" } });
    if (!r.ok) throw new Error(String(r.status));
    const d = await r.json();
    const out = { fetched: Date.now(), stale: false, articles: (d.articles || []).map((a) => ({ title: a.title, url: a.url, domain: a.domain, seendate: a.seendate })) };
    await cache.put(ck, new Response(JSON.stringify(out), { headers: { "cache-control": "max-age=86400" } }));
    return json(out);
  } catch {
    const c = await cache.match(ck);
    if (c) { const o = await c.json(); o.stale = true; return json(o); }
    return json({ error: "provider_unavailable" }, 502);
  }
};
