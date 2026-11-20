"""Offline regression tests for the opt-in Cloudflare publish preflight.
This NEVER runs the actual deploy script.
"""
import pathlib
import shutil
import subprocess
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"tools"/"publish_cf.sh"

class PublishExportPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=SCRIPT.read_text(encoding="utf8")

    def test_bash_syntax(self):
        if shutil.which("bash") is None:
            self.skipTest("bash unavailable")
        proc=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)

    def test_guard_runs_before_any_mutating_publish_step(self):
        s=self.source
        p=s.index('case "${WMM_EXPORT_PREFLIGHT:-off}" in')
        self.assertLess(p,s.index("python3 tools/signals_i18n.py"))
        self.assertLess(p,s.index("python3 tools/cf_variant.py"))
        self.assertLess(p,s.index("rm -rf public functions"))
        self.assertLess(p,s.index("git push -q origin live"))

    def test_default_off_explicit_and_required_is_fail_closed(self):
        s=self.source
        self.assertIn("  off)",s)
        self.assertIn("  required)",s)
        self.assertIn("python3 tools/check_export_inputs.py",s)
        self.assertIn("--export-dir export/countries",s)
        self.assertIn("--min-countries",s)
        self.assertIn("--max-age-days",s)
        self.assertIn('echo "STOP: country export freshness preflight failed; nothing published."',s)
        self.assertIn("    exit 1",s)
        self.assertIn('WMM_EXPORT_PREFLIGHT must be',s)

    def test_public_assets_scanned_before_live_worktree_changes(self):
        s=self.source
        check=s.index("python3 tools/check_public_fixture_leak.py cf/public")
        self.assertLess(s.index("python3 tools/asset_version.py cf/public"),check)
        self.assertLess(check,s.index("cd /home/claude/govradar-live"))
        self.assertLess(check,s.index("rm -rf public functions"))

    def test_does_not_inject_synthetic_qa_data(self):
        s=self.source
        self.assertNotIn("create_tender_fixture",s)
        self.assertNotIn("wmm_qa_fixture_dates",s)

if __name__=="__main__":
    unittest.main()
