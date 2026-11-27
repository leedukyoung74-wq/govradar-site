"""Offline only. Never expose the actual private GitHub Actions value."""
import json
import os
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import wmm_koneps_secret_shape_offline as s


class KonepsSecretShapeTests(unittest.TestCase):
    def test_missing_empty(self):
        self.assertEqual(s.classify(None), "NOT_CONFIGURED")
        self.assertEqual(s.classify(""), "NOT_CONFIGURED")

    def test_plain_decode_value_no_claim_of_authorization(self):
        self.assertEqual(s.classify("SYNTHETIC-ONLY-HEX-123456"),
                         "PLAIN_OPAQUE_KEY_SHAPE")

    def test_percent_encoded_and_bad_escape(self):
        self.assertEqual(s.classify("SYNTHETIC%2FPLUS%3D"),
                         "PERCENT_ENCODED_OR_PERCENT_CONTAINING")
        self.assertEqual(s.classify("SYNTHETIC%ZZ"), "INVALID_PERCENT_ESCAPE")

    def test_wrapped_url_and_query_parameter(self):
        self.assertEqual(s.classify("https://example.test/?serviceKey=XYZ"),
                         "URL_OR_PARAMETER_INSTEAD_OF_KEY")
        self.assertEqual(s.classify("serviceKey=XYZ"), "URL_OR_PARAMETER_INSTEAD_OF_KEY")

    def test_whitespace_and_quotes(self):
        self.assertEqual(s.classify(" KEY"), "HAS_WHITESPACE_OR_MULTILINE")
        self.assertEqual(s.classify("KEY\n"), "HAS_WHITESPACE_OR_MULTILINE")
        self.assertEqual(s.classify('"KEY"'), "HAS_QUOTE_CHARACTERS")

    def test_cli_output_no_secret_and_zero_network(self):
        marker="SYNTHETIC_PRIVATE_NEVER_ECHO"
        env={**os.environ,"KONEPS_KEY":marker}
        p=subprocess.run([sys.executable,str(ROOT/"wmm_koneps_secret_shape_offline.py")],
                         env=env,capture_output=True,text=True,check=True,timeout=4)
        self.assertNotIn(marker,p.stdout+p.stderr)
        obj=json.loads(p.stdout)
        self.assertEqual(obj["api_requests"],0)
        self.assertEqual(obj["items_published"],0)
        self.assertIs(obj["provider_authorization_verified"],False)
        self.assertIs(obj["actual_koneps_access_verified"],False)

    def test_cli_no_key_fails_closed(self):
        env={k:v for k,v in os.environ.items() if k!="KONEPS_KEY"}
        p=subprocess.run([sys.executable,str(ROOT/"wmm_koneps_secret_shape_offline.py")],
                         env=env,capture_output=True,text=True,timeout=4)
        self.assertEqual(p.returncode,2)
        self.assertIn("NOT_CONFIGURED",p.stdout)

    def test_workflow_owner_only_no_post_and_no_live_probe(self):
        w=(ROOT.parent/".github"/"workflows"/"wmm_koneps_secret_shape_owner.yml").read_text()
        for x in ("issue_comment","github.event.issue.number == 80",
                  "github.event.comment.author_association == 'OWNER'",
                  "/govradar-check-koneps-keyformat",
                  "KONEPS_KEY: " + "${{ secrets.KONEPS_KEY }}"):
            self.assertIn(x,w)
        self.assertNotIn("DAPA_KEY:",w)
        self.assertNotIn("wmm_koneps_bounded_probe.py",w)
        self.assertNotIn("curl ",w)

if __name__=="__main__":
    unittest.main()
