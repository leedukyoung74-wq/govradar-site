# WMM GOV RADAR — 사업자 대응 지침 증빙 게이트 (검토 전용)

날짜: 2026-11-21 | 범위: 이미 수집된 무료 미국 NWS 및 CISA KEV 공개 스냅샷의 *오프라인* 사업 대응 프롬프트 실험

## 해결할 실제 문제
공식 재난·사이버 정보는 그 자체로 특정 고객의 피해·업무 중단을 증명하지 못한다. WMM이 실행 가능한 제안을 하려면 정보 출처의 진위, 수집 최신성, 관할 지역, 경보 만료·취소 여부, 기업의 실제 위치·장비 사용 여부가 각각 검증되어야 한다. 본 모듈은 기업 위치/자산/멤버십을 아직 알지 못하므로 실제 고객 경보가 아닌 사람의 점검용 **프롬프트**만 생성한다.

## 입력
* 기존 운영 중인 `data/hz/nws_active.json` — `wmm.nws.v1` / `active_us_weather_alerts` / `coverage=United States only` / NWS 공식 API 출처 / `source_health`.
* 기존 `data/hz/cisa_kev.json` — `wmm.cisa.kev.v1` / `known_exploited_vulnerabilities` / `not_realtime_attack_feed=true` / CISA KEV 카탈로그 / `source_health`.
* 기존 허용 출처와 정해진 형식만 허용한다. 다른 출처·schema가 들어오면 `INVALID_SOURCE`; 수집 오류나 최신성 불분명 시 `SOURCE_UNVERIFIED`; 나이가 NWS 180분·CISA 600분 초과 시 `SOURCE_STALE`로 행동 카드 생성 중단. 이는 제품 가동 목표가 아니라 보수적 QA 신선도 한계다.
* NWS 경보는 `ends_at`이 현재보다 이후이고 `issued_at`이 현재 이후 5분 초과가 아니며 `src=NWS`·severity `Extreme/Severe`인 경우만 검토. 발표/종료 시각이 없으면 제외. NWS `partial_coverage`는 `PARTIAL_COVERAGE`로 기록한다.
* CISA KEV는 공식 카탈로그의 최신 스냅샷에서 최근 45일 신규 항목만 검토 카드로 제시한다. 오래된 기존 KEV가 안전하다는 뜻이 아니며, 카탈로그 전체 취약점 수나 특정 기업의 장비 사용 여부가 검증된 것은 아니다.

## 출력 및 엄격한 구분
* `INTERNAL_PREVIEW_ONLY`: 국가 코드(기상은 미국만), 경보 지역 원문, 공식 URL, 사람의 점검 필요성, NWS 경보 만료시각 및 CISA 제품/공개 CVE만 포함.
* `customer_geolocation_matched=false`, `customer_uses_product_confirmed=false`, `client_impact_confirmed=false`, `attack_confirmed=false`, `customer_notifications_sent=false`, `site_published=false`.
* 경보 존재 = 해당 기업 피해 확인 아님. CISA KEV 등재 = 특정 기업에 공격 발생 아님. 공공기관 22-01 의무 조치 기한 = 모든 민간기업 동일한 법적 마감일 아님. 기업 위치와 기업 자산 일치 여부가 확인되기 전, 실제 개인화 경보 발송 금지.
* 위험 정보가 비거나 소스가 만료됐더라도 안전, 무사고, 무공격 `all clear`라고 표시하지 않는다.

## 읽기 전용 재현 명령 (로컬 데이터만 사용)
```bash
python -m unittest discover -s tests -p 'test_wmm_business_action_preview.py' -v
python tools/wmm_business_action_preview.py --nws data_branch/hz/nws_active.json --cisa data_branch/hz/cisa_kev.json
```
명령은 외부 네트워크 접근 없음. 표준출력 JSON만 생성하고 파일/사용자/사이트를 수정하지 않음. GitHub PR 자동검사는 이미 존재하는 `data` 브랜치의 공개 스냅샷을 *읽어* 모듈의 임계값과 고객 영향 과장 방지 규칙을 점검한 후 임시파일을 삭제한다. 일일 스케줄은 추가하지 않는다.

## 공식 지침 확인
* NWS API 및 CAP 경보 구성: https://www.weather.gov/documentation/services-web-api , https://www.weather.gov/documentation/services-web-alerts
* CISA KEV 카탈로그: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
* CISA BOD 22-01의 적용 대상은 미국 Federal Civilian Executive Branch 기관이며 민간 기업에는 취약점 우선 조치 참고: https://www.cisa.gov/binding-operational-directive-22-01

## 상용화 전에 독립 QA 필수
1. 원본 NWS 지리적 영역을 GIS 좌표로 연결할 때 행정구역명이 동일하다는 이유만으로 기업 위치 일치로 표시하지 않을 것.
2. 현재의 NWS 공개 수집기는 `Actual`, severity `Severe/Extreme`, cancel/test 거부하지만 후속 업데이트·취소된 항목의 삭제/무효화를 완전히 보증하는지 별도 검사 필요.
3. CISA KEV 목록 대조는 실제 고객이 보유한 소프트웨어/SBOM/자산 데이터를 적법하게 얻은 경우에만 개인화. 자산 맵핑이 없으면 일반 점검 권고 유지.
4. 실제 회원별 통지, 작업 중단 명령, 재난 대피 권고, 취약점 자동 패치, 이메일/푸시, D1 쓰기, 유료 API, 원격 사이트 검사는 모두 미구현·미승인.
5. 타 국가 확장 전 공식 공급자와 API 이용약관, 시차·현지시간, 데이터 접근 권한, 이벤트 취소/재게시/중복/최신성, 면책/표시 정책을 문서화.
6. 기존 Draft #159(운영 감시), #152/160/162(국가·지역 기관 링크), #163(언론 출처), #157(유럽·호주 보안 권고)와 중복 병합/수집을 피할 것.

**출시 금지:** NO MERGE / NO DEPLOY / NO CUSTOMER NOTIFICATIONS / NO PAID APIS / NO SCHEDULE. 검증된 기술과 운영 배포 승인은 별개.
