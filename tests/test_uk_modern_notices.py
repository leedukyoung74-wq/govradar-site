"""UK FTS modern Procurement Act notices must not be lost on gross-only values."""
import datetime as dt
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import feed_more as FM


class UKModernNoticesTests(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()
        future=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=30))
        self.deadline=future.strftime("%Y-%m-%dT%H:%M:%SZ")

    def row(self, value):
        return {
            "id":"2026-S-100", "ocid":"ocds-uk-test-123",
            "buyer":{"name":"Public authority"},
            "tender":{"status":"active","title":"Public technology purchase",
                      "tenderPeriod":{"endDate":self.deadline},
                      "value":value}
        }

    def test_gross_only_estimate_kept_and_labelled(self):
        row=FM._ocds_item("UK Find a Tender",self.row(
            {"amountGross":2500000,"currency":"GBP"}),"https://www.find-tender.service.gov.uk/Notice/example")
        self.assertIsNotNone(row)
        self.assertEqual("2500000",row["est"])
        self.assertTrue(row["est_gross"])
        self.assertEqual("GB",row["iso"])

    def test_net_amount_preferred_over_gross_when_both_present(self):
        row=FM._ocds_item("UK Find a Tender",self.row(
            {"amount":2400000,"amountGross":3000000,"currency":"GBP"}),"https://www.find-tender.service.gov.uk/Notice/example")
        self.assertIsNotNone(row)
        self.assertEqual("2400000",row["est"])
        self.assertFalse(row["est_gross"])

    def test_invalid_value_not_included_as_open_procurement(self):
        row=FM._ocds_item("UK Find a Tender",self.row(
            {"amountGross":"not-a-value","currency":"GBP"}),"https://www.find-tender.service.gov.uk/Notice/example")
        self.assertIsNone(row)
        self.assertEqual(1,FM.STATS["UK Find a Tender"]["filtered"].get("invalid-estimate"))

    def test_uk_feed_does_not_filter_out_modern_notice_stages(self):
        with patch.object(FM,"_ocds",return_value=[]) as get:
            self.assertEqual([],FM.uk())
            called_url=get.call_args.args[1]
            self.assertIn("updatedFrom=",called_url)
            self.assertNotIn("stages=",called_url)
            self.assertEqual("UK Find a Tender",get.call_args.args[0])


if __name__=="__main__":
    unittest.main()
