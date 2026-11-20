"""Free, source-backed *public procurement buyer* index.

Public procuring entities appearing in official tenders are NOT verified
commercial importers or contactable sales leads. Never infer emails or scrape
personal contacts. Index creation is deterministic, offline and read-only.
"""
import argparse
import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from deadline import is_listed_open

# Only existing official notice provider hosts. Third-party/redirect pages
# must not be relabelled as authoritative government proof.
OFFICIAL_HOSTS = {
    "World Bank": {"projects.worldbank.org"},
    "EU TED": {"ted.europa.eu"},
    "UK Find a Tender": {"www.find-tender.service.gov.uk"},
    "UK Contracts Finder": {"www.contractsfinder.service.gov.uk"},
    "Prozorro (Ukraine)": {"prozorro.gov.ua"},
    "SAM.gov (US)": {"sam.gov", "www.sam.gov"},
}
CLOSED = {"cancelled", "canceled", "closed", "withdrawn", "expired", "deleted"}

def safe_official_notice(notice):
    source=notice.get("source")
    url=notice.get("url")
    if source not in OFFICIAL_HOSTS or not isinstance(url,str):
        return False
    if any(c in url for c in ("\\n","\\r","\\t")): return False
    try:
        u=urlsplit(url)
        return (u.scheme=="https" and u.hostname in OFFICIAL_HOSTS[source]
                and u.username is None and u.password is None and u.port is None
                and u.fragment=="" and bool(u.path and u.path!="/"))
    except (ValueError,TypeError):
        return False

def normalize_organisation(text):
    if not isinstance(text,str): return ""
    s=re.sub(r"\\s+"," ",text).strip()
    # Avoid indexing obvious direct personal contact or raw phone/email fields.
    if not (4<=len(s)<=160) or "@" in s or re.search(r"\\+?\\d[\\d\\s()-]{7,}\\d",s):
        return ""
    return s

def build(items,now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:raise ValueError("UTC-aware time required")
    index={}
    for item in items:
        if not isinstance(item,dict) or not safe_official_notice(item):
            continue
        iso=item.get("iso")
        title=item.get("title")
        buyer=normalize_organisation(item.get("buyer"))
        if not (isinstance(iso,str) and re.fullmatch(r"[A-Z]{2}",iso)
                and buyer and isinstance(title,str) and title.strip()
                and is_listed_open(item,now)
                and str(item.get("status","")).lower() not in CLOSED):
            continue
        key=(iso,re.sub(r"\\s+"," ",buyer).casefold())
        result=index.setdefault(key,{"country_iso":iso,"procurement_entity":buyer,
                                   "source_verified_notice_count":0,"notices":[]})
        evidence={"title":title[:220],"deadline":item.get("deadline",""),
                  "notice_url":item["url"],"source":item["source"]}
        if any(x["notice_url"]==evidence["notice_url"] for x in result["notices"]):
            continue
        result["source_verified_notice_count"]+=1
        result["notices"].append(evidence)
    rows=sorted(index.values(),key=lambda x:(-x["source_verified_notice_count"],x["country_iso"],x["procurement_entity"].casefold()))
    for row in rows:
        row["notices"]=sorted(row["notices"],key=lambda x:x["deadline"])[:5]
    return {"schema_version":1,"generated_at_utc":now.isoformat(),
            "type":"source_backed_public_procurement_organisations",
            "not_commercial_buyer_directory":True,
            "disclaimer_ko":"공식 공개 조달공고의 발주기관 목록입니다. 상업 수입 바이어·거래 의사·연락처 또는 현재 입찰 가능 상태를 보증하지 않습니다. 원문에서 재확인하세요.",
            "disclaimer_en":"Procuring entities named in official public notices; NOT a verified importer, sales-buyer or contact directory. Confirm notice status with the original issuer.",
            "organisations":rows,
            "country_count":len({x["country_iso"] for x in rows})}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--out",required=True)
    opt=ap.parse_args()
    document=json.loads(Path(opt.source).read_text(encoding="utf-8"))
    items=document.get("items")
    if not isinstance(items,list):raise SystemExit("No validated tender items; refusing to invent buyers")
    result=build(items)
    out=Path(opt.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    print(json.dumps({"organisations":len(result["organisations"]),"countries":result["country_count"],
                      "output":str(out),"public_procurement_not_commercial_buyers":True},ensure_ascii=False))
if __name__=="__main__":
    main()
