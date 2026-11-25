"""Read-only offline regressions for DAPA historic coverage and SAM.gov source accuracy."""
import datetime
import json
import os
import pathlib
import sys
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlsplit
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
import feed_more as FM

def dapa_xml(rows,total):
    body="".join("<item>"+"".join("<"+k+">"+str(v)+"</"+k+">" for k,v in x.items())+"</item>" for x in rows)
    return "<response><header><resultCode>00</resultCode></header><body><totalCount>"+str(total)+"</totalCount><items>"+body+"</items></body></response>"

class CountrySourceAccuracy(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def test_dapa_historic_only_sample_flag(self):
        old={"seqn":"01","bidTo":"20190409","orgPlace":"US","bidNameEng":"Historical"}
        with mock.patch.dict(os.environ,{"DAPA_KEY":"fixture-not-real"}), mock.patch.object(FM,"_get",return_value=dapa_xml([old],501)):
            data=FM.dapa()
        self.assertEqual([],data)
        st=FM.stat("DAPA (Korea)")
        self.assertEqual(st["data_freshness"],"HISTORICAL_SAMPLE")
        self.assertEqual(st["sampled_latest_bid_to"],"2019-04-09")
        self.assertEqual(st["coverage"],"FIRST_AND_LAST_PAGES_ONLY")
        self.assertFalse(st["date_filter_verified"])

    def test_dapa_future_notice_not_falsely_flagged_old(self):
        future=(datetime.date.today()+datetime.timedelta(days=45)).strftime("%Y%m%d")
        row={"seqn":"a","bidTo":future,"orgPlace":"US","bidNameEng":"Future"}
        detail=dapa_xml([{"oriUrl":"https://official.example.gov/1","bidTo":future}],1)
        def fake(src,url,**kwargs):
            return detail if "getDCAIBidInfoDetail" in url else dapa_xml([row],1)
        with mock.patch.dict(os.environ,{"DAPA_KEY":"fixture-not-real"}),mock.patch.object(FM,"_get",side_effect=fake):
            rows=FM.dapa()
        self.assertEqual(len(rows),1)
        self.assertNotIn("data_freshness",FM.stat("DAPA (Korea)"))

    def test_sam_excludes_inactive_and_missing_official_url(self):
        future=(datetime.date.today()+datetime.timedelta(days=25)).isoformat()
        records=[
            {"noticeId":"active1","title":"Good","active":"Yes","responseDeadLine":future,"uiLink":"https://sam.gov/opp/active1/view"},
            {"noticeId":"inactive","title":"Cancelled","active":"No","responseDeadLine":future,"uiLink":"https://sam.gov/opp/inactive/view"},
            {"noticeId":"unknown","title":"Unknown","responseDeadLine":future,"uiLink":"https://sam.gov/opp/unknown/view"},
            {"noticeId":"badurl","title":"No URL","active":"Yes","responseDeadLine":future,"uiLink":"https://untrusted.example/opp"}
        ]
        with mock.patch.dict(os.environ,{"SAM_KEY":"fixture-not-real"}),mock.patch.object(FM,"_get",return_value=json.dumps({"totalRecords":4,"opportunitiesData":records})) as get:
            rows=FM.sam()
        self.assertEqual([x["sid"] for x in rows],["active1"])
        self.assertEqual(get.call_count,1)
        self.assertEqual(FM.stat("SAM.gov (US)")["filtered"]["inactive"],1)
        self.assertEqual(FM.stat("SAM.gov (US)")["filtered"]["active-unverified"],1)
        self.assertEqual(FM.stat("SAM.gov (US)")["filtered"]["nonofficial-or-missing-url"],1)
        self.assertEqual(FM.stat("SAM.gov (US)")["upstream_total"],4)

    def test_sam_bounded_paging_keeps_earliest_deadlines(self):
        today=datetime.date.today()
        # First page has one active late notice and 999 inactive; page two has earlier notice.
        a=[{"noticeId":str(i),"title":"Archived "+str(i),"active":"No","responseDeadLine":(today+datetime.timedelta(days=20)).isoformat(),
            "uiLink":"https://sam.gov/opp/"+str(i)+"/view"} for i in range(999)]
        a.append({"noticeId":"late","title":"Late","active":"Yes","responseDeadLine":(today+datetime.timedelta(days=100)).isoformat(),"uiLink":"https://sam.gov/opp/late/view"})
        b=[{"noticeId":"soon","title":"Soon","active":"Yes","responseDeadLine":(today+datetime.timedelta(days=5)).isoformat(),"uiLink":"https://sam.gov/opp/soon/view"}]
        def fake(src,url,**kwargs):
            q=parse_qs(urlsplit(url).query)
            self.assertIn("rdlfrom",q)
            self.assertIn("rdlto",q)
            return json.dumps({"totalRecords":1001,"opportunitiesData":a if q.get("offset")==["0"] else b})
        with mock.patch.dict(os.environ,{"SAM_KEY":"fixture-not-real"}),mock.patch.object(FM,"_get",side_effect=fake) as get:
            rows=FM.sam()
        self.assertEqual(get.call_count,2)
        self.assertEqual([parse_qs(urlsplit(c.args[1]).query)["offset"][0] for c in get.call_args_list],["0","1"])
        self.assertEqual([r["sid"] for r in rows],["soon","late"])
        st=FM.stat("SAM.gov (US)")
        self.assertEqual(st["raw"],1001)
        self.assertEqual(st["pages_scanned"],2)
        self.assertFalse(st["coverage_partial"])

if __name__=="__main__": unittest.main()
