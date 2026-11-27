"""Reusable feed must build disposable static HTML before generated-page tests.

Offline structural test only. No network calls, secrets or data publication.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/feeds.yml"


class ReusableFeedPreflightTests(unittest.TestCase):
    def test_preflight_before_collect_and_publication(self):
        source=WORKFLOW.read_text(encoding="utf8")
        markers=(
            "python3 build.py --base https://radar.wmm-hoa.com",
            "python3 tools/cf_variant.py dist cf/public",
            "run: python -m unittest discover -s tests",
            "run: python tools/feed_tenders.py",
            "run: python tools/quality_gate.py data_branch",
            "- name: Publish to data branch",
        )
        index=[source.index(x) for x in markers]
        self.assertEqual(index, sorted(index))
        self.assertIn("if: ${{ !inputs.dry_run }}", source)
        self.assertIn("PUBLISH_FAILED after 3 attempts", source)

    def test_no_new_customer_side_effects_in_added_preflight(self):
        source=WORKFLOW.read_text(encoding="utf8")
        fragment=source.split("- name: Build static preview needed by offline tests (NO DEPLOY)",1)[1].split("- name: Offline tests first",1)[0]
        self.assertIn("cf/public",fragment)
        for forbidden in ("git push", "curl", "POST", "SAM_KEY", "DAPA_KEY", "deploy", "npm install"):
            self.assertNotIn(forbidden,fragment)


if __name__ == "__main__":
    unittest.main()
