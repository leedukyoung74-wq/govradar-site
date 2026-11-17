"""Server record for member requests (cf/functions/api/req.js) against an in-memory SQLite stand-in for Cloudflare D1."""
import os, shutil, subprocess, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
class ReqServer(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_limits_duplicates_history_refund(self):
        r = subprocess.run(["node", "--experimental-sqlite", os.path.join(HERE, "js", "req_server_test.mjs")], capture_output=True, text=True)
        if "No such built-in module" in r.stderr or "node:sqlite" in r.stderr: self.skipTest("node without sqlite")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertIn("req_server OK", r.stdout)
