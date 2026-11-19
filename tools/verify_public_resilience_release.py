#!/usr/bin/env python3
"""Read-only public-site version check for GOV RADAR. No auth, no deployment.
Exit 0 if current live version matches release expectations; 2 otherwise.
"""
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASES = ("https://radar.wmm-hoa.com","https://wmm-radar.pages.dev")
LANGS=("ko","en","es","fr","ar","vi","id")
TESTS = [
    *((f"/{lang}/resilience/","wmm-resilience") for lang in LANGS),
    *((f"/{lang}/prepare/","106.4L") for lang in LANGS),
    ("/ko/ready/","재난 대비센터"),
    ("/en/ready/","Preparedness"),
    ("/assets/wmm-resilience.js","countrySourceTitle"),
    ("/assets/wmm-resilience.css",".wmm-rs"),
    ("/data/wmm-food-country-profiles.json",'"local_official_guidance_verified"'),
    ("/data/wmm-food-primary-guidance-reviewed.json",'"product_review_status"'),
    ("/data/countries.json",'"iso"'),
    ("/data/regions.json",'"code"'),
]

def check(url, needle):
    request = urllib.request.Request(url, headers={
        "User-Agent":"WMM-GOV-RADAR-ReadOnly-Version-Sentinel/1.0",
        "Cache-Control":"no-cache",
    })
    try:
        with urllib.request.urlopen(request, timeout=14) as response:
            body=response.read(1500000).decode("utf-8","replace")
            result={"http_status":response.status,
                    "has_release_marker":needle in body,
                    "outdated_water_marker":"84L" in body if "/prepare/" in url else None}
            if url.endswith("/data/wmm-food-country-profiles.json"):
                profiles=json.loads(body)
                product_claims=sum(bool(x.get("local_official_guidance_verified") or
                    x.get("retail_availability_verified") or x.get("shelf_life_verified")) for x in profiles)
                result["profile_count"]=len(profiles)
                result["product_claim_count"]=product_claims
                result["has_release_marker"]=result["has_release_marker"] and len(profiles)==193 and product_claims==0
            elif url.endswith("/data/wmm-food-primary-guidance-reviewed.json"):
                guidance=json.loads(body)
                codes={x["iso"] for x in guidance.get("countries",[])}
                result["guidance_countries"]=sorted(codes)
                result["has_release_marker"]=result["has_release_marker"] and codes=={"KR","JP","US"}
            elif url.endswith("/data/countries.json"):
                result["has_release_marker"]=result["has_release_marker"] and len(json.loads(body))==193
            elif url.endswith("/data/regions.json"):
                result["has_release_marker"]=result["has_release_marker"] and len(json.loads(body))==23
    except urllib.error.HTTPError as exc:
        result={"http_status":exc.code,"has_release_marker":False,
                "outdated_water_marker":None}
    except Exception as exc:
        result={"http_status":None,"has_release_marker":False,
                "outdated_water_marker":None,
                "error_type":type(exc).__name__}
    result["ready"]=result["http_status"]==200 and result["has_release_marker"] and not result["outdated_water_marker"]
    return result

def main():
    details=[]
    for base in BASES:
        for path, marker in TESTS:
            item={"origin":base,"path":path,**check(base+path,marker)}
            details.append(item)
    summary={
        "checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "mode":"read_only",
        "deployment_performed":False,
        "ready_count":sum(int(x["ready"]) for x in details),
        "total_checks":len(details),
        "production_new_release_confirmed":all(x["ready"] for x in details),
        "checks":details,
    }
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0 if summary["production_new_release_confirmed"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
