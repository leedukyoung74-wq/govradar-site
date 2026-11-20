# WMM Four-Platform P0 Operations Checklist — 2026-11-20

Status: REVIEW ONLY. No production rollout or automatic deployment.

## Actual change in this branch
- `scripts/wmm_public_healthcheck.mjs`: read-only checks for existing verified public WMM and GOV RADAR URLs, with HTTP status, response URL and basic server-rendered HTML metadata.
- Local run: `node scripts/wmm_public_healthcheck.mjs --json`
- HTTP availability is **not** login, purchase, CRM, visual or feed accuracy verification. No live test result is claimed until executed and logged.
- Excluded: PLAYGROUND and WORLD MIRACLE MAKERS because their verified public production URLs are not available in the source-of-truth handoff.

## Priority gates before claiming 100%
1. WMM: authenticated login/logout and return URL, M0–M5 entitlement checks, support-map freshness and original source/closure dates, lead capture and CRM consent and routing.
2. GOV RADAR: official sources, ingestion run timestamp, 193 countries and 23 separate special territories, deduplication, bid deadlines and time zones, B2B/B2G inquiry path, incident data provenance and TLP/PII gates.
3. PLAYGROUND: signed-off public URL and hosting/source, 3-minute idea tool, save flow with minimum login, 7-day challenge, opt-in referral to WMM, minors' safeguards.
4. MIRACLE MAKERS: legal entity and fundraising permissions, separate data/accounts, contribution and participant intake controls; do not enable payments before authorized status.
5. PREPARE: preserve existing 7-person master and original date; store primary quote, publishing date, content type, verification, and correction trail. Never present a prediction as an official warning.
6. World Ahead: index years 1987–2027 with official links and verification state. 2027 cover/essay authorship must be sourced; 2028 publication remains UNKNOWN until the publisher verifies it. Do not repost copyrighted full covers without permission.
7. Revenue: measure visit → consented lead → qualified request → proposal → signed agreement → paid invoice with real, attributed events, excluding fictitious numbers. Maintain rollback, audit evidence, and consent retention.
8. UI: WMM official approved round metallic logo, Nexon Lv1 Gothic (only licensed approved files), black #121417, white #FFFFFF, champagne gold #B8A37B. Korean/English and mobile breakpoints; PLAYGROUND accent may differ.

## Acceptance evidence required
For each feature: repo/commit, deployment URL and timestamp, screenshot or browser E2E evidence, test assertion, owner approval if required, customer privacy/security check, and rollback path.

## Safety & change policy
No auto payments, refills, emailing users, intrusive scraping, production configuration changes or merging this PR. Existing production and all other working branches remain unchanged.

## 2026-11-20 verified implementation (review branch only)
- **Observed defect:** `robots.txt` references `https://radar.wmm-hoa.com/sitemap.xml`, while the tracked `main:sitemap.xml` blob is empty (SHA `e3e0a4510e36398042dddbc3c2ea630f4aa2538b`). This is a repository-source defect. Whether the production domain serves the same empty file remains unverified.
- **Fixed in PR branch:** nonempty `sitemap.xml` with exactly 14 existing static routes: 7 localized homepages and 7 localized `prepare` pages, each with reciprocal language alternates. Verified all 14 corresponding `index.html` files in `main` by path. Deliberately excluded `ready` and `resilience`, which lack verified `main` files; future larger sitemap expansion must be generated from full production/route inventory.
- **Predeploy source tests:** `tests/wmm_sitemap.test.mjs` checks URLs, static files, language alternates, and excludes unsupported paths. Existing HTTP test suite now checks for false successes (redirect to login, cross-domain redirect, blank HTML and wrong content type).
- **CI:** `.github/workflows/wmm_public_healthcheck_unit.yml` runs deterministic offline tests on PR changes. CI success means source integrity only; it does not mean indexed pages or real site flows work.
- **Next P0:** verify the production deployment source and live `/sitemap.xml` response, then confirm actual deployment and search-console submission only after approved rollout. Until those steps, production SEO remains UNVERIFIED.
