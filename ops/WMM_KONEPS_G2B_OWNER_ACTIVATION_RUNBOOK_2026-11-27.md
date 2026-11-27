# WMM GOV RADAR — KONEPS / G2B official source activation (owner runbook)
Updated: 2026-11-27 KST · Status: **BLOCKED / NOT PUBLISHING** · No paid services.

## Authoritative contract
- Source: [PPS / Korea KONEPS official tender notices API, dataset 15129394](https://www.data.go.kr/data/15129394/openapi.do), **not** the distinct DAPA overseas-tender API.
- Official 2026-11-10 notice: query window changed from one month to **seven days maximum per call**. This probe currently requests three calendar dates (today and previous two KST dates).
- Official base: `https://apis.data.go.kr/1230000/ad/BidPublicInfoService02/`.
- Exact four operation paths: `getBidPblancListInfoThngPPSSrch02` (goods); `getBidPblancListInfoServcPPSSrch02` (services); `getBidPblancListInfoCnstwkPPSSrch02` (works); `getBidPblancListInfoFrgcptPPSSrch02` (foreign).
- Portal advertises free API and automated developer/operation approvals, but an authenticated account must check its own actual dataset authorization. Provider can still reject a call for key, endpoint, encoding, network policy or traffic limits.

## Historical proof (do not overstate it)
1. Owner-triggered read-only run [45983585920](https://github.com/leedukyoung74-wq/govradar-site/actions/runs/45983585920) returned **four HTTP 403**, `operations_succeeded=0`, `items_published=0`.
2. PR [#326](https://github.com/leedukyoung74-wq/govradar-site/pull/326) fixed an erroneous fallback from `KONEPS_KEY` to `DAPA_KEY`, and fixed an escaped GitHub Actions secret expression. Post-merge checks confirmed exact key expression and no DAPA fallback.
3. PR [#327](https://github.com/leedukyoung74-wq/govradar-site/pull/327) fixed the probe exit code: earlier a **green** job was possible with four 403 responses. Now no key, denied reply, or any of the four categories failing gives nonzero exit; only all four parseable service replies pass the **transport/schema** gate. Mocked offline CI passed.
4. **Neither merged PR proves approved KONEPS API access or an actual current live Korean tender.** No authenticated post-fix owner run is documented here.

## Owner account action — required before fresh external test
1. In the **actual owner account** at `https://www.data.go.kr`, log in and open `조달청_나라장터 입찰공고정보서비스`, dataset **15129394**, then confirm the dataset appears in the account's own API utilization / application records with approved rights. A key for another PPS/DAPA API is not interchangeable.
2. Copy the authorized **decoding** service key (or document the provided encoded/decoded variant) into GitHub repository `leedukyoung74-wq/govradar-site` → Settings → Secrets and variables → Actions → repository secret named **`KONEPS_KEY`**. Do not reveal the key in chat, issues, README, PR, local console recordings or website JS. If the key is already configured, confirm its source dataset privately; rotate only if owner policy calls for it.
3. On the existing owner issue [#80](https://github.com/leedukyoung74-wq/govradar-site/issues/80), signed in as repository OWNER, create one exact comment **`/govradar-probe-koneps`**. This launches an owner-only GitHub Actions job that runs offline mock tests first, then makes **up to four GET requests** with one page and five rows per category. It does not post notices or change user data. To avoid quota waste, do not repeat blindly on 403.
4. Review Actions run log **only for redacted summary**, especially `authorization_probe_gate`, `operations_attempted`, `operations_succeeded`, and per-category HTTP / schema state. Never copy actual keys or raw provider response URLs.

## How to classify results
| Safe signal | Correct conclusion | Next action |
| --- | --- | --- |
| `BLOCKED_NO_KEY` | No KONEPS-specific key in runner | Check repo secret name / owner account permissions; zero API requests |
| All four `403` / `BLOCKED_UPSTREAM_RESPONSE` | KONEPS requests denied; approval / key / provider policy cause **undetermined** | Confirm dataset-specific authorization, secret interpolation, approved key encoding and provider access policy. Do not use DAPA_KEY |
| Mixed 200/403, timeout, 429, malformed JSON/XML | Partial source response, **not live ready** | Inspect only redacted status, isolate provider/service issues and rate-limit policy |
| `SCHEMA_REVIEW_ONLY_NOT_LIVE` | Four endpoints returned accepted service response envelopes | Validate real current individual notices and business rules separately before publication |
| Four `OK_EMPTY` | Transport works but current items unproven | Expand controlled date window and verify actual original notices after authorization |
| Any response includes invalid official URL/date, cancelled tender, incomplete page count | **NOT READY** | Reject or quarantine record; preserve source-candidate status |

## Production acceptance gates (all required; none completed by this runbook)
- Confirm **fresh official** goods/services/works/foreign records for a KST 3–7-day publication window. Match `bidNtceNo`, `bidNtceOrd` revision, notice type/title, originating agency, publication timestamp, bid deadline, cancellation/amendment state and **official original URL**.
- Require correct KST parsing; no expired, cancelled or unknown-deadline items labeled as open. Verify at least a documented review sample against the actual official tender link, and keep `UNKNOWN` separate from `PASS`.
- Preserve quotas: one page/5 rows/4 GETs for probe; production pagination requires explicit quota/cost planning, retries with backoff and evidence of complete/partial coverage. **Do not claim all Korea tenders from four sample calls.**
- Deduplicate using notice number **and revision**, honor amended deadlines and cancellations, and keep source last success and last checked timestamps separate. No fake freshness by touching timestamps.
- Stage isolated candidate records, secure server-side retrieval and validate 7 language views/access controls. Do not merge tender candidates into public `data`, or enable a new schedule, without code review and two demonstrably successful collection → publish → public readback cycles.
- Separate DAPA's 2019 historical overseas example from modern domestic Korea KONEPS procurement. Present partial/unverified labels and disclose limitations.
- No automatic card charges, paid APIs, new always-on server, browser-facing secret, live DNS, live site deploy or customer record access.

## Explicit current status
**Code diagnostics repaired (PR #326 + #327); live KONEPS authorization and real tender ingestion still BLOCKED pending owner-access evidence.** Existing `main` work changes only the **read-only probe** and its offline tests. Do not equate GitHub Action PASS with actual integration.
