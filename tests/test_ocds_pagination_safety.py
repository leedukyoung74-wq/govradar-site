"""No untrusted pagination redirects while collecting UK OCDS source data."""
import json
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import feed_more as FM

START = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?page=1"

class OCDSPaginationSafetyTests(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def run_pages(self, first_next):
        calls = []
        def fake_get(source, url):
            calls.append(url)
            return json.dumps({"releases": [{"id": str(len(calls))}], "links": {"next": first_next}})
        with patch.object(FM, "_get", side_effect=fake_get):
            rows = FM._ocds("UK Find a Tender", START, lambda r: r)
        return rows, calls

    def test_external_host_is_never_requested(self):
        rows, calls = self.run_pages("https://example.org/collect")
        self.assertEqual(1, len(rows))
        self.assertEqual([START], calls)

    def test_http_downgrade_is_never_requested(self):
        rows, calls = self.run_pages("http://www.find-tender.service.gov.uk/elsewhere")
        self.assertEqual(1, len(rows))
        self.assertEqual([START], calls)

    def test_repeated_page_exits_without_extra_request(self):
        rows, calls = self.run_pages(START)
        self.assertEqual(1, len(rows))
        self.assertEqual([START], calls)

    def test_relative_next_page_on_same_host_is_supported(self):
        url2 = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?page=2"
        calls = []
        def fake_get(source, url):
            calls.append(url)
            nxt = "?page=2" if len(calls) == 1 else None
            return json.dumps({"releases": [{"id": str(len(calls))}], "links": {"next": nxt}})
        with patch.object(FM, "_get", side_effect=fake_get):
            rows = FM._ocds("UK Find a Tender", START, lambda r: r)
        self.assertEqual(2, len(rows))
        self.assertEqual([START, url2], calls)

if __name__ == "__main__":
    unittest.main()
