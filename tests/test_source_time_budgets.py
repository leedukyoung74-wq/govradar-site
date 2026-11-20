"""Offline controls: slow/hostile upstream sources cannot monopolize the daily job."""
import datetime as dt
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import feed_more as FM
import feed_tenders as FT

START = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?page=1"


class BoundedOCDS(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def test_cross_host_link_is_rejected_and_records_partial_failure(self):
        urls = []
        def get(src, url, **kwargs):
            urls.append(url)
            return json.dumps({"releases": [{"id": "one"}],
                               "links": {"next": "https://attacker.example/steal"}})
        with patch.object(FM, "_get", side_effect=get):
            result = FM._ocds("UK Find a Tender", START, lambda x: x)
        self.assertEqual(len(result), 1)
        self.assertEqual(urls, [START])
        self.assertEqual(FM.stat("UK Find a Tender")["failed"], 1)

    def test_downgrade_and_cycle_never_fetch_twice(self):
        for next_url in ("http://www.find-tender.service.gov.uk/else", START):
            with self.subTest(next_url=next_url):
                FM.STATS.clear()
                calls = []
                def get(src, url, **kwargs):
                    calls.append(url)
                    return json.dumps({"releases": [{"id": "one"}],
                                       "links": {"next": next_url}})
                with patch.object(FM, "_get", side_effect=get):
                    FM._ocds("UK Find a Tender", START, lambda x: x)
                self.assertEqual(calls, [START])
                self.assertEqual(FM.stat("UK Find a Tender")["failed"], 1)

    def test_relative_page_query_is_supported(self):
        urls = []
        def get(src, url, **kwargs):
            urls.append(url)
            nxt = "?page=2" if len(urls) == 1 else None
            return json.dumps({"releases": [{"id": str(len(urls))}],
                               "links": {"next": nxt}})
        with patch.object(FM, "_get", side_effect=get):
            items = FM._ocds("UK Find a Tender", START, lambda x: x)
        self.assertEqual([x["id"] for x in items], ["1", "2"])
        self.assertEqual(urls[-1], START.replace("page=1", "page=2"))

    def test_wall_clock_expiration_marks_failed_without_fetching(self):
        with patch("time.monotonic", side_effect=[10, 200]), patch.object(FM, "_get") as get:
            items = FM._ocds("UK Find a Tender", START, lambda x: x)
        self.assertEqual(items, [])
        get.assert_not_called()
        self.assertEqual(FM.stat("UK Find a Tender")["failed"], 1)

    def test_retries_have_lower_per_call_bound(self):
        calls = []
        def get(src, url, **kwargs):
            calls.append(kwargs)
            return json.dumps({"releases": [], "links": {}})
        with patch.object(FM, "_get", side_effect=get):
            FM._ocds("UK Find a Tender", START, lambda x: x)
        self.assertEqual(calls[0], {"tries": 2, "timeout": 30})


class BoundedProzorro(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def test_ukraine_pagination_cannot_escape_official_host(self):
        import tempfile
        candidates = [{"id": "x", "status": "complete", "dateModified": FM.TODAY.isoformat()}]
        with tempfile.TemporaryDirectory() as tmp:
            for next_url in ("https://example.org/api/data",
                             "http://public-api.prozorro.gov.ua/api/2.5/tenders",
                             "https://public-api.prozorro.gov.ua/api/2.5/tenders?descending=1&limit=1000&opt_fields=status%2CprocurementMethodType%2CtenderPeriod%2CtenderID"):
                with self.subTest(next_url=next_url):
                    FM.STATS.clear()
                    called = []
                    def fake_get(src, url, **kwargs):
                        called.append(url)
                        return json.dumps({"data": candidates, "next_page": {"uri": next_url}})
                    with patch.object(FM, "FEEDS", tmp), patch.object(FM, "_get", side_effect=fake_get):
                        self.assertEqual(FM.prozorro(), [])
                    self.assertEqual(len(called), 1 if not next_url.startswith("https://public-api.prozorro.gov.ua/api/2.5/tenders") else 2)
                    self.assertGreaterEqual(FM.stat("Prozorro (Ukraine)")["failed"], 1)


class BoundedTED(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def test_deadline_exhaustion_marks_partial_without_requests(self):
        with patch("time.monotonic", side_effect=[10, 200, 201]), patch.object(FM, "_post") as post:
            self.assertEqual(FM.ted(), [])
        post.assert_not_called()
        self.assertGreater(FM.stat("EU TED")["failed"], 0)

    def test_public_api_uses_short_request_limits(self):
        calls = []
        def post(src, url, body, **kwargs):
            calls.append(kwargs)
            return {"notices": []}
        with patch.object(FM, "_post", side_effect=post):
            self.assertEqual(FM.ted(), [])
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(x == {"tries": 2, "timeout": 30} for x in calls))


class CarryTimeBudget(unittest.TestCase):
    def test_unverified_carried_notice_becomes_stale_when_expired(self):
        now = dt.datetime(2026, 11, 20, 8, tzinfo=dt.timezone.utc)
        notice = {
            "iso": "KR", "source": "UK Find a Tender", "title": "Verified tender",
            "buyer": "Public authority", "url": "https://www.find-tender.service.gov.uk/Notice/123",
            "sid": "123", "deadline": "2026-12-01", "deadline_at": "2026-12-01",
            "added": "2026-11-19",
        }
        stamp = now.strftime("%Y-%m-%dT%H:%MZ")
        with patch("time.monotonic", return_value=200):
            extra, counts = FT.carry("UK Find a Tender", [], "ERROR",
                                     {notice["url"]: notice}, now, stamp,
                                     lambda item: self.fail("expired lookup must not run"),
                                     [40, 100])
        self.assertEqual(counts["verify_lookups"], 0)
        self.assertEqual(counts["carried_stale"], 1)
        self.assertTrue(extra[0]["stale"])
        self.assertEqual(extra[0]["verify"], "partial")

    def test_legacy_single_slot_budget_remains_supported(self):
        now = dt.datetime(2026, 11, 20, 8, tzinfo=dt.timezone.utc)
        notice = {"source": "UK Find a Tender", "sid": "1", "title": "Tender",
                  "url": "https://www.find-tender.service.gov.uk/Notice/1",
                  "deadline": "2026-12-01"}
        extra, counts = FT.carry("UK Find a Tender", [], "ERROR",
                                {notice["url"]: notice}, now, "2026-11-20T08:00Z",
                                lambda x: None, [1])
        self.assertEqual(counts["verify_lookups"], 1)
        self.assertTrue(extra[0]["stale"])


if __name__ == "__main__":
    unittest.main()
