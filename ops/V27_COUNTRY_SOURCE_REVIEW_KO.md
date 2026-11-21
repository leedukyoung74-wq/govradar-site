# GOV RADAR v27 국가별 출처 원장 — 검토 전용

기준: 2026-11-21 / 대상: 193개 국가별 출처. 자치·특별 지역은 별도 작업.

## 이번 변경
- ops/source_registry_v27.py: 전체 193개 국가의 상세 JSON 존재 여부와 누락 국가 작업 큐 출력
- ops/source_candidates_cv_is_20261121.json: 카보베르데(CV) 10, 아이슬란드(IS) 9개 출처 후보 등록
- ops/tests/test_source_registry_v27.py: URL 형식·증빙·중복 출처 등에 대한 13개 단위검사
- .github/workflows/wmm_source_registry_v27_review.yml: GitHub Actions에서 읽기전용 테스트 및 증빙 생성

## 출처 검증 기준
각국 정부 3, 언론 3, 환경 1, 기상 1, 비상 대응 1 사이트를 독립 집계한다.
CANDIDATE는 공개 검색에서 발견한 URL을 의미한다. 기관 소유, 공식성, 실시간 갱신, 수집 권한은 미검증이다.
HUMAN_REVIEWED는 최근 60일 이내 담당자·승인일·기관 소유 근거 URL·접속·기관 역할 및 편집 승인 기록이 있는 경우에만 검수 통계에 포함한다.
이 검수 상태도 실제 국가 상세 파일 완성이나 실시간 경보·조달 공고의 공신력을 입증하지 않는다.

## 실행 명령
python -m unittest discover -s ops/tests -p test_source_registry_v27.py -v
python ops/source_registry_v27.py --repo-root . --sources ops/source_candidates_cv_is_20261121.json --as-of 2026-11-21 --output audit-results/v27_country_source_coverage.json

## 안전 규칙
보고서는 audit-results에만 기록. data/ 원본, 사이트, Cloudflare, 운영 기본 브랜치, 메일, 결제 변경 금지.
620개 사업기회 원본에는 원문 URL이 없으므로 출처 검수 없이 실제 현재 입찰이라고 표시하거나 알림 발송 금지.
이 변경을 실서비스에 적용하려면 실제 소스의 관리 주체·현행성·이용약관·품질 및 담당자 승인 필요.

상태: REVIEW ONLY / NOT DEPLOYED / NO LIVE CLAIM
