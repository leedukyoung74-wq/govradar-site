import { verify, json } from "../../_lib/common.js";
// V-World satellite tiles are not connected (same as before the move: vworldAvailable false).
export const onRequestGet = async ({ request }) => (await verify(request)) ? json({ enabled: false }) : json({ error: "google_login_required" }, 401);
