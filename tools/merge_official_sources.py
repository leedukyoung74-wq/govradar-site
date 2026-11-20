#!/usr/bin/env python3
"""Merge the daily six-agency feed with a concurrent USGS fast update.

Used only after a rejected non-fast-forward data-branch push. The latest remote
file is authoritative for fast USGS updates; the freshly collected daily file
is authoritative for other agencies ONLY if its aggregate check is newer.
No APIs, credentials, or external commands are used by this module.
"""
import copy
import datetime as dt
import json
import os
from pathlib import Path
import sys
import tempfile


def kst_stamp(value):
    if not value:
        return ""
    if not isinstance(value, str):
        raise ValueError("invalid official feed timestamp")
    dt.datetime.strptime(value, "%Y-%m-%dT%H:%M")
    return value


def merge(remote, collected):
    for name, src in (("remote", remote), ("collected", collected)):
        if not isinstance(src, dict) or not isinstance(src.get("sources"), dict) or not isinstance(src.get("items"), dict):
            raise ValueError(f"{name} official feed has invalid structure")
        if not src["sources"] or not src["items"]:
            raise ValueError(f"{name} official feed is unexpectedly empty")

    remote_checked = kst_stamp(remote.get("checked"))
    daily_checked = kst_stamp(collected.get("checked"))
    if not remote_checked or not daily_checked:
        raise ValueError("missing daily official check timestamp")

    result = copy.deepcopy(remote)
    new_daily = daily_checked > remote_checked
    if new_daily:
        result["checked"] = daily_checked
        result["v"] = collected.get("v", result.get("v", 1))

    for source, status in collected["sources"].items():
        if not isinstance(status, dict):
            raise ValueError("invalid source status")
        if source == "usgs":
            remote_status = remote["sources"].get(source) or {}
            if not isinstance(remote_status, dict):
                raise ValueError("invalid remote USGS status")
            remote_seen = max(kst_stamp(remote.get("usgs_fast_checked")),
                              kst_stamp(remote_status.get("last_ok")))
            daily_seen = max(kst_stamp(collected.get("usgs_fast_checked")),
                             kst_stamp(status.get("last_ok")))
            use_daily = daily_seen > remote_seen
        else:
            use_daily = new_daily or source not in remote["sources"]

        if use_daily:
            result["sources"][source] = copy.deepcopy(status)
            if source in collected["items"]:
                result["items"][source] = copy.deepcopy(collected["items"][source])
            elif source != "swpc":
                raise ValueError(f"missing items for {source}")
            if source == "swpc":
                result["space"] = copy.deepcopy(collected.get("space"))
    # Never erase a fast-update heartbeat during a slower daily collection.
    result["usgs_fast_checked"] = max(
        kst_stamp(remote.get("usgs_fast_checked")),
        kst_stamp(collected.get("usgs_fast_checked")),
    ) or remote.get("usgs_fast_checked", "")
    return result


def write_atomic(path, result):
    fd, temp = tempfile.mkstemp(prefix=".govradar-merge-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, separators=(",", ":"))
            out.write("\n")
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main(current_path, collected_path):
    current = Path(current_path)
    published = json.loads(current.read_text(encoding="utf-8"))
    newly_collected = json.loads(Path(collected_path).read_text(encoding="utf-8"))
    result = merge(published, newly_collected)
    write_atomic(current, result)
    print(json.dumps({
        "status": "MERGED",
        "daily_checked": result.get("checked"),
        "usgs_fast_checked": result.get("usgs_fast_checked", ""),
        "source_count": len(result["sources"]),
    }))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: merge_official_sources.py REMOTE_OFFICIAL_JSON COLLECTED_OFFICIAL_JSON")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
