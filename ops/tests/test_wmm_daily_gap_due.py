"""Offline-only regression for daily missed publish guard and fallback caps."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("wmm_daily_gap_due",ROOT/"ops"/"wmm_daily_gap_due.py")
P=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)
NOW=dt.datetime(2026,11,28,9,30,tzinfo=P.KST)

def stamps(when="2026-11-27T10:16:00Z"):
    return {"tenders.json":P.read_utc(when),
            "today.json":P.read_utc(when)}

def run(when,ident,event="workflow_run",conclusion="success"):
    return {"id":ident,"created_at":when,"event":event,
            "status":"completed","conclusion":conclusion}

class DailyMissedOnlyTests(unittest.TestCase):
    def test_kst_date_gate_prevents_second_publish_today(self):
        today=stamps("2026-11-27T22:00:00Z") # KST 28th 07:00
        self.assertEqual(P.decision(today,NOW,"scheduled"),
                         ("TODAY_ALREADY_PUBLISHED",False))
        self.assertEqual(P.decision(today,NOW,"fallback",[],[],100),
                         ("TODAY_ALREADY_PUBLISHED",False))

    def test_previous_day_kst_stamps_due_after_owner_window(self):
        prev=stamps()
        self.assertEqual(P.decision(prev,NOW,"scheduled"),
                         ("SCHEDULED_DAILY_MISSING_FOR_TODAY",True))
        self.assertEqual(P.decision(prev,NOW,"fallback",[],[],101),
                         ("MISSING_TODAY_AND_SAFE_TO_COLLECT",True))
        early=dt.datetime(2026,11,28,8,29,tzinfo=P.KST)
        self.assertEqual(P.decision(prev,early,"fallback",[],[],101),
                         ("DEFER_UNTIL_0830_KST",False))

    def test_missing_and_future_timestamps_block(self):
        bad=stamps()
        bad["tenders.json"]=None
        self.assertEqual(P.decision(bad,NOW,"scheduled")[1],False)
        future=stamps("2026-11-29T10:00:00Z")
        self.assertEqual(P.decision(future,NOW,"fallback",[],[],1)[1],False)

    def test_ongoing_primary_daily_recent_prevents_duplicate(self):
        primary=[run("2026-11-28T00:05:00Z",71,"schedule",None)]
        self.assertEqual(P.decision(stamps(),NOW,"fallback",primary,[],5),
                         ("RECENT_PRIMARY_DAILY_ATTEMPT",False))

    def test_recent_owner_fallback_attempt_suppresses_repeat(self):
        last=[run("2026-11-28T00:15:00Z",3)]
        self.assertEqual(P.decision(stamps(),NOW,"fallback",[],last,4),
                         ("DAILY_FALLBACK_COOLDOWN",False))
        # The current GitHub run itself appears in the API list; exclude it.
        self.assertEqual(P.decision(stamps(),NOW,"fallback",[],last,3),
                         ("MISSING_TODAY_AND_SAFE_TO_COLLECT",True))

    def test_attempt_cap_blocks_even_if_retries_are_far_apart(self):
        later=dt.datetime(2026,11,28,17,30,tzinfo=P.KST)
        prior=[run("2026-11-28T00:20:00Z",21),
               run("2026-11-28T04:20:00Z",22)]
        self.assertEqual(P.decision(stamps(),later,"fallback",[],prior,40),
                         ("DAILY_FALLBACK_ATTEMPT_CAP",False))

    def test_different_day_recovery_does_not_block(self):
        older=[run("2026-11-27T01:15:00Z",10)]
        self.assertEqual(P.decision(stamps(),NOW,"fallback",[],older,20)[1],True)

    def test_github_metadata_failure_is_not_unlimited_retry(self):
        self.assertEqual(P.decision(stamps(),NOW,"fallback",None,None,1),
                         ("BLOCKED_GITHUB_METADATA_MISSING",False))

    def test_readonly_feed_state_on_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            feeds=Path(folder)/"feeds";feeds.mkdir()
            for name in ("tenders.json","today.json"):
                (feeds/name).write_text(json.dumps({"updated":"2026-11-27T10:16Z"}),
                                        encoding="utf-8")
            before={x.name:x.read_bytes() for x in feeds.iterdir()}
            values=P.read_feed_times(folder)
            self.assertEqual(P.decision(values,NOW,"scheduled")[1],True)
            self.assertEqual(before,{x.name:x.read_bytes() for x in feeds.iterdir()})

    def test_source_code_scope_and_no_new_schedule(self):
        wf=(ROOT/".github"/"workflows"/"wmm_daily_gap_recovery.yml").read_text()
        scheduled=(ROOT/".github"/"workflows"/"schedule.yml").read_text()
        self.assertIn("WMM GOV RADAR hourly public operations watch",wf)
        self.assertIn("github.event.comment.author_association == 'OWNER'",wf)
        self.assertIn("ops/wmm_daily_gap_due.py --mode fallback",wf)
        self.assertIn("ops/wmm_daily_gap_due.py --mode scheduled",scheduled)
        self.assertNotIn("  schedule:",wf)
        self.assertIn("secrets.DAPA_KEY",wf)
        self.assertIn("secrets.SAM_KEY",wf)
        self.assertIn("dry_run: false",wf)
        self.assertIn("dry_run:",scheduled)
        self.assertIn("10 21 * * *",scheduled)

if __name__ == "__main__":
    unittest.main()
