"""Strict agent gate tests. Never call an API."""
import datetime as dt
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from wmm_24h_agent_gate import coding_gate

START=dt.datetime(2026,11,20,9,0,tzinfo=dt.timezone.utc)
ISO="2026-11-20T09:00:00Z"

class AgentGateTests(unittest.TestCase):
    def test_default_disabled_even_if_other_configuration_present(self):
        for enabled,cost in (("","true"),("true",""),("true","false"),("false","true")):
            with self.subTest(enabled=enabled,cost=cost):
                self.assertFalse(coding_gate("schedule",enabled,cost,ISO,START)["run"])

    def test_manual_never_bypasses_24_hour_window(self):
        for moment in (START-dt.timedelta(seconds=1),START+dt.timedelta(hours=24)):
            with self.subTest(moment=moment):
                self.assertFalse(coding_gate("workflow_dispatch","true","true",ISO,moment)["run"])

    def test_start_missing_or_invalid_blocks_activation(self):
        for start in ("", "2026-11-20T09:00:00", "bad"):
            with self.subTest(start=start):
                self.assertFalse(coding_gate("schedule","true","true",start,START)["run"])

    def test_explicitly_approved_hours_generate_expected_cycle(self):
        for i in range(24):
            with self.subTest(i=i):
                result=coding_gate("schedule","true","true",ISO,START+dt.timedelta(hours=i,minutes=7))
                self.assertTrue(result["run"])
                self.assertEqual(result["cycle"],i)

    def test_unsupported_event_denied(self):
        self.assertFalse(coding_gate("pull_request","true","true",ISO,START)["run"])

if __name__=="__main__":
    unittest.main()
