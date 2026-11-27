# WMM GOV RADAR P0 — verified operating handoff
Updated 2026-11-27 (KST). Intended for owner, ChatGPT and Claude.

## Implemented and evidence-backed

| Area | Verified result | Evidence |
| --- | --- | --- |
| Public M1 fee | KRW 20,000 monthly and KRW 200,000 annually, VAT included, seven languages | PR 309–311; run 45972336571 |
| Actual payment server fee | Previously conflicting 22,000 / 220,000 fixed to 20,000 / 200,000. Live GET /pay/config reads correct amounts; payment_enabled=false; five offline mock tests PASS | PR 322; run 45983961342 |
| Anonymous auth guards | GET /nfform=405, GET /api/req=401, GET /mkey=401; **no real POST, signed-in flow or D1 write test** | PR 323; run 45984359466 |
| Customer-form privacy | 1,925 HTML files and 78 forms audited. Server rejects direct POST without explicit consent. Seven publicly served locale feedback pages show required consent. | PR 318–320; run 45982045922 |
| Site check | Strict fresh PASS/FAIL publication to data, no old success replay | PR 312–313; run 45973769200 |
| Data + monitoring | 22 public checks no failures, two delayed cron events PENDING; actual data checks passed. The five/fifteen-minute GitHub timer is not a timing SLA. | PR 317,323; run 45984359466 |
| UK official tenders | 12-page cap, recent 48h plus 1 of 4 rotating historical shards. Actual latest run 1,200 raw, 12 requests, state PARTIAL. NOT exhaustive | PR 316; data/sources_status.json Nov 27 10:16 UTC |
| US SAM.gov | Three scanned pages, 3,000 scanned vs upstream total 7,194, state PARTIAL. NOT all US bids | PR 316; data/sources_status.json Nov 27 10:16 UTC |
| DAPA overseas tenders | Sample first/last pages latest sampled deadline 2019-04-09, HISTORICAL_SAMPLE, no current verified notice. Not Korean domestic tenders | data/sources_status.json |
| Korea KONEPS | Correct official dataset 15129394; owner-only GET probe with 4 categories returned HTTP 403 ALL FOUR. No new notices published or guessed. | PR 321; run 45983585920 |
| Netlify fallback | Public Netlify homepage GET 200 with no visible form markup; Identity settings GET 200 and Google externally enabled flag true; unsigned user GET 401. No proof of actual registered forms, inbox, Google OAuth callback, or notification email | PR 324; run 45984910652 |

## Blocks requiring third-party owner account access

### Korean current procurement — REQUIRED BEFORE PUBLISH
**2026-11-27 code correction:** PR [#326](https://github.com/leedukyoung74-wq/govradar-site/pull/326) removed the incorrect DAPA credential fallback and repaired secret interpolation. PR [#327](https://github.com/leedukyoung74-wq/govradar-site/pull/327) changed the owner probe to fail rather than display green on HTTP 403, missing key or mixed errors; offline CI passed. An authenticated post-fix owner probe has **not** yet established provider approval. Follow [the exact owner-only KONEPS activation runbook](WMM_KONEPS_G2B_OWNER_ACTIVATION_RUNBOOK_2026-11-27.md) and do not infer that a current Korean bid was ingested.
Official API https://www.data.go.kr/data/15129394/openapi.do. Ask the owner of the data.go.kr account to apply specifically for the PPS KONEPS Bid Public Info Service. A DAPA overseas-bid API key does not imply access. Check the account approval and allowed server IP. Store the authorized service key as GitHub Actions secret KONEPS_KEY — NEVER paste in chat, tickets, code or logs. Rerun only owner issue #80 comment /govradar-probe-koneps. HTTP 403 is access denied but does not distinguish approval from network policy. After permission, separately validate recent source dates, official notice URLs, cancellation/revision rules, 7-day query window and page coverage before actual publishing.

### Netlify customer inquiry — STILL NOT VERIFIED
In the authorized Netlify team for wmm-govradar.netlify.app, inspect Forms and confirm registered forms: consortium, contract-request, expert-apply, feedback, gcsme-member, order, partner-apply, unlock. Check Forms → Submission notifications and recipient-address verification; provider requirements changed November 2026. Only after provider approval, send one authorized synthetic form submission and check the actual dashboard record, receipt email and CRM side. No real customer POST has been sent in these audits. A successful server relay HTTP response alone is NOT proof of a stored message. The connected Gmail search found no matching Netlify notifications in the last 90 days, but that is not proof the Netlify dashboard is empty.

### Identity / member entitlement — STILL NOT VERIFIED
Public settings advertising Google does not prove live Google OAuth sign-in, signed-in D1 writes or roles. Provider-authorized synthetic accounts must test grade m0, m1, owner, revoke/logout, per-user data access, two monthly included analyses and 10-minute deduplication. No unapproved test user or real customer record created.

### Payments — CORRECT AMOUNTS, NOT ACTIVE
Server GET /pay/config: payment_enabled=false. Preserve M1 KRW 20,000/200,000 VAT included. Do NOT enable Toss keys or execute real charges until owner authorizes checkout, VAT/invoicing, refund policy, receipts, account entitlement and a supervised payment test. A confirmed Toss payment currently sends a Netlify order notice but does not automatically grant the Netlify m1 role; fix before paid launch.

### UK / US and scheduled freshness — PARTIAL, NOT SLA
UK one historical shard per day and 12 pages cannot be described as UK-wide exhaustive coverage; sample multiple dates and expose partial status. SAM scanned only a bounded part of its upstream records. Neither public procurement authority listing nor tenders identifies verified private importers. Existing free GitHub cron is best-effort; keep PENDING when schedules lag and FAIL when actual published source data are stale.

## Exact evidence links

- Main site: https://radar.wmm-hoa.com/ko/
- Source status: https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/sources_status.json
- Live site check: https://raw.githubusercontent.com/leedukyoung74-wq/govradar-site/data/feeds/site_check.json
- Owner-only issue commands: https://github.com/leedukyoung74-wq/govradar-site/issues/80
- Korea 4×403 run: https://github.com/leedukyoung74-wq/govradar-site/actions/runs/45983585920
- Payment-price live verification: https://github.com/leedukyoung74-wq/govradar-site/actions/runs/45983961342
- 22-check public watch: https://github.com/leedukyoung74-wq/govradar-site/actions/runs/45984359466
- Netlify GET-only probe: https://github.com/leedukyoung74-wq/govradar-site/actions/runs/45984910652

No private API keys, user tokens, customer records, actual form submissions or payment transactions included.
