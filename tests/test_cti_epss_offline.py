"""Offline WMM KEV + FIRST EPSS enrichment regression tests; no customer data."""
import csv
import gzip
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.cti_epss_offline import analyze, approved_path, parse_epss

NOW = datetime(2026, 11, 21, 2, 30, tzinfo=timezone.utc)
CVE = "CVE-2026-12345"
KEV_SOURCE = "https://raw.githubusercontent.com/cisagov/kev-data/refs/heads/develop/known_exploited_vulnerabilities.json"


def kev(age=3, **changes):
    item = {
        "id": CVE,
        "date_added": "2026-11-20",
        "vendor": "Example Vendor",
        "product": "Example Software",
        "ransomware_reported": False,
        "evidence_level": "OFFICIAL_CISA_KEV",
        "source_url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        "victim_or_outage_confirmed": False,
        "public_redistribution_approval": "REVIEW_REQUIRED",
        "enterprise_impact": "NOT_ASSESSED",
        "tlp": "CLEAR",
    }
    obj = {
        "schema": "wmm-cti-safe-intake.v1",
        "checked_at_utc": (NOW - timedelta(hours=age)).isoformat(),
        "source": KEV_SOURCE,
        "source_sha256": "f" * 64,
        "source_entries": 1,
        "deployable": False,
        "public_release_allowed": False,
        "cti_vendor_connected": False,
        "records": [item],
    }
    obj.update(changes)
    return obj


def csv_data(score_date="2026-11-20", rows=None):
    rows = rows if rows is not None else [(CVE, "0.3542", "0.93")]
    body = f"#model_version:v2026.06.15,score_date:{score_date}\ncve,epss,percentile\n"
    body += "".join(",".join(row) + "\n" for row in rows)
    return body.encode("utf-8")


class EpssPilotTests(unittest.TestCase):
    def make_file(self, directory, data, compressed=False):
        path = Path(directory) / ("scores.csv.gz" if compressed else "scores.csv")
        path.write_bytes(gzip.compress(data) if compressed else data)
        return path

    def test_valid_gzip_and_enrichment_are_not_breach_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_file(directory, csv_data(), compressed=True)
            score_date, scores = parse_epss(path, {CVE}, NOW)
            report = analyze(kev(), scores, score_date, NOW)
            self.assertEqual(score_date, "2026-11-20")
            self.assertEqual(report["matched_count"], 1)
            self.assertEqual(report["source_kev_entries"], 1)
            self.assertEqual(report["sample_priorities"][0]["epss"], 0.3542)
            self.assertEqual(report["sample_priorities"][0]["percentile"], 0.93)
            self.assertEqual(report["status"], "HUMAN_REVIEW_REQUIRED")
            self.assertFalse(report["public_release_allowed"])
            self.assertFalse(report["customer_breaches_confirmed"])
            self.assertFalse(report["customer_vulnerabilities_confirmed"])
            self.assertFalse(report["darkweb_vendor_connected"])

    def test_real_first_utc_timestamp_header_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_file(directory, csv_data(score_date="2026-11-20T12:03:05Z"), compressed=True)
            score_date, scores = parse_epss(path, {CVE}, NOW)
            self.assertEqual(score_date, "2026-11-20")
            self.assertEqual(scores[CVE][0], 0.3542)

    def test_future_same_day_official_timestamp_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_file(directory, csv_data(score_date="2026-11-21T19:00:00Z"), compressed=True)
            with self.assertRaisesRegex(ValueError, "Future EPSS"):
                parse_epss(path, {CVE}, NOW)

    def test_official_timestamp_invalid_hour_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_file(directory, csv_data(score_date="2026-11-20T29:05:05Z"), compressed=True)
            with self.assertRaises(ValueError):
                parse_epss(path, {CVE}, NOW)

    def test_missing_score_does_not_claim_low_risk(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_file(directory, csv_data(rows=[("CVE-2025-9999", "0.88", "0.99")]))
            score_date, scores = parse_epss(path, {CVE}, NOW)
            report = analyze(kev(), scores, score_date, NOW)
            self.assertEqual(report["status"], "NO_SCORE_AVAILABLE")
            self.assertEqual(report["missing_score_count"], 1)
            self.assertEqual(report["sample_priorities"], [])

    def test_stale_and_future_score_dates_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            for day in ("2026-11-15", "2026-11-22"):
                path = self.make_file(directory, csv_data(score_date=day))
                with self.assertRaisesRegex(ValueError, "score date"):
                    parse_epss(path, {CVE}, NOW)

    def test_invalid_score_nan_out_of_range_or_duplicate_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            for value in ("-0.2", "1.01", "NaN", "Infinity", "not-number"):
                path = self.make_file(directory, csv_data(rows=[(CVE, value, "0.88")]))
                with self.subTest(value=value), self.assertRaises(ValueError):
                    parse_epss(path, {CVE}, NOW)
            path = self.make_file(directory, csv_data(rows=[(CVE, "0.3", "0.5"), (CVE, "0.4", "0.6")]))
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                parse_epss(path, {CVE}, NOW)

    def test_header_and_column_schemas_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for value in (b"cve,epss,percentile\n" + CVE.encode() + b",0.2,0.9\n",
                          b"#model_version:v5,score_date:2026-11-20\ncve,epss,email\n" + CVE.encode() + b",0.2,user@x.test\n"):
                path = self.make_file(directory, value)
                with self.assertRaises(ValueError):
                    parse_epss(path, {CVE}, NOW)

    def test_kev_stale_future_and_unsafe_flags_blocked(self):
        score_date = "2026-11-20"
        scores = {CVE: (0.1, 0.8)}
        for sample in (kev(age=72), kev(age=-5), kev(public_release_allowed=True), kev(cti_vendor_connected=True), kev(source="https://evil.example")):
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                analyze(sample, scores, score_date, NOW)

    def test_kev_victim_claim_or_pii_field_rejected(self):
        scores = {CVE: (0.1, 0.8)}
        x = kev(); x["records"][0]["victim_or_outage_confirmed"] = True
        with self.assertRaises(ValueError):
            analyze(x, scores, "2026-11-20", NOW)
        x = kev(); x["records"][0]["email"] = "somebody@example.test"
        with self.assertRaises(ValueError):
            analyze(x, scores, "2026-11-20", NOW)

    def test_public_existing_output_path_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            public = Path(directory) / "public" / "test.json"
            with self.assertRaises(ValueError):
                approved_path(public)
            existing = Path(directory) / "existing.json"
            existing.write_text("{}")
            with self.assertRaises(ValueError):
                approved_path(existing)

    def test_limit_and_duplicate_cves_rejected(self):
        source = kev()
        source["source_entries"] = 2
        source["records"].append(source["records"][0].copy())
        with self.assertRaises(ValueError):
            analyze(source, {CVE: (0.1, 0.8)}, "2026-11-20", NOW)
        with self.assertRaises(ValueError):
            analyze(kev(), {CVE: (0.1, 0.8)}, "2026-11-20", NOW, limit=0)

    def test_large_file_rejected_before_parse(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_file(directory, b"x" * 1024)
            # A minified oversized physical source should never parse as a valid score.
            with self.assertRaises(ValueError):
                parse_epss(path, {CVE}, NOW, max_file_bytes=100)


if __name__ == "__main__":
    unittest.main()
