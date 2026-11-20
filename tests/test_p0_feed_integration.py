"""Combined P0 data-pipeline integration: real subprocesses, no external HTTP."""
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import reconcile_expiring_tenders as R


class P0FeedIntegrationTests(unittest.TestCase):
    def test_prune_ghost_country_and_today_counter_stay_consistent(self):
        now = dt.datetime.now(dt.timezone.utc)
        already_closed = (now - dt.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        still_open = (now + dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with tempfile.TemporaryDirectory() as td:
            data = Path(td)
            feeds = data / "feeds"
            cty = feeds / "cty"
            cty.mkdir(parents=True)
            (cty / "CA.json").write_text(json.dumps({"updated":"2026-01-01T00:00Z","t":{"n":9}}),encoding="utf-8")
            items = [
                {"iso":"CA","deadline":already_closed[:10],"deadline_at":already_closed,"title":"Closed"},
                {"iso":"KR","deadline":still_open[:10],"deadline_at":still_open,"title":"Open",
                 "source":"World Bank","added":now.date().isoformat(),"buyer":"Gov",
                 "url":"https://example.org/open","urgent":False}
            ]
            original_stamp = (now-dt.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%MZ")
            (feeds / "tenders.json").write_text(json.dumps({"updated":original_stamp,"count":2,"items":items}),encoding="utf-8")
            dropped = R.reconcile(data, now=now)
            tender = json.loads((feeds / "tenders.json").read_text(encoding="utf-8"))
            country = json.loads((cty / "CA.json").read_text(encoding="utf-8"))
            summary = json.loads((cty / "_summary.json").read_text(encoding="utf-8"))
            today = json.loads((feeds / "today.json").read_text(encoding="utf-8"))
            self.assertEqual(1,dropped)
            self.assertEqual(1,tender["count"])
            self.assertEqual(original_stamp,tender["updated"])
            self.assertEqual(0,country["t"]["n"])
            self.assertEqual(1,summary["t"]["n"])
            self.assertEqual(1,summary["t"]["c"])
            self.assertEqual(1,today["n"]["open"])


if __name__ == "__main__":
    unittest.main()
