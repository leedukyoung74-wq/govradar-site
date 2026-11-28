"""KST user-facing 'today' versus UTC official deadline regressions (NO NETWORK)."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
def load_tool(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"tools"/(name+".py"))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

import sys
sys.path.insert(0,str(ROOT/"tools"))
CLOCK=load_tool("reporting_clock")


class KstReportingClockTests(unittest.TestCase):
    def test_pre_nine_am_kst_is_previous_utc_calendar_day(self):
        now=dt.datetime(2026,11,27,21,10,tzinfo=dt.timezone.utc)
        self.assertEqual(CLOCK.reporting_day(now).isoformat(),"2026-11-28")
        self.assertEqual(CLOCK.utc_source_day(now).isoformat(),"2026-11-27")

    def test_utc_midnight_source_day_advances_without_changing_kst_day(self):
        before=dt.datetime(2026,11,27,23,59,tzinfo=dt.timezone.utc)
        after=before+dt.timedelta(minutes=2)
        self.assertEqual(CLOCK.reporting_day(before),CLOCK.reporting_day(after))
        self.assertNotEqual(CLOCK.utc_source_day(before),CLOCK.utc_source_day(after))

    def test_unaware_or_malformed_clock_fails_closed(self):
        with self.assertRaises(ValueError):
            CLOCK.reporting_day(dt.datetime(2026,11,28,6,10))
        with self.assertRaises(ValueError):
            CLOCK.utc_source_day(dt.datetime(2026,11,28,6,10))

    def test_new_tenders_use_kst_without_altering_deadline_instant(self):
        src=(ROOT/"tools"/"feed_tenders.py").read_text(encoding="utf-8")
        self.assertIn("TODAY = utc_source_day(); MIN_DL = TODAY.isoformat()",src)
        self.assertIn("REPORT_DATE = reporting_day()",src)
        self.assertIn('x["added"] = (prev.get(x["url"]) or {}).get("added") or REPORT_DATE.isoformat()',src)
        self.assertIn('x["urgent"] = (d - REPORT_DATE).days <= 2',src)
        self.assertIn('x.get("added") == REPORT_DATE.isoformat()',src)
        self.assertIn('FM.still_open',src)
        more=(ROOT/"tools"/"feed_more.py").read_text(encoding="utf-8")
        self.assertIn("end = datetime.datetime.combine",more)
        self.assertIn("datetime.timedelta(hours=-12)",more)

    def test_daily_home_counts_as_kst_today_at_0610(self):
        t=load_tool("feed_today")
        now=dt.datetime(2026,11,27,21,10,tzinfo=dt.timezone.utc)
        item={"title":"Example","iso":"KR","source":"Example",
              "deadline":"2026-12-02","deadline_at":"2026-12-02",
              "url":"https://example.org/notice/1","added":"2026-11-28",
              "urgent":False,"sec":[]}
        future_alert={"date":"2026-11-28","t":"UTC-tomorrow","src":"demo"}
        current_alert={"date":"2026-11-27","t":"UTC-today","src":"demo"}
        def fake_load(p):
            return {"feeds/tenders.json":{"items":[item]},
                    "hz/official.json":{"items":{"obs":[future_alert,current_alert]}},
                    "feeds/sources_status.json":{}}.get(p,{})
        with mock.patch.object(t,"NOW",now),mock.patch.object(t,"load",side_effect=fake_load),mock.patch.object(t,"is_open",return_value=True),mock.patch.object(t,"DLs",return_value="open"):
            result=t.build()
        self.assertEqual(result["date"],"2026-11-28")
        self.assertEqual(result["updated"],"2026-11-27T21:10Z")
        self.assertEqual(result["n"]["new"],1)
        self.assertEqual(result["n"]["alerts"],1)
        self.assertEqual(result["alerts"][0]["date"],"2026-11-27")

    def test_country_dashboard_uses_the_same_reporting_day(self):
        s=(ROOT/"tools"/"feed_cty.py").read_text(encoding="utf-8")
        self.assertIn("today = reporting_day().isoformat()",s)
        t=(ROOT/"tools"/"feed_today.py").read_text(encoding="utf-8")
        self.assertIn("today = reporting_day(NOW).isoformat()",t)
        self.assertIn("alert_utc_today = NOW.date().isoformat()",t)


if __name__ == "__main__":
    unittest.main()
