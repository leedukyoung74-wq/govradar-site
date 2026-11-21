import csv
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from v28_integrity_review import inspect, website_url, day, stable_ref, safe_csv_cell, SOURCE_PER_COUNTRY

class V28IntegrityReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/"data"/"c").mkdir(parents=True)
        self.codes=[chr(65+i//26)+chr(65+i%26) for i in range(193)]
        self.countries=[
            {"iso":code,"names":{"ko":"국가"+str(i),"en":"Country "+str(i)},"done":i<120}
            for i,code in enumerate(self.codes)
        ]
        for i in range(120):
            (self.root/"data"/"c"/(self.codes[i]+".json")).write_text('{"sources":[]}',encoding="utf-8")
        self.opp_items=[]
        for i in range(620):
            kind="biz" if i<462 else "oda" if i<475 else "tenders"
            self.opp_items.append({"iso":self.codes[i%193],"kind":kind,
                "ko":"정부 가상예시 "+str(i),"en":"Dummy opportunity "+str(i),
                "deadline":"2026-11-19" if i<145 else "", "u":"2026-11-07"})
        (self.root/"data"/"countries.json").write_text(json.dumps(self.countries,ensure_ascii=False),encoding="utf-8")
        (self.root/"data"/"opps.json").write_text(json.dumps({"updated":"2026-11-09","items":self.opp_items},ensure_ascii=False),encoding="utf-8")
        (self.root/"data"/"regions.json").write_text("[]",encoding="utf-8")
    def tearDown(self): self.tmp.cleanup()
    def test_iso_date(self):self.assertEqual(str(day("2026-11-21")),"2026-11-21")
    def test_bad_date(self):self.assertIsNone(day("2026-02-30"))
    def test_disallow_plain_http(self):self.assertFalse(website_url("http://www.gov.bj"))
    def test_block_private_ip(self):self.assertFalse(website_url("https://127.0.0.1/admin"))
    def test_block_url_auth(self):self.assertFalse(website_url("https://token:password@example.org/"))
    def test_block_custom_port(self):self.assertFalse(website_url("https://example.org:8080/"))
    def test_block_fragment(self):self.assertFalse(website_url("https://example.org/#a"))
    def test_https_allowed(self):self.assertTrue(website_url("https://www.gouv.bj/"))
    def test_73_missing(self):
        r=inspect(self.root,"2026-11-21")
        self.assertEqual(len(r["missing_countries"]),73)
        self.assertEqual(r["summary"]["country_profiles_existing"],120)
        self.assertEqual(r["summary"]["missing_country_source_tasks"],73*9)
        self.assertEqual(SOURCE_PER_COUNTRY,9)
    def test_no_opportunity_published(self):
        r=inspect(self.root,"2026-11-21")
        self.assertEqual(r["summary"]["opportunities_missing_primary_source"],620)
        self.assertEqual(r["summary"]["opportunity_kinds"],{"biz":462,"oda":13,"tenders":145})
        self.assertEqual(r["summary"]["opportunities_missing_deadline"],475)
        self.assertEqual(r["summary"]["opportunities_expired_by_recorded_deadline"],145)
        self.assertTrue(all(not x["may_send_business_alert"] and not x["may_publish_as_official"] for x in r["opportunity_review_rows"]))
    def test_source_url_alone_not_verified(self):
        self.opp_items[0]["url"]="https://example.org/procurement/abc"
        (self.root/"data"/"opps.json").write_text(json.dumps({"updated":"2026-11-09","items":self.opp_items}),encoding="utf-8")
        r=inspect(self.root,"2026-11-21")
        self.assertIn("SOURCE_LINK_REVIEW_REQUIRED",r["opportunity_review_rows"][0]["status"])
        self.assertFalse(r["opportunity_review_rows"][0]["may_publish_as_official"])
    def test_only_candidate_sources(self):
        d={"sources":[{"id":"BJ-01","iso":self.codes[1],"category":"government","publisher":"Example","url":"https://example.org/","status":"CANDIDATE"}]}
        r=inspect(self.root,"2026-11-21",d)
        self.assertEqual(r["summary"]["candidate_source_urls"],1)
        self.assertEqual(r["summary"]["editorially_verified_new_sources"],0)
        self.assertTrue(all(x["source_slots_editorially_verified"]==0 for x in r["missing_countries"]))
    def test_unapproved_verified_claim_rejected(self):
        d={"sources":[{"id":"BJ-01","iso":self.codes[1],"category":"government","publisher":"Example","url":"https://example.org/","status":"HUMAN_REVIEWED"}]}
        with self.assertRaises(ValueError): inspect(self.root,"2026-11-21",d)
    def test_duplicate_country_rejected(self):
        self.countries[1]["iso"]=self.codes[0]
        (self.root/"data"/"countries.json").write_text(json.dumps(self.countries),encoding="utf-8")
        with self.assertRaises(ValueError):inspect(self.root,"2026-11-21")
    def test_bad_opportunity_kind_rejected(self):
        self.opp_items[0]["kind"]="fiction"
        (self.root/"data"/"opps.json").write_text(json.dumps({"updated":"2026-11-09","items":self.opp_items}),encoding="utf-8")
        with self.assertRaises(ValueError):inspect(self.root,"2026-11-21")
    def test_formula_injection_guard(self):
        self.assertEqual(safe_csv_cell("=HYPERLINK('x')"),"'=HYPERLINK('x')")
        self.assertEqual(safe_csv_cell("@SUM(A1)"),"'@SUM(A1)")
        self.assertEqual(safe_csv_cell("safe"),"safe")
    def test_stable_ids_distinct(self):
        self.assertNotEqual(stable_ref("BJ","biz","test",1),stable_ref("BJ","biz","test",2))
    def test_no_data_mutation(self):
        path=self.root/"data"/"opps.json";before=path.read_bytes()
        inspect(self.root,"2026-11-21")
        self.assertEqual(before,path.read_bytes())

if __name__=="__main__":unittest.main()
