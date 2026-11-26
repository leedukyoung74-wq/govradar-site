"""Unit tests of the read-only procurement provenance review; no network or deployment."""
import datetime as dt
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("tender_truth",ROOT/"ops/wmm_tender_truth_review.py")
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
UTC=dt.timezone.utc


class FakeCanonicalDeadline:
    """Minimal contract mock: deliberately no status from title/country similarity."""
    @staticmethod
    def state(row,now):
        return "closed" if row.get("deadline")<now.date().isoformat() else "date_only"
    @classmethod
    def is_listed_open(cls,row,now):
        return cls.state(row,now)!="closed" and row.get("stale") is not True


class TenderTruthReviewTests(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime(2026,11,21,7,0,tzinfo=UTC)
        self.live={"index_kind":"unverified_country_brief_candidates",
                   "automated_customer_alerts_allowed":False,
                   "verified_official_notice_count":0,
                   "items":[]}
        for k in range(240):
            kind="tenders" if k<235 else "biz"
            self.live["items"].append({"iso":"KR","kind":kind,"slug":"korea",
                "ko":"WMM 가상 분석 "+str(k),"en":"Research only",
                "deadline":"","official_notice_verified":False,
                "may_send_business_alert":False,"is_live_tender":False})
        self.official_rows=[]
        for k in range(105):
            self.official_rows.append({
                "iso":"KR","title":"Foreign source listing "+str(k),
                "deadline":"2026-11-22","deadline_at":"2026-11-22",
                "source":"EU TED","url":"https://ted.europa.eu/en/notice/"+str(k),
                "sid":"TED-"+str(k),"verify":"search","stale":False})
        for k in range(5):
            self.official_rows[k]["verify"]="partial"
            self.official_rows[k]["stale"]=True
        self.feed={"count":len(self.official_rows),"updated":"2026-11-21T06:50Z","items":self.official_rows}
        self.country={"updated":"2026-11-21T06:59Z","t":{"n":100,"c":1}}

    def audit(self):
        return M.audit(self.live,self.feed,self.country,FakeCanonicalDeadline,self.now)

    def test_all_235_country_hypotheses_stay_unverified(self):
        r=self.audit()
        self.assertTrue(r["all_checks_pass"],r["invariants"])
        self.assertEqual(r["country_brief_index"]["tender_candidate_rows"],235)
        self.assertEqual(r["country_brief_index"]["issues"]["MISSING_INDIVIDUAL_OFFICIAL_NOTICE_URL"],235)
        self.assertEqual(r["country_brief_index"]["real_official_tenders_promoted"],0)
        self.assertEqual(r["notifications_sent"],0)
        self.assertEqual(len(r["country_brief_index"]["human_review_first_25"]),25)
        self.assertTrue(all(row["official_publication_approved"] is False for row in r["country_brief_index"]["human_review_first_25"]))

    def test_summary_reconciles_to_canonical_open_only_not_raw_count(self):
        r=self.audit()
        self.assertEqual(r["official_procurement_feed"]["records"],105)
        self.assertEqual(r["official_procurement_feed"]["listed_at_country_summary_time"],100)
        self.assertEqual(r["official_procurement_feed"]["country_summary_reported_count"],100)
        self.assertEqual(r["official_procurement_feed"]["verification_grades"],{"search":100,"partial":5})
        self.assertTrue(r["invariants"]["summary_count_matches_canonical_deadline_at_summary_time"])

    def test_report_does_not_equate_search_with_individual_source_confirmation(self):
        r=self.audit()
        self.assertEqual(r["official_procurement_feed"]["individual_record_reread_grade_current"],0)
        self.assertIn("개별 공고",r["official_procurement_feed"]["search_grade_warning_ko"])
        self.assertIn("UTC-12",r["official_procurement_feed"]["date_only_warning_ko"])

    def test_mismatched_summary_count_fails_without_auto_repairing_it(self):
        self.country["t"]["n"]=101
        r=self.audit()
        self.assertFalse(r["all_checks_pass"])
        self.assertFalse(r["invariants"]["summary_count_matches_canonical_deadline_at_summary_time"])

    def test_mismatched_or_spoofed_original_source_domain_fails(self):
        self.official_rows[10]["url"]="https://ted.europa.eu.evil.example/en/notice/10"
        r=self.audit()
        self.assertFalse(r["invariants"]["no_unapproved_source_hosts"])
        self.assertFalse(r["all_checks_pass"])

    def test_exact_sam_gov_domain_is_accepted(self):
        self.official_rows[10]["source"]="SAM.gov (US)"
        self.official_rows[10]["url"]="https://sam.gov/workspace/contract/opp/1234567890abcdef1234567890abcdef/view"
        self.assertTrue(self.audit()["invariants"]["no_unapproved_source_hosts"])

    def test_sam_gov_spoof_or_subdomain_is_rejected(self):
        self.official_rows[10]["source"]="SAM.gov (US)"
        for url in (
            "https://sam.gov.evil.example/workspace/contract/opp/abc/view",
            "https://www.sam.gov/workspace/contract/opp/abc/view",
            "http://sam.gov/workspace/contract/opp/abc/view",
            "https://sam.gov:444/workspace/contract/opp/abc/view",
            "https://user@sam.gov/workspace/contract/opp/abc/view",
        ):
            with self.subTest(url=url):
                self.official_rows[10]["url"]=url
                self.assertFalse(self.audit()["invariants"]["no_unapproved_source_hosts"])

    def test_any_customer_alert_flag_for_unverified_country_brief_fails(self):
        self.live["items"][7]["may_send_business_alert"]=True
        r=self.audit()
        self.assertFalse(r["all_checks_pass"])
        self.assertEqual(r["country_brief_index"]["issues"]["ALERT_PERMISSION_NOT_BLOCKED"],1)

    def test_false_confirmed_tender_flag_fails(self):
        self.live["items"][1]["is_live_tender"]=True
        r=self.audit()
        self.assertFalse(r["all_checks_pass"])

    def test_duplicate_source_id_fails(self):
        self.official_rows[10]["sid"]=self.official_rows[9]["sid"]
        self.assertFalse(self.audit()["all_checks_pass"])

    def test_bool_zero_is_not_a_valid_verified_notice_counter(self):
        self.live["verified_official_notice_count"]=False
        self.assertFalse(self.audit()["all_checks_pass"])

    def test_no_network_and_invalid_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/"test.json"
            path.write_text(json.dumps(self.feed),encoding="utf8")
            with patch.object(M,"load_deadline_rules",side_effect=AssertionError("must not run")):
                self.assertEqual(M.load_json(path)["count"],105)
            with self.assertRaises(ValueError):
                M.audit({},self.feed,self.country,FakeCanonicalDeadline,self.now)
            with self.assertRaises(ValueError):
                M.audit(self.live,self.feed,self.country,FakeCanonicalDeadline,dt.datetime(2026,11,21))


if __name__=="__main__":
    unittest.main()
