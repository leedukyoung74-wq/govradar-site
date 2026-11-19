# WMM GOV RADAR — implementation status (2026-11-19)

Source of requirements: Google Docs 16–17 section, 12-task checklist (D1–D4, B1–B4, T1–T4).

## Implemented in this draft PR (not production)
- Data integrity audit on country, selected special-region, and opportunity JSON: `scripts/audit-data.mjs`.
- Per-country profile coverage, source links, stale profile dates, and past/invalid tender deadline audit: `scripts/audit-country-details.mjs`.
- Priority queue of 20 human-review source records: `scripts/build-review-queue.mjs`.
- Source quality diagnostics page: `quality/index.html`.
- Search/filter review page for country/special-region opportunity records: `review/index.html`.
- CI validation for page script syntax, required controls, and absence of identity/payment processing in review tools: `scripts/check-review-pages.mjs`.
- GitHub Actions read-only checks and artifact capture: `.github/workflows/wmm_data_quality_gate.yml`.

## Source findings (raw main branch snapshot at review)
- Registered: 193 country records; 23 selected special regions.
- Legacy done flag: 120 country records; 1 special region (not verified coverage).
- Opportunities: 620, all lacking a direct source URL field; 475 with blank deadlines.
- Six records originally rejected by country-only matching were valid `PH-BARMM` regional records and are now recognized without rewriting the data.

## Unfinished, blocking production approval
1. Confirm deployment source is this GitHub repository and protect production main/hosting config.
2. Human-verify at least 20 notices and 20 crisis alerts using current authoritative source, timestamp, license, correction history.
3. Add backend provenance and editorial review status (immutable versions, RLS and audit trail) before any 'verified', 'LIVE' or official-tender claims.
4. Establish correct country/special-region and official agenda data coverage; source URLs are only starting points.
5. Implement single-account authorization across WMM and radar only after verifying actual identity provider and server-side entitlements. Frontend checks are never a billing/permission security boundary.
6. Wire leads, CRM conversion events, consent, opt-out, and paid product tiers only after approved back-end endpoint and privacy terms exist.
7. Test 320/375/768/1280 desktop/mobile, keyboard access, authentication return flows, and bilingual layouts.
8. Clear photo licensing/attribution and image asset manifest; no unrestricted scraping.
9. Review privacy/security/TLP/redistribution before CTI, alerts, or outside syndication.
10. Record backup, rollback, deployment authorization and monitoring evidence.

## Risk/approval gates
- No main merge or deployment by the PR tools. Review pages use noindex, **which is not authentication**; don't expose confidential material through them.
- Original data is unchanged by these scripts.
- CI success = structural/script checks completed, **not** government verification or billing/auth certification.
- Existing Netlify Identity and Supabase config in repository must be audited for actual availability and security; no tokens or secrets should be exposed or copied into documentation.
- No external email, automatic payment, API subscription, emergency alert publication, public incident attribution, or credential collection is authorized.

## To review
1. Check PR #54 and latest GitHub Actions run artifacts (`report.json`, `review-queue.json`, `country-coverage.json`).
2. Inspect the 20 queued records, resolve original source and license, and attach review evidence.
3. Only after QA, stage the review pages behind an actual access control if they contain nonpublic content.
4. Production merge/deploy requires explicit separate approval and successful rollback rehearsal.
