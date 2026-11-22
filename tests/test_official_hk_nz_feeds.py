"""Tests for Hong Kong Observatory and New Zealand GeoNet official feeds.
Source fixtures synthetic. Provider live read is separate and evidence-gated.
"""
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import official_hk_nz_feeds as M

NOW = dt.datetime(2026, 11, 21, 3, 10, tzinfo=dt.timezone.utc)
RSS = b"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>Weather Warning Summary</title><link>https://www.hko.gov.hk/en/wxinfo/dailywx/wxwarntoday.htm</link>
<item><title>Thunderstorm Warning</title><link>https://www.hko.gov.hk/en/wxinfo/dailywx/wxwarntoday.htm</link>
<description>Thunderstorm warning now in force</description>
<pubDate>Sat, 21 Nov 2026 03:00:00 GMT</pubDate></item></channel></rss>"""
NO_WARNINGS = RSS.replace(b"Thunderstorm Warning", b"No Weather Warning").replace(
    b"Thunderstorm warning now in force", b"No weather warning in force")
QUAKES = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [173.1, -41.7]},
        "properties": {
            "publicID": "2026p123456", "time": "2026-11-21T02:45:00.000Z",
            "magnitude": 4.5, "depth": 14.6, "mmi": 5,
            "locality": "24 km NW of Test Town", "quality": "best",
        },
    }, {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [174.1, -41.3]},
        "properties": {
            "publicID": "2025p888888", "time": "2025-11-20T02:45:00.000Z",
            "magnitude": 4.9, "depth": 12.0, "mmi": 5,
            "locality": "Historic example", "quality": "preliminary",
        },
    }]
}

class OfficialHKAndNZ(unittest.TestCase):
    def test_hong_kong_territory_scope_not_country(self):
        result = M.parse_hko_rss(RSS, NOW)
        self.assertEqual(result["geo_scope"], "CN-HK")
        self.assertEqual(result["sovereign_parent"], "CN")
        self.assertEqual(result["feed_type"], "current_official_warning_summary")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["title"], "Thunderstorm Warning")
        self.assertTrue(result["items"][0]["warning_summary_not_individual_cap"])
        self.assertFalse(result["government_website_attack_confirmed"])

    def test_hko_no_warning_is_zero_not_disaster(self):
        result = M.parse_hko_rss(NO_WARNINGS, NOW)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["warning_state"], "NO_WARNINGS_IN_SUMMARY")
        self.assertFalse(result["government_website_attack_confirmed"])

    def test_hko_stale_date_refuses_current_warning_claim(self):
        old = RSS.replace(b"21 Nov 2026", b"11 Nov 2026")
        r = M.parse_hko_rss(old, NOW)
        self.assertEqual(r["warning_state"], "SUMMARY_AGE_UNVERIFIED")
        self.assertFalse(r["items"][0]["current_verified"])

    def test_hko_html_xml_entities_and_unsafe_links_rejected(self):
        with self.assertRaises(ValueError):
            M.parse_hko_rss(b'<!DOCTYPE rss [<!ENTITY steal SYSTEM "file:///etc/passwd">]>' + RSS, NOW)
        evil = RSS.replace(b"https://www.hko.gov.hk/en/wxinfo/dailywx/wxwarntoday.htm",
                           b"https://www.hko.gov.hk.evil.invalid/wrong")
        result = M.parse_hko_rss(evil, NOW)
        self.assertEqual(result["items"][0]["source_url"], M.HKO_URL)

    def test_hko_malformed_feed_blocks(self):
        for data in (b"", b"<rss><channel></channel></rss>", b"<script>alert(1)</script>"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                M.parse_hko_rss(data, NOW)

    def test_geonet_latest_48h_only_and_no_attack_claims(self):
        x = M.parse_geonet_quakes(QUAKES, NOW)
        self.assertEqual(x["geo_scope"], "NZ")
        self.assertEqual(x["count"], 1)
        self.assertEqual(x["items"][0]["id"], "2026p123456")
        self.assertTrue(x["items"][0]["is_event_observation"])
        self.assertFalse(x["items"][0]["is_government_site_outage"])
        self.assertFalse(x["government_website_attack_confirmed"])

    def test_geonet_no_recent_events_is_not_feed_failure(self):
        old = dict(QUAKES, features=[QUAKES["features"][1]])
        x = M.parse_geonet_quakes(old, NOW)
        self.assertEqual(x["count"], 0)
        self.assertEqual(x["scope_note"], "Recent quake observations; not government attacks or emergency declarations.")

    def test_geonet_invalid_or_deleted_and_duplicate_rejected(self):
        wrong = dict(QUAKES, features=[{**QUAKES["features"][0],
                                      "properties": {**QUAKES["features"][0]["properties"], "quality": "deleted"}}])
        self.assertEqual(M.parse_geonet_quakes(wrong, NOW)["count"], 0)
        dup = dict(QUAKES, features=[QUAKES["features"][0], QUAKES["features"][0]])
        with self.assertRaises(ValueError):
            M.parse_geonet_quakes(dup, NOW)

    def test_geonet_invalid_magnitude_nan_time_prevent_false_alert(self):
        for bad in ("NaN", 100, -2):
            row = {**QUAKES["features"][0], "properties": {**QUAKES["features"][0]["properties"], "magnitude": bad}}
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                M.parse_geonet_quakes({"type": "FeatureCollection", "features": [row]}, NOW)

    def test_https_allowlist_rejects_nonofficial_redirect_or_credentials(self):
        self.assertTrue(M.allowed(M.HKO_URL, "hko"))
        self.assertTrue(M.allowed(M.GEONET_URL, "geonet"))
        for s in ("http://rss.weather.gov.hk/rss/WeatherWarningSummaryv2.xml",
                  "https://rss.weather.gov.hk.evil.invalid/rss/WeatherWarningSummaryv2.xml",
                  "https://user:password@rss.weather.gov.hk/rss/WeatherWarningSummaryv2.xml",
                  "https://api.geonet.org.nz:444/quake?MMI=3"):
            self.assertFalse(M.allowed(s, "hko") and M.allowed(s, "geonet"))

    def test_stale_preserves_previous_result_and_denies_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/"pilot.json"
            x = M.collect(p,NOW,{"hko":lambda:RSS,"geonet":lambda:QUAKES})
            self.assertEqual(x["health"]["hko"]["status"], "OK")
            y = M.collect(p,NOW+dt.timedelta(hours=3),{
                "hko":lambda: (_ for _ in ()).throw(TimeoutError()),
                "geonet":lambda: QUAKES})
            self.assertEqual(y["health"]["hko"]["status"], "STALE")
            self.assertEqual(y["feeds"]["hko"],x["feeds"]["hko"])
            self.assertFalse(y["publication_allowed"])
            self.assertFalse(y["customer_data_processed"])

    def test_invalid_provider_first_run_error_not_empty_success(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"pilot.json"
            x=M.collect(p,NOW,{"hko":lambda:RSS,"geonet":lambda:(_ for _ in ()).throw(TimeoutError())})
            self.assertEqual(x["health"]["geonet"]["status"], "ERROR")
            self.assertEqual(x["feeds"]["geonet"]["count"], None)

    def test_refuse_public_output_and_unsafe_input(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                M.collect(Path(folder)/"public"/"feed.json",NOW,{"hko":lambda:RSS,"geonet":lambda:QUAKES})
            with self.assertRaises(ValueError):
                M.collect(Path(folder)/"dist"/"feed.json",NOW,{"hko":lambda:RSS,"geonet":lambda:QUAKES})


if __name__=="__main__":
    unittest.main()
