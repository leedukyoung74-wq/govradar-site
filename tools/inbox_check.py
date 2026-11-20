"""ChatGPT 조사 파일 무료 검수기 (AI 크레딧 0).

사용: python tools/inbox_check.py <inbox 폴더> <출력 폴더> [--no-net]
 - inbox 폴더의 GPT_COUNTRY_*.json 을 읽어 나라별로 형식·금지어·출처 링크를 검사한다.
 - 출력: <출력>/<이름>.report.json (나라별 PASS/FAIL 와 사유)
         <출력>/<이름>.ready.json  (통과한 나라만: {"d1":{ISO:..}, "tr":{언어:{ISO:..}}, "tenders":[...]})
 - 의미 검수(내용이 출처와 맞는지)는 하지 않는다 — 그건 Claude/ChatGPT 표본 검수 몫.
"""
import json, re, sys, pathlib, urllib.request, ssl

HANGUL = re.compile(r"[가-힣]")
PHONE = re.compile(r"01[016789][-. ]?\d{3,4}[-. ]?\d{4}")
BANNED = ["수주 보장", "선정 보장", "독점", "유일한", "예언", "prophecy"]
LANGS = ["es", "fr", "ar", "vi", "id"]
REQ = ["asof", "summary", "leader", "agenda", "needs", "biz", "watch", "risk", "sources", "_change", "_change_en", "en"]
ISO = re.compile(r"^[A-Z]{2}$")


def texts(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from texts(v)
    elif isinstance(o, list):
        for v in o:
            yield from texts(v)


def reach(url, timeout=12):
    """True=열림, False=없음(404/DNS), None=판단불가(403·SSL·시간초과: 봇 차단일 수 있음)"""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 GOV-RADAR-linkcheck"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
            return r.status < 400
    except urllib.error.HTTPError as e:
        return False if e.code in (404, 410) else None
    except urllib.error.URLError as e:
        return False if "Name or service not known" in str(e.reason) or "nodename" in str(e.reason) else None
    except Exception:
        return None


def check_country(iso, v, tr, net=True):
    why = []
    if not ISO.match(iso):
        why.append("ISO 코드 형식 아님")
    for k in REQ:
        if k not in v:
            why.append(f"필수 항목 없음: {k}")
    if why:
        return why
    en = v["en"]
    if any(HANGUL.search(t) for t in texts(en)) or HANGUL.search(v.get("_change_en", "")):
        why.append("en 안에 한글이 있음")
    for k in ("agenda", "needs", "biz"):
        n = len(v[k])
        if len(en.get(k, [])) != n:
            why.append(f"{k} 개수 불일치(한국어 {n}, en {len(en.get(k, []))})")
    nb = len(v["biz"])
    for L in LANGS:
        t = (tr.get(L) or {}).get(iso)
        if not t:
            why.append(f"{L} 번역 없음")
            continue
        for key, n in (("a", len(v["agenda"])), ("n", len(v["needs"])), ("b", nb), ("w", nb), ("t", nb)):
            if len(t.get(key, [])) != n:
                why.append(f"{L}.{key} 개수 불일치")
    for b in v["biz"]:
        if b.get("fit") not in ("high", "medium", "low"):
            why.append("biz.fit 값 오류")
            break
    if (v["risk"] or {}).get("level") not in ("high", "medium", "low"):
        why.append("risk.level 값 오류")
    src = [s.get("url", "") for s in v["sources"] if isinstance(s, dict)]
    if len(src) < 2:
        why.append("출처 2개 미만")
    if any(not u.startswith("https://") for u in src):
        why.append("https 아닌 출처")
    allt = " ".join(texts(v)) + " " + " ".join(texts({L: (tr.get(L) or {}).get(iso) for L in LANGS}))
    for w in BANNED:
        if w in allt:
            why.append(f"금지어: {w}")
    if PHONE.search(allt):
        why.append("휴대폰 번호 형태")
    if net and src and not why:
        res = [reach(u) for u in src]
        if res.count(False) > 0:
            why.append(f"열리지 않는 출처 {res.count(False)}개(404/DNS)")
        if res.count(True) == 0:
            why.append("열리는 출처 0개(모두 차단·시간초과) — 사람 확인 필요")
    return why


def run(inbox, out, net=True):
    inbox, out = pathlib.Path(inbox), pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    done = []
    for f in sorted(inbox.glob("GPT_COUNTRY_*.json")):
        name = f.stem
        if (out / f"{name}.report.json").exists():
            continue
        rep = {"file": f.name, "countries": {}, "error": None}
        try:
            j = json.load(open(f, encoding="utf-8"))
            C, tr = j["countries"], j.get("tr", {})
        except Exception as e:
            rep["error"] = f"JSON 읽기 실패: {e}"
            json.dump(rep, open(out / f"{name}.report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            done.append(rep)
            continue
        ready = {"d1": {}, "tr": {L: {} for L in LANGS}, "tenders": []}
        for iso, v in C.items():
            why = check_country(iso, v, tr, net)
            rep["countries"][iso] = {"verdict": "PASS" if not why else "FAIL", "why": why}
            if not why:
                ready["d1"][iso] = v
                for L in LANGS:
                    ready["tr"][L][iso] = tr[L][iso]
        ok = set(ready["d1"])
        for t in j.get("tenders", []):
            if isinstance(t, list) and len(t) == 8 and t[0] in ok and str(t[4]).startswith("https://"):
                ready["tenders"].append(t)
        rep["pass"] = len(ok)
        rep["fail"] = len(C) - len(ok)
        json.dump(rep, open(out / f"{name}.report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if ok:
            json.dump(ready, open(out / f"{name}.ready.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        done.append(rep)
    return done


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    r = run(a[0], a[1], net="--no-net" not in sys.argv)
    for x in r:
        print(x["file"], "PASS", x.get("pass", 0), "FAIL", x.get("fail", 0), x["error"] or "")
    if not r:
        print("새 파일 없음")
