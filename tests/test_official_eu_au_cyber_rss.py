"""Official CERT-EU + Australian Cyber Security Centre cybersecurity advisory RSS tests."""
import datetime as dt
from pathlib import Path
import tempfile
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import official_eu_au_cyber_rss as M
NOW=dt.datetime(2026,11,21,4,0,tzinfo=dt.timezone.utc)
CERT=b"""<?xml version="1.0"?><rss version="2.0"><channel><title>CERT-EU Security Advisories</title>
<item><title>2026-999: Example Critical Software Vulnerability</title>
<link>https://cert.europa.eu/publications/security-advisories/2026-999</link>
<pubDate>Fri, 20 Nov 2026 09:00:00 GMT</pubDate><description>Technical advisory</description></item>
</channel></rss>"""
AUS=b"""<?xml version="1.0"?><rss version="2.0"><channel><title>ACSC Alerts</title>
<item><title>Update your systems now</title>
<link>https://www.cyber.gov.au/alerts-and-advisories/2026-11-example</link>
<pubDate>Fri, 20 Nov 2026 06:00:00 GMT</pubDate></item>
</channel></rss>"""

class SecurityOfficialFeedTests(unittest.TestCase):
    def test_eu_is_multistate_authority_not_member_state(self):
        x=M.parse_official(CERT,NOW,"cert_eu")
        self.assertEqual(x["geo_scope"],"EU")
        self.assertFalse(x["is_sovereign_country"])
        self.assertEqual(x["count"],1)
        self.assertFalse(x["items"][0]["confirmed_government_compromise"])
        self.assertFalse(x["items"][0]["enterprise_impact_confirmed"])
        self.assertTrue(x["source_is_official"])

    def test_au_advisory_is_not_confirmed_incident(self):
        x=M.parse_official(AUS,NOW,"acsc_au")
        self.assertEqual(x["geo_scope"],"AU")
        self.assertEqual(x["count"],1)
        self.assertEqual(x["items"][0]["advisory_type"],"OFFICIAL_ADVISORY_NOT_VERIFIED_INCIDENT")
        self.assertFalse(x["government_site_attack_confirmed"])

    def test_invalid_and_dtd_xml_refused(self):
        for b in (b"",b"<html/>",b'<!DOCTYPE rss [<!ENTITY x SYSTEM "file:///etc/passwd">]>'+CERT):
            with self.subTest(source=b[:60]),self.assertRaises(ValueError):
                M.parse_official(b,NOW,"cert_eu")

    def test_redirect_and_link_restricted_to_official_host(self):
        self.assertTrue(M.allowed_source(M.CERT_URL,"cert_eu"))
        self.assertTrue(M.allowed_source(M.AUS_URL,"acsc_au"))
        for url in ("http://cert.europa.eu/publications/security-advisories-rss",
                    "https://cert.europa.eu.bad.invalid/publications/security-advisories-rss",
                    "https://user:pass@www.cyber.gov.au/rss/alerts",
                    "https://www.cyber.gov.au:8080/rss/alerts"):
            self.assertFalse(M.allowed_source(url,"cert_eu") or M.allowed_source(url,"acsc_au"))

    def test_old_or_unofficial_article_not_published(self):
        old=CERT.replace(b"20 Nov 2026",b"20 Jan 2026")
        self.assertEqual(M.parse_official(old,NOW,"cert_eu")["count"],0)
        malicious=CERT.replace(b"https://cert.europa.eu/publications/security-advisories/2026-999",
                               b"https://cert.europa.eu.bad.invalid/steal")
        self.assertEqual(M.parse_official(malicious,NOW,"cert_eu")["count"],0)

    def test_repeat_article_deduplicated(self):
        x=CERT.replace(b"</channel></rss>",CERT[CERT.index(b"<item>"):CERT.index(b"</item>")+7]+b"</channel></rss>")
        self.assertEqual(M.parse_official(x,NOW,"cert_eu")["count"],1)

    def test_clean_empty_feed_valid_but_no_all_clear_claim(self):
        x=M.parse_official(b'<rss version="2.0"><channel><title>Alerts</title></channel></rss>',NOW,"acsc_au")
        self.assertEqual(x["count"],0)
        self.assertFalse(x["government_site_attack_confirmed"])

    def test_private_only_and_stale_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"result.json"
            a=M.collect(p,NOW,{"cert_eu":lambda:CERT,"acsc_au":lambda:AUS})
            self.assertFalse(a["public_release_allowed"])
            self.assertFalse(a["customer_data_processed"])
            b=M.collect(p,NOW+dt.timedelta(hours=3),{
                "cert_eu":lambda:(_ for _ in ()).throw(TimeoutError()),"acsc_au":lambda:AUS})
            self.assertEqual(b["health"]["cert_eu"]["status"],"STALE")
            self.assertEqual(b["feeds"]["cert_eu"],a["feeds"]["cert_eu"])

    def test_public_output_path_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                M.collect(Path(tmp)/"public"/"alert.json",NOW,{"cert_eu":lambda:CERT,"acsc_au":lambda:AUS})

if __name__=="__main__":unittest.main()
