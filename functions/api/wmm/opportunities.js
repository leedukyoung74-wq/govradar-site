import { verify, json } from "../../_lib/common.js";
// 기업마당 live API needs a server key (not yet provided). Without it the page shows its verified snapshot (seed.js), as designed.
export const onRequestGet = async ({ request, env }) => {
  if (!(await verify(request))) return json({ error: "google_login_required" }, 401);
  if (!env.BIZINFO_KEY) return json({ error: "provider_not_configured" }, 503);
  try {
    const u = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do?crtfcKey=" + encodeURIComponent(env.BIZINFO_KEY) + "&dataType=json&searchCnt=180";
    const r = await fetch(u, { cf: { cacheTtl: 21600, cacheEverything: true } });
    const d = await r.json();
    const items = (d.jsonArray || []).map((x) => ({ id: x.pblancId, title: x.pblancNm, url: x.pblancUrl ? (x.pblancUrl.startsWith("http") ? x.pblancUrl : "https://www.bizinfo.go.kr" + x.pblancUrl) : "", org: x.jrsdInsttNm, agency: x.excInsttNm, period: x.reqstBeginEndDe, region: x.hashtags || "", category: x.pldirSportRealmLclasCodeNm || "" }));
    return json({ mode: "live", fetchedAt: new Date().toISOString(), items });
  } catch { return json({ error: "provider_error" }, 502); }
};
