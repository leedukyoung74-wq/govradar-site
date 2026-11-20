"""Read-only fallback gate for GOV RADAR's already-reviewed public NWS/CISA feeds.

GitHub's schedule is best effort, not a 15-minute SLA. A *successful* USGS
workflow can wake the NWS/CISA collector if published source timestamps are
too old. This gate does not fetch any API, write feed files, or publish data.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

UTC = dt.timezone.utc
# Stay under the watch's NWS 180min and CISA 600min limits when wakeups occur.
LIMITS = (("nws_active.json", 90 * 60), ("cisa_kev.json", 8 * 3600))
CLOCK_SKEW_SECONDS = 5 * 60
# On upstream failures, do not hammer official endpoints each time a
# successful USGS run wakes the fallback. Keep delayed status visible.
FAILED_RETRY_COOLDOWN_SECONDS = 30 * 60


def parse_utc(s):
    if not isinstance(s, str) or not s:
        return None
    try:
        value = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError, OverflowError):
        return None
    return value.astimezone(UTC) if value.tzinfo else None


def needs_refresh(path, max_age_seconds, now):
    """Missing, unhealthy, invalid or old data MUST NOT count as fresh."""
    try:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        h = d["source_health"]
        if not isinstance(h, dict):
            return True
        if h.get("ok") is not True or h.get("stale") is not False:
            checked = parse_utc(h.get("checked_at"))
            if checked is not None:
                seconds = (now - checked).total_seconds()
                if -CLOCK_SKEW_SECONDS <= seconds < FAILED_RETRY_COOLDOWN_SECONDS:
                    return False  # failed recently; retain public delayed signal
            return True
        stamp = parse_utc(h.get("last_ok"))
        if stamp is None:
            return True
        age = (now - stamp).total_seconds()
        return age < -CLOCK_SKEW_SECONDS or age >= max_age_seconds
    except (OSError, UnicodeError, TypeError, ValueError, KeyError, AttributeError):
        return True


def should_refresh(event, data_root, now=None):
    if event != "workflow_run":
        # Preserve the existing manual/scheduled/push execution behavior.
        return True
    now = now or dt.datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("now must have a timezone")
    folder = Path(data_root) / "hz"
    return any(needs_refresh(folder / name, limit, now) for name, limit in LIMITS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, choices=("workflow_run", "schedule", "workflow_dispatch", "push"))
    parser.add_argument("--data", required=True, type=Path)
    args = parser.parse_args()
    # Must be a single strict key=value line: GitHub reads this via $GITHUB_OUTPUT.
    print("refresh=" + ("true" if should_refresh(args.event, args.data) else "false"))


if __name__ == "__main__":
    main()
