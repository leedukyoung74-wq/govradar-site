# WMM / GCSME — Cloudflare Web Analytics activation runbook (2026-11-27)
Scope: www.wmm-hoa.com, wmm-hoa.com, www.gcsme.kr, gcsme.kr. Review only, no deployment.

## Verified evidence
- Cloudflare dashboard shows three Web Analytics sites: radar.wmm-hoa.com (nonzero), www.wmm-hoa.com (0), www.gcsme.kr (0).
- GitHub read-only public GET run 45947945502: HTTP 200 and CF-Ray/Server: cloudflare on all 4 WMM/GCSME host variants; no `static.cloudflareinsights.com/beacon.min.js` tag found **in initial HTML** for any.
- This alone cannot exclude dynamic JS injection or prove that a beacon request was/was not sent. The web analytics dashboard is the authority for actual recorded RUM data.
- Existing local PowerShell collector `Refresh_Analytics.ps1` already allows all four production WMM/GCSME hosts in the Cloudflare GraphQL query. No need to recreate the account token.

## Safe next change (requires live site/Cloudflare ownership permissions)
1. Open the Cloudflare Web Analytics entries for each site. Verify if the Cloudflare zone in this account offers **automatic Web Analytics injection** for proxied hostnames; if available, prefer this over an additional manual tag. Confirm per-site mode and avoid duplicates.
2. Otherwise, in **each ChatGPT Sites editor** insert the exact **site-specific** copied Cloudflare Web Analytics snippet once in the shared head/body template, respecting editor's supported HTML embedding. Never reuse GCSME token on WMM or vice versa. Do not post any unrelated Cloudflare API token, password, or private analytics account ID in site source.
3. Where Sites does not allow external script embedding, document the limitation and use only a supported edge injection or first-party host setting after a staging test; do **not** change DNS, proxies or production routing speculatively.
4. Verify CSP script-src/connect-src as per Cloudflare docs, on staging first if changes are needed.
5. Publish only the reviewed snippet/configuration changes with explicit owner authorization.
6. On the public site in a normal browser open Developer Tools > Network; visit a page, observe beacon JS loaded, confirm a proper POST to `/cdn-cgi/rum` (automatic) or `cloudflareinsights.com/cdn-cgi/rum` (manual); never manually POST synthetic metrics.
7. Verify WMM and GCSME **separately** in Cloudflare dashboard after normal visits; 0 today does not mean 'broken' if there were no measured visits.
8. Only after RUM collection is verified, check WMM BUSINESS MANAGER's next existing 6h `analytics-data.js` generatedAt/rows for hosts www.wmm-hoa.com/wmm-hoa.com/www.gcsme.kr/gcsme.kr. Never invent 0 if data unavailable; preserve snapshots as historical.
9. Keep existing 11 Windows scheduled tasks, Ollama bridge, Cloudflare read-only DPAPI token and GOV RADAR unchanged.

## Completion criteria
- [ ] One configured beacon per production site (auto or manual, not both)
- [ ] Correct per-site RUM token/zone ownership
- [ ] Verified browser Network beacon POST for each site
- [ ] Dashboard receives observed real pageviews for both
- [ ] Local scheduled Cloudflare GraphQL collector produces corresponding WMM and GCSME rows
- [ ] BUSINESS MANAGER UI displays these rows, separated by metric definition and date range
- [ ] Existing site styling, links, login and request forms unaffected

Reference: https://developers.cloudflare.com/web-analytics/get-started/
