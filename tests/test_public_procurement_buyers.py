"""Free public procurement organization list: never treat as commercial importers."""
import datetime as dt
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_public_procurement_buyers as BP

NOW=dt.datetime(2026,11,20,14,tzinfo=dt.timezone.utc)

def entry(**kw):
    value={"iso":"GB","source":"UK Find a Tender","buyer":"London Borough of Camden",
           "title":"Public technology procurement",
           "url":"https://www.find-tender.service.gov.uk/Notice/123",
           "deadline":"2026-12-01","deadline_at":"2026-12-01","stale":False}
    value.update(kw)
    return value

class PublicProcurementBuyersTests(unittest.TestCase):
    def test_sourced_open_records_are_grouped_and_deduplicated(self):
        rows=[entry(),entry(),entry(title="Other notice",
                      url="https://www.find-tender.service.gov.uk/Notice/456"),
              entry(buyer="City of Bristol",url="https://www.find-tender.service.gov.uk/Notice/789")]
        output=BP.build(rows,NOW)
        self.assertEqual(2,len(output["organisations"]))
        self.assertEqual("source_backed_public_procurement_organisations",output["type"])
        self.assertTrue(output["not_commercial_buyer_directory"])
        self.assertEqual(2,output["organisations"][0]["source_backed_notice_count"])
        self.assertEqual(1,output["country_count"])
        self.assertIn("notices",output["organisations"][0])

    def test_closed_stale_and_malformed_or_unofficial_notice_rejected(self):
        rows=[entry(stale=True),entry(deadline="2025-01-01",deadline_at="2025-01-01"),
              entry(url="https://attacker.example/Notice/123"),
              entry(source="UNVERIFIED BLOG"),
              entry(url="http://www.find-tender.service.gov.uk/Notice/123"),
              entry(url="https://www.find-tender.service.gov.uk\\@evil.test/Notice/123"),
              entry(url="https://www.find-tender.service.gov.uk/Notice/123#fragment"),
              entry(buyer="name@example.org"),
              entry(status="cancelled"),
              entry(url="https://www.find-tender.service.gov.uk/Notice/ok")]
        results=BP.build(rows,NOW)
        self.assertEqual(1,len(results["organisations"]))
        self.assertEqual(1,results["organisations"][0]["source_backed_notice_count"])

    def test_no_missing_links_are_fabricated(self):
        self.assertEqual([],BP.build([],NOW)["organisations"])
        self.assertFalse(BP.safe_official_notice(entry(url="https://sam.gov/")))
        self.assertEqual("",BP.normalize_organisation("+82 10-1234-5678"))
        with self.assertRaises(ValueError):
            BP.build([],dt.datetime(2026,11,20))

if __name__=="__main__":
    unittest.main()
