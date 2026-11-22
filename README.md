# www.wmm-hoa.com (branch `www`)

2026-11-22 chatgpt.site → GitHub + Cloudflare Pages 이전 (대표 승인).

- `public/` 정적 사이트. 첫 화면 `index.html` = 네 개의 문, 기존 홈페이지는 `home.html` (예전 `/#...` 주소는 자동으로 `home.html#...`).
- `functions/api/wmm/*` 서버 기능 (Cloudflare Pages Functions): config, session(Firebase 토큰 검증), map-config, tiles(미연결), news(GDELT), opportunities(기업마당 키 `BIZINFO_KEY` 있을 때), `?resource=` grants(중기부 RSS)·community·projects·ledger(KV `WMM_KV` 바인딩 있을 때).
- Cloudflare Pages 설정: Production branch `www`, Build command 없음, Build output `public`.
