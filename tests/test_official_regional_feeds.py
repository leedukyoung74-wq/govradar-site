"""Tests for two official, free and read-only regional information feeds.

No network requests or actual government site polling in unit tests.
The UK Environment Agency covers England; JMA Atom is a bulletin index,
not proof that each listed warning is still in force.
"""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import official_regional_feeds as M

NOW = dt.datetime(2026, 11, 21, 3, 0, tzinfo=dt.timezone.utc)
EA = {
    "meta": {"publisher": "Environment Agency", "licence": "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"},
    "items": [
        {"severity": "Severe Flood Warning", "severityLevel": 1,
         "description": "Flooding expected in Example Valley", "message": "Take action",
         "timeRaised": "2026-11-20T21:00:00Z",
         "floodArea": {"label": "Example Valley"}, "floodAreaID": "flood-42",
         "@id": "https://environment.data.gov.uk/flood-monitoring/id/floods/42"},
        {"severity": "Warning no Longer in Force", "severityLevel": 4,
         "description": "No longer in force", "floodAreaID": "flood-43"}
    ]
}
ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>JMA Extra</title><updated>2026-11-21T02:00:00Z</updated>
<entry><id>urn:uuid:notice-123</id><title>気象警報情報</title>
<updated>2026-11-21T01:30:00Z</updated>
<link type="application/xml" href="https://www.data.jma.go.jp/developer/xml/data/202611210130_0.xml"/></entry>
</feed>""".encode("utf-8")


class OfficialRegionalFeeds(unittest.TestCase):
    def test_england_flood_warnings_are_not_all_uk_and_ignore_cancelled(self):
        result = M.parse_england_floods(EA, NOW)
        self.assertEqual(result["geo_scope"], "GB-ENG")
        self.assertEqual(result["source_name"], "Environment Agency")
        self.assertEqual(result["feed_type"], "active_flood_warnings_england")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["severity"], "Severe Flood Warning")
        self.assertEqual(result["items"][0]["source_url"], EA["items"][0]["@id"])
        self.assertTrue(result["source_is_official"])
        self.assertFalse(result["government_website_cyberattack_confirmed"])

    def test_ea_official_lowercase_retired_warning_skipped(self):
        # The EA API reference itself says "Warning no longer in force".
        retired = dict(EA["items"][1], severity="Warning no longer in force")
        result = M.parse_england_floods({"items": [EA["items"][0], retired]}, NOW)
        self.assertEqual(result["count"], 1)

    def test_ea_numeric_severity_level_4_blocks_even_with_ambiguous_label(self):
        retired = dict(EA["items"][1], severity="Flood Warning", severityLevel=4)
        result = M.parse_england_floods({"items": [retired]}, NOW)
        self.assertEqual(result["count"], 0)

    def test_england_empty_active_feed_is_not_an_error_or_attack(self):
        result = M.parse_england_floods({"items": []}, NOW)
        self.assertEqual(result["count"], 0)
        self.assertFalse(result["government_website_cyberattack_confirmed"])

    def test_england_bad_schema_and_duplicate_id_refused(self):
        with self.assertRaises(ValueError):
            M.parse_england_floods({"items": None}, NOW)
        same = EA["items"][0]
        with self.assertRaises(ValueError):
            M.parse_england_floods({"items": [same, dict(same)]}, NOW)

    def test_jma_atom_feed_is_index_not_active_alert(self):
        result = M.parse_jma_feed(ATOM, NOW)
        self.assertEqual(result["geo_scope"], "JP")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["feed_type"], "recent_jma_xml_bulletin_index")
        self.assertFalse(result["items"][0]["confirmed_active"])
        self.assertFalse(result["government_website_cyberattack_confirmed"])
        self.assertEqual(result["items"][0]["source_url"], "https://www.data.jma.go.jp/developer/xml/data/202611210130_0.xml")

    def test_jma_excludes_old_bulletins_and_unsafe_links(self):
        old = ATOM.replace(b"2026-11-21T01:30:00Z", b"2026-11-14T01:30:00Z")
        self.assertEqual(M.parse_jma_feed(old, NOW)["count"], 0)
        evil = ATOM.replace(b"https://www.data.jma.go.jp/developer/xml/data/202611210130_0.xml",
                            b"https://www.data.jma.go.jp.evil.invalid/trap")
        self.assertEqual(M.parse_jma_feed(evil, NOW)["count"], 0)

    def test_xml_entity_and_doctype_rejected(self):
        with self.assertRaises(ValueError):
            M.parse_jma_feed(b'<!DOCTYPE feed [<!ENTITY x SYSTEM "file:///etc/passwd">]>' + ATOM, NOW)

    def test_url_allowlist_https_and_no_redirects(self):
        self.assertTrue(M.is_allowed_url(M.EA_URL, "ea"))
        self.assertTrue(M.is_allowed_url(M.JMA_URL, "jma"))
        for invalid in ["http://environment.data.gov.uk/flood-monitoring/id/floods",
                        "https://environment.data.gov.uk.evil.invalid/flood-monitoring/id/floods",
                        "https://evil.invalid/redirect",
                        "https://user:pass@environment.data.gov.uk/flood-monitoring/id/floods",
                        "https://environment.data.gov.uk:444/flood-monitoring/id/floods",
                        "https://environment.data.gov.uk/\nother"]:
            self.assertFalse(M.is_allowed_url(invalid, "ea"), invalid)

    def test_failed_fetch_is_stale_and_does_not_erase_last_good(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "review.json"
            r = M.run_collector(
                path, NOW, {"ea": lambda: EA, "jma": lambda: ATOM})
            self.assertEqual(r["feed_health"]["ea"]["status"], "OK")
            first = json.loads(path.read_text())
            r = M.run_collector(path, NOW + dt.timedelta(hours=3),
                                {"ea": lambda: (_ for _ in ()).throw(TimeoutError()),
                                 "jma": lambda: ATOM})
            self.assertEqual(r["feed_health"]["ea"]["status"], "STALE")
            self.assertEqual(r["feeds"]["ea"]["items"], first["feeds"]["ea"]["items"])
            self.assertEqual(r["feed_health"]["ea"]["last_success_at"],
                             first["feed_health"]["ea"]["last_success_at"])
            self.assertFalse(r["public_publish_allowed"])

    def test_first_run_failed_provider_not_reported_as_empty_success(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "pilot.json"
            result = M.run_collector(
                p, NOW,
                {"ea": lambda: (_ for _ in ()).throw(TimeoutError()),
                 "jma": lambda: ATOM})
            self.assertEqual(result["feed_health"]["ea"]["status"], "ERROR")
            self.assertIsNone(result["feed_health"]["ea"]["last_success_at"])
            self.assertFalse(result["feeds"]["ea"]["source_is_official"])

    def test_public_paths_and_overwrite_outside_internal_review_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                M.run_collector(Path(d) / "public" / "hazards.json", NOW,
                                {"ea": lambda: EA, "jma": lambda: ATOM})
            with self.assertRaises(ValueError):
                M.run_collector(Path(d) / "dist" / "hazards.json", NOW,
                                {"ea": lambda: EA, "jma": lambda: ATOM})

    def test_no_inference_of_cyberincident_or_company_impact(self):
        with tempfile.TemporaryDirectory() as d:
            r = M.run_collector(Path(d) / "private.json", NOW,
                                {"ea": lambda: EA, "jma": lambda: ATOM})
            self.assertFalse(r["public_publish_allowed"])
            self.assertFalse(r["customer_data_processed"])
            self.assertFalse(r["cyberattack_confirmed"])
            self.assertFalse(r["customer_impact_confirmed"])
            self.assertEqual(r["feed_health"]["jma"]["status"], "OK")


if __name__ == "__main__":
    unittest.main()
