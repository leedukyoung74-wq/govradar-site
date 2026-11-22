"""Non-network tests: WMM CTI candidate inventory matching is not impact detection."""
import importlib.util
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
TOOLS=Path(__file__).resolve().parents[1]/"tools"
sys.path.insert(0,str(TOOLS))
spec=importlib.util.spec_from_file_location("cti_asset_match",TOOLS/"cti_asset_match.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def inventory(authorization="EXPLICIT_OWNER_AUTHORIZATION"):
    return {"schema":"wmm-demo-asset-inventory.v1","authorization":authorization,
      "authorization_reference":"AUTH-DEMO-20261119",
      "assets":[{"asset_tag":"TEST-01","vendor":"Example Vendor","product":"Example App","version":"1.0"}]}
class MatchTests(unittest.TestCase):
 def test_candidate_not_confirmed(self):
    source={"records":[{"id":"CVE-2026-12345","vendor":"Example Vendor","product":"Example App"}]}
    x=m.match(source,inventory()["assets"])
    self.assertEqual(x["candidate_count"],1)
    self.assertEqual(x["matched_assets"][0]["status"],"UNVERIFIED_CANDIDATE")
    self.assertFalse(x["matched_assets"][0]["confirmed_vulnerable"])
    self.assertFalse(x["matched_assets"][0]["confirmed_breached"])
    self.assertFalse(x["signed_authorization_verified_by_tool"])
 def test_no_authorization_blocked(self):
    with TemporaryDirectory() as d:
      f=Path(d)/"inventory.json";f.write_text(json.dumps(inventory("NONE")))
      with self.assertRaisesRegex(ValueError,"authorization"):m.read_inventory(f)
 def test_private_field_blocked(self):
    with TemporaryDirectory() as d:
      v=inventory();v["assets"][0]["email"]="someone@example.com"
      f=Path(d)/"inventory.json";f.write_text(json.dumps(v))
      with self.assertRaisesRegex(ValueError,"PII"):m.read_inventory(f)
 def test_password_metadata_blocked(self):
    with TemporaryDirectory() as d:
      v=inventory();v["assets"][0]["product"]="password:abc"
      f=Path(d)/"inventory.json";f.write_text(json.dumps(v))
      with self.assertRaisesRegex(ValueError,"private"):m.read_inventory(f)
 def test_nonmatching_product_not_inferred(self):
    r={"records":[{"id":"CVE-2026-12345","vendor":"Example Vendor","product":"Example App"}]}
    a=inventory()["assets"];a[0]["product"]="Other App"
    self.assertEqual(m.match(r,a)["candidate_count"],0)
if __name__=="__main__": unittest.main()
