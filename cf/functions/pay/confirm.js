import { PRODUCTS } from "./_products.js";
// 결제 승인: 금액 위변조 검사 → 토스페이먼츠 승인 API → 대표에게 주문 알림(Netlify Forms)
export async function onRequestPost({ request, env }) {
  const j = (o, s = 200) => Response.json(o, { status: s, headers: { "cache-control": "no-store" } });
  if (!env.TOSS_SECRET_KEY) return j({ ok: false, code: "NOT_READY", message: "결제 준비 중입니다." }, 503);
  let b; try { b = await request.json(); } catch { return j({ ok: false, code: "BAD_REQUEST" }, 400); }
  const { paymentKey, orderId, amount, item, email } = b || {};
  const p = PRODUCTS[item];
  if (!p || !paymentKey || !orderId || Number(amount) !== p.amount || !String(orderId).startsWith(item + "-"))
    return j({ ok: false, code: "AMOUNT_MISMATCH", message: "결제 정보가 맞지 않습니다." }, 400);
  const r = await fetch("https://api.tosspayments.com/v1/payments/confirm", {
    method: "POST",
    headers: { "authorization": "Basic " + btoa(env.TOSS_SECRET_KEY + ":"), "content-type": "application/json", "idempotency-key": orderId },
    body: JSON.stringify({ paymentKey, orderId, amount: p.amount })
  });
  const t = await r.json().catch(() => ({}));
  if (!r.ok) return j({ ok: false, code: t.code || "CONFIRM_FAILED", message: t.message || "결제 승인에 실패했습니다." }, 400);
  // 대표 알림: 기존 '주문(order)' 양식으로 접수 → Netlify 알림 메일
  const f = new URLSearchParams({ "form-name": "order", hp: "", name: b.name || "결제 고객",
    email: email || t.customerEmail || "", product: "[결제완료] " + p.name,
    need: `결제 완료 · ${p.name} · ${p.amount}원 · 주문번호 ${orderId} · 승인 ${t.approvedAt || ""} · 회원 코드 발급 필요`,
    lang: "ko", privacy_agree: "yes" });
  await fetch("https://wmm-govradar.netlify.app/", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: f.toString() }).catch(() => {});
  return j({ ok: true, item: p.name, amount: p.amount, orderId, method: t.method || "", receipt: (t.receipt && t.receipt.url) || "" });
}
