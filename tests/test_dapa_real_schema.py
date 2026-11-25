"""DAPA historical-publication and real-field parser regression, no network."""
import datetime
import pathlib
import sys
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import feed_more as FM


def xml(rows, total):
    items = "".join("<item>"+"".join("<"+k+">"+str(v)+"</"+k+">" for k,v in r.items())+"</item>" for r in rows)
    return "<response><body><totalCount>"+str(total)+"</totalCount><items>"+items+"</items></body></response>"


class DapaRealSchemaTest(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def test_bidto_yyyymmdd_parse(self):
        self.assertEqual(FM._dapa_day("20261220"), "2026-12-20")
        self.assertEqual(FM._dapa_day("20190318"), "2019-03-18")
        self.assertEqual(FM._dapa_day("20191399"), "")
        self.assertEqual(FM._dapa_day(""), "")

    def test_archive_is_not_published_as_current(self):
        old={"seqn":"1","bidTo":"20190318","orgPlace":"US","bidNameEng":"Old US bid"}
        def fake(src,url, **kwargs):
            return xml([old],501)
        with patch.dict("os.environ",{"DAPA_KEY":"test-not-real"}),patch.object(FM,"_get",side_effect=fake) as g:
            self.assertEqual(FM.dapa(), [])
            self.assertEqual(g.call_count,2)
        self.assertTrue(any("no_verified_open_notice" in note for note in FM.stat("DAPA (Korea)")["notes"]))
        self.assertTrue(any("latest_page_max_bidTo=2019-03-18" in note for note in FM.stat("DAPA (Korea)")["notes"]))

    def test_only_current_detail_with_real_link_can_publish(self):
        future=(datetime.date.today()+datetime.timedelta(days=25)).strftime("%Y%m%d")
        old={"seqn":"1","bidTo":"20190318","orgPlace":"US","bidNameEng":"Old US bid"}
        new={"seqn":"501","bidTo":future,"orgPlace":"US","orgPlaceNm":"United States",
             "bidNameEng":"Recent US bid","anucTypeNm":"Bid"}
        detail="<response><body><items><item><oriUrl>https://official.example.gov/notice/501</oriUrl><orderOrgan>Agency A</orderOrgan><bidTo>"+future+"</bidTo></item></items></body></response>"
        def fake(src,url,**kwargs):
            if "getDCAIBidInfoDetail" in url: return detail
            q=parse_qs(urlsplit(url).query)
            return xml([new] if q["pageNo"]==["2"] else [old],501)
        with patch.dict("os.environ",{"DAPA_KEY":"test-not-real"}),patch.object(FM,"_get",side_effect=fake):
            rows=FM.dapa()
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["iso"],"US")
        self.assertEqual(rows[0]["source"],"DAPA (Korea)")
        self.assertEqual(rows[0]["url"],"https://official.example.gov/notice/501")
        self.assertEqual(rows[0]["deadline"],FM._dapa_day(future))


if __name__=="__main__": unittest.main()
