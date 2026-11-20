# WMM World Ahead 2027 — 검토용 페이지 구축 기록 (2026-11-20)

## 작업 범위
- Economist Group **공식 2027년 특집 보도자료**를 기반으로 10개 주제를 독립적인 WMM 전망 허브로 정리.
- /ko/world-ahead-2027/ 경로에 검색/분야 필터/원문 링크/업무 활용을 포함하는 **정적 단일 HTML** 생성.
- 2027년 전쟁·시장 붕괴를 예언처럼 표시하지 않도록 전망/확정의 경계를 명시.
- 표지 이미지, 결제, 개인정보, 위험경보 발행, 네트워크 API 자동호출, 기존 공개 피드 수정 없음.
- **기존 main/live/data/src 운영 브랜치에 대한 배포/병합 승인 아님**. 단독 리뷰용 Draft PR.

## 기준 출처
1. Economist Group 공식 전망: https://www.economistgroup.com/press-centre/the-economist/the-economist-launches-the-world-ahead-2027-heralding-the-post-trump-era-amid-upheaval-from-bond-markets-and-ai
2. IMF 2026-10 WEO: https://www.imf.org/en/Publications/WEO/Issues/2026/10/13/world-economic-outlook-october-2026
3. IMF GFSR: https://www.imf.org/en/Publications/GFSR/Issues/2026/10/13/global-financial-stability-report-october-2026
4. IEA 2026 WEO: https://www.iea.org/reports/world-energy-outlook-2026/setting-the-scene
5. WMO 기후 전망: https://wmo.int/resources/publication-series/wmo-global-annual-decadal-climate-update/global-annual-decadal-climate-update-2026-2035
6. 프랑스 정부 2027 선거: https://www.info.gouv.fr/actualite/election-presidentielle-2027
7. 미국 ODNI 2026 위협평가 p22: https://archive.dni.gov/files/ODNI/documents/assessments/ATA-2026-Unclassified-Report.pdf
8. WHO GLP-1: https://www.who.int/news/item/01-12-2025-who-issues-global-guideline-on-the-use-of-GLP-1-medicines-in-treating-obesity
9. NASA 상업 우주정거장: https://www.nasa.gov/humans-in-space/commercial-space/commercial-space-stations/
10. UNESCO 창작경제: https://www.unesco.org/en/reshaping-creativity-reports

## 운영상 주의
- **Issue #80:** 공개 입찰 피드 최신성 실패가 별도로 남음. 이 자료가 이를 고치거나 검증하지는 않음.
- **PR #79:** 24시간 Codex 개발 검토 작업대는 독립적으로 유지. 본 PR이 유료 AI, 자동코딩, 신규 서버를 활성화하지 않음.
- 정적 데이터 기준일 2026-11-20. 인터넷에서 원문을 다시 확인하지 않으면 이후에도 같은 정보가 남음.
- 예정 작업: 공식 소스별 버전·정정 이력·국가 영향 지표, 실제 권한·운영 검증, 번역 QA. 본 PR 단계에서는 수행되지 않음.

## 독립 QA 체크리스트
- [ ] 데스크톱/모바일 320·375·768·1280 화면 배치 확인
- [ ] 주제 10개, 검색, 필터, 확장/축소, 외부 링크 동작
- [ ] SEO noindex, 외부 링크 noopener, 키/사용자정보/유료 API 없음
- [ ] 실제 배포 전 라이선스·원본 출처·연락 수신 및 수정 권한 검토
