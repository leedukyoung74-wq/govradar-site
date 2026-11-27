"""Regression tests for honest optional-collector result and no false-green feeds."""
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


class CollectorHealthTests(unittest.TestCase):
    def test_clean_complete_six_events_pass(self):
        src="".join(f"{name}\tPASS\n" for name in MOD.EXPECTED)
        result=MOD.report(src)
        self.assertEqual(result["state"],"PASS")
        self.assertEqual(result["failed_collectors"],[])
        self.assertEqual(result["not_run_collectors"],[])
        self.assertFalse(result["source_freshness_verified"])
        self.assertFalse(result["public_site_readback_verified"])

    def test_one_failed_collector_fails_gate(self):
        src="".join(f"{name}\t{'FAIL' if name == 'feed_econ' else 'PASS'}\n"
                    for name in MOD.EXPECTED)
        self.assertEqual(MOD.report(src)["state"],"DEGRADED")
        self.assertEqual(MOD.report(src)["failed_collectors"],["feed_econ"])
        with tempfile.TemporaryDirectory() as tmp:
            inputpath=Path(tmp)/"collector.tsv"
            outputpath=Path(tmp)/"collector.json"
            inputpath.write_text(src,encoding="utf-8")
            r=subprocess.run([sys.executable,str(SCRIPT),"report",str(inputpath),str(outputpath)],
                             text=True,capture_output=True,timeout=5)
            self.assertEqual(r.returncode,0)
            c=subprocess.run([sys.executable,str(SCRIPT),"gate",str(outputpath)],
                             text=True,capture_output=True,timeout=5)
            self.assertEqual(c.returncode,1)
            self.assertEqual(json.loads(outputpath.read_text())["state"],"DEGRADED")

    def test_missing_or_duplicate_is_not_a_pass(self):
        self.assertEqual(MOD.report("")["state"],"INCOMPLETE")
        self.assertEqual(MOD.report("feed_intel\tPASS\n")["state"],"INCOMPLETE")
        rows="".join(f"{name}\tPASS\n" for name in MOD.EXPECTED)
        self.assertEqual(MOD.report(rows+"feed_intel\tPASS\n")["state"],"INCOMPLETE")

    def test_unknown_and_untrusted_line_never_leaks(self):
        secret="SENSITIVE_API_TOKEN_NEVER_PRINT"
        malicious="".join(f"{name}\tPASS\n" for name in MOD.EXPECTED)
        malicious+=secret+"\tPASS\n"
        out=MOD.report(malicious)
        self.assertEqual(out["state"],"INCOMPLETE")
        self.assertTrue(out["invalid_or_duplicate_events"])
        self.assertNotIn(secret,json.dumps(out))

    def test_complete_cli_pass_and_incomplete_cli_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"report.json"
            src=Path(tmp)/"events.tsv"
            src.write_text("".join(f"{name}\tPASS\n" for name in MOD.EXPECTED),encoding="utf-8")
            subprocess.run([sys.executable,str(SCRIPT),"report",str(src),str(p)],
                           check=True,capture_output=True,text=True,timeout=5)
            ok=subprocess.run([sys.executable,str(SCRIPT),"gate",str(p)],
                              text=True,capture_output=True,timeout=5)
            self.assertEqual(ok.returncode,0)
            p.unlink()
            failed=subprocess.run([sys.executable,str(SCRIPT),"gate",str(p)],
                                  text=True,capture_output=True,timeout=5)
            self.assertNotEqual(failed.returncode,0)

    def test_workflow_never_swallows_collector_exit_again(self):
        path=ROOT/".github"/"workflows"/"feeds.yml"
        s=path.read_text(encoding="utf-8")
        for name in MOD.EXPECTED:
            self.assertNotIn("python tools/"+name+".py || echo",s)
            self.assertIn("printf '"+name+"\\tFAIL\\n'",s)
            self.assertIn("printf '"+name+"\\tPASS\\n'",s)
        self.assertIn("tools/optional_collector_health.py report",s)
        self.assertIn("tools/optional_collector_health.py gate",s)
        self.assertIn("runner.temp",s)
        self.assertLess(s.index("Keep the outputs of this run"),
                        s.index("Fail closed if optional collectors failed or did not run"))


if __name__=="__main__":
    unittest.main()
