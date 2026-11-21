import json
import sys
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from v28_live_feed_integrity import analyze, parse_timestamp, age_minutes, good_url

NOW=datetime(2026,11,21,4,50,tzinfo=timezone.utc)

class LiveFeedTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        for path in ('hz','feeds/cty'):(self.root/path).mkdir(parents=True)
        data={
          'feeds/tenders.json':{'updated':'2026-11-21T02:06Z','count':2,'items':[
            {'iso':'BJ','verify':'search','url':'https://www.marches-publics.bj/notice/1','deadline':'2026-11-20','sid':'one'},
            {'iso':'MD','verify':'partial','url':'https://mtender.gov.md/en/notice/2','deadline':'2026-11-26','sid':'two'}]},
          'feeds/awards.json':{'updated':'2026-11-21T02:10Z','count':1532,'items':[{'title':'one'}]},
          'feeds/cty/_summary.json':{'updated':'2026-11-21T02:11Z','t':{'n':1}},
          'hz/official.json':{'checked':'2026-11-21T11:11','usgs_fast_checked':'2026-11-21T09:21','sources':{}},
          'hz/nws_active.json':{'items':[{'event':'test'}],'source_health':{'ok':True,'stale':False,'last_ok':'2026-11-21T00:53:55Z'}},
          'hz/cisa_kev.json':{'items':[],'source_health':{'ok':True,'stale':False,'last_ok':'2026-11-21T00:53:55Z'},'not_realtime_attack_feed':True}
        }
        for name,obj in data.items():
            (self.root/name).write_text(json.dumps(obj),encoding='utf-8')
    def tearDown(self):self.tmp.cleanup()
    def test_tender_methods_not_official_status(self):
        r=analyze(self.root,NOW)
        self.assertEqual(r['tender_feed']['verification_method_counts'],{'search':1,'partial':1})
        self.assertFalse(r['tender_feed']['may_auto_certify_currently_open'])
    def test_expired_is_not_open(self):
        self.assertEqual(analyze(self.root,NOW)['tender_feed']['records_with_deadline_before_as_of'],1)
    def test_urls_count(self):
        self.assertEqual(analyze(self.root,NOW)['tender_feed']['source_urls_present'],2)
    def test_awards_total_is_not_display_count(self):
        r=analyze(self.root,NOW)
        self.assertEqual(r['awards']['reported_total'],1532)
        self.assertEqual(r['awards']['displayed_items'],1)
        self.assertTrue(r['awards']['truncated_for_display'])
    def test_stale_source_health_flag_not_trusted(self):
        r=analyze(self.root,NOW)
        self.assertEqual(r['nws']['health_flag_in_file'],False)
        self.assertFalse(r['nws']['fresh_at_check'])
    def test_usgs_kst_interpretation(self):
        r=analyze(self.root,NOW)
        self.assertGreater(r['hazards']['usgs_fast_age_minutes'],250)
        self.assertFalse(r['hazards']['usgs_fast_fresh_at_check'])
    def test_cisa_not_realtime_attack_feed(self):
        r=analyze(self.root,NOW)
        self.assertTrue(r['cisa_kev']['not_realtime_attack_feed'])
        self.assertTrue(r['cisa_kev']['fresh_at_check'])
    def test_tender_feed_snapshot_age(self):
        r=analyze(self.root,NOW)
        self.assertEqual(r['tender_feed']['snapshot_age_minutes'],164.0)
    def test_no_customer_alerting(self):
        self.assertFalse(analyze(self.root,NOW)['alerting_operational_ready'])
    def test_bad_url_rejected(self):
        self.assertFalse(good_url('http://localhost:9000'))
    def test_naive_timestamp_kst(self):
        self.assertEqual(parse_timestamp('2026-11-21T09:21',assume_utc=False).isoformat(),'2026-11-21T00:21:00+00:00')
    def test_invalid_timestamp(self):
        self.assertIsNone(parse_timestamp('not date'))
if __name__=='__main__':unittest.main()
