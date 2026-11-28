#!/usr/bin/env python3
"""External, public-URL GET-only customer readiness evidence. NEVER POST/charge."""
import concurrent.futures as futures
import datetime as dt
import html
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
import sys

LANGS=("ko","en","es","fr","ar","vi","id")
BASE="https://radar.wmm-hoa.com"
PUBLIC={
 "ko":"VAT 포함","en":"VAT incl.","es":"IVA incluido","fr":"TTC",
 "ar":"شامل الضريبة","vi":"đã gồm VAT","id":"termasuk PPN"
}
OLD={
 "ko":"VAT 별도","en":"VAT excl.","es":"sin IVA","fr":"(HT)",
 "ar":"دون الضريبة","vi":"chưa VAT","id":"belum PPN"
}
CHECKS=[("radar_home_"+l,BASE+"/"+l+"/?stay=1") for l in LANGS]+[
 ("support_hub",BASE+"/support/?lang=ko"),
 ("form_get",BASE+"/nfform"),
 ("payment_config",BASE+"/pay/config"),
 ("wmm_root","https://www.wmm-hoa.com/"),
 ("wmm_services","https://www.wmm-hoa.com/home"),
 ("gcsme_kr_contact","https://www.gcsme.kr/contact"),
 ("gcsme_uk_partner","https://gcsme.club/partner-with-gcsme")
]
HOSTS={"radar.wmm-hoa.com","www.wmm-hoa.com","wmm-hoa.com",
       "gcsme.kr","www.gcsme.kr","gcsme.club","www.gcsme.club"}
MAX_BYTES=350_000

def read_one(row):
    key,url=row
    check={"name":key,"url":url,"kind":"UNKNOWN","http_status":None,"notes":[]}
    req=urllib.request.Request(url,headers={
        "User-Agent":"WMM-customer-check-GET-only/1.0",
        "Accept":"text/html,application/json",
        "Cache-Control":"no-cache"
    },method="GET")
    def evaluate(response):
        status=response.status
        final=urllib.parse.urlsplit(response.geturl())
        check["http_status"]=status
        if final.scheme!="https" or final.hostname not in HOSTS:
            check["kind"]="UNEXPECTED_REDIRECT"
            return check
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            check["kind"]="TOO_LARGE_TO_VERIFY"
            return check
        body=raw.decode("utf-8","replace")
        if key.startswith("radar_home_"):
            lang=key.split("_")[-1]
            # Look only at the M1 selector, never confuse B2B VAT-excluded services.
            anchor=re.search(r'<input\b[^>]*value="Analysis membership"[^>]*>[\s\S]{0,450}?</label>',body,re.I)
            if not anchor:
                check["kind"]="M1_SELECTOR_NOT_FOUND"
            else:
                option=html.unescape(anchor.group(0))
                vat=PUBLIC[lang] in option and OLD[lang] not in option
                check["kind"]="M1_VAT_CORRECT" if vat else "M1_VAT_INCORRECT"
            return check
        if key=="support_hub":
            check["kind"]="FAQ_PUBLISHED" if 'id="faqs"' in body and "EXTRA_FAQ" in body else "FAQ_NOT_VERIFIED"
        elif key=="form_get":
            check["kind"]="FORM_GET_METHOD_OK" if status==405 and "POST required" in body else "FORM_GET_NOT_VERIFIED"
        elif key=="payment_config":
            try:
                obj=json.loads(body)
                data=obj.get("products") or {}
                am=data.get("analysis-month") or {}
                ay=data.get("analysis-year") or {}
                right=am.get("amount")==20000 and ay.get("amount")==200000
                enabled=obj.get("enabled") is True
                check["kind"]="PAYMENT_CONFIG_SAFE" if right and not enabled else "PAYMENT_CONFIG_REVIEW"
                check["public_amounts_correct"]=right
                check["monthly_price_krw"]=am.get("amount") if isinstance(am.get("amount"),int) else None
                check["annual_price_krw"]=ay.get("amount") if isinstance(ay.get("amount"),int) else None
                check["live_checkout_enabled"]=enabled
                # NEVER store or print a client key from provider config.
            except (ValueError,TypeError,AttributeError):
                check["kind"]="PAYMENT_CONFIG_UNREADABLE"
        elif key.startswith("wmm_"):
            if re.search(r"(?:20,000(?:원)?|200,000(?:원)?)[^<>]{0,100}VAT\\s*별도|VAT\\s*별도[^<>]{0,100}(?:20,000(?:원)?|200,000(?:원)?)",body):
                check["kind"]="WMM_PRICE_VAT_CONTRADICTION"
            elif "20,000" in body:
                check["kind"]="WMM_PRICE_PRESENT_REVIEW_TAX_CONTEXT"
            else:check["kind"]="WMM_SITE_REACHABLE_RENDER_CHECK_NEEDED"
        elif key=="gcsme_kr_contact":
            old="wmm-online-office.bronzegoby17.chatgpt.site" in body
            check["kind"]="GCSME_KR_OLD_WMM_LINK_PRESENT" if old else "GCSME_KR_CONTACT_REVIEW"
            check["links_old_host"]=old
        else:check["kind"]="GCSME_UK_REACHABLE_FORM_NOT_SUBMITTED"
        return check
    try:
        with urllib.request.urlopen(req,timeout=16) as response:
            return evaluate(response)
    except urllib.error.HTTPError as err:
        # Expected form sentinel is 405, which urllib reports as an HTTPError.
        if key=="form_get" and err.code==405:
            check["http_status"]=405
            try:
                body=err.read(MAX_BYTES).decode("utf-8","replace")
                check["kind"]="FORM_GET_METHOD_OK" if "POST required" in body else "FORM_405_UNKNOWN_HANDLER"
            except Exception:check["kind"]="FORM_405_UNREADABLE"
        elif key=="support_hub" and err.code==404:
            check["http_status"]=404
            check["kind"]="SUPPORT_ROUTE_NOT_PUBLISHED"
        elif key=="form_get" and err.code==404:
            check["http_status"]=404
            check["kind"]="FORM_GET_ROUTE_NOT_DEPLOYED"
        else:
            check["http_status"]=err.code
            check["kind"]="HTTP_ERROR_NOT_PROOF_OF_SITE_OUTAGE"
        return check
    except Exception as e:
        # Cloudflare bot blocking and transient network errors are UNKNOWN, not verified outage.
        check["kind"]="UNKNOWN_NETWORK"
        check["notes"].append(type(e).__name__)
        return check

def main():
    with futures.ThreadPoolExecutor(max_workers=6) as ex:
        entries=list(ex.map(read_one,CHECKS))
    problems=[x["name"] for x in entries if x["kind"] in {
        "M1_VAT_INCORRECT","M1_SELECTOR_NOT_FOUND","FAQ_NOT_VERIFIED",
        "SUPPORT_ROUTE_NOT_PUBLISHED","FORM_GET_ROUTE_NOT_DEPLOYED",
        "FORM_GET_NOT_VERIFIED","FORM_405_UNKNOWN_HANDLER","PAYMENT_CONFIG_REVIEW",
        "PAYMENT_CONFIG_UNREADABLE","WMM_PRICE_VAT_CONTRADICTION",
        "GCSME_KR_OLD_WMM_LINK_PRESENT"}]
    report={
       "schema":"wmm.customer.public-get-review.v1",
       "checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "scope":"14_PUBLIC_READ_ONLY_GET_REQUESTS_NO_CUSTOMER_DATA",
       "sites_checked":len(entries),
       "customer_post_tested":False,
       "customer_inbox_tested":False,
       "membership_grant_tested":False,
       "paid_checkout_tested":False,
       "release_ready":False,
       "mismatches_found":problems,
       "results":entries
    }
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    path=pathlib.Path("customer_public_get_review.json")
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # This audits CURRENT PROD, not the PR; never reject a safe proposed fix
    # just because the current public deployment still has old bugs.
    return 0

if __name__=="__main__":sys.exit(main())
