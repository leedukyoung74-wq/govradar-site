"""Offline contract: country-brief opportunity index cannot claim to be a verified public tender."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "build.py"


class OpportunityEvidenceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_output_json_declares_no_verified_notices(self):
        self.assertIn('"index_kind": "unverified_country_brief_candidates"', self.source)
        self.assertIn('"verified_official_notice_count": 0', self.source)
        self.assertIn('"automated_customer_alerts_allowed": False', self.source)
        self.assertIn('"source_evidence_policy":', self.source)

    def test_each_generated_record_remains_non_alertable(self):
        self.assertIn('"source_review_status": "individual_notice_unverified"', self.source)
        self.assertIn('"official_notice_verified": False', self.source)
        self.assertIn('"may_send_business_alert": False', self.source)
        self.assertIn('"is_live_tender": False', self.source)
        self.assertNotIn('"may_send_business_alert": True', self.source)

    def test_widget_fail_closed_if_source_policy_missing(self):
        self.assertIn('if(o.automated_customer_alerts_allowed!==false', self.source)
        self.assertIn('o.verified_official_notice_count!==0', self.source)
        self.assertIn('o.index_kind!=="unverified_country_brief_candidates"', self.source)

    def test_widget_warns_all_seven_supported_languages(self):
        import re
        match = re.search(r'const warning=\{(.*?)\};\s*document\.getElementById\("source-disclaimer"\)',self.source,re.S)
        self.assertIsNotNone(match)
        for language in ("ko","en","es","fr","ar","vi","id"):
            self.assertIn(language + ':', match.group(1))
        self.assertIn('document.getElementById("source-disclaimer").textContent=warning[L]||warning.en',self.source)

    def test_user_facing_badge_marks_unverified_individual_entry(self):
        self.assertIn('x.official_notice_verified===false?"⚠ ":""',self.source)
        self.assertIn('id="source-disclaimer" role="note"',self.source)

    def test_widget_hides_deadlines_for_unverified_candidates(self):
        self.assertIn('x.official_notice_verified===true&&x.deadline', self.source)

    def test_widget_still_uses_textcontent_for_untrusted_titles(self):
        self.assertIn('li.querySelector(".t").textContent=x[lk]||x.en',self.source)
        self.assertIn('li.querySelector("small").textContent=',self.source)

    def test_index_source_types_may_not_be_called_validated_bids(self):
        self.assertIn('("biz", d.get("biz"), en.get("biz"))',self.source)
        self.assertIn('("tenders", d.get("tenders"), en.get("tenders"))',self.source)
        self.assertIn('("oda", d.get("oda"), en.get("oda"))',self.source)
        self.assertIn('Individual official notice URL + current publication deadline',self.source)

    def test_no_new_network_or_customer_notification_service(self):
        for snippet in ("import smtplib","sendgrid","mailgun","customer_email","CALL_PAYMENT_API"):
            self.assertNotIn(snippet,self.source)


if __name__ == "__main__":
    unittest.main()
