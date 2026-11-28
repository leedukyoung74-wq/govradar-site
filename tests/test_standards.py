import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import qa_deliverable as Q

GOOD = """---
product: fit-review
client: 예시 주식회사
target: UA-2026-10-28-009474-a · 지토미르주 · 우크라이나
date: 2026-11-16
data_as_of: 2026-11-16
reviewer: 홍길동
version: 1
---
# 입찰 적합도 검토
## 1. 결론
조건부 권장 [1]
## 2. 공고 요약
| 추정 금액 | UAH 860,831,483 [1] |
| 마감 | 2026-11-23 09:00 (UTC+02:00) [1] |
## 3. 참여 자격 대조표
## 4. 필요 서류
## 5. 현지 파트너 필요 여부
## 6. 일정
## 7. 위험
- 제재 명단(UN·OFAC·EU·UK) 확인 결과: 등재 없음 [2]
## 8. 다음 행동
## 9. 출처
1. 공고 원문 — https://prozorro.gov.ua/tender/UA-2026-10-28-009474-a (T1)
2. OFAC 검색 — https://sanctionssearch.ofac.treas.gov/ (T1)
---
AI 작성 + 사람 검수 · 검수자 홍길동 · 2026-11-16
공개 자료 기준이며, 계약·투자 전에는 원문을 확인하세요. 문의 leedukyoung74@gmail.com
"""

def res(t): return {x["id"]: x["result"] for x in Q.check(t)}

class Standards(unittest.TestCase):
    def test_good_passes(self):
        r = res(GOOD); self.assertNotIn("FAIL", r.values(), r); self.assertNotIn("UNKNOWN", r.values(), r)

    def test_banned_content(self):
        self.assertEqual(res(GOOD + "\n연락 010-1234-5678")["banned"], "FAIL")
        self.assertEqual(res(GOOD + "\n서울 서초구 사무실")["banned"], "FAIL")
        self.assertEqual(res(GOOD + "\nceo@example.com")["contact"], "FAIL")

    def test_missing_label_and_order(self):
        self.assertEqual(res(GOOD.replace("AI 작성 + 사람 검수", ""))["label"], "FAIL")
        swapped = GOOD.replace("## 1. 결론", "## 1. 임시").replace("## 8. 다음 행동", "## 8. 다음 행동\n## 결론")
        self.assertEqual(res(swapped)["sections"], "FAIL")

    def test_deadline_needs_timezone_and_iso_dates(self):
        self.assertEqual(res(GOOD.replace(" (UTC+02:00)", ""))["deadline-timezone"], "FAIL")
        self.assertEqual(res(GOOD + "\n마감 11/23/2026")["dates"], "FAIL")

    def test_unsourced_money_is_unknown(self):
        self.assertEqual(res(GOOD.replace("| UAH 860,831,483 [1] |", "| UAH 860,831,483 |"))["numbers-sourced"], "UNKNOWN")

    def test_templates_are_unfilled(self):
        d = os.path.join(os.path.dirname(__file__), "..", "docs", "standards", "templates")
        for f in os.listdir(d):
            self.assertEqual(res(open(os.path.join(d, f), encoding="utf8").read())["placeholders"], "FAIL", f)
