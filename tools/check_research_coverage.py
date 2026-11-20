#!/usr/bin/env python3
"""Read-only coverage audit: researched country != file present.
Encrypted vault files are intentionally never decoded here.
"""
import argparse
import datetime
import json
from pathlib import Path

def check_coverage(export_dir, meta_path, minimum=0):
    countries=json.loads(Path(meta_path).read_text(encoding="utf-8"))
    known={x["iso"] for x in countries if isinstance(x,dict) and isinstance(x.get("iso"),str)}
    researched=set()
    present=set()
    issues=[]
    for fp in sorted(Path(export_dir).glob("*.json")):
        try:
            doc=json.loads(fp.read_text(encoding="utf-8"))
            if not isinstance(doc,dict) or ("iv" in doc and "c" in doc):
                issues.append({"path":fp.name,"problem":"UNSUPPORTED_OR_ENCRYPTED_EXPORT"})
                continue
            iso=doc.get("id") or fp.stem[:2]
            payload=doc.get("data",doc)
            if iso not in known:
                issues.append({"path":fp.name,"problem":"UNKNOWN_COUNTRY_ISO"})
                continue
            if not isinstance(payload,dict):
                issues.append({"path":fp.name,"problem":"INVALID_COUNTRY_DATA"})
                continue
            present.add(iso)
            if payload.get("agenda"):
                researched.add(iso)
        except (ValueError,OSError,UnicodeError) as exc:
            issues.append({"path":fp.name,"problem":"MALFORMED_EXPORT","detail":str(exc)[:100]})
    missing=sorted(known-present)
    pass_status=len(researched)>=minimum and not issues
    return {"classification":"OFFLINE_COVERAGE_AUDIT_NOT_OFFICIAL_VERIFICATION",
            "presentCountries":len(present),"researchedCountries":len(researched),
            "totalKnownCountries":len(known),"minimumResearched":minimum,
            "missingCountryCodes":missing,"issues":issues,"passed":pass_status,
            "caveat":"Country agenda is a local completion signal; it does not prove a tender is official or current."}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--export-dir",default="export/countries")
    p.add_argument("--metadata",default="src/countries_meta.json")
    p.add_argument("--min-researched",type=int,default=1)
    a=p.parse_args()
    if a.min_researched<0:
        p.error("minimum must be >= 0")
    result=check_coverage(a.export_dir,a.metadata,a.min_researched)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["passed"] else 1)
