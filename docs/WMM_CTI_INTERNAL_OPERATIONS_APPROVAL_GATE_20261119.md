# WMM CTI internal pilot — approval-gated operations

**Task:** T20261119-SECRETARY34-CTI-02 | **State:** DRAFT / NO DEPLOY / NO MERGE
**Owner:** WMM CEO | **Updated:** 2026-11-19 KST

## Implemented in PR #69

- `tools/cti_safe_intake.py` — GET CISA-maintained KEV data only; bound response; canonical CVE/date/count; SHA-256; non-sensitive vendor/product/CVE fields; no usernames, payloads, malware, event accusations.
- `tools/cti_internal_review.py` — offline risk brief, recent 30-day catalog additions, no automatic victim detection, freshness <=48h; stale material is blocked for current risk assessment.
- `tools/cti_asset_match.py` — offline exact vendor+product candidate matching ONLY with a local sanitized inventory and an authorization reference. The software **cannot verify the authenticity of a signature**. Every hit has status `UNVERIFIED_CANDIDATE`, and version/vendor advisory confirmation by a qualified reviewer is mandatory. No network scanning and no customer-data export.
- `tests/test_cti_safe_intake.py`, `test_cti_internal_review.py`, `test_cti_asset_match.py` — no-network regression tests.
- `.github/workflows/wmm_cti_safe_intake_qa.yml` — ephemeral GitHub Actions read-only validation: **no persistent artifacts, no push, no secrets, no web publication**.

## Internal demonstration on an authorized, isolated machine

Commands below are an **example only**; they are not permission to add system schedules or run on customer assets. Prefer the CI's synthetic offline tests first.

```sh
python -m unittest discover -s tests -p 'test_cti_safe_intake.py' -v
python -m unittest discover -s tests -p 'test_cti_internal_review.py' -v
python -m unittest discover -s tests -p 'test_cti_asset_match.py' -v
# One manual GET from CISA-maintained public feed, *after* the owner approves source use:
python tools/cti_safe_intake.py --out /tmp/wmm-cti-review/kev.json
python tools/cti_internal_review.py --input /tmp/wmm-cti-review/kev.json --out /tmp/wmm-cti-review/brief.json
```

No public/ or data_branch/ output; never commit the internal output. Never store raw feed in the approved Windows WMM PackageHub: its allowlist manages separate CTI ZIP artifacts.

## Gate for any ongoing operation

1. **Approval**: exact collection scope, CISA terms/attribution, HTTPS-only source, update cadence, cost ceiling, retention, alert recipient, incident owner and rollback plan approved by WMM CEO. Date + reviewer + evidence link required.
2. **Technical safety**: input hash, staleness/failure records, deduplication, false-positive and withdrawal log, fixed allowlist, optional network egress restrictions, no PII, no provider secrets in CI logs.
3. **Darkweb vendor**: until contract and terms reviewed, SOCRadar/Flare/Searchlight Cyber/URLhaus/ThreatFox data sources remain disabled. TLP and redistribution must be separately approved. No Tor/.onion, leaked data, passwords, malware samples, attacker communications or customer notifications.
4. **Defensive outcomes**: prioritization is for an **owner-approved inventory**, after reviewer confirms exact versions and vendor advice. KEV inclusion does not prove a particular company's compromise.
5. **Publication**: public safety instructions and verified original advisories may be linked only with separate explicit approval and license review. CTI raw feeds remain internal. Never automatically publish attacker allegations.

## Human cross-QA

- Compare live customer domain and current `src` / `live` branch state read-only. This PR does not alter `live`.
- Reproduce CI tests and inspect logs; record CVE catalog counts at run time, not as eternal truths.
- Test invalid CVE/duplicate/time travel/large payload, stale 48h, illegal release flag, wrong TLP, unauthorized inventory, PII fields, exact-match false positives.
- Document any known gaps: only CISA KEV supported; no vendor darkweb connectors, no KISA source adapter, no 24/7 running daemon, no approved customer list, no SOC staffing, no official incident response service or revenue.

## Sources and terms to verify

- CISA KEV: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- Official GitHub mirror: https://github.com/cisagov/kev-data
- FIRST TLP 2.0: https://www.first.org/tlp/
- URLhaus API terms: https://urlhaus.abuse.ch/api/
- ThreatFox API terms: https://threatfox.abuse.ch/api/
- Customer business/commercial rights and API terms require legal confirmation before activation.
