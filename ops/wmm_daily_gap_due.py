#!/usr/bin/env python3
"""WMM GOV RADAR daily feed freshness gate. No source API calls or publication.

Used by two existing, trusted workflows:
- DEFAULT branch daily schedule: skip a delayed duplicate if today's KST feed
  was already published by a successful fallback.
- EXISTING hourly watch's workflow_run: recover when that day's scheduled
  feed has not published after 08:30 KST, with a conservative 3h cooldown
  and at most two fallback attempts per KST day.

Read only two public GitHub Actions metadata lists when mode=fallback.
Never print GitHub tokens, provider raw HTTP responses, customer records.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

UTC = dt.timezone.utc
KST = dt.timezone(dt.timedelta(hours=9))
REPO = "leedukyoung74-wq/govradar-site"
WORKFLOWS = ("schedule.yml", "wmm_daily_gap_recovery.yml")
RETRY_COOLDOWN = dt.timedelta(hours=3)
FALLBACK_START = dt.time(8, 30)
MAX_FALLBACKS_PER_KST_DAY = 2


def read_utc(value):
    if not isinstance(value, str) or len(value) > 45:
        return None
    try:
        moment = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return moment.astimezone(UTC) if moment.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def read_feed_times(folder):
    root = Path(folder)
    result = {}
    for name in ("tenders.json", "today.json"):
        try:
            item = json.loads((root / "feeds" / name).read_text(encoding="utf-8"))
            value = item.get("updated") if isinstance(item, dict) else None
        except (OSError, UnicodeError, TypeError, ValueError):
            value = None
        result[name] = read_utc(value)
    return result


def get_runs(name, token):
    if name not in WORKFLOWS:
        raise ValueError("workflow name not allowlisted")
    if not token:
        raise ValueError("metadata token missing")
    url = ("https://api.github.com/repos/" + REPO +
           "/actions/workflows/" + name + "/runs?per_page=30")
    request = urllib.request.Request(
        url, method="GET",
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "WMM-daily-gap-readonly/1.0"})
    with urllib.request.urlopen(request, timeout=12) as response:
        if response.status != 200:
            raise ValueError("GitHub metadata status")
        raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("GitHub metadata response too large")
    parsed = json.loads(raw)
    runs = parsed.get("workflow_runs") if isinstance(parsed, dict) else None
    if not isinstance(runs, list):
        raise ValueError("invalid metadata schema")
    return runs


def decision(stamps, now, mode="fallback", scheduled=None, fallback=None,
             current_id=None):
    if now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    now = now.astimezone(KST)
    today = now.date()
    if any(stamps.get(n) is None for n in ("tenders.json", "today.json")):
        return "BLOCKED_MISSING_PUBLICATION_TIMESTAMP", False
    dates = [stamps[n].astimezone(KST) for n in ("tenders.json", "today.json")]
    if any(x > now + dt.timedelta(minutes=5) for x in dates):
        return "BLOCKED_PUBLICATION_CLOCK_SKEW", False
    if all(x.date() == today for x in dates):
        return "TODAY_ALREADY_PUBLISHED", False
    if any(x.date() > today for x in dates):
        return "BLOCKED_PUBLICATION_CLOCK_SKEW", False
    if mode == "scheduled":
        return "SCHEDULED_DAILY_MISSING_FOR_TODAY", True
    if mode != "fallback":
        raise ValueError("unapproved mode")
    if now.timetz().replace(tzinfo=None) < FALLBACK_START:
        return "DEFER_UNTIL_0830_KST", False
    if scheduled is None or fallback is None:
        return "BLOCKED_GITHUB_METADATA_MISSING", False

    # Even a started official daily schedule may still be running or publishing.
    # Never race a recently started scheduled daily job.
    for run in scheduled:
        if not isinstance(run, dict) or run.get("event") != "schedule":
            continue
        started = read_utc(run.get("created_at"))
        if started is None:
            continue
        elapsed = now - started.astimezone(KST)
        if dt.timedelta(0) <= elapsed < RETRY_COOLDOWN:
            return "RECENT_PRIMARY_DAILY_ATTEMPT", False

    recent_fallback = []
    day_start = dt.datetime.combine(today, FALLBACK_START, tzinfo=KST)
    for run in fallback:
        if not isinstance(run, dict) or run.get("event") not in (
                "workflow_run", "issue_comment"):
            continue
        if str(run.get("id")) == str(current_id):
            continue
        started = read_utc(run.get("created_at"))
        if started is None:
            continue
        started = started.astimezone(KST)
        if day_start <= started <= now:
            recent_fallback.append(started)
    if len(recent_fallback) >= MAX_FALLBACKS_PER_KST_DAY:
        return "DAILY_FALLBACK_ATTEMPT_CAP", False
    if recent_fallback and now - max(recent_fallback) < RETRY_COOLDOWN:
        return "DAILY_FALLBACK_COOLDOWN", False
    return "MISSING_TODAY_AND_SAFE_TO_COLLECT", True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("scheduled", "fallback"), required=True)
    p.add_argument("--data", type=Path, required=True)
    a = p.parse_args()
    now = dt.datetime.now(UTC)
    stamps = read_feed_times(a.data)
    if a.mode == "scheduled":
        reason, due = decision(stamps, now, "scheduled")
    else:
        # Do not query GH API if the feed has already been published today or
        # the fallback time window has not started.
        preliminary, _ = decision(stamps, now, "scheduled")
        if preliminary == "TODAY_ALREADY_PUBLISHED":
            reason, due = preliminary, False
        elif now.astimezone(KST).time() < FALLBACK_START:
            reason, due = "DEFER_UNTIL_0830_KST", False
        elif preliminary.startswith("BLOCKED"):
            reason, due = preliminary, False
        else:
            try:
                token = os.environ.get("GH_TOKEN", "")
                scheduled = get_runs("schedule.yml", token)
                fallback = get_runs("wmm_daily_gap_recovery.yml", token)
                reason, due = decision(
                    stamps, now, "fallback", scheduled, fallback,
                    os.environ.get("GITHUB_RUN_ID"))
            except (OSError, ValueError, TypeError, urllib.error.URLError,
                    json.JSONDecodeError):
                reason, due = "BLOCKED_GITHUB_METADATA_ERROR", False

    result = {"gate": "WMM_DAILY_MISSING_ONLY", "mode": a.mode,
              "status": reason, "due": due, "checked_at_utc": now.isoformat(),
              "source_requests": 0, "items_published_by_gate": 0,
              "secret_exposed": False, "data_files_modified": False}
    print(json.dumps(result, sort_keys=True))
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as out:
            out.write("due=" + str(due).lower() + "\n")
            out.write("reason=" + reason + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as out:
            out.write("\n### Daily feed due-check: " + reason +
                      "\n\nNo public data modified by this gate. "
                      "Publish and official-source validation occur only in the "
                      "existing reusable collector after this gate passes.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
