"""공공조달 발주기관 검색 페이지 게시 준비 (AI 크레딧 0).
cf/public 이 만들어진 뒤 실행: 데이터 JSON 생성 + 페이지 복사 + 대표 서체(넥슨Lv1고딕, WMM Nexon) 적용."""
import re, subprocess, sys, pathlib
R = pathlib.Path(__file__).resolve().parent.parent
pub = R / "cf/public"
src = R / "data_branch/feeds/tenders.json"
if not src.exists():
    print("buyers: tenders.json 없음 — 건너뜀"); sys.exit(0)
subprocess.run([sys.executable, str(R / "tools/build_public_procurement_buyers.py"), "--source", str(src),
                "--out", str(pub / "data/public-procurement-buyers.json")], check=True)
css = (pub / "assets/site.css").read_text(encoding="utf-8")
faces = "".join(m for m in re.findall(r"@font-face\{[^}]*\}", css) if "WMM Nexon" in m)
html = (R / "src/web/public_procurement_buyers.html").read_text(encoding="utf-8")
html = html.replace('font-family:"NEXON Lv1 Gothic"', 'font-family:"WMM Nexon","NEXON Lv1 Gothic"', 1)
html = html.replace("<style>", "<style>" + faces, 1)
(pub / "buyers").mkdir(parents=True, exist_ok=True)
(pub / "buyers/index.html").write_text(html, encoding="utf-8")
print("buyers page ok, font-face", faces.count("@font-face"))
