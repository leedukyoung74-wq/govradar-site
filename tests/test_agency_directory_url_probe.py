"""Offline checks for nine candidate agency websites; never performs network I/O."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ops"))
import verify_official_directory_urls as mod


class AgencyDirectoryReachabilityTests(unittest.TestCase):
    def test_catalog_nine_unverified_candidates_and_strict_hosts(self):
        d = json.loads((ROOT / "src/environment_weather_emergency_sites.json").read_text(encoding="utf-8"))
        items = mod.candidates(d)
        self.assertEqual(len(items), 9)
        self.assertEqual({x["iso"] for x in items}, {"CV", "CM", "ET"})
        self.assertEqual({x["category"] for x in items}, set(mod.CATEGORIES))
        self.assertEqual(len({x["host"] for x in items}), 9)

    def test_mismatched_http_userinfo_ip_redirect_and_tracking_fragment_denied(self):
        for bad in (
            "http://maa.gov.cv/",
            "https://maa.gov.cv.evil.example/",
            "https://user:pass@maa.gov.cv/",
            "https://127.0.0.1/",
            "https://maa.gov.cv:8443/",
            "https://maa.gov.cv/#fragment",
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                mod.validate_url(bad, "maa.gov.cv")
        self.assertEqual(mod.validate_url("https://www.maa.gov.cv/a?b=1", "maa.gov.cv"),
                         "https://www.maa.gov.cv/a?b=1")

    def test_redirect_outside_official_host_denied(self):
        handler = mod.RestrictedRedirects("maa.gov.cv")
        request = MagicMock()
        with self.assertRaises(ValueError):
            handler.redirect_request(request, None, 302, "Moved", {}, "https://example.net/")

    def test_head_200_only_means_homepage_reachability(self):
        item = {"iso": "CV", "category": "environment", "host": "maa.gov.cv",
                "url": "https://www.maa.gov.cv/"}
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
