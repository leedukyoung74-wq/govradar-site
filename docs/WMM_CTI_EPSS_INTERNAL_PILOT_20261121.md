# WMM GOV RADAR: Internal CISA KEV + FIRST EPSS pilot (2026-11-21)

STATUS: DRAFT REVIEW ONLY. No merge, no deployment, no live customers, no vendor API, no billing.

## Goal
Enrich the EXISTING normalized internal KEV dataset from PR #69 with daily FIRST EPSS offline CSV/CSV.GZ, without any additional network request or collection of real customer data.

- FIRST data and usage: https://www.first.org/epss/data (API for small lookups; daily CSV for bulk).
- Existing CISA KEV intake: tools/cti_safe_intake.py on draft wmm/cti-safe-operational-intake-20261119.
- No Tor, stolen data, malware files, customer domains, credentials or darkweb vendors.

## Approved isolated trial
1. Obtain fresh normalized CISA KEV JSON from existing approved manual intake in PR #69.
2. Obtain the official daily FIRST EPSS CSV.GZ through an owner-approved download flow. Source: https://epss.empiricalsecurity.com/epss_scores-current.csv.gz; check rights/date.
3. Execute in a PRIVATE temporary directory:

    python tools/cti_epss_offline.py --kev /tmp/private/kev.json --epss /tmp/private/epss_scores-current.csv.gz --out /tmp/private/kev-epss-review.json
    python -m unittest discover -s tests -p 'test_cti_epss_offline.py' -v

There are ZERO HTTP calls in the enrichment tool. It refuses expired KEV inputs, old/future EPSS score dates, malformed/oversized/duplicate data, unauthorized source claims and public deployment directories. Existing output files are not overwritten.

## Interpretation and limitations
- KEV: CVE observed exploited; not evidence a customer was compromised.
- EPSS: global estimated exploitation probability over next 30 days; not a customer's breach probability.
- Missing scores => NO_SCORE_AVAILABLE; never infer low risk.
- This report never determines exact affected versions or validates authorization for customer-owned assets. Vendor advisory and qualified human review required.
- No auto downloads, scheduled jobs, customer email, operational release or paid sources until explicit approval, privacy/licensing review and deployment security verification.
- Check draft PRs #77, #78, #106 for auth/revocation/customer ownership before introducing any sensitive member data.

LOCAL_TEST_PASS: 10/10 synthetic offline tests passed. Re-verify the dependent PR CI independently. No live SOC or darkweb monitoring claim.
