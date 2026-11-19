import datetime as dt
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import wmm_fast_usgs_publish as F

NOW = dt.datetime(2026, 11, 19, 3, 40, tzinfo=dt.timezone.utc)

def old():
    return {'v': 1, 'checked': '2026-11-19T12:30',
            'sources': {'usgs': {'ok': True, 'last_ok': '2026-11-19T12:30', 'n': 1},
                        'gdacs': {'ok': True, 'last_ok': '2026-11-19T07:00', 'n': 2}},
            'items': {'usgs': [{'k': 'quake', 'url': 'https://earthquake.usgs.gov/earthquakes/eventpage/old'}],
                      'gdacs': [{'k': 'storm', 't': 'existing'}]}}


def event(mag=6.0, tsunami=0, url='https://earthquake.usgs.gov/earthquakes/eventpage/test'):
    return {'properties': {'mag': mag, 'place': 'Japan', 'time': 1795059600000, 'url': url,
                           'tsunami': tsunami, 'alert': 'orange'},
            'geometry': {'coordinates': [139.0, 35.0, 5.0]}}

class FastUSGSTests(unittest.TestCase):
    def test_normal_rows(self):
        x = F.quake_rows({'features': [event()]})
        self.assertEqual(x[0]['k'], 'quake')
        self.assertEqual(x[0]['src'], 'USGS')

    def test_tsunami_flag_never_labels_as_warning(self):
        x = F.quake_rows({'features': [event(tsunami=1)]})
        self.assertEqual(x[0]['k'], 'quake')

    def test_only_usgs_changes(self):
        before = old()
        new, changed = F.transform(before, {'features': [event()]}, NOW)
        self.assertTrue(changed)
        self.assertEqual(new['items']['gdacs'], before['items']['gdacs'])
        self.assertEqual(new['sources']['gdacs'], before['sources']['gdacs'])

    def test_reject_wrong_domain(self):
        self.assertEqual(F.quake_rows({'features': [event(url='https://evil.example/a')]}), [])

    def test_reject_invalid_schema(self):
        with self.assertRaises(ValueError):
            F.quake_rows({'features': None})

    def test_failure_keeps_last_good(self):
        before = old()
        new, changed = F.transform(before, None, NOW, error=TimeoutError())
        self.assertTrue(changed)
        self.assertEqual(new['items']['usgs'], before['items']['usgs'])
        self.assertFalse(new['sources']['usgs']['ok'])

    def test_no_write_during_fast_poll_without_changes(self):
        before = old()
        before['items']['usgs'] = F.quake_rows({'features': [event()]})
        before['sources']['usgs']['n'] = len(before['items']['usgs'])
        new, changed = F.transform(before, {'features': [event()]}, NOW)
        self.assertFalse(changed)
        self.assertEqual(new, before)

    def test_heartbeat_updates_15_minutes(self):
        before = old()
        before['checked'] = '2026-11-19T12:10'
        before['items']['usgs'] = F.quake_rows({'features': [event()]})
        new, changed = F.transform(before, {'features': [event()]}, NOW)
        self.assertTrue(changed)
        self.assertEqual(new['checked'], '2026-11-19T12:40')

    def test_refuse_to_write_without_existing_official(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                F.run(pathlib.Path(t)/'missing.json', getter=lambda: {'features': []}, now=NOW)

    def test_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as t:
            path = pathlib.Path(t)/'official.json'
            F.save_atomic(path, old())
            self.assertEqual(json.loads(path.read_text())['items']['gdacs'][0]['t'], 'existing')

if __name__ == '__main__':
    unittest.main()
