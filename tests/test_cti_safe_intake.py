"""No-network regression tests for WMM CISA-only CTI intake."""
import importlib.util, json, unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("cti_safe_intake",root/"tools/cti_safe_intake.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
TODAY=datetime(2026,11,19,tzinfo=timezone.utc)

def fixture(**changes):
    row={"cveID":"CVE-2026-12345","vendorProject":"Example Vendor","product":"Example Product",
         "dateAdded":"2026-11-17","knownRansomwareCampaignUse":"Known",
         "shortDescription":"DO NOT COPY this sample body with a fake credential"}
    row.update(changes)
    return json.dumps({"catalogVersion":"2026.11.19","dateReleased":"2026-11-19T00:00:00Z",
                       "count":1,"vulnerabilities":[row]}).encode()

class IntakeTests(unittest.TestCase):
    def test_only_approved_non_sensitive_fields(self):
        result=m.normalize(fixture(),TODAY)
        m.validate_safe_records(result)
        self.assertEqual(result["source_entries"],1)
        self.assertFalse(result["cti_vendor_connected"])
        self.assertFalse(result["public_release_allowed"])
        self.assertFalse(result["records"][0]["victim_or_outage_confirmed"])
        self.assertTrue(result["records"][0]["ransomware_reported"])
        self.assertNotIn("shortDescription",str(result))
        self.assertNotIn("credential",str(result))
        self.assertNotIn("urlhaus",str(result).lower())
        self.assertEqual(result["records"][0]["source_url"],m.OFFICIAL)
    def test_invalid_cve_rejected(self):
        with self.assertRaisesRegex(ValueError,"CVE"):
            m.normalize(fixture(cveID="not-a-cve"),TODAY)
    def test_future_date_rejected(self):
        with self.assertRaisesRegex(ValueError,"Future"):
            m.normalize(fixture(dateAdded="2030-01-01"),TODAY)
    def test_unsupported_feed_or_payload_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"schema"):
            m.normalize(b'{"records":[]}',TODAY)
    def test_victim_status_never_claimed(self):
        out=m.normalize(fixture(),TODAY)
        out["records"][0]["victim_or_outage_confirmed"]=True
        with self.assertRaisesRegex(ValueError,"victim"):
            m.validate_safe_records(out)
    def test_no_sensitive_extra_fields(self):
        out=m.normalize(fixture(),TODAY)
        out["records"][0]["exfiltrated_passwords"]="bad"
        with self.assertRaisesRegex(ValueError,"Unsafe fields"):
            m.validate_safe_records(out)
    def test_bad_count_or_duplicate(self):
        raw=json.loads(fixture())
        raw["count"]=2
        with self.assertRaisesRegex(ValueError,"count mismatch"):
            m.normalize(json.dumps(raw).encode(),TODAY)
        raw["vulnerabilities"].append(raw["vulnerabilities"][0].copy())
        with self.assertRaisesRegex(ValueError,"duplicate"):
            m.normalize(json.dumps(raw).encode(),TODAY)
    def test_bytes_limit(self):
        with self.assertRaisesRegex(ValueError,"Feed too large"):
            m.normalize(b"x"*(m.MAX_BYTES+1),TODAY)

if __name__=="__main__": unittest.main()
