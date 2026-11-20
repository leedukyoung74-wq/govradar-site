"""Read-only directory sections for candidate territorial and national defence sources.
All entries are curated candidates, NOT live military or emergency data feeds.
"""
import html, json
from pathlib import Path

CATEGORIES = [
    ("government_business", "정부·공공사업", "Government & business"),
    ("news_media", "언론·뉴스", "News publishers"),
    ("environment", "환경", "Environment"),
    ("meteorology", "기상", "Weather"),
    ("emergency", "비상사태·재난", "Emergencies & disasters"),
    ("defence_security", "군사·안보", "Defence & security"),
    ("public_health", "공중보건", "Public health"),
    ("critical_infrastructure", "전력·수도·교통 등 기반시설", "Critical infrastructure")
]

def load(root):
    root = Path(root) / "src"
    territories = json.loads((root / "territory_official_sources.json").read_text(encoding="utf-8"))["territories"]
    defence = json.loads((root / "country_defence_official_sources.json").read_text(encoding="utf-8"))["countries"]
    return territories, defence

def render(iso, is_territory, language, territories, defence):
    esc = lambda x: html.escape(str(x), quote=True)
    ko = language == "ko"
    label = ("검토용 공식 출처 링크 · 실시간 수집/접속 확인 아님" if ko else
             "Curated official-source candidates · not verified live links or live alerts")
    if is_territory:
        item = territories.get(iso)
        if not item: return ""
        groups = [(k, ko_name if ko else en_name, item.get(k) or []) for k, ko_name, en_name in CATEGORIES]
        total = sum(len(records) for _,_,records in groups)
        heading = "자치·특별 지역 공식 정보원" if ko else "Autonomous & special region sources"
    else:
        item = defence.get(iso)
        if not item: return ""
        _civil = item.get("defence_structure") in ("no_standing_army", "no_regular_armed_forces")
        _grpname = ("국방 담당·공공안보 기관 (상비군 없음)" if ko else "Defence responsibilities and civilian security (no standing army)") if _civil else ("국방·군사 공식기관" if ko else "Official defence institutions")
        groups = [("official_sites", _grpname, item.get("official_sites") or [])]
        total = sum(len(records) for _,_,records in groups)
        heading = "국가 국방·안보 공식 정보원" if ko else "National defence and security official sources"
    out = [f'<h2>{esc(heading)}</h2><p class="note">{esc(label)}</p>']
    if not is_territory and item.get("defence_structure") in ("no_standing_army", "no_regular_armed_forces"):
        out.append('<p class="note">' + ("상비군 없음: 경찰·해안경비·정부 국방책임기관은 육·해·공군으로 계산하지 않습니다." if ko else "No standing army: civilian security and coast guard sources are not military services.") + "</p>")
    for key, name, records in groups:
        out.append(f'<h3>{esc(name)} <small>{len(records)}' + ("/3" if key in ("government_business","news_media","official_sites") else "") + "</small></h3>")
        if not records:
            out.append('<p class="note">' + ("공식 출처 미조사·미연결" if ko else "Official sources not yet researched or linked") + '</p>')
            continue
        out.append("<ul>")
        for src in records:
            url = src.get("url", "")
            if not url.startswith("https://"): continue
            name = src.get("name") or src.get("agency_name") or url
            scope = src.get("authority_scope") or src.get("role") or ""
            if scope == "parent_authority":
                scope = "소속 국가 담당기관" if ko else "Parent-state authority"
            out.append(f'<li><a href="{esc(url)}" target="_blank" rel="noopener noreferrer nofollow">{esc(name)}</a> <small>{esc(scope)}</small></li>')
        out.append("</ul>")
    return "".join(out)
