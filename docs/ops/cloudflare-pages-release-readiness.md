# WMM GOV RADAR — Cloudflare Pages production preflight (read-only)

**Identified from public DNS on 2026-11-19:** `radar.wmm-hoa.com` has CNAME `wmm-radar.pages.dev`, and the parent domain uses Gabia nameservers. This establishes the hosting destination but **does not** establish the repository integration, production branch, deployment permissions, last-good deployment, or which account owns the project.

## Status
- GitHub canonical `src` includes PR #56, #57, #58, #59 source changes.
- GitHub generated `main` should not be treated as the authoritative source for the rebuilt 7-language module.
- Public `/ko/prepare/` still displays the legacy **84L**, whereas the verified source build shows **106.4L** for 2 adults / 14 days.
- Public `/ko/resilience/` and `/quality/` return HTTP 404 as of this check; therefore production publication is not complete.
- Country-level official guidance evidence exists only for KR/JP/US, **not** for any retail product. All country food examples must remain unverified.

## Cloudflare administrator verification
1. Sign in to [Cloudflare Dashboard](https://dash.cloudflare.com/), then Workers & Pages → **wmm-radar**.
2. Confirm that its Custom Domains includes `radar.wmm-hoa.com` and record the last successful production deployment ID and creation date for rollback.
3. In Settings → Builds, inspect Source type. Cloudflare documents **Git integration** versus **Direct Upload** as distinct deployment configurations.
4. For Git integration, inspect the actual GitHub repository, production branch, build command, output directory and root directory. Expected for direct source build: `leedukyoung74-wq/govradar-site`, `src`, `python3 build.py --base https://radar.wmm-hoa.com`, `dist`, root `/`. These are **targets to compare**, not verified facts about the actual project.
5. If Direct Upload, **do not** switch hosting mode or upload the partial review delta. Preserve the existing project and prepare a **complete** `dist/` build, including any required Pages Functions, with review/rollback.
6. Inspect last known good deployment and enable a rollback path: Pages → Deployments → three-dot menu → Rollback to this deployment. Never delete the last-good deployment during release.
7. Approve the policy for unverified country-product examples, draft translations, and noindex review routes before public release.

## Optional read-only API inspection
Use `tools/cloudflare_pages_readonly_preflight.py` with the Cloudflare account ID and a Cloudflare API token limited to **Pages: Read** (subject to account permissions). Store credentials only in a local secure shell or secret manager. **Do not paste tokens into chat or commit them to GitHub.** The script requests only `GET /accounts/{account_id}/pages/projects/wmm-radar` and reports sanitized project fields, source branch/build configuration, hostname match, and blockers. It performs **no deployment**.

For example, in a private shell where variables are already set:
```powershell
python tools/cloudflare_pages_readonly_preflight.py
```
An absent token produces a BLOCKED message and no outgoing request.

## Go/no-go
A successful GitHub build or PR merge is not itself a production release. Before publication, capture current production deployment ID, check build output and required functions against production, obtain final owner approval, then verify at both `https://wmm-radar.pages.dev` and `https://radar.wmm-hoa.com`:
- HTTP 200: `/ko/resilience/`, `/en/resilience/`, all other 5 locales, `/quality/`, `/review/`
- HTTP 200: critical JSON and JS/CSS assets (including `/data/wmm-food-country-profiles.json`)
- Old /prepare page updated to 106.4L, safety instructions retained; /ready and all existing country/region routes still work.
- All 193 country profiles remain unverified for product and shelf life; official general guidance limited to 3 country records. No user-data or payment activation.
- Failed smoke check: rollback in Cloudflare dashboard and investigate. Do not modify DNS as a workaround.

Official references:
- https://developers.cloudflare.com/pages/configuration/git-integration/
- https://developers.cloudflare.com/pages/configuration/branch-build-controls/
- https://developers.cloudflare.com/pages/configuration/rollbacks/
