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
    ("", "2026-02-31", "2026-01-01T00:00:00Z", False),    # impossible date: unknown -> NOT open
    ("", "", "2026-01-01T00:00:00Z", False),              # no deadline: unknown -> NOT open
    ("not a date", "", "2026-01-01T00:00:00Z", False),
]

class Python(unittest.TestCase):
    def test_cases(self):
        for at, d, now, want in CASES:
            self.assertEqual(D.is_open({"deadline_at": at, "deadline": d}, U(now)), want, (at, d, now))

    def test_states(self):
        n = U("2026-11-20T00:00:00Z")
        self.assertEqual(D.state({"deadline_at": "2026-11-27T17:00:00Z"}, n), "open")
        self.assertEqual(D.state({"deadline": "2026-11-27"}, n), "date_only")
        self.assertEqual(D.state({"deadline": "2026-11-01"}, n), "closed")
        self.assertEqual(D.state({"deadline": ""}, n), "unknown")

    def test_stale_is_shown_but_not_counted(self):
        x = {"deadline_at": "2026-11-27T17:00:00Z", "stale": True}
        self.assertTrue(D.is_open(x, U("2026-11-20T00:00:00Z"))); self.assertFalse(D.is_listed_open(x, U("2026-11-20T00:00:00Z")))

@unittest.skipUnless(shutil.which("node"), "node not installed")
class Browser(unittest.TestCase):
    def run_js(self, code):
        js = "global.window={};" + open(os.path.join(ROOT, "web", "dl.js"), encoding="utf8").read() + ";" + code
        return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)

    def test_same_answer_as_python(self):
        res = self.run_js("console.log(JSON.stringify(%s.map(function(c){return GRDL.info(c[0],c[1],Date.parse(c[2])).open})))" % json.dumps(CASES))
        self.assertEqual(res, [c[3] for c in CASES])

    def test_states_and_unknown_label(self):
        r = self.run_js("""var n=Date.parse('2026-11-20T00:00:00Z');console.log(JSON.stringify([GRDL.info('2026-11-27T17:00:00Z','',n).state,
          GRDL.info('','2026-11-27',n).state,GRDL.info('','2026-11-01',n).state,GRDL.info('','',n).state,GRDL.label(GRDL.info('','',n),'ko'),
          GRDL.label(GRDL.info('2026-11-27T17:00:00Z','',n),'en','2026-11-19T06:10Z')]))""")
        self.assertEqual(r[:4], ["open", "date_only", "closed", "unknown"]); self.assertIn("마감일 미확인", r[4]); self.assertIn("verification delayed", r[5])
        r2 = self.run_js("console.log(JSON.stringify(GRDL.label(GRDL.info('2026-11-27T17:00:00Z','',Date.parse('2026-11-20T00:00:00Z')),'en','-')))")
        self.assertEqual(r2, "verification delayed · check the notice")

    def test_open_page_drops_row_at_deadline(self):
        # a row closing 1 s from now disappears on the next sweep, while the page stays open
        r = self.run_js("""var rows=[{dataset:{at:new Date(Date.now()+1000).toISOString().replace(/\.\d+Z$/,'Z'),dl:''},removed:false,remove:function(){this.removed=true},querySelector:function(){return null}}];
          global.document={querySelectorAll:function(){return rows}};GRDL.sweep(document,'en');var before=rows[0].removed;
          setTimeout(function(){GRDL.sweep(document,'en');console.log(JSON.stringify([before,rows[0].removed]))},1600)""")
        self.assertEqual(r, [False, True])

    def test_labels(self):
        r = self.run_js("""var a=GRDL.info('2026-11-23T09:00:00+02:00','',Date.parse('2026-11-22T07:00:00Z')),
          b=GRDL.info('','2026-11-30',Date.parse('2026-11-20T00:00:00Z')),c=GRDL.info('2026-11-23T09:00:00+02:00','',Date.parse('2026-11-23T06:30:00Z'));
          console.log(JSON.stringify([GRDL.label(a,'ko'),GRDL.label(b,'ko'),GRDL.label(c,'en'),GRDL.days(a),a.src]))""")
        self.assertIn("2026-11-23 09:00 (UTC+02:00)", r[0]); self.assertIn("내 시간", r[0])
        self.assertIn("시각 미확인", r[1]); self.assertNotIn("내 시간", r[1])
        self.assertIn("30minleft", r[2].replace(" ", "")); self.assertEqual(r[3], 1)
