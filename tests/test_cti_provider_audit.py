"""No-network permission gates for CTI providers."""
import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"tools/cti_provider_audit.py"
spec=importlib.util.spec_from_file_location("cti_provider_audit",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def registry():return json.loads((ROOT/"ops/cti_provider_registry.json").read_text(encoding="utf8"))
class ProviderAuditTests(unittest.TestCase):
 def test_default_denial(self):
    r=m.check(registry())
    self.assertEqual(r["provider_count"],9)
    self.assertEqual(r["production_enabled"],0)
    self.assertEqual(r["redistribution_approved"],0)
 def test_unapproved_vendor_api_blocked(self):
    d=registry();d["providers"][1]["enabled_for_production"]=True
    with self.assertRaisesRegex(ValueError,"live use"):m.check(d)
 def test_unapproved_automated_collection_blocked(self):
    d=registry();d["providers"][1]["automated_collection_approved"]=True
    with self.assertRaisesRegex(ValueError,"live use"):m.check(d)
 def test_unapproved_resale_blocked(self):
    d=registry();d["providers"][3]["client_redistribution"]=True
    with self.assertRaisesRegex(ValueError,"resale"):m.check(d)
 def test_provider_missing_blocked(self):
    d=registry();d["providers"].pop()
    with self.assertRaisesRegex(ValueError,"count"):m.check(d)
 def test_duplicate_provider_blocked(self):
    d=registry();d["providers"][1]["id"]=d["providers"][0]["id"]
    with self.assertRaisesRegex(ValueError,"Missing/duplicate"):m.check(d)
 def test_tokens_or_extra_fields_blocked(self):
    d=registry();d["providers"][1]["api_key"]="should-not-be-present"
    with self.assertRaisesRegex(ValueError,"secret payload"):m.check(d)
 def test_unsafe_url_blocked(self):
    d=registry();d["providers"][1]["source"]="http://example.test/"
    with self.assertRaisesRegex(ValueError,"Unsafe"):m.check(d)
 def test_unlicensed_payload_blocked(self):
    d=registry();d["providers"][1]["allowed_data"]="SECRET_DUMP"
    with self.assertRaisesRegex(ValueError,"contract"):m.check(d)
 def test_unapproved_status_blocked(self):
    d=registry();d["providers"][1]["status"]="LIVE"
    with self.assertRaisesRegex(ValueError,"production status"):m.check(d)
if __name__=="__main__":unittest.main()
