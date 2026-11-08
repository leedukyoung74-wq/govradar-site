# GOV RADAR 공개 사이트 — 배포 안내

193개국 × 7개 언어(한국어·영어·스페인어·프랑스어·아랍어·베트남어·인도네시아어) 정적 사이트입니다.
비회원은 모든 내용을 볼 수 있고, AI 질문·입찰 담기·국가 알림·Foresight는 로그인한 회원만 씁니다.

## 폴더
| 경로 | 내용 |
|---|---|
| `build.py` | 사이트 생성기. `python3 build.py --base https://주소` → `dist/` |
| `export/` | 레이더 데이터(국가 193개, 관측). 자동 작업이 매일 덮어씀 |
| `export/regions/` | 자치·특별 지역 데이터 (PH-BARMM 등). 평일 06:52 자동 갱신 |
| `src/` | 로고·국가명(7개 언어)·대비 체크리스트·관측기관 목록·플레이북 |
| `web/` | 화면 스타일·스크립트, `config.js`(Supabase 키 입력) |
| `functions/api/ask.js` | 회원 전용 AI 질문 (Cloudflare Pages Function) |
| `workers/alerts/` | 회원 자동 알림 (이메일·카카오 알림톡·Slack·Teams), 매일 09:17 |
| `supabase/schema.sql` | 회원·프로필·알림·Foresight 테이블과 접근 규칙 |
| `gcsme/` | gcsme.kr에 붙여 넣는 섹션·상단 배너·메뉴·플로팅 버튼 (한/영) |

## 만들어지는 것
- `/ko/` `/en/` … 홈: 지도, 193개국 국기, 기회 보드, 행사, 지구·우주 관측, Foresight, 멤버십
- `/ko/philippines/bangsamoro-…/` 같은 자치·특별 지역 23곳 페이지 (소속 국가 페이지에도 바로가기)
- `/ko/vietnam/` 같은 나라별 고정 주소 1,351개 (검색·AI 검색 노출용, hreflang·구조화 데이터 포함)
- `/feeds/ko/ai-digital.xml` 등 업종별 RSS 18개 → LinkedIn·뉴스레터·Slack 자동 게시에 사용
- `/widget/` `/embed.js` 협회·기관 사이트에 넣는 위젯
- `/sitemap.xml` `/robots.txt` `/llms.txt`(AI 검색용 요약)
- 지진(USGS)·우주기상(NOAA)·소행성(NASA JPL)은 방문자 브라우저에서 실시간으로 불러오고, 나머지 관측은 6시간마다 갱신된 자료를 씀

## 주소 추천 (사용 가능 여부는 등록 사이트에서 확인 필요)
1. **govradar.ai** — 가장 임팩트 있음, AI 서비스 느낌 (연 7~10만 원대)
2. **govradar.io** / **govradar.global** — 세계 서비스 느낌 (연 5만 원 안팎)
3. **govradar.kr** — 국내 신뢰감 (연 2만 원 안팎)
4. 무료로 바로: **radar.wmm-hoa.com** 또는 **radar.gcsme.kr** (기존 도메인의 하위 주소)

→ 권장: 지금은 `radar.wmm-hoa.com`으로 시작하고, `govradar.ai`(또는 .io)를 확보해 연결.

## 비용
| 항목 | 비용 |
|---|---|
| Cloudflare Pages 호스팅·자동 빌드 | 무료 |
| 데이터 수집·갱신 (Claude 예약 작업) | 추가 비용 없음 (현재 Claude 요금제 사용량에서 차감) |
| Supabase 로그인·회원 DB | 무료 (월 활성 5만 명까지) |
| Cloudflare Worker 알림 | 무료 (하루 10만 요청) |
| 이메일 발송 (Resend) | 월 3,000통 무료 |
| 회원 AI 질문 (Claude API) | 사용한 만큼 유료 — 회원만, 하루 질문 수 제한(기본 20) |
| 카카오 알림톡 (솔라피 등) | 건당 약 10원 안팎 (선택) |
| 도메인 | 하위 주소는 무료, 새 도메인은 연 2~10만 원 |

## 배포 순서 (계정 연결이 필요한 단계)
1. **GitHub**: claude.ai 설정 → 커넥터에서 GitHub 연결 → 저장소 이름 알려 주기 (예: `wmm/govradar`). 이후 Claude가 코드를 올리고, 매일 데이터를 갱신해 자동으로 다시 배포합니다.
2. **Cloudflare Pages**: Cloudflare 가입 → Pages → GitHub 저장소 연결 → Build command `python3 build.py --base https://radar.wmm-hoa.com`, Output `dist`.
3. **주소 연결**: wmm-hoa.com DNS에 `radar` CNAME → `<프로젝트>.pages.dev` 추가 (Pages 화면에서 안내).
4. **Supabase**(로그인): 가입 → 새 프로젝트 → SQL Editor에 `supabase/schema.sql` 실행 → Authentication에서 Email(매직 링크) 켜고 Site URL을 사이트 주소로 → `web/config.js`에 Project URL과 anon key 입력.
5. **AI 질문**(회원): Cloudflare Pages 환경변수에 `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ANTHROPIC_API_KEY`, `ASK_DAILY_LIMIT=20`.
6. **알림 Worker**: `workers/alerts`를 Cloudflare Workers로 배포(KV 하나 만들어 연결), Resend 키·발신 주소 등록.
7. **회원 등급**: Supabase `members` 표에 회원 user_id와 등급(M1~M5)을 넣으면 해당 기능이 열림. M3 이상은 Foresight.

## 카카오톡 알림톡
1. 카카오톡 채널 개설(무료) → 비즈니스 인증(사업자등록증)
2. 발송 대행사(솔라피, NHN Cloud 등) 가입 → 채널 연결 → 템플릿 3개 심사 신청
   - 새 기회: `[GOV RADAR] #{제목}\n#{내용}\n자세히 보기: 레이더`
   - 마감 임박: `[GOV RADAR 마감 알림] #{제목}\n#{내용}`
   - 주간 브리핑: `[GOV RADAR 주간 브리핑] #{제목}\n#{내용}`
3. Worker 환경변수에 SOLAPI 키·채널 ID·템플릿 ID 입력
4. 회원은 '내 정보'에서 휴대폰 번호와 카카오 알림을 켜야 발송됨 (정보성 알림). 광고성 내용은 별도 동의(마케팅 수신 동의) 받은 회원에게만.

## 결제 (다음 단계)
- 국내 카드·계좌이체·간편결제: **토스페이먼츠** 정기결제(빌링) — 사업자 심사 필요, 수수료 약 3%대
- 해외 카드: **Stripe** (한국 법인은 직접 가입이 제한될 수 있어 Paddle·Lemon Squeezy 같은 대행형도 검토)
- 흐름: 멤버십 선택 → 결제창 → 결제 성공 웹훅 → Supabase `members` 등급 자동 기록
- 통신판매업 신고(제2024-서울서초-2185호)는 이미 있음. 온라인 판매 시 사업자 정보 표시 의무를 함께 확인

## 법적 주의
- 광고성 메일·카톡은 수신 동의한 회원에게만 (정보통신망법 제50조)
- AI 요약이므로 원문 확인 안내 문구 유지, 출처 링크 유지

## 구축 현황 섹션 (2026-10-31)
- 공개 사이트: `/ko/about/` 등 7개 언어, 하단에 "구축 현황 · 비축 키트" 링크
- wmm-hoa.com: `embeds/wmm-hoa-build-ko.html`(영문 `-en`)을 원하는 위치에 붙여 넣기 (스타일 포함, 클래스 접두어 grb-)
- gcsme.kr: `gcsme/gcsme-radar-ko.html` 하단에 같은 섹션이 추가됨
- 문구는 `src/about.json` 하나만 고치면 `python3 gen_build_section.py`와 `build.py`가 모두 반영
- 버튼 링크는 radar.wmm-hoa.com 기준 — 공개 사이트가 열린 뒤 동작
