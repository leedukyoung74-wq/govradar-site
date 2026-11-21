"""Official UK Met Office RSS & Canada ECCC Toronto ATOM read-only tests."""
import datetime as dt
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import official_uk_ca_feeds as M

NOW=dt.datetime(2026,11,21,3,30,tzinfo=dt.timezone.utc)
UK=b"""<?xml version="1.0"?><rss version="2.0"><channel><title>Met Office UK warnings</title>
<item><title>Amber Rain Warning</title><link>https://weather.metoffice.gov.uk/warnings-and-advice/uk-warnings</link>
<pubDate>Sat, 21 Nov 2026 02:40:00 GMT</pubDate><description>Weather warning summary</description></item></channel></rss>"""
CA=b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Weather Alerts Toronto</title>
<updated>2026-11-21T03:00:00Z</updated>
<entry><title>Wind Warning for City of Toronto</title>
<updated>2026-11-21T02:40:00Z</updated>
<link href="https://weather.gc.ca/en/location/index.html?coords=43.656,-79.383"/></entry>
</feed>"""

class OfficialUKCanadaTests(unittest.TestCase):
    def test_uk_coverage_and_link_required_but_not_confirmed_active(self):
        x=M.parse_uk_metoffice(UK,NOW)
        self.assertEqual(x["geo_scope"],"GB")
        self.assertEqual(x["count"],1)
        self.assertEqual(x["items"][0]["title"],"Amber Rain Warning")
        self.assertFalse(x["items"][0]["confirmed_active"])
        self.assertTrue(x["requires_link_to_source"])
        self.assertFalse(x["government_website_attack_confirmed"])

    def test_canada_single_city_not_whole_country(self):
        x=M.parse_canada_eccc(CA,NOW)
        self.assertEqual(x["geo_scope"],"CA-ON-TORONTO")
        self.assertEqual(x["count"],1)
        self.assertFalse(x["items"][0]["confirmed_active"])
        self.assertFalse(x["government_website_attack_confirmed"])

    def test_empty_feed_is_not_emergency(self):
        empty_uk=b'<?xml version="1.0"?><rss version="2.0"><channel><title>Met Office UK warnings</title></channel></rss>'
        empty_ca=b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Toronto Alerts</title><updated>2026-11-21T03:00:00Z</updated></feed>'
        self.assertEqual(M.parse_uk_metoffice(empty_uk,NOW)["count"],0)
        self.assertEqual(M.parse_canada_eccc(empty_ca,NOW)["count"],0)

    def test_stale_entries_do_not_create_live_alerts(self):
        old=UK.replace(b"21 Nov 2026",b"11 Nov 2026")
        x=M.parse_uk_metoffice(old,NOW)
        self.assertEqual(x["count"],0)
        old_ca=CA.replace(b"2026-11-21T02:40:00Z",b"2026-11-01T02:40:00Z")
        self.assertEqual(M.parse_canada_eccc(old_ca,NOW)["count"],0)

    def test_dtd_entity_and_unsafe_link_blocked(self):
        for provider,parser,xml in (("uk",M.parse_uk_metoffice,UK),("ca",M.parse_canada_eccc,CA)):
            with self.subTest(provider=provider),self.assertRaises(ValueError):
                parser(b'<!DOCTYPE rss [<!ENTITY x SYSTEM "file:///etc/passwd">]>'+xml,NOW)
        bad=UK.replace(b"https://weather.metoffice.gov.uk/warnings-and-advice/uk-warnings",b"https://weather.metoffice.gov.uk.bad.invalid/xyz")
        self.assertEqual(M.parse_uk_metoffice(bad,NOW)["count"],0)

    def test_url_allowlist_https_prevents_redirect_host_trick(self):
        self.assertTrue(M.allowed(M.MET_URL,"uk"))
        self.assertTrue(M.allowed(M.CA_URL,"ca"))
        for x in ("http://www.metoffice.gov.uk/public/data/PWSCache/WarningsRSS/Region/UK",
                  "https://www.metoffice.gov.uk.bad.invalid/public/data/PWSCache/WarningsRSS/Region/UK",
                  "https://foo:bar@weather.gc.ca/rss/battleboard/on61_e.xml",
                  "https://weather.gc.ca:123/rss/battleboard/on61_e.xml"):
            self.assertFalse(M.allowed(x,"uk") or M.allowed(x,"ca"))

    def test_official_output_can_only_be_private_not_customer_breach(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"private.json"
            result=M.collect(out,NOW,{"uk":lambda:UK,"ca":lambda:CA})
            self.assertFalse(result["public_publish_allowed"])
            self.assertFalse(result["customer_data_processed"])
            self.assertFalse(result["cyberattack_confirmed"])
            self.assertEqual(result["health"]["uk"]["status"],"OK")
            self.assertEqual(result["health"]["ca"]["status"],"OK")
            with self.assertRaises(ValueError):
                M.collect(Path(folder)/"public"/"status.json",NOW,{"uk":lambda:UK,"ca":lambda:CA})

    def test_stale_source_retains_previous_but_error_not_active(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"status.json"
            initial=M.collect(p,NOW,{"uk":lambda:UK,"ca":lambda:CA})
            next_run=M.collect(p,NOW+dt.timedelta(hours=1),{
                "uk":lambda:(_ for _ in ()).throw(TimeoutError()),"ca":lambda:CA})
            self.assertEqual(next_run["health"]["uk"]["status"],"STALE")
            self.assertEqual(next_run["feeds"]["uk"],initial["feeds"]["uk"])
            self.assertFalse(next_run["public_publish_allowed"])

if __name__=="__main__": unittest.main()
