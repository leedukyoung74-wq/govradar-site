#!/usr/bin/env python3
"""Automatic pre-check of a customer deliverable (Markdown) against docs/standards.
Usage: python tools/qa_deliverable.py deliverable.md [--json]
Checks only what a machine can check — front matter, required sections in order, the "AI 작성 + 사람 검수" label,
the disclaimer, links, banned content, date formats, numbers without a source. It never replaces the human review.
Each check is PASS, FAIL or UNKNOWN; exit code 1 if any FAIL."""
import json, re, sys

FIELDS = ["product", "client", "target", "date", "data_as_of", "reviewer", "version"]
SECTIONS = {
    "fit-review": ["결론", "공고 요약", "참여 자격", "필요 서류", "현지 파트너", "일정", "위험", "다음 행동", "출처"],
    "country-brief": ["결론", "한눈에", "정부 우선 과제", "입찰", "낙찰", "한국 지원", "위험", "진입 경로", "다음 행동", "출처"],
    "quarterly": ["결론", "한눈에", "정부 우선 과제", "입찰", "낙찰", "한국 지원", "위험", "진입 경로", "다음 행동", "출처"],
    "quick": [], "weekly": [], "partnership": [],
}
LABEL = "AI 작성 + 사람 검수"
PHONE = re.compile(r"(?<!\d)01[016789][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)")
BANNED = [("예언", "예언 표현"), ("서울 서초", "사업장 주소"), ("서초구", "사업장 주소")]
MONEY = re.compile(r"(US\$|\$|€|£|₩|원\b|억|조\b|\bbn\b|\bM\b|%|\b[A-Z]{3}\s?\d)")
REF = re.compile(r"\[\d+\]|\]\(https?://|https?://")

def front(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m: return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line: k, v = line.split(":", 1); meta[k.strip()] = v.strip()
    return meta, text[m.end():]

def check(text):
    r = []
    def add(cid, state, why): r.append({"id": cid, "result": state, "why": why})
    meta, body = front(text)
    miss = [f for f in FIELDS if not meta.get(f) or "{{" in meta.get(f, "")]
    add("front-matter", "FAIL" if miss else "PASS", "missing or placeholder: " + ", ".join(miss) if miss else "all fields filled")
    prod = meta.get("product", "")
    if prod not in SECTIONS: add("product", "FAIL", f"unknown product '{prod}'"); prod = None
    else: add("product", "PASS", prod)
    if "{{" in body: add("placeholders", "FAIL", f"{body.count('{{')} template placeholders left")
    else: add("placeholders", "PASS", "none left")
    if prod:
        heads = [h.strip() for h in re.findall(r"^##\s+(?:\d+\.\s*)?(.+)$", body, re.M)]
        pos, bad = -1, []
        for s in SECTIONS[prod]:
            i = next((n for n, h in enumerate(heads) if s in h), None)
            if i is None or i < pos: bad.append(s)
            else: pos = i
        add("sections", "FAIL" if bad else "PASS", "missing or out of order: " + ", ".join(bad) if bad else f"{len(SECTIONS[prod])} sections in order")
    add("label", "PASS" if LABEL in body else "FAIL", LABEL)
    add("reviewer-sign", "PASS" if re.search(r"검수자\s+\S+", body) else "FAIL", "검수자 이름 표기")
    add("disclaimer", "PASS" if "원문을 확인" in body else "FAIL", "면책 문구")
    links = re.findall(r"https?://[^\s)>\]]+", body)
    add("links", "PASS" if links else "FAIL", f"{len(links)} links")
    plain = [u for u in links if u.startswith("http://")]
    add("https", "UNKNOWN" if plain else "PASS", "http links (check they are official): " + ", ".join(plain[:3]) if plain else "all https")
    found = [why for w, why in BANNED if w in body] + (["휴대폰 번호"] if PHONE.search(body) else [])
    add("banned", "FAIL" if found else "PASS", ", ".join(sorted(set(found))) or "none")
    emails = set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", body)) - {"73036396@naver.com"}
    add("contact", "FAIL" if emails else "PASS", "other e-mail addresses: " + ", ".join(sorted(emails)) if emails else "only 73036396@naver.com")
    bad_dates = re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}\.\d{1,2}\.\d{1,2}\b", body)
    add("dates", "FAIL" if bad_dates else "PASS", "use YYYY-MM-DD: " + ", ".join(bad_dates[:3]) if bad_dates else "YYYY-MM-DD")
    src_part = body.split("출처")[-1] if prod else ""
    nosrc = [l.strip()[:60] for l in body.splitlines()
             if MONEY.search(l) and re.search(r"\d", l) and not REF.search(l) and not l.lstrip().startswith(("#", "|---")) and l not in src_part]
    add("numbers-sourced", "UNKNOWN" if nosrc else "PASS", f"{len(nosrc)} lines with money/% but no source ref, e.g. {nosrc[:2]}" if nosrc else "every money/% line has a ref")
    if prod == "fit-review":
        dl = [l for l in body.splitlines() if "마감" in l and re.search(r"\d{4}-\d{2}-\d{2}", l)]
        tz = any(re.search(r"UTC[+-−]\d", l) for l in dl)
        add("deadline-timezone", "PASS" if tz else ("FAIL" if dl else "UNKNOWN"), "마감에 시간대(UTC±hh:mm)" + ("" if dl else " — 마감 줄을 찾지 못함"))
        add("sanctions-checked", "PASS" if re.search(r"제재 명단.*(UN|OFAC)", body) else "FAIL", "4개 제재 명단 확인 결과")
    if prod in ("country-brief", "quarterly"):
        add("sanctions-wording", "PASS" if re.search(r"(나라|국가) 전체 제재를 뜻하지 않", body) else "FAIL", "제재 = 명단 등재 건수 문구")
    return r

if __name__ == "__main__":
    res = check(open(sys.argv[1], encoding="utf8").read())
    if "--json" in sys.argv: print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        for x in res: print(f"{x['result']:8} {x['id']:18} {x['why']}")
    n = {k: sum(1 for x in res if x["result"] == k) for k in ("PASS", "FAIL", "UNKNOWN")}
    print("summary", n); sys.exit(1 if n["FAIL"] else 0)
