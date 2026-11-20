"""Reconcile notices whose official closing time passed during a long feed run.

This runs immediately before the strict quality gate. It removes only notices
that became *closed* according to the shared deadline rule, then rebuilds
derived country/home counters. It never invents new records, refreshes source
timestamps, contacts an API, or publishes any data.
"""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deadline import state

ROOT = Path(__file__).resolve().parents[1]


def prune_closed(items, now):
    """Keep unexpired/unknown notices; unknown still fails the normal gate."""
    kept, closed = [], 0
    for item in items:
        if not isinstance(item, dict):
            kept.append(item)  # leave broken records for the strict gate
        elif state(item, now) == "closed":
            closed += 1
        else:
            kept.append(item)
    return kept, closed


def reconcile(data_root, now=None, rebuild=True):
    """Return removed count. Only local workspace files are changed."""
    data_root = Path(data_root).resolve()
    feed_path = data_root / "feeds" / "tenders.json"
    with feed_path.open("r", encoding="utf-8") as fh:
        feed = json.load(fh)
    if not isinstance(feed, dict) or not isinstance(feed.get("items"), list):
        raise ValueError("tenders.json must contain an items array")
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    kept, closed = prune_closed(feed["items"], now)
    if not closed:
        print("Deadline reconciliation: 0 newly closed notices; existing files unchanged")
        return 0

    feed["items"] = kept
    feed["count"] = len(kept)
    # Deliberately keep feed['updated'] unchanged: pruning is not a source refresh.
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=feed_path.parent,
                                         prefix=".tenders-reconciled-", suffix=".json",
                                         delete=False) as fh:
            tmp_path = Path(fh.name)
            json.dump(feed, fh, ensure_ascii=False)
        os.replace(tmp_path, feed_path)
        tmp_path = None
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)

    if rebuild:
        # Regenerate derived counters from the reconciled feed; a failure
        # aborts the workflow before the quality gate / publish step.
        subprocess.run([sys.executable, str(ROOT / "tools" / "feed_cty.py"),
                        str(data_root / "feeds")], check=True)
        subprocess.run([sys.executable, str(ROOT / "tools" / "feed_today.py"),
                        str(data_root)], check=True)
    print(f"Deadline reconciliation: dropped {closed} closed notices; "
          f"kept {len(kept)}; regenerated dependent counters" if rebuild else
          f"Deadline reconciliation: dropped {closed} closed notices; kept {len(kept)}")
    return closed


if __name__ == "__main__":
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data_branch"
    reconcile(base)
