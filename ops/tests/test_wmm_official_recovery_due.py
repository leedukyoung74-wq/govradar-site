import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wmm_official_recovery_due import needs,kst_stamp,utc_stamp,UTC,KST,USGS_LIMIT,NWS_LIMIT,CISA_LIMIT
NOW=dt.datetime(2026,11,21,5,0,tzinfo=UTC)

class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  self.root=Path(self.t.name);(self.root/'hz').mkdir()
  self.fill(5,10,10)
 def write(self,name,obj):
  (self.root/'hz'/name).write_text(json.dumps(obj),encoding='utf-8')
 def fill(self,usgs,nws,cisa):
  stamp=(NOW-dt.timedelta(minutes=usgs)).astimezone(KST).strftime('%Y-%m-%dT%H:%M')
  self.write('official.json',{'usgs_fast_checked':stamp,'sources':{'usgs':{'ok':True}},'items':{}})
  for n,a in [('nws_active.json',nws),('cisa_kev.json',cisa)]:
   val=(NOW-dt.timedelta(minutes=a)).isoformat()
   self.write(n,{'source_health':{'ok':True,'stale':False,'last_ok':val,'checked_at':val},'items':[]})
 def test_recent_no_fetch(self):
  r=needs(self.root,NOW);self.assertFalse(r['usgs']);self.assertFalse(r['nws_cisa'])
 def test_stale_usgs(self):
  self.fill(40,10,10);self.assertTrue(needs(self.root,NOW)['usgs'])
 def test_stale_nws(self):
  self.fill(5,80,10);self.assertTrue(needs(self.root,NOW)['nws_cisa'])
 def test_stale_cisa(self):
  self.fill(5,10,490);self.assertTrue(needs(self.root,NOW)['cisa'])
 def test_force(self):
  r=needs(self.root,NOW,force=True);self.assertTrue(r['usgs'] and r['nws_cisa'])
 def test_missing_nws(self):
  (self.root/'hz'/'nws_active.json').unlink()
  self.assertTrue(needs(self.root,NOW)['nws_cisa'])
 def test_bad_json(self):
  (self.root/'hz'/'nws_active.json').write_text('{',encoding='utf-8')
  self.assertTrue(needs(self.root,NOW)['nws_cisa'])
 def test_recent_failed_nws_backoff(self):
  self.write('nws_active.json',{'source_health':{'ok':False,'stale':True,'checked_at':(NOW-dt.timedelta(minutes=5)).isoformat()}})
  self.assertFalse(needs(self.root,NOW)['nws_cisa'])
 def test_old_failed_nws_retry(self):
  self.write('nws_active.json',{'source_health':{'ok':False,'stale':True,'checked_at':(NOW-dt.timedelta(minutes=22)).isoformat()}})
  self.assertTrue(needs(self.root,NOW)['nws_cisa'])
 def test_recent_failed_usgs_backoff(self):
  self.fill(3,5,5)
  x=json.loads((self.root/'hz'/'official.json').read_text());x['sources']['usgs']['ok']=False
  self.write('official.json',x);self.assertFalse(needs(self.root,NOW)['usgs'])
 def test_old_failed_usgs_retry(self):
  self.fill(22,5,5)
  x=json.loads((self.root/'hz'/'official.json').read_text());x['sources']['usgs']['ok']=False
  self.write('official.json',x);self.assertTrue(needs(self.root,NOW)['usgs'])
 def test_kst_parse(self):
  self.assertEqual(kst_stamp('2026-11-21T14:00'),NOW)
 def test_strict_utc_parse(self):
  self.assertIsNone(utc_stamp('2026-11-21T14:00'))
 def test_future_rejected(self):
  self.fill(-60,10,10);self.assertTrue(needs(self.root,NOW)['usgs'])
 def test_naive_time_rejected(self):
  with self.assertRaises(ValueError):needs(self.root,dt.datetime(2026,11,21,5,0))
 def test_limits(self):
  self.assertEqual((USGS_LIMIT,NWS_LIMIT,CISA_LIMIT),(2100,4500,28800))
 def test_owner_comment_does_not_force_recovery(self):
  workflow=(Path(__file__).resolve().parents[2]/'.github'/'workflows'/
            'wmm_official_gap_recovery.yml').read_text(encoding='utf-8')
  self.assertIn("github.event.comment.body == '/govradar-refresh-official'",workflow)
  self.assertIn("OWNER_EXPLICIT_FORCE:",workflow)
  self.assertIn("inputs.force && 'true' || 'false'",workflow)
  self.assertIn("if [ \"$TRIGGER\" = 'workflow_dispatch' ] && [ \"$OWNER_EXPLICIT_FORCE\" = 'true' ]; then",workflow)
  self.assertNotIn("if [ \"$TRIGGER\" = 'issue_comment' ] || [ \"$TRIGGER\" = 'workflow_dispatch' ]; then",workflow)
  self.assertIn("python3 control/ops/wmm_official_recovery_due.py --data data_branch\n",workflow)

 def test_independent_nws_cisa_recovery_after_usgs_failure(self):
  workflow=(Path(__file__).resolve().parents[2]/'.github'/'workflows'/
            'wmm_official_gap_recovery.yml').read_text(encoding='utf-8')
  block=workflow.split('  recover_nws_cisa:\n',1)[1]
  self.assertIn('needs: [due, recover_usgs]',block)
  self.assertIn("always() && needs.due.result == 'success'",block)
  self.assertIn("needs.due.outputs.nws_cisa == 'true'",block)
  for outcome in ('success','skipped','failure'):
   self.assertIn("needs.recover_usgs.result == '"+outcome+"'",block)
  self.assertNotIn("needs.recover_usgs.result == 'cancelled'",block)
  self.assertIn('wmm_nws_cisa_official.yml@src',block)
  self.assertIn('dry_run:',block)
  self.assertEqual(workflow.count("    - cron:"),1)
  self.assertIn("cron: '7,37 * * * *'",workflow)

 def test_stale_only_gate_does_not_mutate(self):
  self.fill(5, 5, 5)
  before=[(self.root/'hz'/n).read_bytes() for n in
          ('official.json','nws_active.json','cisa_kev.json')]
  self.assertFalse(needs(self.root,NOW)['usgs'])
  self.assertFalse(needs(self.root,NOW)['nws_cisa'])
  after=[(self.root/'hz'/n).read_bytes() for n in
         ('official.json','nws_active.json','cisa_kev.json')]
  self.assertEqual(before,after)

 def test_source_unchanged(self):
  p=self.root/'hz'/'official.json';b=p.read_bytes();needs(self.root,NOW)
  self.assertEqual(p.read_bytes(),b)
if __name__=='__main__':unittest.main()
