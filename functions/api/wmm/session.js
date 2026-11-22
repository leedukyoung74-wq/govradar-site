import { verify, json } from "../../_lib/common.js";
export const onRequestGet = async ({ request }) => {
  const u = await verify(request);
  return u ? json({ authenticated: true, uid: u.sub, email: u.email || "" }) : json({ authenticated: false, error: "google_login_required" }, 401);
};
