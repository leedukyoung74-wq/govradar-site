# WMM GOV RADAR — Data Quality Gate (staging / review only)

This is the first non-destructive implementation step for Google Doc section 16, D1–D4.

## Run
```bash
node scripts/audit-data.mjs
```

Node.js 20+ recommended. Reads existing `data/countries.json`, `data/regions.json`, and `data/opps.json` without modifying the files or calling the network.

## Output and interpretation
- Country and selected special-region registration counts are **not** equivalent to verified, up-to-date coverage.
- A legacy `done` flag is shown as-is; it does not prove official-source verification.
- Missing source URLs, blank deadlines, and possible duplicates are *warnings* for editorial review, not silently fabricated data.
- Unknown parent countries, duplicate country/region identifiers, and malformed input produce a nonzero exit code.
- Country/territory claims and business opportunities must be verified against primary sources and licenses before public "LIVE" or "verified" labeling.

## Follow-on work
1. Introduce source provenance fields and migrations in a separate backend repository (if the backend exists).
2. Inspect 20 original notices and 20 crisis events before changing the public counters.
3. Implement independent evidence status, TLP and redistribution controls, membership authorization, audit trails, and accessible UI in staging.
4. Require backup, diff, tests, and explicit production deployment approval.

No deployment, charge, authentication change, or automated public announcement is included in this branch.
