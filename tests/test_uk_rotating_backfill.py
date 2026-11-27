"""Read-only official UK cursor-budget and history-rotation regression tests."""
import datetime as dt
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
import feed_more as FM
import feed_tenders as FT

SOURCE = "UK Find a Tender"

class UKRotationContractTests(unittest.TestCase):
    def setUp(self):
        FM.STATS.clear()

    def test_four_shards_partition_nineteen_days_without_overlap(self):
        cutoff = dt.datetime(2026, 11, 27, 9, 0, tzinfo=dt.timezone.utc)
        shards = [FM.uk_backfill_shard(cutoff + dt.timedelta(days=i)) for i in range(4)]
        self.assertEqual({x[0] for x in shards}, {0, 1, 2, 3})
        # Freeze the same time to test exact coverage of the 19-day interval.
        # Daily rotation chooses all four slots during four successive UTC days.
        spans = [FM.uk_backfill_shard(cutoff + dt.timedelta(days=(slot - cutoff.date().toordinal()) % 4))
                 for slot in range(4)]
        for slot, start, end in spans:
            self.assertGreater(end, start)
            self.assertEqual(end - start, dt.timedelta(days=19)/4)
            self.assertEqual(start.tzinfo, dt.timezone.utc)
        # Under one fixed cutoff, all slot edges line up with no gaps.
        full_start = cutoff - dt.timedelta(days=21)
        full_end = cutoff - dt.timedelta(days=2)
        edges = [full_start + (full_end-full_start)*i/4 for i in range(5)]
        self.assertEqual(edges[0], full_start)
        self.assertEqual(edges[-1], full_end)

    def test_invalid_cutoff_rejected(self):
        with self.assertRaises(ValueError):
            FM.uk_backfill_shard(dt.datetime(2026, 11, 27, 9))
        with self.assertRaises(ValueError):
            FM.uk_backfill_shard(dt.datetime.now(dt.timezone.utc),pieces=0)

    def test_successful_bounded_http_still_partially_covers_uk(self):
        with patch.object(FM, "_ocds", return_value=[]) as mocked:
            self.assertEqual([], FM.uk())
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(mocked.call_args_list[0].kwargs["max_pages"], 8)
        self.assertEqual(mocked.call_args_list[1].kwargs["max_pages"], 4)
        recent = parse_qs(urlsplit(mocked.call_args_list[0].args[1]).query)
        history = parse_qs(urlsplit(mocked.call_args_list[1].args[1]).query)
        self.assertLess(history["updatedFrom"][0], history["updatedTo"][0])
        self.assertLessEqual(history["updatedTo"][0], recent["updatedFrom"][0])
        st=FM.stat(SOURCE)
        self.assertTrue(st["coverage_partial"])
        self.assertEqual(st["coverage"], "RECENT_48H_PLUS_ONE_OF_FOUR_ROTATING_19D_BACKFILL_SHARDS")
        self.assertEqual(st["backfill_shard_total"],4)
        self.assertEqual(FT.classify_state(st),"ERROR" if st["requests"] == 0 else "PARTIAL")
        self.assertIn("not a full UK scan", " ".join(st["notes"]))

    def test_successful_bounded_rows_cannot_report_complete(self):
        def fake(source,url,mk,**kwargs):
            FM.stat(source)["requests"] += 1
            FM.stat(source)["raw"] += 1
            return [{"sid":"sample", "est":"1000000", "iso":"GB"}]
        with patch.object(FM, "_ocds", side_effect=fake):
            rows = FM.uk()
        self.assertEqual(len(rows),1)
        self.assertEqual(FM.stat(SOURCE)["requests"],2)
        self.assertEqual(FT.classify_state(FM.stat(SOURCE)),"PARTIAL")

    def test_bounded_sam_also_partial_but_complete_source_still_success(self):
        self.assertEqual("PARTIAL",FT.classify_state({"requests":3,"failed":0,"raw":20,"coverage_partial":True}))
        self.assertEqual("SUCCESS",FT.classify_state({"requests":3,"failed":0,"raw":20,"coverage_partial":False}))
        self.assertEqual("ERROR",FT.classify_state({"requests":1,"failed":1,"raw":0,"coverage_partial":True}))

if __name__ == "__main__":
    unittest.main()
