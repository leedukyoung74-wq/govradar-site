#!/usr/bin/env python3
"""Stage a NEVER-DEPLOYED selective WMM resilience overlay over a live snapshot.

This script reads the existing Cloudflare live/public tree and a canonical
src->dist->cf/public generated tree. It writes a third *preview only* folder.
It never invokes git, Cloudflare, payments, email, or a remote API.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

LANGS=("ko","en","es","fr","ar","vi","id")
ALLOW=[
    *(f"{lang}/{page}/index.html" for lang in LANGS for page in ("prepare","resilience")),
    "assets/wmm-resilience.js",
    "assets/wmm-resilience.css",
    "data/wmm-food-country-profiles.json",
    "data/wmm-food-primary-guidance-reviewed.json",
]
PROTECTED=(
    "_routes.json","_headers","_redirects",
    "assets/auth.js","assets/site.js",
    "ko/index.html","en/index.html",
    "data/countries.json","data/regions.json",
)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def stage(generated:Path, current:Path, output:Path):
    generated=generated.resolve()
    current=current.resolve()
    output=output.resolve()
    if not current.is_dir() or not generated.is_dir():
        raise RuntimeError("Missing live/public snapshot or generated Cloudflare site")
    if output==current or output==generated or current in output.parents or generated in output.parents:
        raise RuntimeError("Refusing to modify source or existing live trees")
    if output.exists(): raise RuntimeError("Output must be new; refusing to overwrite prior evidence")
    old_files={str(p.relative_to(current)):sha(p) for p in current.rglob("*") if p.is_file()}
    for rel in PROTECTED:
        if rel not in old_files: raise RuntimeError("Missing protected live file: "+rel)
    if len(ALLOW)!=18: raise RuntimeError("Unexpected overlay allowlist length")
    for rel in ALLOW:
        p=generated/rel
        if not p.is_file(): raise RuntimeError("Missing required generated file: "+rel)
        if rel.endswith("/prepare/index.html"):
            page=p.read_text(encoding="utf-8")
            if "106.4L" not in page or "84L" in page:
                raise RuntimeError("Unsafe legacy water baseline in "+rel)
        if rel.endswith("/resilience/index.html"):
            page=p.read_text(encoding="utf-8")
            if "noindex, nofollow" not in page or "wmm-resilience" not in page:
                raise RuntimeError("Missing review/launch guards "+rel)
    guides=json.loads((generated/"data/wmm-food-primary-guidance-reviewed.json").read_text("utf-8"))
    food=json.loads((generated/"data/wmm-food-country-profiles.json").read_text("utf-8"))
    if {x["iso"] for x in guides["countries"]}!={"KR","JP","US"}:
        raise RuntimeError("Official general guidance records changed unexpectedly")
    if len(food)!=193 or any(x["local_official_guidance_verified"] or x["retail_availability_verified"] or x["shelf_life_verified"] for x in food):
        raise RuntimeError("Country-product evidence claims are not approved")
    shutil.copytree(current,output)
    changes=[]
    for rel in ALLOW:
        dest=output/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        previous=sha(dest) if dest.exists() else None
        shutil.copy2(generated/rel,dest)
        changes.append({"path":rel,"previous_sha256":previous,"staged_sha256":sha(dest)})
    for rel,digest in old_files.items():
        if rel not in ALLOW and sha(output/rel)!=digest:
            raise RuntimeError("Protected live file modified unexpectedly: "+rel)
    for rel in PROTECTED:
        if sha(output/rel)!=old_files[rel]:
            raise RuntimeError("Protected auth/core/route file changed: "+rel)
    staged_files={str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
    if not set(old_files).issubset(staged_files):
        raise RuntimeError("Current live files were deleted during review staging")
    result={
        "type":"WMM_SELECTIVE_LIVE_OVERLAY_REVIEW",
        "deployable":False,
        "publication_performed":False,
        "live_files_retained":len(old_files),
        "changed_or_added_files":len(changes),
        "protected_live_paths":list(PROTECTED),
        "not_included_review_routes":["quality/","review/"],
        "verified_country_products":0,
        "file_changes":changes,
    }
    report=output.parent/"live-overlay-review-manifest.json"
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--generated",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    summary=stage(args.generated,args.live,args.out)
    print("PASS: staged review only",summary["changed_or_added_files"],"allowlisted files; originals untouched")
