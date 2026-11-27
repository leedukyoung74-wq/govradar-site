"""Offline regression for honest optional-collector and provider flags."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"tools"/"optional_collector_health.py"
SPEC=importlib.util.spec_from_file_location("optional_collector_health",SCRIPT)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def events(bad=None):
    return "".join(f"{n}\t{'FAIL' if n==bad else 'PASS'}\n" for n in MOD.EXPECTED)


def fixtures(base, failed=None, omit=None):
    for section, (rel, parent, names) in MOD.PROVIDER_FEEDS.items():
        out=Path(base)/rel
        out.parent.mkdir(parents=True,exist_ok=True)
        src={}
        for name in names:
            if (section,name)==omit:
                continue
            src[name]={"ok": False if (section,name)==failed else True}
        out.write_text(json.dumps({parent:src}),encoding="utf-8")


class CollectorHealthTests(unittest.TestCase):
    def test_six_processes_and_all_provider_flags_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures(tmp)
            result=MOD.report(events(),tmp)
            self.assertEqual(result["state"],"PASS")
            self.assertTrue(result["provider_status_complete"])
            self.assertEqual(len(result["provider_status_only"]),16)
            self.assertEqual(result["failed_collectors"],[])
            self.assertFalse(result["source_freshness_verified"])
            self.assertFalse(result["public_site_readback_verified"])

    def test_one_failed_collector_degrades_after_report_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures(tmp)
            inp=Path(tmp)/"collectors.tsv"
            inp.write_text(events("feed_econ"),encoding="utf-8")
            out=Path(tmp)/"health.json"
            self.assertEqual(MOD.report(inp.read_text(),tmp)["state"],"DEGRADED")
            r=subprocess.run([sys.executable,str(SCRIPT),"report",str(inp),str(out),tmp],
                             text=True,capture_output=True,timeout=5)
            self.assertEqual(r.returncode,0)
            c=subprocess.run([sys.executable,str(SCRIPT),"gate",str(out)],
                             text=True,capture_output=True,timeout=5)
            self.assertEqual(c.returncode,1)
            data=json.loads(out.read_text())
            self.assertEqual(data["failed_collectors"],["feed_econ"])

    def test_provider_failure_detected_even_when_process_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures(tmp,failed=("official","gdacs"))
            result=MOD.report(events(),tmp)
            self.assertEqual(result["failed_collectors"],[])
            self.assertEqual(result["state"],"DEGRADED")
            self.assertEqual(result["provider_failure_sources"],["official.gdacs"])
            self.assertFalse(result["public_site_readback_verified"])

    def test_partial_economy_and_sanctions_are_not_full_green(self):
        for bad in (("econ","fx"),("sanctions","uk")):
            with tempfile.TemporaryDirectory() as tmp:
                fixtures(tmp,failed=bad)
                result=MOD.report(events(),tmp)
                self.assertEqual(result["state"],"DEGRADED")
                self.assertEqual(len(result["provider_failure_sources"]),1)

    def test_missing_source_or_feed_file_is_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures(tmp,omit=("official","who"))
            result=MOD.report(events(),tmp)
            self.assertEqual(result["state"],"INCOMPLETE")
            self.assertIn("official.who",result["provider_not_reported_sources"])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(MOD.report(events(),tmp)["state"],"INCOMPLETE")

    def test_missing_duplicate_invalid_events_are_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures(tmp)
            for raw in ("", "feed_intel\tPASS\n", events()+"feed_intel\tPASS\n",
                        events()+"untrusted_collector\tPASS\n"):
                self.assertEqual(MOD.report(raw,tmp)["state"],"INCOMPLETE")

    def test_untrusted_line_cannot_echo_customer_or_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures(tmp)
            secret="MY_PRIVATE_SERVICE_TOKEN_NEVER_OUTPUT"
            bad=MOD.report(events()+secret+"\tPASS\n",tmp)
            self.assertNotIn(secret,json.dumps(bad))
            self.assertTrue(bad["invalid_or_duplicate_events"])

    def test_end_to_end_report_and_gate_pass_with_complete_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures(tmp)
            inp=Path(tmp)/"collectors.tsv"
            out=Path(tmp)/"collectors.json"
            inp.write_text(events(),encoding="utf-8")
            subprocess.run([sys.executable,str(SCRIPT),"report",str(inp),str(out),tmp],
                           check=True,capture_output=True,text=True,timeout=5)
            ok=subprocess.run([sys.executable,str(SCRIPT),"gate",str(out)],
                              capture_output=True,text=True,timeout=5)
            self.assertEqual(ok.returncode,0)
            self.assertEqual(json.loads(out.read_text())["state"],"PASS")
            out.unlink()
            fail=subprocess.run([sys.executable,str(SCRIPT),"gate",str(out)],
                                capture_output=True,text=True,timeout=5)
            self.assertEqual(fail.returncode,1)

    def test_workflow_preserves_publication_then_fails_on_degradation(self):
        s=(ROOT/".github"/"workflows"/"feeds.yml").read_text(encoding="utf-8")
        for name in MOD.EXPECTED:
            self.assertNotIn("python tools/"+name+".py || echo",s)
            self.assertIn("printf '"+name+"\\tPASS\\n'",s)
            self.assertIn("printf '"+name+"\\tFAIL\\n'",s)
        self.assertIn("tools/optional_collector_health.py report",s)
        self.assertIn("tools/optional_collector_health.py gate",s)
        self.assertIn("runner.temp",s)
        self.assertIn("data_branch\n      - name: Keep the outputs",s)
        self.assertLess(s.index("Keep the outputs of this run"),
                        s.index("Fail closed if optional collectors failed or did not run"))


if __name__=="__main__":
    unittest.main()
