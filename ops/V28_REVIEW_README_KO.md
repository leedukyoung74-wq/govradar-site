# WMM GOV RADAR — v28 country, opportunity, and cron review (NO DEPLOY)

기준 2026-11-21. 자료 검수 자동화 작업용이며, 운영 데이터·웹사이트·외부 알림을 수정하지 않습니다.

## 실제 조사 대상
- `data/countries.json`: 193개 국가, `data/c/` 국가별 파일 존재 여부
- `data/opps.json`: 전체 620개 사업기회 (biz 462, oda 13, tenders 145)
- `data/regions.json`: 특별지역 목록 (국가와 분리)
- `ops/v28_candidate_sites_bj_md_tl_vu.json`: 베냉·몰도바·동티모르·바누아투 15개 출처 후보, 아직 모두 미검증

## 생성되는 3종 산출물 (원본 변경 없음)
1. `audit-results/v28/missing_countries.csv`: 실제 국가별 프로필이 없는 73개국
2. `audit-results/v28/source_tasks.csv`: 73개국 × 정부 3, 언론 3, 환경 1, 날씨 1, 비상사태 1 = 657개 출처 조사 슬롯
3. `audit-results/v28/opportunities_draft_review.csv`: 620개 사업기회를 원문·마감일·검증 여부별로 구분. 모든 항목 공식공고 표시·알림 차단

## 실행 방법
python -m unittest discover -s ops/tests -p 'test_v28_*.py' -v
python ops/v28_integrity_review.py --repo-root . --sources ops/v28_candidate_sites_bj_md_tl_vu.json --as-of 2026-11-21 --out-dir audit-results/v28
python ops/v28_schedule_triage.py --input audit-results/github_actions_runs.json --as-of 2026-11-21T04:40:00+00:00 --out audit-results/v28/cron_triage.json

GitHub에서 PR을 열면 `.github/workflows/wmm_v28_integrity_review.yml`이 로컬·원본 데이터를 자동 테스트하고 보고서를 GitHub Actions artifact로 올립니다.
Actions run 결과에 나타난 pass는 파일·코드 구조와 분류 정책에 대한 검증입니다. 620개 공고가 진짜인지 확인했다는 뜻이 아닙니다.

## 원문 출처 검증 기준
정부 사이트 3개·언론 3개는 서로 다른 운영 주체 및 신뢰가능 원문을 확인하고, 기상·환경·재난 기관은 해당 기관의 경보·업데이트 주기를 별도 확인합니다.
기관 URL 발견이나 정부 도메인 존재만으로 개별 입찰의 공고번호/마감일/취소 여부는 입증되지 않습니다.
지금은 15개 후보만 추가되었으며 이전 v27의 CV/IS 19개 후보 원장은 별도의 Draft PR #165에 있습니다. 두 PR 모두 병합되지 않았습니다.

## 24시간 운영 감시 핵심
GitHub Actions `schedule`은 지정된 분마다 실행을 보장하지 않습니다. 각 워크플로의 마지막 스케줄 실행과 마지막 성공 실행을 분리해 확인해야 합니다.
기존 hourly watch는 NWS/CISA 15분 schedule이 336.2분 동안 오지 않아 실패한 기록이 있습니다. 이후 별도 NWS/CISA 성공 기록은 존재하지만, 그 사실이 hourly watch 복구나 실시간 데이터 최신성까지 증명하지는 않습니다.
신규 `ops/v28_schedule_triage.py`는 CRON 누락·마지막 실패·오래된 성공·최근 성공을 분류하며, 실제 복구를 자동 실행하지 않습니다.

## 공개 차단 원칙
현재 `data/opps.json` 620개 모두 개별 출처 URL 필드가 없어 실제 최신 공식조달 공고로 발표하지 않습니다.
`may_publish_as_official=false` 및 `may_send_business_alert=false`는 원문과 수동 승인 증빙이 갖춰질 때까지 유지합니다.
기존 `main`, Cloudflare, DNS, 회원, 결제, 실제 메일, Gov Radar 공개 데이터 모두 그대로 둡니다.

다음 실구축 순서: 73개 프로필 출처 조사 → 국가별 자료 확정 → 620개 원문 공고 데이터 검수 → 외부 HTTPS/일일수집 장애복구 실험 → 기업별 영향/행동 권고 엔진에 검증 데이터만 연결.
