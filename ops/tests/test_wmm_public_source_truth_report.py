"""Offline-only deterministic tests; no live API, checkout writes or payments."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"ops"/"wmm_public_source_truth_report.py"
SPEC=importlib.util.spec_from_file_location("wmm_public_source_truth_report",SCRIPT)
P=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)
NOW=dt.datetime(2026,11,27,12,30,tzinfo=dt.timezone.utc)


def mock_inputs(age_hours=2):
    opps={"updated":"2026-11-09","items":[{"kind":"biz","deadline":""},
                                            {"kind":"tenders","deadline":"2026-12-01"}]}
    countries=[{"done":True},{"done":False}]
    regions=[{"done":False}]
    tenders={"updated":(NOW-dt.timedelta(hours=age_hours)).isoformat(),
             "items":[{"verify":"search"},{"verify":"full"},{"verify":"partial"}]}
    sources={"World Bank":{"state":"SUCCESS","kept":317},
             "UK Find a Tender":{"state":"PARTIAL","coverage_partial":True},
             "DAPA (Korea)":{"state":"SUCCESS","kept":0}}
    site={"result":"PASS","pages":[{"page":"/ko/","status":200},
                                    {"page":"/ko/about/","status":200}]}
    return opps,countries,regions,tenders,sources,site


class PublicProvenanceTests(unittest.TestCase):
    def test_static_snapshot_is_never_current_tender_coverage(self):
        r=P.build(*mock_inputs(),now=NOW)
        self.assertEqual(r["result"],"PENDING")
        self.assertEqual(r["static_opportunity_snapshot"]["classification"],
                         "CURATED_RESEARCH_SNAPSHOT_NOT_LIVE_TENDER")
        self.assertEqual(r["static_opportunity_snapshot"]["items"],2)
        self.assertEqual(r["static_opportunity_snapshot"]["with_evidence_url"],0)
        self.assertEqual(r["static_opportunity_snapshot"]["with_deadline"],1)
        self.assertEqual(r["official_tenders"]["verification_grades"],
                         {"search":1,"full":1,"partial":1,"unknown":0})
        self.assertEqual(r["collector_coverage"]["partial_sources"],1)
        self.assertFalse(r["site_smoke_evidence"]["login_payment_forms_verified"])

    def test_tenders_stale_even_if_site_smoke_says_pass(self):
        r=P.build(*mock_inputs(age_hours=40),now=NOW)
        self.assertEqual(r["result"],"FAIL")
        self.assertEqual(r["official_tenders"]["freshness"],"STALE")
        self.assertIn("PUBLISHED_TENDER_FRESHNESS_UNVERIFIED",r["warnings"])

    def test_unparseable_or_future_timestamp_is_not_pass(self):
        v=list(mock_inputs())
        v[3]={"updated":"not-a-time","items":[]}
        self.assertEqual(P.build(*v,now=NOW)["result"],"FAIL")
        v[3]={"updated":(NOW+dt.timedelta(hours=2)).isoformat(),"items":[]}
        self.assertEqual(P.build(*v,now=NOW)["result"],"FAIL")

    def test_verified_full_count_cannot_be_inferred_from_search(self):
        v=list(mock_inputs())
        v[3]["items"]=[{"verify":"full"},{"verify":"full"}]
        r=P.build(*v,now=NOW)
        self.assertTrue(r["official_tenders"]["all_items_individually_verified"])
        self.assertEqual(r["official_tenders"]["verification_grades"]["search"],0)
        self.assertEqual(r["result"],"PENDING")  # Other coverage gaps remain.

    def test_get_public_is_frozen_allowlist(self):
        with self.assertRaises(ValueError):
            P.get_public("http://evil.invalid")
        with self.assertRaises(ValueError):
            P.get_public("sam_key.json")

    def test_no_new_schedule_checkout_or_customer_post(self):
        s=(ROOT/".github"/"workflows"/"wmm_operations_watch.yml").read_text()
        self.assertIn("cron: '17 * * * *'",s)
        self.assertIn("ops/wmm_public_source_truth_report.py",s)
        self.assertIn("persist-credentials: false",s)
        self.assertIn("if: always()",s)
        code=SCRIPT.read_text()
        self.assertNotIn("urllib.request.Request(url, data=",code)
        self.assertNotIn("POST",code.split("def get_public")[1].split("def timestamp")[0])
        self.assertNotIn("github_token",code.lower())


if __name__=="__main__":
    unittest.main()
