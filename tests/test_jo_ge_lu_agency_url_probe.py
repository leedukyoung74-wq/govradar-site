"""Offline checks for nine candidate agency websites; never performs network I/O."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ops"))
import verify_jo_ge_lu_agency_urls as mod


class AgencyDirectoryReachabilityTests(unittest.TestCase):
    def test_catalog_nine_unverified_candidates_and_strict_hosts(self):
        d = json.loads((ROOT / "src/environment_weather_emergency_sites.json").read_text(encoding="utf-8"))
        items = mod.candidates(d)
        self.assertEqual(len(items), 9)
        self.assertEqual({x["iso"] for x in items}, {"JO", "GE", "LU"})
        self.assertEqual({x["category"] for x in items}, set(mod.CATEGORIES))
        self.assertEqual(len({x["host"] for x in items}), 9)

    def test_mismatched_http_userinfo_ip_redirect_and_tracking_fragment_denied(self):
        for bad in (
            "http://moenv.gov.jo/",
            "https://moenv.gov.jo.evil.example/",
            "https://user:pass@moenv.gov.jo/",
            "https://127.0.0.1/",
            "https://moenv.gov.jo:8443/",
            "https://moenv.gov.jo/#fragment",
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                mod.validate_url(bad, "moenv.gov.jo")
        self.assertEqual(mod.validate_url("https://www.moenv.gov.jo/a?b=1", "moenv.gov.jo"),
                         "https://www.moenv.gov.jo/a?b=1")

    def test_redirect_outside_official_host_denied(self):
        handler = mod.RestrictedRedirects("moenv.gov.jo")
        request = MagicMock()
        with self.assertRaises(ValueError):
            handler.redirect_request(request, None, 302, "Moved", {}, "https://example.net/")

    def test_head_200_only_means_homepage_reachability(self):
        item = {"iso": "JO", "category": "environment", "host": "moenv.gov.jo",
                "url": "https://www.moenv.gov.jo/"}
        response = MagicMock()
        response.status = 200
        response.geturl.return_value = item["url"]
        manager = MagicMock()
        manager.__enter__.return_value = response
        opener = MagicMock()
        opener.open.return_value = manager
        r = mod.probe_one(item, opener_factory=lambda _handler: opener)
        self.assertTrue(r["reachable_http_200"])
        self.assertEqual(r["http_status"], 200)
        self.assertFalse(r["feed_confirmed"])
        self.assertFalse(r["license_confirmed"])
        self.assertEqual(r["evidence_kind"], "homepage_head_only")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 10)
        self.assertEqual(opener.open.call_args.args[0].get_method(), "HEAD")


if __name__ == "__main__":
    unittest.main()
