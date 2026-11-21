"""Run the existing source-video check hidden and record publication metadata for review."""

from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys

from pipeline.audit_feeds import KST, atomic_json


ROOT = Path(__file__).resolve().parent
EXISTING = Path.home() / "WMM-AI-Workspace" / "04_Free_Radar_Global" / "WMM_Free_Radar_Global_v2"
VIDEO = re.compile(r"[a-zA-Z0-9_-]{11}")


def todays_links(path, now):
    found = {}
    if not path.is_file():
        return []
    local_day = now.date()
    with path.open(encoding="utf-8-sig") as source:
        for line in source:
            try:
                item = json.loads(line)
                video = item.get("video_id", "")
                when = datetime.fromisoformat(item["published_at"]).astimezone(KST)
                if when.date() != local_day or when > now or not VIDEO.fullmatch(video):
                    continue
                if item["status"] != "official_channel_publication":
                    continue
                found[video] = {"speaker": item["person"][:80], "title": item["title"][:220],
                                "published_at_kst": when.isoformat(), "url": f"https://www.youtube.com/watch?v={video}",
                                "state": "source_publication_only"}
            except (AttributeError, KeyError, TypeError, ValueError):
                continue
    return sorted(found.values(), key=lambda x: x["published_at_kst"], reverse=True)[:24]


def main():
    command = [str(Path(sys.executable).with_name("python.exe")), str(EXISTING / "prophecy_daily_run.py")]
    try:
        result = subprocess.run(command, cwd=EXISTING, capture_output=True, timeout=510,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False)
        ok = result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        ok = False
    now = datetime.now(KST)
    links = todays_links(EXISTING / "prophecy_watch" / "youtube_history.jsonl", now)
    atomic_json(ROOT / "state" / "prophecy" / "latest.json",
                {"checked_at_kst": now.isoformat(), "collection_status": "ok" if ok else "recheck",
                 "items": links, "claims_verified": False})
    return int(not ok)


if __name__ == "__main__":
    raise SystemExit(main())
