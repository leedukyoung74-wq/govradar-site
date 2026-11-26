#!/usr/bin/env python3
"""Read-only Cloudflare Pages production deployment preflight for WMM GOV RADAR.

Requires CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN in environment.
Only issues GET requests. Does not print credentials or raw API response.
DOES NOT deploy, modify DNS, mutate branches or charge anything.
"""
import json
import os
import sys
import urllib.error
import urllib.request

PROJECT = "wmm-radar"
HOSTNAME = "radar.wmm-hoa.com"

def summarize(project):
    source = project.get("source") or {}
    source_config = source.get("config") or {}
    build = project.get("build_config") or {}
    latest = project.get("latest_deployment") or {}
    deployment = latest.get("deployment_trigger") or {}
    owner = source_config.get("owner") or ""
    repo_name = source_config.get("repo_name") or ""
    repo = (owner + "/" + repo_name).strip("/")
    production = ((project.get("deployment_configs") or {}).get("production") or {})
    d1 = production.get("d1_databases") or {}
    # Only the binding presence is reported. Never serialize D1 IDs, values or tokens.
    binding = d1.get("GV_DB") if isinstance(d1,dict) else None
    d1_configured = bool(isinstance(binding,dict) and binding.get("id"))
    result = {
        "production_d1_gv_db_binding_present": d1_configured,
        "project_name": project.get("name"),
        "production_branch": project.get("production_branch") or None,
        "source_type": source.get("type") or "direct_upload_or_unspecified",
        "repository": repo or None,
        "build_command": build.get("build_command") or None,
        "destination_dir": build.get("destination_dir") or None,
        "root_dir": build.get("root_dir") or None,
        "latest_deployment_id": latest.get("id"),
        "latest_deployment_environment": latest.get("environment"),
        "latest_deployment_trigger": deployment.get("type"),
        "hostname_matches": HOSTNAME in (project.get("domains") or []),
        "safe_to_deploy_automatically": False,
    }
    issues = []
    if result["project_name"] != PROJECT: issues.append("Unexpected Cloudflare Pages project.")
    if not result["hostname_matches"]: issues.append("Custom domain not confirmed in Pages project.")
    if result["repository"] not in (None,"leedukyoung74-wq/govradar-site"):
        issues.append("Connected repository differs from WMM GOV RADAR.")
    if result["source_type"] not in ("github","direct_upload_or_unspecified"):
        issues.append("Unknown or unsupported source type.")
    if result["production_branch"] != "live":
        issues.append("Production branch is not the verified live branch; do not change it without review.")
    if result["source_type"] == "github":
        if result["repository"] != "leedukyoung74-wq/govradar-site":
            issues.append("GitHub source repository is not confirmed.")
        # The deployed site is a generated static 'live' tree, NOT the src build.
        # Avoid imposing an obsolete src build command/directory on production.
        if result["build_command"] == "python3 build.py --base https://radar.wmm-hoa.com":
            issues.append("Unexpected source-branch build command on live; confirm complete site output.")
        if result["destination_dir"] == "dist":
            issues.append("Unexpected source-build destination on live; verify generated tree and Functions.")
    else:
        issues.append("Direct Upload or unspecified project: DO NOT assume git push triggers a website deploy.")
    if not result["production_d1_gv_db_binding_present"]:
        issues.append("Production GV_DB D1 binding absent or not confirmed from project read-only metadata.")
    issues.append("A binding shown in configuration is NOT proof the requests table exists or D1 writes succeed.")
    issues.append("Manual owner sign-off and production rollback target are required before publishing.")
    return result, issues

def main():
    account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    token = os.getenv("CLOUDFLARE_API_TOKEN")
    if not account or not token:
        print(json.dumps({"status":"BLOCKED","reason":"Cloudflare read-only credentials not configured; no requests sent."}))
        return 2
    if not all(c.isalnum() or c in "_-" for c in account):
        print(json.dumps({"status":"BLOCKED","reason":"Invalid account ID format."}))
        return 2
    url = "https://api.cloudflare.com/client/v4/accounts/{}/pages/projects/{}".format(account, PROJECT)
    req = urllib.request.Request(url, headers={
        "Authorization":"Bearer "+token, "Accept":"application/json",
        "User-Agent":"WMM-GOV-RADAR-ReadOnlyPreflight/1.0",
    },method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            payload=json.load(response)
    except urllib.error.HTTPError as exc:
        print(json.dumps({"status":"BLOCKED","reason":"Cloudflare API request failed","http_status":exc.code}))
        return 2
    except Exception:
        print(json.dumps({"status":"BLOCKED","reason":"Unable to read Cloudflare API"}))
        return 2
    if not payload.get("success"):
        print(json.dumps({"status":"BLOCKED","reason":"Cloudflare API did not confirm success"}))
        return 2
    output, issues=summarize(payload.get("result") or {})
    print(json.dumps({"status":"REVIEW_REQUIRED" if issues else "CHECKED",
      "project":output,"deployment_blockers":issues},ensure_ascii=False,indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
