#!/usr/bin/env python3
"""Fail-closed check for accidental synthetic fixtures in public release assets.

This does not authenticate a notice or publish anything. It checks local files.
Run after Cloudflare variant generation but before touching the live git worktree.
"""
import argparse
import json
from pathlib import Path

MARKERS=(b"WMM_QA_SYNTHETIC_",b"wmm-qa-future",b"wmm-qa-past")
def check_release_assets(root):
    root=Path(root)
    issues=[]
    if not root.is_dir():
        return {"passed":False,"issues":[{"code":"MISSING_BUILD_OUTPUT","path":str(root)}],"filesScanned":0}
    files=0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in (".html",".json",".js",".xml"):
            continue
        files+=1
        try:
            raw=p.read_bytes()
        except OSError:
            issues.append({"code":"UNREADABLE_OUTPUT","path":str(p.relative_to(root))})
            continue
        if any(marker in raw for marker in MARKERS):
            issues.append({"code":"SYNTHETIC_FIXTURE_IN_PUBLIC_OUTPUT","path":str(p.relative_to(root))})
    if files==0:
        issues.append({"code":"EMPTY_BUILD_OUTPUT","path":str(root)})
    return {"passed":not issues,"filesScanned":files,"issues":issues,
            "note":"No synthetic fixture found does not imply fresh official notices or adequate country coverage."}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("directory",help="Local built public root, such as cf/public")
    args=parser.parse_args()
    result=check_release_assets(args.directory)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["passed"] else 1)
