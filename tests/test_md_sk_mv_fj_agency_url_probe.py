"""Offline checks for eleven candidate agency websites; never performs network I/O."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ops"))
import verify_md_sk_mv_fj_agency_urls as mod


class AgencyDirectoryReachabilityTests(unittest.TestCase):
    def test_catalog_eleven_unverified_candidates_and_strict_hosts(self):
        d = json.loads((ROOT / "src/environment_weather_emergency_sites.json").read_text(encoding="utf-8"))
        items = mod.candidates(d)
        self.assertEqual(len(items), 11)
        self.assertEqual({x["iso"] for x in items}, {"MD", "SK", "MV", "FJ"})
        self.assertEqual({x["category"] for x in items}, set(mod.CATEGORIES))
        self.assertEqual({x["category"] for x in items if x["iso"]=="FJ"}, {"environment","emergency"})
        self.assertEqual(len({x["host"] for x in items}), 11)

    def test_mismatched_http_userinfo_ip_redirect_and_tracking_fragment_denied(self):
        for bad in (
            "http://mediu.gov.md/",
            "https://mediu.gov.md.evil.example/",
            "https://user:pass@mediu.gov.md/",
            "https://127.0.0.1/",
            "https://mediu.gov.md:8443/",
            "https://mediu.gov.md/#fragment",
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                mod.validate_url(bad, "mediu.gov.md")
        self.assertEqual(mod.validate_url("https://www.mediu.gov.md/a?b=1", "mediu.gov.md"),
                         "https://www.mediu.gov.md/a?b=1")

    def test_redirect_outside_official_host_denied(self):
        handler = mod.RestrictedRedirects("mediu.gov.md")
        request = MagicMock()
        with self.assertRaises(ValueError):
            handler.redirect_request(request, None, 302, "Moved", {}, "https://example.net/")

    def test_head_200_only_means_homepage_reachability(self):
        item = {"iso": "MD", "category": "environment", "host": "mediu.gov.md",
                "url": "https://www.mediu.gov.md/"}
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
