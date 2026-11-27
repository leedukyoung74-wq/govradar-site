# WMM GOV RADAR Cloudflare Cron fallback — STAGED, NOT DEPLOYED

Audit #334: in one observed 24-hour window GitHub USGS 5-minute scheduled
workflow ran 3 of 288 ideal times; NWS/CISA 15-minute ran 3 of 96.
A working source collector plus best-effort GitHub cron is not a realtime SLA.

## Safe default
- The provided wrangler.toml.example cannot deploy unchanged; its KV namespace
  ID is a placeholder and the dispatch switch is FALSE.
- DISPATCH_ENABLED=false: three public read-only data-file GETs, zero POSTs.
- No new site, login, customer record, payment, KONEPS calls, DNS change,
  account key, KV namespace, new Cron or paid plan has been activated.
- Existing GitHub official source scripts and recovery stay unchanged.

## Mandatory approval gates before live account deployment
1. Verify Cloudflare account uses Workers Free and has sufficient headroom for
   one Cron Trigger, 5-minute invocations, CPU, outgoing requests and Workers KV
   reads/writes. Confirm spend management / automatic paid overages are OFF.
2. Owner explicitly approves issuing ONE fine-grained GitHub token scoped
   to this single public repository with Actions WRITE only. Store ONLY as a
   Cloudflare Workers secret GH_DISPATCH_TOKEN, never in source, chat, issue,
   public HTML, build logs or static feeds. Rotate/revoke as required.
3. Create/bind a tiny KV namespace as WMM_CRON_STATE. The only stored keys are
   cooldown_usgs and cooldown_nws_cisa, with UTC timestamps, no user data.
   KV eventual consistency makes cooldown best-effort, not exactly-once.
4. Initially stage with DISPATCH_ENABLED=false, validate 3 approved GETs,
   no GH POSTs, no new fees, no provider errors and reasonable CPU.
5. Separately approve enabling DISPATCH_ENABLED=true, validate one bounded
   stale-feed GH dispatch chain, and audit 48 hours of Cron, GH workflow run,
   public data readback and actual Cloudflare quota usage. Disable immediately
   on unexpected cost, security or data quality issues.

## Source freshness thresholds and safety
- Single 5-minute Cron. USGS >20min stale, NWS >45min or KEV >6h stale.
- Hardcoded allowlisted three public GitHub raw JSON files; no arbitrary URLs.
- At most two POST requests per event to existing official GitHub Actions
  workflows, only after private auth + KV are configured and flag is enabled.
- Per-source successful-dispatch KV cooldowns USGS 15min and NWS/CISA 30min.
- Missing/malformed source timestamps -> fail closed, never speculative POST.
- HTTP 204 dispatch accepted is NOT verified source collection or publication.
- No guarantee of 5-minute realtime alerts. Existing free GH schedule still
  best-effort and public mobile/login/payment remain separate QA.

Offline test (NO NETWORK): node --test ops/cloudflare-watchdog/worker.test.mjs

No Cloudflare account change, token generation, KV allocation or live
deployment is authorized by this review-only code package itself.

Official docs: https://developers.cloudflare.com/workers/platform/limits/
https://developers.cloudflare.com/workers/configuration/cron-triggers/
https://developers.cloudflare.com/kv/platform/limits/
https://developers.cloudflare.com/workers/platform/spend-management/
