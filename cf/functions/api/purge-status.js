// Public health check for the retention purge (no personal data): when it last ran and last succeeded.
// A daily GitHub Actions check (.github/workflows/purge-watch.yml) fails — and GitHub emails the owner — if the last
// successful purge is older than 36 hours while the database is connected.
export async function onRequestGet({ env }) {
  const h = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
  if (!env.GV_DB) return new Response(JSON.stringify({ configured: false }), { headers: h });
  try {
    const ok = await env.GV_DB.prepare("select at from purge_runs where ok=1 order by at desc limit 1").first();
    const last = await env.GV_DB.prepare("select at, ok, source from purge_runs order by at desc limit 1").first();
    const age = ok ? (Date.now() - Date.parse(ok.at)) / 36e5 : null;
    return new Response(JSON.stringify({ configured: true, last_ok_at: ok ? ok.at : null, last_run_at: last ? last.at : null,
      last_run_ok: last ? !!last.ok : null, last_run_source: last ? last.source : null, hours_since_ok: age == null ? null : Math.round(age * 10) / 10,
      stale: age == null || age > 36 }), { headers: h });
  } catch (e) { return new Response(JSON.stringify({ configured: true, error: "unreadable", stale: true }), { status: 500, headers: h }); }
}
