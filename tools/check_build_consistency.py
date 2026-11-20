#!/usr/bin/env python3
"""Read-only staging build consistency check, independent of file timestamps.

The generated public country flags, country profile files, localized pages and
opportunity counts must reflect the same local export inputs. No data is written.
This is NOT a primary-source or real-time tender validity verification.
"""
import argparse
import json
from pathlib import Path

LANGS=("ko","en","es","fr","ar","vi","id")
KINDS=("biz","tenders","oda")

def inspect_build(export_dir="export/countries",public_dir="dist",*,min_researched=1):
    src=Path(export_dir)
    out=Path(public_dir)
    failures=[]
    if not out.is_dir():
        return {"passed":False,"errors":["MISSING_OUTPUT_ROOT"],"researched":0}
    countries_path=out/"data"/"countries.json"
    opps_path=out/"data"/"opps.json"
    try:
        countries=json.loads(countries_path.read_text(encoding="utf8"))
        opps=json.loads(opps_path.read_text(encoding="utf8"))
        if not isinstance(countries,list) or not isinstance(opps,dict) or not isinstance(opps.get("items"),list):
            raise ValueError("malformed output schema")
        by_country={x["iso"]:x for x in countries if isinstance(x,dict) and isinstance(x.get("iso"),str)}
        if len(by_country)!=len(countries):
            failures.append("DUPLICATE_OR_INVALID_PUBLISHED_COUNTRIES")
    except (OSError,ValueError,KeyError,TypeError) as error:
        return {"passed":False,"errors":["MISSING_OR_INVALID_OUTPUT_JSON",str(error)[:120]],"researched":0}
    researched=set()
    expected_opps=0
    source_count=0
    for path in sorted(src.glob("*.json")):
        try:
            data=json.loads(path.read_text(encoding="utf8"))
            if not isinstance(data,dict) or ("iv" in data and "c" in data):
                failures.append("UNREADABLE_OR_ENCRYPTED_EXPORT:"+path.name)
                continue
            iso=data.get("id") or path.stem[:2]
            payload=data.get("data",data)
            if not isinstance(payload,dict) or iso not in by_country:
                failures.append("INVALID_OR_UNPUBLISHED_EXPORT:"+path.name)
                continue
            source_count+=1
            done=bool(payload.get("agenda"))
            if bool(by_country[iso].get("done"))!=done:
                failures.append("STALE_COUNTRY_DONE_FLAG:"+iso)
            if not done:
                continue
            researched.add(iso)
            slug=by_country[iso].get("slug")
            if not isinstance(slug,str) or not slug:
                failures.append("MISSING_COUNTRY_SLUG:"+iso)
                continue
            country_data=out/"data"/"c"/(iso+".json")
            if not country_data.is_file():
                failures.append("MISSING_PUBLISHED_COUNTRY_DATA:"+iso)
            for lang in LANGS:
                page=out/lang/slug/"index.html"
                if not page.is_file():
                    failures.append("MISSING_LOCALIZED_COUNTRY_PAGE:"+lang+":"+iso)
            for kind in KINDS:
                arr=payload.get(kind) or []
                if not isinstance(arr,list):
                    failures.append("INVALID_SOURCE_OPPORTUNITIES:"+iso+":"+kind)
                    continue
                expected_opps+=sum(isinstance(x,dict) for x in arr)
        except (OSError,ValueError,TypeError) as error:
            failures.append("INVALID_EXPORT:"+path.name+":"+str(error)[:70])
    published_done={x for x,c in by_country.items() if c.get("done")}
    if researched!=published_done:
        failures.append("PUBLISHED_RESEARCH_COUNTRY_SET_MISMATCH")
    if len(opps["items"])!=expected_opps:
        failures.append("PUBLISHED_OPPORTUNITY_COUNT_MISMATCH")
    if len(researched)<min_researched:
        failures.append("INSUFFICIENT_RESEARCHED_EXPORTS")
    return {"classification":"OFFLINE_BUILD_INPUT_OUTPUT_CONSISTENCY_ONLY",
            "passed":not failures,"sourceFiles":source_count,
            "researched":len(researched),"publishedResearched":len(published_done),
            "expectedOpportunityItems":expected_opps,"publishedOpportunityItems":len(opps["items"]),
            "errors":failures,
            "caveat":"Consistency does not imply source agency verification, freshness, deadline amendments, or production deployment."}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--export-dir",default="export/countries")
    ap.add_argument("--public-dir",default="dist")
    ap.add_argument("--min-researched",type=int,default=1)
    args=ap.parse_args()
    if args.min_researched<0:
        ap.error("--min-researched must be nonnegative")
    result=inspect_build(args.export_dir,args.public_dir,min_researched=args.min_researched)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["passed"] else 1)
