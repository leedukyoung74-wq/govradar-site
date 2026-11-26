"""Read-only deployment preflight contracts: mock data only, never network."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("cf_preflight", ROOT/"tools/cloudflare_pages_readonly_preflight.py")
preflight=importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)

class CloudflarePreflightSafetyTest(unittest.TestCase):
    def project(self):
        return {
            "name":"wmm-radar","production_branch":"live",
            "domains":["radar.wmm-hoa.com"],
            "source":{"type":"github","config":{"owner":"leedukyoung74-wq","repo_name":"govradar-site"}},
            "build_config":{"build_command":"python3 build.py --base https://radar.wmm-hoa.com",
                "destination_dir":"dist","root_dir":""},
            "deployment_configs":{"production":{"d1_databases":{"GV_DB":{"id":"TEST_PRIVATE_DB_ID"}}}},
            "latest_deployment":{"id":"example","environment":"production"}
        }
    def test_matching_project_requires_manual_approval(self):
        result, issues=preflight.summarize(self.project())
        self.assertEqual(result["repository"],"leedukyoung74-wq/govradar-site")
        self.assertFalse(result["safe_to_deploy_automatically"])
        self.assertTrue(any("sign-off" in issue for issue in issues))
    def test_mismatched_production_branch_is_blocked(self):
        p=self.project();p["production_branch"]="main"
        _,issues=preflight.summarize(p)
        self.assertTrue(any("branch" in x.lower() for x in issues))
    def test_gv_db_binding_presence_redacted(self):
        result,issues=preflight.summarize(self.project())
        self.assertTrue(result["production_d1_gv_db_binding_present"])
        self.assertNotIn("TEST_PRIVATE_DB_ID",str(result))
        self.assertNotIn("TEST_PRIVATE_DB_ID",str(issues))

    def test_missing_production_binding_is_blocked_but_not_claimed_as_failed_write(self):
        p=self.project();p["deployment_configs"]["production"]["d1_databases"]={}
        result,issues=preflight.summarize(p)
        self.assertFalse(result["production_d1_gv_db_binding_present"])
        self.assertTrue(any("GV_DB" in v for v in issues))
        self.assertTrue(any("NOT proof" in v for v in issues))

    def test_preview_binding_does_not_count_as_production(self):
        p=self.project();p["deployment_configs"]={"preview":{"d1_databases":{"GV_DB":{"id":"x"}}}}
        result,issues=preflight.summarize(p)
        self.assertFalse(result["production_d1_gv_db_binding_present"])

    def test_unconfirmed_custom_domain_is_blocked(self):
        p=self.project();p["domains"]=[]
        _,issues=preflight.summarize(p)
        self.assertTrue(any("domain" in x.lower() for x in issues))
    def test_direct_upload_does_not_assume_git_deploy(self):
        p=self.project();p["source"]=None
        _,issues=preflight.summarize(p)
        self.assertTrue(any("Direct Upload" in x for x in issues))
    def test_mismatched_repo_and_build_blocked(self):
        p=self.project()
        p["source"]["config"]["repo_name"]="wrong"
        p["build_config"]["destination_dir"]="public"
        _,issues=preflight.summarize(p)
        self.assertTrue(any("repository" in x.lower() for x in issues))
        self.assertTrue(any("directory" in x.lower() for x in issues))
    def test_no_credentials_no_calls(self):
        with patch.dict("os.environ",{},clear=True):
            self.assertEqual(preflight.main(),2)

if __name__=="__main__":unittest.main()
