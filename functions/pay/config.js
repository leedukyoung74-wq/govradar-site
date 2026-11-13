import { PRODUCTS } from "./_products.js";
// 결제창에 필요한 공개 키(클라이언트 키)만 돌려줌. 키가 없으면 '준비 중'.
export async function onRequestGet({ env }) {
  const ck = env.TOSS_CLIENT_KEY || "";
  return Response.json({ enabled: !!(ck && env.TOSS_SECRET_KEY), clientKey: ck, products: PRODUCTS },
    { headers: { "cache-control": "no-store" } });
}
