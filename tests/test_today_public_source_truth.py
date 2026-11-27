"""Fail-closed public source labels; no network, production data or writes."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import feed_today as F


class PublicSourceTruthTests(unittest.TestCase):
    def test_dapa_archival_sample_not_current_success(self):
        x = {"state":"SUCCESS", "kept":0, "data_freshness":"HISTORICAL_SAMPLE",
             "coverage":"FIRST_AND_LAST_PAGES_ONLY", "date_filter_verified":False}
        self.assertEqual("HISTORICAL_ONLY", F.public_source_state("DAPA (Korea)", x))
        self.assertEqual("SUCCESS", F.public_source_state("World Bank", x))
        self.assertEqual("ERROR", F.public_source_state("DAPA (Korea)", dict(x, state="ERROR")))
        self.assertEqual("SUCCESS", F.public_source_state("DAPA (Korea)", dict(x, kept=1)))

    def test_us_partial_pagination_not_full_coverage(self):
        x = {"state":"SUCCESS", "coverage_partial":True, "kept":80,
             "coverage":"BOUNDED_PAGES_NOT_ALL_US_NOTICES"}
        self.assertEqual("PARTIAL", F.public_source_state("SAM.gov (US)", x))
        self.assertEqual("SUCCESS", F.public_source_state(
            "SAM.gov (US)", dict(x, coverage_partial=False, coverage="COMPLETE")))
        self.assertEqual("ERROR", F.public_source_state("SAM.gov (US)", dict(x, state="ERROR")))

    def test_other_provider_states_retained(self):
        for label in ("SUCCESS", "PARTIAL", "ERROR", "EMPTY_SUCCESS", "UNKNOWN"):
            self.assertEqual(label, F.public_source_state("UK Find a Tender", {"state":label}))

    def test_today_summary_preserves_ingestion_state_provenance(self):
        records = {
            "DAPA (Korea)":{"state":"SUCCESS", "kept":0, "new_today":0,
                "data_freshness":"HISTORICAL_SAMPLE", "date_filter_verified":False,
                "coverage":"FIRST_AND_LAST_PAGES_ONLY"},
            "SAM.gov (US)":{"state":"SUCCESS", "kept":80, "new_today":4,
                "coverage_partial":True, "coverage":"BOUNDED_PAGES_NOT_ALL_US_NOTICES"},
            "World Bank":{"state":"SUCCESS", "kept":317, "new_today":20},
        }
        def fake_load(filename):
            return {"feeds/sources_status.json":records}.get(filename,{})
        with patch.object(F, "load", side_effect=fake_load):
            out = F.build()
        src = {x["name"]:x for x in out["src"]}
        self.assertEqual("HISTORICAL_ONLY", src["DAPA (Korea)"]["state"])
        self.assertEqual("SUCCESS", src["DAPA (Korea)"]["ingestion_state"])
        self.assertEqual("PARTIAL", src["SAM.gov (US)"]["state"])
        self.assertEqual("SUCCESS", src["SAM.gov (US)"]["ingestion_state"])
        self.assertEqual("SUCCESS", src["World Bank"]["state"])
        self.assertEqual(0, out["n"]["open"])


if __name__ == "__main__":
    unittest.main()
