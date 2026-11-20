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
        store(self.l,"public/ko/index.html",'<b id="kp-t">1013</b>')
        for s,l in (("web/auth.js","public/assets/auth.js"),
                    ("cf/functions/nfform.js","functions/nfform.js"),
                    ("cf/functions/api/req.js","functions/api/req.js")):
            store(self.s,s,"working program")
            store(self.l,l,"working program")
        store(self.s,"src/government_business_sites.json",{"countries":{("XX"+str(i)): [1,2,3] for i in range(193)}})

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
