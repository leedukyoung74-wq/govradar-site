"""Offline regression for best-effort GitHub schedule evidence (no real API calls)."""
import datetime as dt
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "wmm_schedule_event_coverage",ROOT/"ops"/"wmm_schedule_event_coverage.py")
P=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)
NOW=dt.datetime(2026,11,28,0,0,tzinfo=dt.timezone.utc)


def fake_events(minutes,how_many):
    return [{"event":"schedule","created_at":(
        NOW-dt.timedelta(minutes=minutes*n)).isoformat(),
        "status":"completed","conclusion":"success"} for n in range(how_many)]


class ScheduleEvidenceTests(unittest.TestCase):
    def test_ideal_24h_schedule_counts_are_not_sla(self):
        datasets={"wmm_fast_timer.yml":fake_events(5,288),
                  "wmm_nws_cisa_timer.yml":fake_events(15,96)}
        def fetch(name,page,token=""):
            return datasets[name][(page-1)*100:page*100]
        result=P.run(NOW,fetch)
        self.assertEqual(result["result"],"PASS_OBSERVED_EVENTS_ONLY")
        a=result["workflows"]["USGS_5MIN"]
        self.assertEqual(a["observed_distinct_schedule_invocations"],288)
        self.assertEqual(a["max_inter_invocation_gap_minutes"],5)
        self.assertFalse(a["source_freshness_verified"])
        self.assertFalse(a["hard_realtime_SLA_proven"])
        self.assertFalse(result["real_time_SLA_claimed"])
        self.assertFalse(result["published_data_modified"])

    def test_missing_schedule_gaps_are_reported_without_fake_success(self):
        datasets={"wmm_fast_timer.yml":fake_events(90,5),
                  "wmm_nws_cisa_timer.yml":fake_events(15,96)}
        def fetch(name,page,token=""):
            return datasets[name][(page-1)*100:page*100]
        x=P.run(NOW,fetch)
        self.assertEqual(x["result"],"PENDING")
        self.assertEqual(x["workflows"]["USGS_5MIN"]["state"],
                         "SCHEDULE_GAP_OBSERVED")
        self.assertEqual(x["workflows"]["NWS_CISA_15MIN"]["state"],
                         "SCHEDULE_EVENTS_OBSERVED")

    def test_metadata_error_not_mislabelled_green(self):
        def broken(name,page,token=""):
            raise OSError("synthetic error with token DO_NOT_PRINT_ME")
        x=P.run(NOW,broken)
        self.assertEqual(x["result"],"PENDING")
        for v in x["workflows"].values():
            self.assertEqual(v["state"],"UNKNOWN_GITHUB_METADATA")
        self.assertNotIn("DO_NOT_PRINT_ME",str(x))

    def test_deduplicates_and_ignores_unrequested_runs(self):
        rows=fake_events(5,2)
        rows.append(dict(rows[-1]))
        rows.append({"event":"workflow_dispatch","created_at":NOW.isoformat()})
        x=P.summarize("USGS_5MIN",5,rows,NOW)
        self.assertEqual(x["observed_distinct_schedule_invocations"],2)

    def test_bad_timestamps_are_not_counted(self):
        x=P.summarize("USGS_5MIN",5,
                      [{"event":"schedule","created_at":"invalid"}],NOW)
        self.assertEqual(x["state"],"SCHEDULE_GAP_OBSERVED")
        self.assertIsNone(x["last_scheduled_age_minutes"])

    def test_request_allowlist_prevents_unapproved_api_calls(self):
        for name in ("https://other.invalid", "../secrets", "any.yml"):
            with self.assertRaises(ValueError):
                P.api_get(name,1)
        with self.assertRaises(ValueError):
            P.api_get("wmm_fast_timer.yml",5)
        with self.assertRaises(ValueError):
            P.api_get("wmm_fast_timer.yml",0)

    def test_uses_existing_hourly_watcher_only(self):
        wf=(ROOT/".github"/"workflows"/"wmm_operations_watch.yml").read_text()
        self.assertIn("cron: '17 * * * *'",wf)
        self.assertIn("ops/wmm_schedule_event_coverage.py",wf)
        for path in ("ops/wmm_public_source_truth_report.py",
                     "ops/wmm_seven_locale_readonly.py",
                     "ops/wmm_schedule_event_coverage.py"):
            self.assertIn("      - "+path,wf.split("permissions:")[0])
        self.assertIn("GH_TOKEN:",wf)
        code=(ROOT/"ops"/"wmm_schedule_event_coverage.py").read_text()
        self.assertNotIn("POST",code.split("def api_get")[1].split("def summarize")[0])
        self.assertNotIn("workflow_dispatch",wf.split("steps:")[1].split("permissions:")[0])

if __name__=="__main__":
    unittest.main()
