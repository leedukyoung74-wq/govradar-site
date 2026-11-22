import { FIREBASE, json } from "../../_lib/common.js";
export const onRequestGet = () => json({ enabled: true, firebase: FIREBASE, vworldAvailable: false });
