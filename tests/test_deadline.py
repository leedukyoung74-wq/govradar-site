"""Deadline rule — Python (tools/deadline.py) and the browser (web/dl.js) must agree. JS cases run in node."""
import datetime as dt, json, os, shutil, subprocess, sys, unittest
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import deadline as D

U = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
CASES = [  # (deadline_at, deadline, now UTC, open?)
    ("2026-11-27T17:00:00Z", "2026-11-27", "2026-11-27T16:59:00Z", True),     # 1 minute before
    ("2026-11-27T17:00:00Z", "2026-11-27", "2026-11-27T17:01:00Z", False),    # 1 minute after
    ("2026-11-23T09:00:00+02:00", "2026-11-23", "2026-11-23T06:59:00Z", True),  # Kyiv 09:00 = 07:00 UTC
    ("2026-11-23T09:00:00+02:00", "2026-11-23", "2026-11-23T07:00:30Z", False),
    ("2026-03-08T12:00:00-04:00", "2026-03-08", "2026-03-08T15:59:00Z", True),  # New York after the DST switch
    ("2026-03-08T12:00:00-04:00", "2026-03-08", "2026-03-08T16:00:01Z", False),
    ("2026-11-16T23:30:00+09:00", "2026-11-16", "2026-11-16T14:00:00Z", True),  # D-0 in Seoul, 30 min left
    ("", "2026-11-16", "2026-11-17T11:00:00Z", True),     # date only: kept until the day ends at UTC-12
    ("", "2026-11-16", "2026-11-17T12:00:00Z", False),
    ("2026-11-16", "", "2026-11-17T11:59:00Z", True),     # date-only text in deadline_at
    ("", "2026-02-31", "2026-01-01T00:00:00Z", True),     # impossible date: unknown -> kept, no date shown
    ("", "", "2026-01-01T00:00:00Z", True),
]

class Python(unittest.TestCase):
    def test_cases(self):
        for at, d, now, want in CASES:
            self.assertEqual(D.is_open({"deadline_at": at, "deadline": d}, U(now)), want, (at, d, now))

@unittest.skipUnless(shutil.which("node"), "node not installed")
class Browser(unittest.TestCase):
    def run_js(self, code):
        js = "global.window={};" + open(os.path.join(ROOT, "web", "dl.js"), encoding="utf8").read() + ";" + code
        return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)

    def test_same_answer_as_python(self):
        res = self.run_js("console.log(JSON.stringify(%s.map(function(c){return GRDL.info(c[0],c[1],Date.parse(c[2])).open})))" % json.dumps(CASES))
        self.assertEqual(res, [c[3] for c in CASES])

    def test_labels(self):
        r = self.run_js("""var a=GRDL.info('2026-11-23T09:00:00+02:00','',Date.parse('2026-11-22T07:00:00Z')),
          b=GRDL.info('','2026-11-30',Date.parse('2026-11-20T00:00:00Z')),c=GRDL.info('2026-11-23T09:00:00+02:00','',Date.parse('2026-11-23T06:30:00Z'));
          console.log(JSON.stringify([GRDL.label(a,'ko'),GRDL.label(b,'ko'),GRDL.label(c,'en'),GRDL.days(a),a.src]))""")
        self.assertIn("2026-11-23 09:00 (UTC+02:00)", r[0]); self.assertIn("내 시간", r[0])
        self.assertIn("시각 미확인", r[1]); self.assertNotIn("내 시간", r[1])
        self.assertIn("30minleft", r[2].replace(" ", "")); self.assertEqual(r[3], 1)
