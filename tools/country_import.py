"""scratch 조사 묶음 {ISO:{...}} -> export/countries/{ISO}.json (기존 risk 등 보존 후 병합)"""
import json, sys, pathlib, datetime
TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime("%Y-%m-%d")
D = pathlib.Path("/home/claude/site/export/countries")
for iso, v in json.load(open(sys.argv[1], encoding="utf-8")).items():
    f = D / f"{iso}.json"
    d = json.load(open(f, encoding="utf-8")) if f.exists() else {}
    risk = d.get("risk") or {}
    if "risk" in v: risk.update(v.pop("risk"))
    risk["checked"] = TODAY; risk.setdefault("level", "low")
    for k in ("conflict", "disaster", "epidemic"): risk.setdefault(k, [])
    ren = d.get("risk_en") or {}
    if "risk_en" in v: ren.update(v.pop("risk_en"))
    for k in ("conflict", "disaster", "epidemic"): ren.setdefault(k, [])
    d.update(v); d["risk"] = risk; d["risk_en"] = ren
    for k in ("projects", "tenders", "oda", "krwins", "krsupport", "events"): d.setdefault(k, [])
    for b in d.get("biz", []): b.setdefault("isNew", True)
    d["updated"] = TODAY
    d["history"] = (d.get("history") or []) + [{"date": TODAY, "change": "첫 조사: 정부 과제·지도자·예산·위험 정리", "en": "First review: government agenda, leaders, budget and risks"}]
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(iso, "ok", len(d.get("agenda", [])))
