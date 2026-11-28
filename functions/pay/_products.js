// 결제 상품표 — 고객에게 표시된 최종 결제금액(VAT 포함), 서버가 승인 금액 검증
// 회원 가격 원칙: 월 20,000원 / 연 200,000원. 별도 VAT 10%를 추가 청구하지 않음.
export const PRODUCTS = {
  "analysis-month": { name: "GOV RADAR 분석 회원 1개월", amount: 20000 },
  "analysis-year":  { name: "GOV RADAR 분석 회원 12개월", amount: 200000 }
};
