# WMM Four-Platform P0 QA & Source Integrity — corrected 2026-11-20

Status: REVIEW ONLY. No production deployment or code merge. Preserve all source-generated production XML.

## Critical correction: large-file read is not proof of an empty sitemap
The GitHub `fetch_file` connector returned an empty text field for the large single-line `sitemap.xml` blobs, while still returning valid, nonempty blob SHAs. A direct `fetch_blob` read proved both files contain their full original XML.
- `main:sitemap.xml`: blob `e3e0a4510e36398042dddbc3c2ea630f4aa2538b`, **1,261,718 characters, 1,736 unique localized URLs**, 248 per language.
- `live:public/sitemap.xml`: blob `b801e7e4d08c7bcde892093b92d13ef53a763994`, **1,281,262 characters, 1,764 unique localized URLs**, 252 per language. Includes the /ready/ path and excludes the unapproved /resilience/ path.
- `main:robots.txt` and `live:public/robots.txt` both contain the correct sitemap directive.
- There is NO proven empty-sitemap incident. Earlier notes claiming an empty sitemap or a missing robots directive were wrong and superseded by this record.
- The main generated sitemap was **fully restored byte-for-byte** in PR #71 using the original blob, with exact original SHA confirmed. DO NOT replace it with only 14 routes.

## What this PR actually provides
- `scripts/wmm_public_healthcheck.mjs`: bounded, read-only HTTP-only health checks for WMM/GOV RADAR known public routes; does not verify authenticated journeys, client UX, transactions or source accuracy.
- `tests/wmm_public_healthcheck.test.mjs`: offline mock-only route tests.
- `tests/wmm_sitemap.test.mjs`: checks that the original large generated source sitemap is preserved and is not accidentally reduced to a small landing-page list.
- `scripts/wmm_sitemap_preview.mjs`: review-only inventory of committed localized pages with a self-canonical and noindex filter. Does NOT rewrite site files.
- `tests/wmm_sitemap_preview.test.mjs`: offline preview and country-page tests.
- `.github/workflows/wmm_public_healthcheck_unit.yml`: CI source tests and a temporary review artifact.

GitHub Actions run `44651693727` passed 14 offline tests and produced a **review-only** 1,764-URL / 252-group inventory. That inventory is NOT proof of production visibility. It must not overwrite the main 1,736-URL source sitemap.

## Actual source/deploy mapping
- `src:build.py` is the actual static site generator. It already writes a complete sitemap.
- `src:tools/publish_cf.sh` prepares the Cloudflare `live` branch using `cf/public`.
- `main` is generated static output; the README says not to edit it by hand.
- Source-side PR #72 adds a **read-only** final sitemap/robots validation gate to `src`. It must not regenerate or truncate the production XML.
- The source repository/actual Cloudflare account binding and live deployment remain subject to verification before any rollout.

## Four-platform acceptance gates before any '100%' claim
1. WMM official site: authenticated login/logout and return URL, M0–M5 permissions, original domestic support announcements, consented lead-to-CRM handoff, quote/contract/payment proof.
2. GOV RADAR: credible original URLs, collection timestamps, 193 countries and 23 separate regions, deadlines/time zones, source licenses, cyber/incident PII/TLP protections, customer request path.
3. PLAYGROUND: verified hosting/source, original 3-minute idea workflow, save/login, 7-day challenge, voluntary referral/consent, minors' safeguards.
4. MIRACLE MAKERS: legal status, separate account/books, privacy, recruitment and donations only after authorization.
5. PREPARE: existing 7-person prediction ledger is preserved from 2026-10-25; quotes have first publication/source/translation/fact-check status. Do not portray predictions as official emergency warnings.
6. World Ahead: publisher-sourced annual records 1987–2027 and only verified 2028 material; copyrighted covers used only under appropriate rights.
7. Revenue and design: visit → consented lead → quote → contract → paid invoice, evidence-based metrics, approved WMM logo and fonts, mobile/KO-EN QA.
8. All changes require rollback evidence, no surprise charges, no unapproved production release, and a truthful reported state.

## Correct operating status
Code and tests exist in draft PRs; public source deployment, browser-level authentication/CRM QA, and the other three platform builds have NOT been completed here. No source deletion, existing branch overwrite, auto-billing, customer email or production deploy occurred.

## 2026-11-20 follow-up: static opportunity data provenance audit
- Actual tracked dataset inspection: `data/countries.json` has 193 country records, `data/regions.json` has 23 separately identified special regions, and `data/opps.json` contains 620 opportunities (462 `biz`, 13 `oda`, 145 `tenders`).
- Six opportunities use special region code `PH-BARMM`. This is a valid special-region reference, **not** an invalid sovereign country ISO. Validation accepts either known country ISO or separate region code, while requiring regions to reference valid parent countries.
- At the explicit as-of date 2026-11-20, 78/145 tenders had past calendar deadline dates; ten have an equal-date deadline and 57 future dates. Deadline timezone and later amendments are NOT verified; no real-time closure claim.
- All 620 opportunities lack per-item official source URLs in the tracked file. The displayed rows are **unverified source records**, not independent proof of open live tenders, government budgets, or firm contracting opportunities. Do not invent original links.
- Added read-only audit module `scripts/wmm_data_quality_audit.mjs`, run with `node scripts/wmm_data_quality_audit.mjs --json --as-of 2026-11-20`. Reports structural errors vs quality warnings without changing datasets. Added `tests/wmm_data_quality_audit.test.mjs` and included it in PR CI.
- GitHub Actions run **44656122109**: **22/22 tests PASS**, no production deploy. Current CI asserts observed static values as a regression baseline; these are not timeless requirements. When officially verified new source records are added, update baseline tests and retain historical log.
- P0 production gate: a data importer must store official per-opportunity original URL, agency, fetched/verified timestamp, immutable source ID, application deadline with timezone, amendment/cancellation state, and licensing. Until that evidence exists, labels must distinguish editorial opportunities vs official verified tenders.

## 2026-11-20: rendered tender-board vs JSON provenance reconciliation
- **Critical distinction:** the `data/opps.json` source records lack individual source URL keys (620/620), but generated `ko/mdb/index.html` and `en/mdb/index.html` contain 121 individual card anchors with external notice URLs. Thus 'all published listings lack links' would be incorrect; audit both layers separately.
- The presence of an external URL is NOT verification that it is an official issuer URL, currently open, or reflects an amendment. Some displayed links point to `bidsfactory.com` (third-party aggregator).
- Added `scripts/wmm_rendered_tenders_audit.mjs` (read-only) and `tests/wmm_rendered_tenders_audit.test.mjs` to inspect localized rendered MDB cards, distinguish elapsed/same-day/future/invalid dates, flag missing link and potentially misleading 'open tenders' headings, and preserve official-status UNKNOWN until source verification.
- GitHub Actions run **44657776029**: **27/27 offline tests passed**. No live website observation, source-build refactor, merge, or deployment asserted.
- Required next gate: have the source builder retain original notice URL, issuer, update/correction timestamp and deadline timezone in structured records, and render status based on verified notice updates. Review prior PR #72 source build guards before editing publishing code. Avoid claiming that a past calendar deadline alone proves a tender cancelled.
