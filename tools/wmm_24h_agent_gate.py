#!/usr/bin/env python3
"""Strict approval and 24-hour window gate for ACTUAL coding agent (not review-only).

This script does not invoke paid APIs. It validates explicit operational flags.
"""
import datetime as dt
import json
import os
from wmm_24h_review_cycle import evaluate

def coding_gate(event, enabled, budget_approved, start, now):
    if event not in ("schedule","workflow_dispatch"):
        return {"run":False,"reason":"unsupported_event","cycle":None}
    if str(budget_approved).strip().lower()!="true":
        return {"run":False,"reason":"budget_approval_required","cycle":None}
    # Even manual dispatch MUST satisfy strict schedule 24-hour window.
    return evaluate("schedule",enabled,start,now)

if __name__=="__main__":
    result=coding_gate(os.getenv("GITHUB_EVENT_NAME",""),
                       os.getenv("WMM_AUTOBUILD_ENABLED",""),
                       os.getenv("WMM_AUTOBUILD_COST_APPROVED",""),
                       os.getenv("WMM_AUTOBUILD_START_UTC",""),
                       dt.datetime.now(dt.timezone.utc))
    print(json.dumps(result,ensure_ascii=False))
    out=os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out,"a",encoding="utf8") as f:
            f.write("run="+("true" if result["run"] else "false")+"\n")
            f.write("cycle="+(str(result["cycle"]) if result["cycle"] is not None else "")+"\n")
            f.write("reason="+result["reason"]+"\n")
