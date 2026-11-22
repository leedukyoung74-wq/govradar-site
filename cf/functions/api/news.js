// 실시간 뉴스 제목 모음 (2026-11-23 대표 요청) — 구글 뉴스 RSS 검색 결과(제목·언론사·시각·링크)만, 15분 캐시
// GET /api/news?t=war|cyber|disaster|epidemic|prep&l=ko   또는   /api/news?c=VN&l=ko
import { NAMES } from "./_names.js";
const LANGS = ["ko", "en", "es", "fr", "ar", "vi", "id"];
const ED = { ko: "hl=ko&gl=KR&ceid=KR:ko", en: "hl=en-US&gl=US&ceid=US:en", es: "hl=es&gl=ES&ceid=ES:es", fr: "hl=fr&gl=FR&ceid=FR:fr", ar: "hl=ar&gl=AE&ceid=AE:ar", vi: "hl=vi&gl=VN&ceid=VN:vi", id: "hl=id&gl=ID&ceid=ID:id" };
const Q = {
  war: { ko: "전쟁 OR 공습 OR 휴전 OR 무력충돌", en: "war OR airstrike OR ceasefire OR \"armed conflict\"", es: "guerra OR bombardeo OR \"alto el fuego\"", fr: "guerre OR frappes OR \"cessez-le-feu\"", ar: "حرب OR غارة OR \"وقف إطلاق النار\"", vi: "chiến tranh OR không kích OR \"ngừng bắn\"", id: "perang OR serangan udara OR gencatan senjata" },
  cyber: { ko: "사이버 공격 OR 해킹 OR 랜섬웨어 OR \"개인정보 유출\"", en: "cyberattack OR ransomware OR \"data breach\" OR hackers", es: "ciberataque OR ransomware OR hackeo", fr: "cyberattaque OR rançongiciel OR piratage", ar: "هجوم سيبراني OR اختراق OR فدية", vi: "\"tấn công mạng\" OR ransomware OR \"tin tặc\"", id: "\"serangan siber\" OR ransomware OR peretasan" },
  disaster: { ko: "지진 OR 태풍 OR 홍수 OR 산불 OR 화산", en: "earthquake OR typhoon OR hurricane OR flood OR wildfire OR volcano", es: "terremoto OR huracán OR inundación OR incendio forestal", fr: "séisme OR typhon OR inondation OR incendie", ar: "زلزال OR إعصار OR فيضان", vi: "\"động đất\" OR bão OR lũ lụt", id: "gempa OR banjir OR topan OR kebakaran hutan" },
  epidemic: { ko: "감염병 OR 전염병 OR 집단감염 OR 질병관리청 OR WHO", en: "outbreak OR epidemic OR WHO OR virus cases", es: "brote OR epidemia OR OMS", fr: "épidémie OR OMS OR flambée", ar: "تفشي OR وباء OR منظمة الصحة العالمية", vi: "\"dịch bệnh\" OR \"bùng phát\" OR WHO", id: "wabah OR epidemi OR WHO" },
  prep: { ko: "비상 대비 권고 OR 비상용품 OR \"72시간\" OR 대피 요령 OR 민방위 OR 재난문자", en: "\"emergency kit\" OR \"72 hours\" OR \"urges residents\" OR \"prepare for\" government advice", es: "\"kit de emergencia\" OR \"72 horas\" OR \"recomienda a la población\"", fr: "\"kit d'urgence\" OR \"72 heures\" OR \"se préparer\" gouvernement", ar: "\"حقيبة الطوارئ\" OR \"72 ساعة\" OR الاستعداد", vi: "\"72 giờ\" OR \"chuẩn bị\" khẩn cấp chính phủ", id: "\"72 jam\" OR \"tas siaga\" OR siaga bencana pemerintah" },
};
const dec = s => s.replace(/<!\[CDATA\[|\]\]>/g, "").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").trim();
const J = (o, ttl) => new Response(JSON.stringify(o), { headers: { "content-type": "application/json; charset=utf-8", "cache-control": `public, max-age=${ttl || 300}` } });
export async function onRequestGet(ctx) {
  const u = new URL(ctx.request.url), l = LANGS.includes(u.searchParams.get("l")) ? u.searchParams.get("l") : "en";
  const t = u.searchParams.get("t"), c = (u.searchParams.get("c") || "").toUpperCase();
  let q;
  if (c && NAMES[c]) q = `"${NAMES[c][LANGS.indexOf(l)] || NAMES[c][1]}" when:3d`;
  else if (Q[t]) q = `(${Q[t][l] || Q[t].en}) when:2d`;
  else return J({ error: "bad topic" }, 60);
  const key = new Request(`https://radar.wmm-hoa.com/api/news?k=${encodeURIComponent(l + "|" + (c || t))}&v=1`), cache = caches.default;
  const hit = await cache.match(key); if (hit) return hit;
  let items = [], src = "Google News";
  const parse = (x, bing) => {
    const out = [], seen = new Set();
    for (const m of x.matchAll(/<item>([\s\S]*?)<\/item>/g)) {
      const it = m[1], g = k => { const mm = it.match(new RegExp(`<${k}[^>]*>([\\s\\S]*?)</${k}>`)); return mm ? dec(mm[1]) : ""; };
      const s = g(bing ? "News:Source" : "source"); let title = g("title"); if (s && title.endsWith(" - " + s)) title = title.slice(0, -(s.length + 3));
      let link = g("link"); if (bing) { try { link = new URL(link).searchParams.get("url") || link; } catch (e) {} }
      const k2 = title.slice(0, 40); if (!title || seen.has(k2)) continue; seen.add(k2);
      out.push({ t: title, s, u: link, d: Date.parse(g("pubDate")) || 0 });
    }
    return out;
  };
  const UA = { "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "accept-language": l };
  try { const r = await fetch(`https://news.google.com/rss/search?q=${encodeURIComponent(q)}&${ED[l]}`, { headers: UA }); if (r.ok) items = parse(await r.text(), false); } catch (e) {}
  if (!items.length) {
    const MK = { ko: "ko-KR", en: "en-US", es: "es-ES", fr: "fr-FR", ar: "ar-XA", vi: "vi-VN", id: "id-ID" };
    const bq = q.replace(/\s*when:\d+d/, "");
    try { const r = await fetch(`https://www.bing.com/news/search?q=${encodeURIComponent(bq)}&format=rss&sortbydate=1&setlang=${l}&mkt=${MK[l]}`, { headers: UA }); if (r.ok) { items = parse(await r.text(), true); src = "Bing News"; } } catch (e) {}
  }
  const cut = Date.now() - (c ? 7 : 3) * 864e5;
  items = items.filter(x => !x.d || x.d > cut).sort((a, b) => b.d - a.d).slice(0, 25);
  const res = J({ at: new Date().toISOString(), items, ok: items.length > 0, src }, items.length ? 900 : 120);
  if (items.length) ctx.waitUntil(cache.put(key, res.clone()));
  return res;
}
