# WMM PLAYGROUND (뭉치고) — 공개 미리보기 정적 사이트

- 이 브랜치(`playground`)는 Cloudflare Pages 프로젝트 전용입니다. 빌드 명령 없음, 출력 폴더 `/`.
- GOV RADAR(main·src·live)와 완전히 분리되어 있습니다.
- 서버 저장·로그인·결제·외부 API 없음. 기록은 사용자 브라우저(localStorage)에만 저장됩니다.
- `_headers`로 noindex·CSP 적용. 정식 공개 전 검색 노출 차단.
- 변경은 Claude가 검수(기능 32항목·접근성·5개 화면폭) 후 이 브랜치에 올립니다.
