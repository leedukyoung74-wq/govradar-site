import sys
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from v28_schedule_triage import analyze_runs, utc_date, POLICIES

NOW=datetime(2026,11,21,4,40,tzinfo=timezone.utc)
FAST="WMM GOV RADAR fast official data publishing"
NWS="WMM Official NWS + CISA KEV public updates"
WATCH="WMM GOV RADAR hourly public operations watch"
DAY="Scheduled feeds"

def run(name,age,conclusion="success",status="completed"):
    return {"name":name,"event":"schedule","created_at":(NOW-timedelta(minutes=age)).isoformat(),
            "conclusion":conclusion,"status":status,"id":int(age)+10}

class TriageTest(unittest.TestCase):
    def state(self,runs,name):
        return next(x for x in analyze_runs(runs,NOW)["monitors"] if x["name"]==name)
    def test_no_cron(self):
        self.assertEqual(self.state([],FAST)["state"],"NO_SCHEDULE_RUN")
    def test_recent_success(self):
        self.assertEqual(self.state([run(FAST,12)],FAST)["state"],"RUN_SUCCESS_RECENT")
    def test_delayed_success_is_not_recent(self):
        self.assertEqual(self.state([run(FAST,300)],FAST)["state"],"NO_RECENT_SUCCESS")
    def test_failure_overrides_previous_success(self):
        x=self.state([run(WATCH,12,"failure"),run(WATCH,90)],WATCH)
        self.assertEqual(x["state"],"LATEST_RUN_FAILED")
        self.assertFalse(x["healthy_run_schedule"])
    def test_in_progress_not_pass(self):
        x=self.state([run(NWS,3,None,"in_progress"),run(NWS,19)],NWS)
        self.assertEqual(x["state"],"RUN_PENDING")
    def test_recovered_run(self):
        x=self.state([run(NWS,1),run(NWS,300,"failure")],NWS)
        self.assertTrue(x["healthy_run_schedule"])
    def test_no_data_freshness_claim(self):
        self.assertFalse(self.state([run(FAST,2)],FAST)["public_data_freshness_verified"])
    def test_wrong_date_rejected(self):
        with self.assertRaises(ValueError):analyze_runs([],datetime(2026,11,21,4,0))
    def test_default_policy_count(self):
        self.assertEqual(len(POLICIES),4)
    def test_nontimezone_rejected(self):
        self.assertIsNone(utc_date("2026-11-21T12:00"))
    def test_daily_window(self):
        self.assertEqual(self.state([run(DAY,1800)],DAY)["state"],"RUN_SUCCESS_RECENT")
    def test_cron_failed_not_masked_by_other_success(self):
        x=analyze_runs([run(NWS,2),run(WATCH,60,"failure")],NOW)
        self.assertFalse(x["all_schedule_checks_healthy"])
    def test_only_scheduled(self):
        self.assertEqual(self.state([{"name":FAST,"event":"push","status":"completed","conclusion":"success","created_at":NOW.isoformat()}],FAST)["state"],"NO_SCHEDULE_RUN")
if __name__=="__main__":unittest.main()
