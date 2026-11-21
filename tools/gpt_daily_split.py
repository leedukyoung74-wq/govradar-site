"""ChatGPT GPT_DAILY_YYYYMMDD 통합 파일 → 기존 검사·반영 형식으로 나누기 (AI 크레딧 0).

사용: python tools/gpt_daily_split.py <GPT_DAILY 파일(.json 또는 문서 본문 .txt)> <출력 폴더> [--seen <처리기록.json>]
 - 문서 본문이면 ===JSON START=== 와 ===JSON END=== 사이만 읽는다.
 - 출력: <출력>/country/GPT_COUNTRY_YYYYMMDD.json (inbox_check.py 입력 형식 그대로)
         <출력>/hazard/GPT_HAZARD_YYYYMMDD.json, <출력>/directory/DIR_YYYYMMDD.json (검토용, 자동 반영 안 함)
         <출력>/split_report.json (NODATA / DUPLICATE / SCHEMA_FAIL / SPLIT_OK, 내용 SHA-256)
 - 같은 내용(SHA-256)을 이미 처리했으면 DUPLICATE 로 끝낸다(중복 실행 방지).
"""
import hashlib, json, pathlib, re, sys

LANGS = ["es", "fr", "ar", "vi", "id"]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def extract(text):
    m = re.search(r"===JSON START===\s*(.*?)\s*===JSON END===", text, re.S)
    body = m.group(1) if m else text
    body = body.strip().strip("`")
    if body.startswith("json"):
        body = body[4:]
    return body.strip()


def split(raw_text, out, seen_path=None):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    rep = {"status": None, "sha256": None, "date": None, "countries": 0, "hazard": False, "directory": 0, "errors": []}
    body = extract(raw_text or "")
    if not body:
        rep["status"] = "NODATA"; return finish(out, rep)
    rep["sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    seen = {}
    if seen_path and pathlib.Path(seen_path).exists():
        try: seen = json.loads(pathlib.Path(seen_path).read_text(encoding="utf-8"))
        except Exception: seen = {}
    if rep["sha256"] in seen:
        rep["status"] = "DUPLICATE"; rep["date"] = seen[rep["sha256"]]; return finish(out, rep)
    try:
        d = json.loads(body)
    except Exception as e:
        rep["status"] = "SCHEMA_FAIL"; rep["errors"].append(f"JSON 읽기 실패: {str(e)[:80]}"); return finish(out, rep)
    if not isinstance(d, dict) or d.get("kind") != "wmm_govradar_daily":
        rep["errors"].append("kind 가 wmm_govradar_daily 아님")
    date = str(d.get("date", ""))
    if not DATE.match(date):
        rep["errors"].append("date 형식 오류(YYYY-MM-DD)")
    rep["date"] = date
    c = d.get("country") or {}
    if not isinstance(c.get("countries", {}), dict) or not isinstance(c.get("tr", {}), dict) or not isinstance(c.get("tenders", []), list):
        rep["errors"].append("country 형식 오류(countries·tr·tenders)")
    if rep["errors"]:
        rep["status"] = "SCHEMA_FAIL"; return finish(out, rep)
    ymd = date.replace("-", "")
    countries = c.get("countries") or {}
    if countries:
        cdir = out / "country"; cdir.mkdir(exist_ok=True)
        tr = {L: (c.get("tr") or {}).get(L, {}) for L in LANGS}
        json.dump({"kind": "country", "date": date, "by": d.get("by", "ChatGPT"), "countries": countries, "tr": tr,
                   "tenders": c.get("tenders") or []}, open(cdir / f"GPT_COUNTRY_{ymd}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    rep["countries"] = len(countries)
    hz = d.get("hazard") or {}
    if hz.get("summary_ko") or hz.get("hotspots") or hz.get("disasters"):
        hdir = out / "hazard"; hdir.mkdir(exist_ok=True)
        json.dump(hz, open(hdir / f"GPT_HAZARD_{ymd}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        rep["hazard"] = True
    od = d.get("official_directory_updates") or {}
    n = sum(len(v or {}) for v in od.values() if isinstance(v, dict))
    if n:
        ddir = out / "directory"; ddir.mkdir(exist_ok=True)
        json.dump(od, open(ddir / f"DIR_{ymd}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    rep["directory"] = n
    rep["notes"] = d.get("notes") or {}
    rep["status"] = "SPLIT_OK" if (countries or rep["hazard"] or n) else "NODATA"
    if seen_path:
        seen[rep["sha256"]] = date
        pathlib.Path(seen_path).write_text(json.dumps(seen, ensure_ascii=False, indent=1), encoding="utf-8")
    return finish(out, rep)


def finish(out, rep):
    (pathlib.Path(out) / "split_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


if __name__ == "__main__":
    a = [x for x in sys.argv[1:]]
    seen = None
    if "--seen" in a:
        i = a.index("--seen"); seen = a[i + 1]; del a[i:i + 2]
    text = pathlib.Path(a[0]).read_text(encoding="utf-8") if pathlib.Path(a[0]).exists() else ""
    r = split(text, a[1], seen)
    print(json.dumps({k: r[k] for k in ("status", "date", "countries", "hazard", "directory", "errors")}, ensure_ascii=False))
