# 비서 3-4 인수인계 — WMM GOV RADAR 재난 대비센터 전체 보완 (검토 브랜치)
기준일: 2026-11-19
대상 운영 사이트: https://radar.wmm-hoa.com/ko/ready/ 및 https://radar.wmm-hoa.com/ko/prepare/
저장소: https://github.com/leedukyoung74-wq/govradar-site
브랜치: feature/multilingual-self-reliance-20261119
**상태: 구현된 독립 검토용 모듈. 운영 배포·기존 페이지 수정·PR 병합 완료가 아님.**

## 1. 완료한 코드 항목
- 한국어·영어·스페인어·프랑스어·아랍어·베트남어·인도네시아어 7개 경로 `/{lang}/resilience/`. 한국어·영어 문구가 가장 충실하고 기타 5개 언어는 주요 화면 번역 + 영어 fallback이며 전문 감수 미완료.
- 사용자의 요청에 맞춘 ‘자가발전·생존 인프라 개념도’: 국가 언어 전환 시 부품명이 다국어로 표시. 태양광/풍력·소수력/충전제어/배터리/조명·정수·식품. 연결선을 실제 배선도와 혼동하지 말 것.
- 인원·일수·물 사용량·식량 식수량 계산. 3·7·14·30·60·90·365일(장기 계획 예시). CDC 1갤런(약 3.8L)/인/일 기본값 및 표시.
- 전력 계산: 배터리 Wh·필수 부하 Wh/일·태양광 W·피크 일조시간, 시험용 손실 가정 0.8/0.7 적용. 외부 에너지 없는 무한발전 주장은 금지.
- 193개국 ISO 데이터와 정확히 1:1 대응하는 식품 프로필 193건. 42개국 ‘검토 예시’(illustrative), 151개국 ‘현지 자료 미검증’(pending). 지역별 구매가능 여부·제품 소비기한·식품안전당국 지침을 확인하기 전에는 완성이라고 발표하지 말 것.
- 공식 제조사·기관 링크 포함. EcoFlow, Victron, Ryse, Sawyer, Katadyn, ReadyWise, Midland, Briar, Kiwix, Organic Maps, Red Cross, NCHFP 등.
- 이용자 브라우저에만 저장되는 재난 대비 체크리스트(16항목), 지우기, 텍스트파일 다운로드. 회원가입과 서버 데이터 전송 없음.
- CDC/USDA/Ready.gov 공식 근거 링크, 발전기·정수필터·식품 보존·정전 냉장식품 안전 고지.
- Python 정적 계약검사와 Node JS 구문검사용 GitHub Actions.
- 기존 /ko/ready/, /ko/prepare/, 운영 중 /hazards/, /cyber/, /ko/ 내 페이지 및 기존 WMM 프로젝트/예약작업은 변경하지 않음.

## 2. 구현 파일
- assets/wmm-resilience.css — 독립 스코프 CSS, 반응형 UI
- assets/wmm-resilience.js — 다국어·계산·식품/제품·체크리스트
- data/wmm-food-country-profiles.json — 193국 데이터와 검증 상태
- ko/en/es/fr/ar/vi/id/resilience/index.html — 공개 검토용이되 noindex 태그 적용
- tests/check_wmm_resilience.py — 계약검증
- .github/workflows/wmm_resilience_check.yml — PR 리뷰용 검사

## 3. 반드시 검증할 미완료 작업 (운영 적용 전 차단 조건)
P0: PR 검사 PASS와 코드리뷰, 브라우저 PC·모바일·태블릿/RTL/키보드 접근성, 실제 사이트와 GitHub 빌드 소스 정합성.
P0: 현재 live /ko/ready/ 페이지와 저장소 main에 /ko/ready/ 코드가 일치하지 않음. 자동생성 배포본 직접 수정·덮어쓰기 금지. **소스 생성 파이프라인과 live 브랜치의 배포 기준**을 확인하고 병합 후 빌드에 반영할 적법한 경로 찾을 것.
P0: 원문과 실제 제품 공식 사이트 링크, 193국 유효 국가코드·정치/행정 구분, 7개 언어 번역 숫자·안전 경고 검수.
P0: 개인용 발전기를 220V 분전반에 연결하거나 보조 배터리의 임의 셀팩 제작을 안내하지 말 것. 발전 도면은 아직 실물 시제품·안전인증 미확인.
P1: 개인별 생존가방·대피·응급처치·식량 순환·복약/특수식 체크리스트 기존 재난 대비센터와 중복 없이 통합.
P1: 193개국 식품은 실제 시판 제품, 국가별 정부 식품안전당국, 장기보관 조건, 기후대·유통·식습관을 **국가별로 1차 출처 검증 후** 점진 채움. 42개국 예시에도 보관기간은 미검증. 추정으로 10년·20년 이상 유통기한 표기 금지.
P1: 23개 선정 자치·특별 지역은 193개국과 별도의 데이터/정치적 지위 표시를 유지. 현재 본 모듈은 193국만 포함.
P1: 7개 언어 콘텐츠 전문 감수, 접근성(스크린리더), 오프라인 저장(PWA)이 필요한지 별도 검토. 앱 형태가 승인되기 전 임의 로그인·결제 기능 추가 금지.
P2: 신규 독립 사이트 도메인 disaster.wmm-hoa.com은 제안만 있었고 DNS/SSL/배포는 미설정. 기존 GOV RADAR와 WMM 멤버십 연동은 검증 후 별도 프로젝트로.
P2: 국가별 공식 경보는 본 계획용 계산기와 분리. 'LIVE' 표시는 실제 관측과 신선도 증거가 있을 때만.
P2: 실제 CTI 파트너 연결은 사용권/개인정보/검증을 충족한 정제 메타데이터만. 다크웹 직접 접속, 유출된 원문, 악성 샘플 저장 또는 자동 게시 금지.

## 4. 공식 근거 자료
- CDC emergency water: https://www.cdc.gov/water-emergency/about/how-to-create-and-store-an-emergency-water-supply.html
- CDC food during outages: https://www.cdc.gov/food-safety/foods/keep-food-safe-after-emergency.html
- USDA canned shelf-life guidance: https://ask.fsis.usda.gov/article/How-long-can-you-keep-canned-goods
- CDC botulism prevention: https://www.cdc.gov/botulism/prevention/index.html
- CDC generator safety: https://www.cdc.gov/natural-disasters/psa-toolkit/use-a-generator-safely.html
- Sawyer filter limitations: https://www.sawyer.com/faqs
- Ready.gov kit: https://www.ready.gov/kit

## 5. 기존 WMM 운영 통제
사용자의 운영 통제: **PR #54는 병합하지 않음. 운영 배포/PR 자동병합/실제 고객 메일 발송/결제 활성화/기존 SQLite·수집기·예약작업 변경 금지.**
이번 PR 역시 merge 금지, 검토·실험 브랜치에 머물러야 함. 다른 워크플로의 기존 배포/자동수집 상태를 이 작업의 성공 증거로 간주하지 말 것.

## 6. 표준 다운로드·패키지 인수인계
패키지는 PC `C:\Users\user\Downloads`에서 먼저 받고 → 출처·SHA-256·악성코드 위험·권한 검증 → 승인 후 `C:\Users\user\WMM-AI-Workspace\00_WMM_PackageHub`에서 관리. 현재 CTI PackageHub 자동승인은 CTI 승인 목록만 처리; 재난 대비 페이지 코드는 GitHub 브랜치로 별도 관리.

## 7. 비서 3-4에 전달할 명시적 업무 지시
'WMM 재난 대비센터 전체 보완 코드가 별도 검토 브랜치에 들어가 있습니다. PR과 위 데이터/테스트 문서를 먼저 확인하고, 운영 중인 /ko/ready/·/ko/prepare/·/hazards/·/cyber/을 절대 덮어쓰지 마세요. 193개국 데이터의 미검증 상태를 공개적으로 유지하고 7개 언어/모바일/안전성/중복 기능을 검수한 후, 실제 생성 파이프라인에 통합할 변경안을 별도 PR로 제안하세요. 기존 PR #54와 이번 PR 모두 사용자 승인 전 병합하지 마세요. 비서 3-4 채팅 자체에는 자동 메시지 전송되지 않았으며 이 문서 링크를 전달받아야 합니다.'
