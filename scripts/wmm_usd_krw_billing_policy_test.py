#!/usr/bin/env python3
"""Read-only currency rollout and safety contract checks, never charges or deploys."""
from pathlib import Path
import json,sys,re
root=Path(__file__).resolve().parents[1]
p=json.loads((root/"config/wmm_currency_pricing_review.json").read_text(encoding="utf-8"))
fail=[]
def check(ok,msg):
  if not ok:fail.append(msg)
check(p.get("policy_status")=="PROPOSED_NOT_LIVE","must remain proposed")
check(p.get("payment_live") is False,"checkout must not activate")
check(p.get("auto_renew") is False,"auto renewal must be disabled")
check(bool(p.get("tax_note")),"tax disclosure must be required")
by={x["id"]:x for x in p["catalog"]}
for k,amount in [("analysis_month",19800),("analysis_year",198000),("tender_fit",100000),("market_entry_brief",300000)]:
  x=next((s for s in by[k]["country_offers"] if s["region"]=="KR"),{})
  check(x.get("currency")=="KRW" and x.get("unit_amount")==amount,f"current KRW {k} unchanged")
for k,amount in [("analysis_month",1900),("analysis_year",19000)]:
  x=next((s for s in by[k]["country_offers"] if s["region"]=="INTERNATIONAL"),{})
  check(x.get("currency")=="USD" and x.get("unit_amount")==amount and x.get("status")=="PROPOSED",f"review-only USD {k}")
for x in p["catalog"]:
  check(x.get("billing_mode") in ("prepay_manual_nonrecurring","invoice_quote"),f"{x['id']} no unauthorized subscription")
  for y in x["country_offers"]:
    v=y.get("unit_amount")
    check(v is None or (isinstance(v,int) and not isinstance(v,bool) and v>=0),f"{x['id']} integer cents/won")
    if y["region"]=="INTERNATIONAL" and x["id"] not in ("analysis_month","analysis_year"):
      check(v is None and y.get("status")=="QUOTE_REQUIRED",f"{x['id']} international enterprise must be quote")
check(p["settlement_rules"].get("payment_confirmation")=="VERIFIED_SERVER_SIDE_ONLY","verified server payment required")
check(p["settlement_rules"].get("exchange_rate")=="SNAPSHOT_FOR_REPORTING_ONLY_NEVER_REPRICE_CONFIRMED_ORDER","rate only for reporting")
langs=("ko","en","es","fr","ar","vi","id")
lines=[]
for lang in langs:
  f=root/lang/"pricing/index.html"
  if not f.exists():
    check(False,f"missing pricing page {lang}")
    continue
  html=f.read_text(encoding="utf-8")
  matches=bool(re.search(r"19.?800|19,800|19 800",html))
  check(matches,f"{lang}: current KRW membership price marker missing")
  # Existing production storefront has no USD payment checkout. This is expected.
  lines.append((lang,len(html),matches))
print("WMM USD/KRW proposed policy checks:", "PASS" if not fail else "FAIL")
for lang,n,marker in lines:
  print(f"  {lang}: html={n} bytes, existing monthly KRW marker={marker}")
if fail:
  print("FAILURES:")
  for f in fail:print(" - "+f)
  sys.exit(1)
print("No production prices changed, no checkout, no provider API called.")
