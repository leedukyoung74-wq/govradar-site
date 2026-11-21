#!/usr/bin/env python3
"""WMM 길 네 단계 띠 — GOV RADAR 메인(/welcome/ 와 언어별 /welcome/<L>/)에 '2단계 · 지금 여기'를 표시.
publish_cf.sh 에서 cf_variant.py 다음에 실행:  python3 tools/path4.py cf/public
글자는 7개 언어 사전을 이 파일 안에 둠(번역 키 시스템과 분리). 다시 실행해도 한 번만 들어감."""
import pathlib, re, sys
PUB = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "cf/public")
PG = "/playground/"
T = {
 "ko": ("WMM 길 · 네 단계", ["시험하기", "확인하기", "실행하기", "나누기"], ["WMM 플레이그라운드 · 무료", "GOV RADAR · 지금 여기", "WMM 홈페이지 · 상담·프로젝트", "World Miracles Makers · 준비 중"]),
 "en": ("The WMM Path · 4 steps", ["Test", "Check", "Build", "Share"], ["WMM Playground · free", "GOV RADAR · you are here", "WMM · consulting & projects", "World Miracles Makers · coming"]),
 "es": ("El camino WMM · 4 pasos", ["Probar", "Verificar", "Construir", "Compartir"], ["WMM Playground · gratis", "GOV RADAR · estás aquí", "WMM · consultoría y proyectos", "World Miracles Makers · próximamente"]),
 "fr": ("Le parcours WMM · 4 étapes", ["Tester", "Vérifier", "Réaliser", "Partager"], ["WMM Playground · gratuit", "GOV RADAR · vous êtes ici", "WMM · conseil et projets", "World Miracles Makers · bientôt"]),
 "ar": ("مسار WMM · أربع خطوات", ["جرّب", "تحقّق", "نفّذ", "شارك"], ["WMM Playground · مجاني", "GOV RADAR · أنت هنا", "WMM · استشارات ومشاريع", "World Miracles Makers · قريبًا"]),
 "vi": ("Lộ trình WMM · 4 bước", ["Thử", "Kiểm tra", "Thực hiện", "Chia sẻ"], ["WMM Playground · miễn phí", "GOV RADAR · bạn đang ở đây", "WMM · tư vấn và dự án", "World Miracles Makers · sắp ra mắt"]),
 "id": ("Jalur WMM · 4 langkah", ["Uji", "Periksa", "Wujudkan", "Berbagi"], ["WMM Playground · gratis", "GOV RADAR · Anda di sini", "WMM · konsultasi & proyek", "World Miracles Makers · segera"]),
}
HREF = [PG, None, "https://www.wmm-hoa.com/#request", PG + "path.html#miracle"]
CSS = ('<style id="wmm-path4-css">.wmm-p4{background:#0b1633;color:#fff;font-family:"WMM Nexon","NEXON Lv1 Gothic OTF",inherit;padding:14px 16px}'
 '.wmm-p4 .in{max-width:1180px;margin:0 auto;display:flex;align-items:center;gap:10px 14px;flex-wrap:wrap}'
 '.wmm-p4 b.t{font-size:14px;color:#c8f03a;margin-right:4px;white-space:nowrap}.wmm-p4 ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px}'
 '.wmm-p4 li a,.wmm-p4 li span.cur{display:inline-flex;align-items:center;gap:6px;padding:7px 12px;border-radius:999px;font-size:14px;line-height:1.2;text-decoration:none;color:#fff;border:1px solid rgba(255,255,255,.28)}'
 '.wmm-p4 li a:hover{border-color:#c8f03a}.wmm-p4 li span.cur{background:#c8f03a;color:#0b1633;border-color:#c8f03a;font-weight:700}'
 '.wmm-p4 i{font-style:normal;font-weight:700}.wmm-p4 small{opacity:.85;font-size:13px}.wmm-p4 li span.cur small{opacity:1}</style>')
def strip(L):
    title, verbs, subs = T.get(L, T["en"])
    items = []
    for n, (v, s, h) in enumerate(zip(verbs, subs, HREF), 1):
        inner = f'<i>{n}</i> {v} <small>{s}</small>'
        items.append(f'<li><span class="cur" aria-current="step">{inner}</span></li>' if h is None else f'<li><a href="{h}"{" target=\"_blank\" rel=\"noopener\"" if h.startswith("http") else ""}>{inner}</a></li>')
    return f'<!--path4:start-->{CSS}<nav class="wmm-p4" aria-label="{title}"><div class="in"><b class="t">{title}</b><ol>{"".join(items)}</ol></div></nav><!--path4:end-->'
n = 0
for f in sorted((PUB / "welcome").glob("**/index.html")):
    rel = f.relative_to(PUB / "welcome").parts
    if len(rel) > 2: continue                      # 홈만: /welcome/ 과 /welcome/<L>/
    if len(rel) == 2 and rel[0] not in T: continue
    L = rel[0] if len(rel) == 2 else "ko"
    s = f.read_text("utf-8")
    s = re.sub(r"<!--path4:start-->.*?<!--path4:end-->", "", s, flags=re.S)
    m = re.search(r"</header>", s)
    if not m: continue
    s = s[:m.end()] + strip(L) + s[m.end():]
    f.write_text(s, "utf-8"); n += 1
print("path4 strip:", n)
