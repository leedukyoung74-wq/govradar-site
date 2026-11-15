// 신청서 접수: Netlify Forms로 전달한 뒤 우리 사이트의 '접수 완료' 페이지로 돌려보냄
export async function onRequestPost({ request }) {
  const u = new URL(request.url);
  let next = u.searchParams.get("next") || "/ko/thanks/";
  if (!next.startsWith("/") || next.startsWith("//")) next = "/ko/thanks/";
  const body = await request.text();
  const r = await fetch("https://wmm-govradar.netlify.app/", {
    method: "POST",
    headers: { "content-type": request.headers.get("content-type") || "application/x-www-form-urlencoded", "user-agent": "GOV RADAR form relay" },
    body, redirect: "manual"
  });
  if (r.status >= 400) return new Response("접수 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요. / Submission failed, please retry.", { status: 502, headers: { "content-type": "text/plain; charset=utf-8" } });
  return Response.redirect(new URL(next, u.origin).toString(), 303);
}
