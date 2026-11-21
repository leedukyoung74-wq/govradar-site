import json
import sys
import unittest
import tempfile
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ops'))
from source_registry_v27 import source_url_good, parse_date, review_ok, analyze

class RegistryTest(unittest.TestCase):
    def test_good_https(self): self.assertTrue(source_url_good('https://govt.cv/en/'))
    def test_reject_http(self): self.assertFalse(source_url_good('http://govt.cv'))
    def test_reject_auth(self): self.assertFalse(source_url_good('https://user:pass@govt.cv'))
    def test_reject_private_ip(self): self.assertFalse(source_url_good('https://127.0.0.1/admin'))
    def test_reject_bad_port(self): self.assertFalse(source_url_good('https://govt.cv:8080/'))
    def test_reject_crlf(self): self.assertFalse(source_url_good('https://govt.cv/\nnew'))
    def test_reject_invalid_date(self): self.assertIsNone(parse_date('2026-02-30'))
    def test_candidate_not_verified(self):
        self.assertFalse(review_ok({'status':'CANDIDATE','url':'https://govt.cv'},date(2026,11,21)))
    def test_review_requires_approval(self):
        self.assertFalse(review_ok({'status':'HUMAN_REVIEWED','url':'https://govt.cv','verification':{'reviewed_at':'2026-11-20','reviewer':'reviewer1','evidence_url':'https://govt.cv'}} ,date(2026,11,21)))
    def test_stale_review_not_verified(self):
        row={'status':'HUMAN_REVIEWED','url':'https://govt.cv','verification':{'reviewed_at':'2026-09-01','reviewer':'reviewer1','evidence_url':'https://govt.cv','institution_ownership_confirmed':True,'link_reachable':True,'category_role_confirmed':True,'editor_approved':True}}
        self.assertFalse(review_ok(row,date(2026,11,21)))
    def test_verified_requires_all(self):
        row={'status':'HUMAN_REVIEWED','url':'https://govt.cv','verification':{'reviewed_at':'2026-11-20','reviewer':'reviewer1','evidence_url':'https://govt.cv','institution_ownership_confirmed':True,'link_reachable':True,'category_role_confirmed':True,'editor_approved':True}}
        self.assertTrue(review_ok(row,date(2026,11,21)))
    def test_profile_coverage_and_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp); (path/'data'/'c').mkdir(parents=True)
            cs=[{'iso':f'{chr(65+i//26)}{chr(65+i%26)}','names':{'ko':'나라'},'done':i==0} for i in range(193)]
            (path/'data'/'countries.json').write_text(json.dumps(cs),encoding='utf-8')
            (path/'data'/'c'/f'{cs[0]["iso"]}.json').write_text('{}',encoding='utf-8')
            sources={'sources':[{'id':'A','iso':cs[0]['iso'],'category':'government','url':'https://www.example.org/','publisher':'Sample','status':'CANDIDATE'}]}
            r=analyze(path,sources,'2026-11-21');self.assertEqual(r['missing_profile_count'],192);self.assertEqual(r['candidate_source_count'],1);self.assertEqual(r['source_ready_country_count'],0)
    def test_duplicate_domain_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp); (path/'data'/'c').mkdir(parents=True)
            cs=[{'iso':f'{chr(65+i//26)}{chr(65+i%26)}','names':{},'done':False} for i in range(193)]
            (path/'data'/'countries.json').write_text(json.dumps(cs),encoding='utf-8')
            p={'sources':[{'id':'one','iso':'AA','category':'news','url':'https://news.example.org/one','publisher':'one','status':'CANDIDATE'}, {'id':'two','iso':'AA','category':'news','url':'https://news.example.org/two','publisher':'two','status':'CANDIDATE'}]}
            with self.assertRaises(ValueError):analyze(path,p,'2026-11-21')
if __name__=='__main__':unittest.main()
