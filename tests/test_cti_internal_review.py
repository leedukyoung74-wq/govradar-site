"""Offline/no-network CI for internal advisory only. No customer records."""
import importlib.util
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

p=Path(__file__).resolve().parents[1]/"tools/cti_internal_review.py"
spec=importlib.util.spec_from_file_location("cti_internal_review",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
NOW=datetime(2026,11,19,14,30,tzinfo=timezone.utc)
def sample(age=2,overrides=None):
    row={"id":"CVE-2026-12345","date_added":"2026-11-17","vendor":"Example Corp","product":"Sample App",
        "ransomware_reported":False,"evidence_level":"OFFICIAL_CISA_KEV",
        "source_url":"https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        "victim_or_outage_confirmed":False,"public_redistribution_approval":"REVIEW_REQUIRED",
        "enterprise_impact":"NOT_ASSESSED","tlp":"CLEAR"}
    row.update(overrides or {})
    return {"schema":"wmm-cti-safe-intake.v1","source_entries":1,"records":[row],
        "checked_at_utc":(NOW-timedelta(hours=age)).isoformat(),"source_sha256":"a"*64,
        "source":"https://raw.githubusercontent.com/cisagov/kev-data/refs/heads/develop/known_exploited_vulnerabilities.json",
        "deployable":False,"public_release_allowed":False,"cti_vendor_connected":False}
class ReviewTests(unittest.TestCase):
    def test_internal_brief_not_incident_statement(self):
        with TemporaryDirectory() as folder:
            f=Path(folder)/"input.json"
            f.write_text(json.dumps(sample()),encoding="utf-8")
            out=m.triage(m.load(f),NOW)
            self.assertEqual(out["freshness"],"REVIEW_REQUIRED")
            self.assertFalse(out["public_release_allowed"])
            self.assertFalse(out["provider_darkweb_connected"])
            self.assertEqual(out["confirmed_customer_breaches"],0)
            self.assertEqual(out["recent_30d_entries"],1)
            self.assertEqual(out["customer_asset_matching"],"DISABLED_UNTIL_SIGNED_AUTHORIZATION")
    def test_stale_blocked(self):
        out=m.triage(sample(age=72),NOW)
        self.assertEqual(out["freshness"],"STALE_BLOCKED")
    def test_future_timestamp_blocked(self):
        with self.assertRaisesRegex(ValueError,"future"):
            m.triage(sample(age=-5),NOW)
    def test_release_flag_blocked(self):
        with TemporaryDirectory() as folder:
            d=sample();d["public_release_allowed"]=True
            f=Path(folder)/"input.json";f.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,"publication"):
                m.load(f)
    def test_attack_claim_blocked(self):
        with TemporaryDirectory() as folder:
            d=sample(overrides={"victim_or_outage_confirmed":True})
            f=Path(folder)/"input.json";f.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,"victim"):
                m.load(f)
    def test_tlp_restricted_or_license_blocked(self):
        with TemporaryDirectory() as folder:
            d=sample(overrides={"tlp":"AMBER"})
            f=Path(folder)/"input.json";f.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,"TLP"):
                m.load(f)
    def test_duplicate_cve_fails(self):
        with TemporaryDirectory() as folder:
            d=sample();d["records"].append(d["records"][0].copy());d["source_entries"]=2
            f=Path(folder)/"input.json";f.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                m.load(f)
    def test_public_destination_blocked(self):
        with TemporaryDirectory() as folder:
            target=Path(folder)/"public"/"private.json"
            with self.assertRaisesRegex(ValueError,"public"):
                m.approved_path(target)
    def test_preexisting_report_blocked(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/"report.json";p.write_text("{}")
            with self.assertRaisesRegex(ValueError,"exists"):
                m.approved_path(p)
    def test_oversized_input_blocked(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/"input.json";p.write_bytes(b"x"*(m.MAX_IN+1))
            with self.assertRaisesRegex(ValueError,"large"):
                m.load(p)
if __name__=="__main__": unittest.main()
