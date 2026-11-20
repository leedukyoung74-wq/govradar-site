"""Review-only contract for actual Codex code-editing workflow (never invokes Codex)."""
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/wmm_govradar_codex_autobuild.yml"

class CodexAutobuildWorkflowContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body=WORKFLOW.read_text(encoding="utf8")

    def test_agent_is_real_coding_tool_but_off_by_default(self):
        s=self.body
        self.assertIn("openai/codex-action@v1",s)
        self.assertIn("permission-profile: ':workspace'",s)
        self.assertIn("vars.WMM_AUTOBUILD_ENABLED == 'true'",s)
        self.assertIn("vars.WMM_AUTOBUILD_COST_APPROVED == 'true'",s)
        self.assertIn("WMM_AUTOBUILD_START_UTC",s)
        self.assertIn("tools/wmm_24h_agent_gate.py",s)

    def test_no_operating_deployment_or_public_branch_write(self):
        s=self.body
        self.assertNotIn("wrangler deploy",s)
        self.assertNotIn("cloudflare",s.lower())
        self.assertNotIn("git push origin HEAD:refs/heads/main",s)
        self.assertNotIn("git push origin HEAD:refs/heads/live",s)
        self.assertIn("git push origin HEAD:refs/heads/review/wmm-govradar-autobuild-24h-20261120",s)
        self.assertIn("contents: read",s)
        self.assertIn("contents: write",s)

    def test_secret_only_agent_and_verify_without_api_secret(self):
        s=self.body
        self.assertEqual(s.count("secrets.OPENAI_API_KEY"),1)
        self.assertIn("safety-strategy: drop-sudo",s)
        self.assertIn("persist-credentials: false",s)
        self.assertIn("Test changed implementation without any API key",s)
        self.assertIn("python -m unittest discover -s tests -v",s)

    def test_commit_only_after_separate_code_validation(self):
        s=self.body
        self.assertIn("verify_patch:",s)
        self.assertIn("save_review_branch_only:",s)
        self.assertIn("if: needs.verify_patch.result == 'success'",s)
        self.assertIn("python tools/wmm_autobuild_diff_guard.py validate",s)
        self.assertIn("git apply --check",s)
        self.assertIn("timeout-minutes: 18",s)

    def test_cannot_run_through_untrusted_pr_trigger(self):
        s=self.body
        self.assertNotIn("pull_request:",s)
        self.assertIn("workflow_dispatch:",s)
        self.assertIn("schedule:",s)

if __name__=="__main__":
    unittest.main()
