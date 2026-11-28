"""Read-only release audit treats source code and real production as distinct."""
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from ops.govradar_release_readiness import inspect,parse_time

UTC=dt.timezone.utc
NOW=dt.datetime(2026,11,20,14,0,tzinfo=UTC)

class AuditTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        t=Path(self.temp.name)
        self.s,self.l,self.d=t/"src",t/"live",t/"data"
        def store(root,path,body):
            p=root/path;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(body if isinstance(body,str) else json.dumps(body),encoding="utf-8")
        self.store=store
        store(self.d,"feeds/cty/_summary.json",{"updated":"2026-11-20T13:50Z","t":{"n":1013}})
        store(self.d,"feeds/sources_status.json",{x:{"state":"SUCCESS"} for x in
              ("UK Find a Tender","DAPA (Korea)","SAM.gov (US)")})
        for f in ("nws_active.json","cisa_kev.json"):
            store(self.d,"hz/"+f,{"source_health":{"ok":True,"stale":False,"last_ok":"2026-11-20T13:50Z"}})
        for lang in ("ko","en","es","fr","ar","vi","id"):
            store(self.l,f"public/{lang}/index.html",
                  '<b id="kp-t">—</b><b id="kp-u">—</b><b id="td-open">—</b>'
                  '<script>fetch("data/feeds/today.json");var ageLimit=108000000;</script>')
        for s,l in (("web/auth.js","public/assets/auth.js"),
                    ("cf/functions/nfform.js","functions/nfform.js"),
                    ("cf/functions/api/req.js","functions/api/req.js")):
            store(self.s,s,"working program")
            store(self.l,l,"working program")
        store(self.s,"web/auth.js",'const API = "/.netlify/identity", KEY = "wmm.auth.v1";')
        store(self.l,"public/assets/auth.js",'const API = "/nfid", KEY = "wmm.auth.v1";')
        store(self.s,"src/government_business_sites.json",{"countries":{("XX"+str(i)): [1,2,3] for i in range(193)}})
        prices='export const PRODUCTS = { "analysis-month": {name:"Monthly",amount: 20000}, "analysis-year": {name:"Annual",amount: 200000} };'
        store(self.s,"cf/functions/pay/_products.js",prices)
        store(self.l,"functions/pay/_products.js",prices)


    def states(self):
        return {r["id"]:r for r in inspect(self.s,self.l,self.d,NOW)["checks"]}

    def test_green_sources_cannot_falsely_claim_real_member_login(self):
        report=inspect(self.s,self.l,self.d,NOW)
        self.assertEqual("NOT_READY",report["result"])
        self.assertEqual([],report["blockers"])
        self.assertIn("member_login_authorized",report["unverified"])
        self.assertIn("buyer_intake_authorized",report["unverified"])

    def test_uk_partial_and_us_kr_skipped_always_block(self):
        obj=json.loads((self.d/"feeds/sources_status.json").read_text())
        for key,status in (("UK Find a Tender","PARTIAL"),("SAM.gov (US)","SKIPPED"),
                           ("DAPA (Korea)","SKIPPED")):obj[key]["state"]=status
        self.store(self.d,"feeds/sources_status.json",obj)
        states=self.states()
        for key in ("uk_fts","us_sam","kr_dapa"):
            self.assertEqual("block",states[key]["status"])

    def test_dapa_historical_sample_is_not_ready_even_when_http_success(self):
        obj=json.loads((self.d/"feeds/sources_status.json").read_text())
        obj["DAPA (Korea)"].update({
            "state":"SUCCESS","data_freshness":"HISTORICAL_SAMPLE",
            "sampled_latest_bid_to":"2019-04-09","in":0})
        obj["SAM.gov (US)"].update({"state":"SUCCESS",
            "coverage_partial":True,"coverage":"BOUNDED_PAGES_NOT_ALL_US_NOTICES"})
        self.store(self.d,"feeds/sources_status.json",obj)
        states=self.states()
        self.assertEqual("block",states["kr_dapa"]["status"])
        self.assertEqual("historical_archive_not_live_notice",states["kr_dapa"]["detail"]["reason"])
        self.assertEqual("pass",states["us_sam"]["status"])
        self.assertTrue(states["us_sam"]["detail"]["coverage_partial"])

    def test_missing_locale_or_dynamic_fetch_blocks_static_count_guard(self):
        self.store(self.l,"public/ar/index.html",'<b id="kp-t">—</b>')
        st=self.states()["public_static_open_count"]
        self.assertEqual("block",st["status"])
        self.assertIn("ar",st["detail"]["failed_locales"])

    def test_seven_locale_dash_not_rejected_as_missing_verified_count(self):
        st=self.states()["public_static_open_count"]
        self.assertEqual("pass",st["status"])
        self.assertEqual(7,st["detail"]["placeholder_lc_covered"])

    def test_exact_auth_proxy_rewrite_is_expected_not_a_drift(self):
        # Site is served by Cloudflare Pages /nfid relay rather than Netlify
        # /.netlify/identity directly; everything else must match exactly.
        source='const API = "/.netlify/identity", KEY = "wmm.auth.v1";'
        target='const API = "/nfid", KEY = "wmm.auth.v1";'
        self.store(self.s,"web/auth.js",source)
        self.store(self.l,"public/assets/auth.js",target)
        self.assertEqual("pass",self.states()["live_auth_js"]["status"])
        self.store(self.l,"public/assets/auth.js",target+" window.evil=1;")
        self.assertEqual("block",self.states()["live_auth_js"]["status"])

    def test_source_only_price_fix_does_not_unblock_live_billing(self):
        self.assertEqual("pass",self.states()["billing_price_source_live_parity"]["status"])
        self.store(self.l,"functions/pay/_products.js",
                   'export const PRODUCTS = {"analysis-month":{amount:22000},"analysis-year":{amount:220000}};')
        state=self.states()["billing_price_source_live_parity"]
        self.assertEqual("block",state["status"])
        self.assertEqual({"month":20000,"year":200000},state["detail"]["expected_final_krw"])
        self.assertEqual({"month":22000,"year":220000},state["detail"]["published_live_final_krw"])
        self.assertFalse(state["detail"]["real_charge_executed"])

    def test_missing_malformed_or_duplicate_product_file_is_not_approved(self):
        self.store(self.s,"cf/functions/pay/_products.js",
                   'export const PRODUCTS = {"analysis-month":{amount:20000},"analysis-month":{amount:20000},"analysis-year":{amount:200000}};')
        self.assertEqual("block",self.states()["billing_price_source_live_parity"]["status"])
        (self.s/"cf/functions/pay/_products.js").unlink()
        self.assertEqual("block",self.states()["billing_price_source_live_parity"]["status"])

    def test_equal_prices_are_not_proof_of_checkout_entitlement(self):
        report=inspect(self.s,self.l,self.d,NOW)
        self.assertNotIn("billing_price_source_live_parity",report["blockers"])
        self.assertIn("payment_entitlement_authorized",report["unverified"])

    def test_stale_public_html_and_code_drift_are_independent(self):
        self.store(self.l,"public/ko/index.html",'<b id="kp-t">235</b>')
        self.store(self.l,"public/assets/auth.js","old auth")
        self.store(self.l,"functions/nfform.js","unsafe old relay")
        statuses=self.states()
        for key in ("public_static_open_count","live_auth_js","live_form_relay"):
            self.assertEqual("block",statuses[key]["status"])
        self.assertEqual("pass",statuses["live_request_api"]["status"])

    def test_stale_and_future_source_data_fail_closed(self):
        for stamp in ("2026-11-10T10:00Z","2026-11-20T15:00Z","INVALID"):
            self.store(self.d,"feeds/cty/_summary.json",{"updated":stamp,"t":{"n":1013}})
            self.assertEqual("block",self.states()["official_tenders"]["status"])

    def test_missing_catalog_does_not_mark_all_193_country_sites_complete(self):
        (self.s/"src/government_business_sites.json").unlink()
        self.assertEqual("block",self.states()["national_government_portals"]["status"])

    def test_readonly_and_source_clock(self):
        before=(self.d/"feeds/sources_status.json").read_bytes()
        inspect(self.s,self.l,self.d,NOW)
        self.assertEqual(before,(self.d/"feeds/sources_status.json").read_bytes())
        self.assertIsNone(parse_time("bad timestamp"))
        self.assertEqual(NOW,parse_time("2026-11-20T14:00Z"))


if __name__=="__main__":
    unittest.main()
