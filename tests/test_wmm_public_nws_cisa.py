import datetime as dt
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import wmm_public_nws_cisa as M

NOW = dt.datetime(2026, 11, 19, 4, 0, tzinfo=dt.timezone.utc)


def nws_event(severity='Severe', status='Actual', url='https://api.weather.gov/alerts/urn:oid:test', end='2026-11-19T18:00:00Z'):
    return {'id': url, 'properties': {'id': 'nws-test-one', 'status': status, 'messageType': 'Alert',
             'headline': 'Severe Thunderstorm Warning', 'event': 'Thunderstorm Warning',
             'severity': severity, 'urgency': 'Immediate', 'certainty': 'Observed',
             'areaDesc': 'Example County', 'sent': '2026-11-19T03:00:00Z', 'ends': end}}


def cisa_catalog(n=1000):
    return {'catalogVersion': '2026.11.19', 'dateReleased': '2026-11-19T00:00:00.000Z', 'count': n,
            'vulnerabilities': [
                {'cveID': 'CVE-2026-%04d' % (i+1000), 'vendorProject': 'Vendor',
                 'product': 'Example', 'vulnerabilityName': 'Example Flaw',
                 'dateAdded': '2026-11-19', 'dueDate': '2026-12-19'}
                for i in range(n)]}


class OfficialOnlyTests(unittest.TestCase):
    def test_nws_valid(self):
        result = M.nws_rows([{'features': [nws_event()]}], NOW)
        self.assertEqual(result['filtered_count'], 1)
        self.assertEqual(result['items'][0]['src'], 'NWS')

    def test_nws_test_never_becomes_real_alert(self):
        result = M.nws_rows([{'features': [nws_event(status='Test')]}], NOW)
        self.assertEqual(result['filtered_count'], 0)

    def test_nws_non_severe_excluded(self):
        result = M.nws_rows([{'features': [nws_event(severity='Minor')]}], NOW)
        self.assertEqual(len(result['items']), 0)

    def test_nws_expired_excluded(self):
        result = M.nws_rows([{'features': [nws_event(end='2026-11-18T01:00:00Z')]}], NOW)
        self.assertEqual(len(result['items']), 0)

    def test_nws_empty_valid_not_fake_warning(self):
        result = M.nws_rows([{'features': []}], NOW)
        self.assertEqual(result['filtered_count'], 0)

    def test_nws_bad_schema_rejected(self):
        with self.assertRaises(ValueError):
            M.nws_rows([{'features': None}], NOW)

    def test_official_source_https_allowlist(self):
        self.assertTrue(M.official_url(M.NWS_URL, M.NWS_HOSTS))
        self.assertFalse(M.official_url('http://api.weather.gov/alerts', M.NWS_HOSTS))
        self.assertFalse(M.official_url('https://api.weather.gov.evil.org/alerts', M.NWS_HOSTS))

    def test_nws_link_falls_back_to_official(self):
        item = nws_event(url='javascript:alert(1)')
        result = M.nws_rows([{'features': [item]}], NOW)
        self.assertEqual(result['items'][0]['url'], 'https://www.weather.gov/alerts')

    def test_cisa_catalog_valid(self):
        v = M.cisa_rows(cisa_catalog())
        self.assertEqual(v['total_vulnerabilities'], 1000)
        self.assertEqual(v['displayed'], 100)
        self.assertTrue(v['not_realtime_attack_feed'])

    def test_cisa_count_mismatch_blocks(self):
        bad = cisa_catalog()
        bad['count'] = 999
        with self.assertRaises(ValueError):
            M.cisa_rows(bad)

    def test_cisa_duplicate_cve_blocks(self):
        bad = cisa_catalog()
        bad['vulnerabilities'][-1]['cveID'] = bad['vulnerabilities'][0]['cveID']
        with self.assertRaises(ValueError):
            M.cisa_rows(bad)

    def test_failure_preserves_last_good(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)/'nws.json'
            before = {'items': [{'title': 'last-good'}], 'source_health': {
                'ok': True, 'last_ok': '2026-11-19T00:00:00Z'}}
            M.save_atomic(p, before)
            def broken(now):
                raise TimeoutError('no network')
            r = M.collect_one(p, 'nws', broken, 0, NOW)
            self.assertEqual(r['status'], 'delayed')
            result = json.loads(p.read_text())
            self.assertTrue(result['source_health']['stale'])
            self.assertEqual(result['items'], before['items'])

    def test_no_cache_failure_displays_unavailable_not_all_clear(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)/'nws.json'
            r = M.collect_one(p, 'nws', lambda now: 1, 0, NOW)
            self.assertEqual(r['status'], 'delayed')
            result = json.loads(p.read_text())
            self.assertFalse(result['source_health']['ok'])
            self.assertEqual(result['items'], [])

    def test_min_interval_skips_redundant_download(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)/'kev.json'
            M.save_atomic(p, {'items': [], 'source_health': {
                'ok': True, 'last_ok': '2026-11-19T03:00:00Z'}})
            r = M.collect_one(p, 'cisa_kev', lambda now: self.fail('should not fetch'), 7200, NOW)
            self.assertEqual(r['status'], 'skipped_recent_good')

    def test_save_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)/'feed.json'
            M.save_atomic(p, {'items': [], 'ok': True})
            self.assertEqual(json.loads(p.read_text())['ok'], True)

if __name__ == '__main__':
    unittest.main()
