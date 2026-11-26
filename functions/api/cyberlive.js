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
// CISA KEV is an official *exploited vulnerability catalog*, not a live breach feed.
// Read the independently validated GitHub Actions public snapshot from the data branch
// instead of assuming the Cloudflare edge can always reach cisa.gov (403 is common).
const SNAPSHOT = "https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/hz/cisa_kev.json";
function mapKev(v) {
  const id = String(v.cve || v.cveID || "");
  if (!/^CVE-\d{4}-\d{4,19}$/.test(id)) return null;
  return { d: String(v.date_added || v.dateAdded || "").slice(0, 10), id,
    v: String(v.vendor || v.vendorProject || "").slice(0, 120),
    p: String(v.product || "").slice(0, 130),
    n: String(v.name || v.vulnerabilityName || "").slice(0, 230),
    r: String(v.ransomware_use || v.knownRansomwareCampaignUse || "") === "Known" };
}
async function kev() {
  try {
    const r = await fetch(SNAPSHOT, { headers: { accept: "application/json" } });
    if (!r.ok) throw new Error("snapshot " + r.status);
    const j = await r.json(), h = j && j.source_health;
    if (!j || j.kind !== "known_exploited_vulnerabilities" ||
        !Array.isArray(j.items) || !h || typeof h.ok !== "boolean" ||
        typeof h.stale !== "boolean" || !(j.total_vulnerabilities >= 1000))
      throw new Error("snapshot_schema");
    const last = Date.parse(h.last_ok || "");
    if (!Number.isFinite(last) || last > Date.now() + 600000 ||
        Date.now() - last > 14 * 864e5)
      throw new Error("snapshot_too_old");
    const items = j.items.map(mapKev).filter(Boolean).slice(0, 15);
    if (!items.length) throw new Error("snapshot_no_kevs");
    // Never label 15-minute data as a real-time exploit. Surface source age.
    return { items, source: "validated_official_snapshot", last_ok: new Date(last).toISOString(),
      stale: h.stale || !h.ok || Date.now() - last > 12 * 3600e3 };
  } catch (e) {
    // Last-resort direct official source if the public snapshot is inaccessible.
    const r = await fetch("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
      { headers: { "user-agent": "GOV-RADAR/1.0", accept: "application/json" } });
    if (!r.ok) throw new Error("CISA_KEV_UNAVAILABLE");
    const j = await r.json();
    if (!j || !Array.isArray(j.vulnerabilities) || j.vulnerabilities.length < 1000)
      throw new Error("CISA_KEV_BAD_SCHEMA");
    const items = j.vulnerabilities.sort((a,b)=>
      String(b.dateAdded || "").localeCompare(String(a.dateAdded || "")))
      .map(mapKev).filter(Boolean).slice(0, 15);
    return { items, source: "cisa_official_direct", last_ok: new Date().toISOString(), stale: false };
  }
}
export async function onRequestGet(ctx) {
  const cache = caches.default, key = new Request("https://radar.wmm-hoa.com/api/cyberlive?v=2");
  const hit = await cache.match(key);
  if (hit) return hit;
  const [a,b] = await Promise.allSettled([rw(),kev()]);
  const ready = b.status === "fulfilled" ? b.value : null;
  const body = { at: new Date().toISOString(),
    rw: a.status === "fulfilled" ? a.value : [], kev: ready ? ready.items : [],
    ok: { rw: a.status === "fulfilled", kev: !!ready },
    status: { rw: a.status === "fulfilled" ? "ok" : "unavailable",
      kev: !ready ? "unavailable" : ready.stale ? "delayed" : "ok" },
    kev_last_ok: ready ? ready.last_ok : null, kev_source: ready ? ready.source : null,
    not_realtime_attack_feed: true,
    src: { rw: "https://www.ransomware.live/",
      kev: "https://www.cisa.gov/known-exploited-vulnerabilities-catalog" } };
  const res = new Response(JSON.stringify(body), {
    headers: { "content-type":"application/json; charset=utf-8",
      "cache-control": "public, max-age=" + TTL,
      "access-control-allow-origin":"*" } });
  if (body.ok.rw || body.ok.kev) ctx.waitUntil(cache.put(key,res.clone()));
  return res;
}
