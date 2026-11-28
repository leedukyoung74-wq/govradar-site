// 결제 상품표 — 실제 결제금액(서버가 승인 금액 검증)
// 회원 가격 원칙(대표 결정 2026-11-22, 재확인 2026-11-28): 월 20,000원 / 연 200,000원 VAT 별도 → 부가세 10% 포함 결제 22,000원 / 220,000원
export const PRODUCTS = {
  "analysis-month": { name: "GOV RADAR 분석 회원 1개월", amount: 22000 },
  "analysis-year":  { name: "GOV RADAR 분석 회원 12개월", amount: 220000 }
};
