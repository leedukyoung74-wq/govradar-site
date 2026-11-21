"""Deterministic safety tests for official-only business action preview (no network)."""
import datetime as dt
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import wmm_business_action_preview as M

NOW = dt.datetime(2026, 11, 21, 4, 0, tzinfo=dt.timezone.utc)


def nws():
    return {
        "schema": "wmm.nws.v1", "kind": "active_us_weather_alerts",
        "source_url": M.NWS_SOURCE, "coverage": "United States only",
        "not_global_all_clear": True, "partial_coverage": False,
        "source_health": {"ok": True, "stale": False, "last_ok": "2026-11-21T03:00:00Z"},
        "items": [{
            "src": "NWS", "event": "Flash Flood Warning",
            "title": "Flash Flood Warning near Example County",
            "area": "Example County, Example State",
            "severity": "Extreme", "urgency": "Immediate", "certainty": "Likely",
            "issued_at": "2026-11-21T02:00:00Z", "ends_at": "2026-11-21T07:00:00Z",
            "url": "https://api.weather.gov/alerts/urn:oid:test"
        }]
    }


def cisa():
    return {
        "schema": "wmm.cisa.kev.v1",
        "kind": "known_exploited_vulnerabilities",
        "source_url": M.CISA_SOURCE, "not_realtime_attack_feed": True,
        "total_vulnerabilities": 1200,
        "source_health": {"ok": True, "stale": False, "last_ok": "2026-11-21T00:30:00Z"},
        "items": [{
            "cve": "CVE-2026-123456", "vendor": "ExampleCorp",
            "product": "Example Server", "date_added": "2026-11-20",
            "due_date": "2026-11-23",
            "url": "https://nvd.nist.gov/vuln/detail/CVE-2026-123456"
        }]
    }


class BusinessActionPreviewTests(unittest.TestCase):
    def test_valid_alert_produces_human_review_not_automatic_closure(self):
        x = M.build_preview(nws(), cisa(), NOW)
        self.assertEqual(x["schema"], "wmm.business-action.review.v1")
        self.assertEqual(x["status"], "INTERNAL_PREVIEW_ONLY")
        self.assertFalse(x["customer_matching_performed"])
        self.assertFalse(x["customer_notifications_sent"])
        self.assertFalse(x["site_published"])
        self.assertFalse(x["paid_api_used"])
        cards = x["source_modules"][0]["cards"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["iso"], "US")
        self.assertEqual(cards[0]["priority"], "URGENT_HUMAN_REVIEW")
        self.assertEqual(cards[0]["action_code"], "CHECK_SITE_SAFETY")
        self.assertFalse(cards[0]["client_impact_confirmed"])
        self.assertFalse(cards[0]["customer_geolocation_matched"])
        self.assertFalse(cards[0]["notification_allowed"])

    def test_stale_nws_keeps_no_fake_live_cards(self):
        x = nws()
        x["source_health"]["last_ok"] = "2026-11-20T23:00:00Z"
        a = M.weather_cards(x, NOW)
        self.assertEqual(a["state"], "SOURCE_STALE")
        self.assertEqual(a["cards"], [])

    def test_upstream_failure_last_good_is_suppressed(self):
        x = nws()
        x["source_health"] = {"ok": False, "stale": True, "last_ok": "2026-11-21T03:30:00Z"}
        self.assertEqual(M.weather_cards(x, NOW)["state"], "SOURCE_UNVERIFIED")
        y = cisa()
        y["source_health"]["stale"] = True
        self.assertEqual(M.kev_cards(y, NOW)["cards"], [])

    def test_missing_health_is_not_considered_current(self):
        x = nws()
        del x["source_health"]
        self.assertEqual(M.weather_cards(x, NOW)["state"], "SOURCE_UNVERIFIED")
        y = cisa()
        y["source_health"]["last_ok"] = "not_a_time"
        self.assertEqual(M.kev_cards(y, NOW)["state"], "SOURCE_UNVERIFIED")

    def test_expired_or_future_weather_is_excluded(self):
        x = nws()
        x["items"][0]["ends_at"] = "2026-11-21T03:00:00Z"
        self.assertEqual(M.weather_cards(x, NOW)["cards"], [])
        x["items"][0]["ends_at"] = ""
        self.assertEqual(M.weather_cards(x, NOW)["cards"], [])
        x["items"][0]["ends_at"] = "2026-11-21T07:00:00Z"
        x["items"][0]["issued_at"] = "2026-11-21T06:00:00Z"
        self.assertEqual(M.weather_cards(x, NOW)["cards"], [])

    def test_nonsevere_or_unverified_origin_is_excluded(self):
        x = nws()
        x["items"][0]["severity"] = "Moderate"
        self.assertEqual(M.weather_cards(x, NOW)["cards"], [])
        x["items"][0]["severity"] = "Severe"
        x["items"][0]["src"] = "anonymous"
        self.assertEqual(M.weather_cards(x, NOW)["cards"], [])

    def test_nws_wrong_schema_or_jurisdiction_is_blocked(self):
        x = nws()
        x["coverage"] = "Global"
        self.assertEqual(M.weather_cards(x, NOW)["state"], "INVALID_SOURCE")
        x["coverage"] = "United States only"
        x["source_url"] = "https://attacker.example.com/alerts"
        self.assertEqual(M.weather_cards(x, NOW)["state"], "INVALID_SOURCE")

    def test_fake_or_retired_official_alert_url_reverts_to_api(self):
        x = nws()
        x["items"][0]["url"] = "https://api.weather.gov.evil.org/alerts"
        self.assertEqual(M.weather_cards(x, NOW)["cards"][0]["source_url"], M.NWS_SOURCE)
        x["items"][0]["url"] = "https://alice:pw@api.weather.gov/alerts"
        self.assertEqual(M.weather_cards(x, NOW)["cards"][0]["source_url"], M.NWS_SOURCE)
        x["items"][0]["url"] = "https://www.weather.gov/alerts"
        self.assertEqual(M.weather_cards(x, NOW)["cards"][0]["source_url"], M.NWS_SOURCE)

    def test_malicious_title_scrubbed_and_duplicate_suppressed(self):
        x = nws()
        x["items"][0]["title"] = "<script>alert(1)</script>\nFlash Flood"
        x["items"].append(dict(x["items"][0]))
        cards = M.weather_cards(x, NOW)["cards"]
        self.assertEqual(len(cards), 1)
        self.assertNotIn("<", cards[0]["title"])
        self.assertNotIn("\n", cards[0]["title"])

    def test_nws_partial_coverage_remains_visible_as_partial(self):
        x = nws()
        x["partial_coverage"] = True
        result = M.weather_cards(x, NOW)
        self.assertEqual(result["state"], "PARTIAL_COVERAGE")
        self.assertEqual(len(result["cards"]), 1)
        self.assertTrue(result["zero_cards_not_all_clear"])

    def test_cisa_requires_cisa_schema_and_breach_disclaimer(self):
        x = cisa()
        result = M.kev_cards(x, NOW)
        self.assertEqual(result["state"], "CURRENT_SNAPSHOT")
        item = result["cards"][0]
        self.assertEqual(item["cve"], "CVE-2026-123456")
        self.assertFalse(item["business_affected_confirmed"])
        self.assertFalse(item["customer_uses_product_confirmed"])
        self.assertFalse(item["attack_confirmed"])
        self.assertFalse(item["due_date_is_universal_business_deadline"])
        self.assertEqual(item["source_url"], M.CISA_SOURCE)
        x["not_realtime_attack_feed"] = False
        self.assertEqual(M.kev_cards(x, NOW)["state"], "INVALID_SOURCE")

    def test_kev_dedup_aged_and_malformed_records_excluded(self):
        x = cisa()
        x["items"].append(dict(x["items"][0]))
        self.assertEqual(len(M.kev_cards(x, NOW)["cards"]), 1)
        x["items"][0]["date_added"] = "2025-01-01"
        x["items"][1]["date_added"] = "2025-01-01"
        self.assertEqual(M.kev_cards(x, NOW)["cards"], [])
        x["items"][0]["date_added"] = "2026-11-20"
        x["items"][0]["cve"] = "not-cve"
        self.assertEqual(M.kev_cards(x, NOW)["cards"], [])

    def test_stale_kev_suppresses_business_action(self):
        x = cisa()
        x["source_health"]["last_ok"] = "2026-11-20T16:00:00Z"
        y = M.kev_cards(x, NOW)
        self.assertEqual(y["state"], "SOURCE_STALE")
        self.assertEqual(y["cards"], [])

    def test_no_inputs_and_future_health_cannot_imply_all_clear(self):
        output = M.build_preview(now=NOW)
        self.assertEqual([x["state"] for x in output["source_modules"]],
                         ["INPUT_NOT_PROVIDED", "INPUT_NOT_PROVIDED"])
        x = nws()
        x["source_health"]["last_ok"] = "2026-11-21T06:00:00Z"
        self.assertEqual(M.weather_cards(x, NOW)["state"], "SOURCE_STALE")

    def test_no_network_and_size_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "public.json"
            p.write_text(json.dumps(nws()), encoding="utf-8")
            loaded = M.load_snapshot(p)
            self.assertEqual(loaded["schema"], "wmm.nws.v1")
            p.write_bytes(b"x" * (M.MAX_INPUT_BYTES + 1))
            with self.assertRaises(ValueError):
                M.load_snapshot(p)

    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            M.build_preview(now=dt.datetime(2026, 11, 21, 4))
        self.assertIsNone(M.parse_utc("2026-11-21T04:00:00"))
        self.assertIsNone(M.parse_utc("malformed"))


if __name__ == "__main__":
    unittest.main()
