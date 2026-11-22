import { json } from "../../_lib/common.js";
export const onRequestGet = () => json({ error: "tiles_not_connected" }, 503);
