// 사이버 공격 실시간 소식 (2026-11-22 대표 요청) — 10분마다 원 출처에서 새로 받아 캐시
//  1) ransomware.live: 랜섬웨어 조직이 유출 사이트에 올린 피해 주장 (사실 확인 전). 피해 기관 이름·유출 링크·본문은 싣지 않고 나라·업종·조직·날짜만.
//  2) 미국 CISA KEV: 실제 공격에 쓰인 것이 확인된 취약점 (최근 추가분)
import { CENT } from "./_cent.js";
const TTL = 600;
const J = (o, s) => new Response(JSON.stringify(o), { status: s || 200, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=300", "access-control-allow-origin": "*" } });
async function rw() {
  const r = await fetch("https://api.ransomware.live/v2/recentvictims", { headers: { "user-agent": "GOV-RADAR/1.0 (+https://radar.wmm-hoa.com)", accept: "application/json" } });
  if (!r.ok) throw new Error("rw " + r.status);
  const a = await r.json(), since = Date.now() - 7 * 864e5, out = [];
  for (const v of Array.isArray(a) ? a : []) {
    const d = v.discovered || v.attackdate || v.published; const t = Date.parse(d);
    if (!t || t < since) continue;
    const c = String(v.country || "").toUpperCase().slice(0, 2), p = CENT[c];
    out.push({ t, c, s: (String(v.activity || "") === "Not Found" ? "" : String(v.activity || "")).slice(0, 60), g: String(v.group || v.group_name || "").slice(0, 40), la: p ? p[0] : null, lo: p ? p[1] : null });
  }
  out.sort((x, y) => y.t - x.t);
  return out.slice(0, 120);
}
async function kev() {
  const r = await fetch("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json", { headers: { "user-agent": "GOV-RADAR/1.0", accept: "application/json" } });
  if (!r.ok) throw new Error("kev " + r.status);
  const j = await r.json();
  return (j.vulnerabilities || []).sort((a, b) => (b.dateAdded || "").localeCompare(a.dateAdded || "")).slice(0, 15)
    .map(v => ({ d: v.dateAdded, id: v.cveID, v: v.vendorProject, p: v.product, n: v.vulnerabilityName, r: v.knownRansomwareCampaignUse === "Known" }));
}
export async function onRequestGet(ctx) {
  const cache = caches.default, key = new Request("https://radar.wmm-hoa.com/api/cyberlive?v=1");
  const hit = await cache.match(key);
  if (hit) return hit;
  const [a, b] = await Promise.allSettled([rw(), kev()]);
  const body = { at: new Date().toISOString(), rw: a.status === "fulfilled" ? a.value : [], kev: b.status === "fulfilled" ? b.value : [],
    ok: { rw: a.status === "fulfilled", kev: b.status === "fulfilled" },
    src: { rw: "https://www.ransomware.live/", kev: "https://www.cisa.gov/known-exploited-vulnerabilities-catalog" } };
  const res = new Response(JSON.stringify(body), { headers: { "content-type": "application/json; charset=utf-8", "cache-control": `public, max-age=${TTL}`, "access-control-allow-origin": "*" } });
  if (body.ok.rw || body.ok.kev) ctx.waitUntil(cache.put(key, res.clone()));
  return res;
}
