#!/usr/bin/env python3
"""Publish only current, evidence-backed site_check.json, preserving concurrent data writes.

This runs ONLY in the owner-authorized non-dry-run feed workflow, AFTER feed
publication and site probe. Never promotes old success, never edits production
HTML, and never accesses customer data.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import tempfile


FMT = "%Y-%m-%dT%H:%MZ"


def clock(value):
    if not isinstance(value, str):
        raise ValueError("checked timestamp missing")
    return dt.datetime.strptime(value, FMT).replace(tzinfo=dt.timezone.utc)


def validate_report(report, now=None):
    if not isinstance(report, dict) or report.get("result") not in ("PASS", "FAIL"):
        raise ValueError("site check must explicitly say PASS or FAIL")
    now = now or dt.datetime.now(dt.timezone.utc)
    age = (now - clock(report.get("checked"))).total_seconds()
    if age < -120 or age > 5400:
        raise ValueError("stale or future site-check evidence cannot be published")
    if not isinstance(report.get("pages"), list) or len(report["pages"]) < 4:
        raise ValueError("insufficient page probe evidence")
    if not isinstance(report.get("feeds"), dict) or not {
        "tenders.json", "cty/_summary.json", "awards.json"
    }.issubset(report["feeds"]):
        raise ValueError("insufficient feed evidence")
    if not isinstance(report.get("local"), dict):
        raise ValueError("local feed schema evidence missing")
    if report["result"] == "PASS":
        if any(p.get("status") != 200 or p.get("reads_feed") is not True
               for p in report["pages"]):
            raise ValueError("PASS contradicts public page evidence")
        if any(f.get("status") != 200 or f.get("fresh") is not True or
               f.get("issue") != "ok" or (f.get("count") or 0) <= 0
               for f in report["feeds"].values()):
            raise ValueError("PASS contradicts public feed evidence")
        if report["local"].get("issue") != "ok":
            raise ValueError("PASS contradicts local data evidence")
    return clock(report["checked"])


def decision(existing, candidate):
    """A newer already-published report wins, including when it is FAIL."""
    if existing is None:
        return "publish"
    try:
        old = clock(existing.get("checked"))
        new = clock(candidate["checked"])
    except (TypeError, ValueError, KeyError):
        return "publish"  # malformed existing report cannot block valid evidence
    return "skip" if old >= new else "publish"


def git(path, *args, allow_fail=False):
    command = ["git", "-C", str(path), *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode and not allow_fail:
        raise RuntimeError("git operation failed: " + " ".join(args) +
                           " / " + result.stderr[:180])
    return result


def publish(branch_dir, report_file):
    branch_dir = Path(branch_dir).resolve()
    report_file = Path(report_file).resolve()
    if report_file != branch_dir / "feeds" / "site_check.json":
        raise ValueError("can publish only data/feeds/site_check.json")
    current = json.loads(report_file.read_text(encoding="utf-8"))
    validate_report(current)
    name = git(branch_dir, "branch", "--show-current").stdout.strip()
    if name != "data":
        raise ValueError("requires checked-out data branch")
    payload = json.dumps(current, ensure_ascii=False, indent=1) + "\n"

    # A detached, temporary worktree isolates the report push from uncommitted
    # sample-verification artifacts in the primary data_branch checkout.
    with tempfile.TemporaryDirectory(prefix="wmm-sitecheck-") as folder:
        worktree = Path(folder) / "wt"
        git(branch_dir, "worktree", "add", "--detach", "-q", str(worktree), "HEAD")
        try:
            for attempt in range(1, 4):
                if attempt > 1:
                    git(branch_dir, "fetch", "-q", "origin",
                        "data:refs/remotes/origin/data")
                    git(worktree, "reset", "--hard", "origin/data")
                destination = worktree / "feeds" / "site_check.json"
                try:
                    existing = json.loads(destination.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    existing = None
                if decision(existing, current) == "skip":
                    print("SITE_CHECK_ALREADY_CURRENT_OR_NEWER=YES")
                    return
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(payload, encoding="utf-8")
                git(worktree, "add", "--", "feeds/site_check.json")
                if not git(worktree, "diff", "--cached", "--quiet",
                           allow_fail=True).returncode:
                    print("SITE_CHECK_NO_CHANGE=YES")
                    return
                git(worktree, "config", "user.name", "GOV RADAR bot")
                git(worktree, "config", "user.email", "leedukyoung74@gmail.com")
                git(worktree, "commit", "-m",
                    "Site check " + current["result"] + " " + current["checked"])
                push = git(worktree, "push", "origin", "HEAD:refs/heads/data",
                           allow_fail=True)
                if push.returncode == 0:
                    print("SITE_CHECK_EVIDENCE_PUBLISHED=YES")
                    print("SITE_CHECK_REPORTED_RESULT=" + current["result"])
                    return
                print("site_check non-fast-forward; rebase report on latest data",
                      attempt)
            raise RuntimeError("SITE_CHECK_PUBLISH_FAILED after 3 attempts; "
                               "no forced data overwrite")
        finally:
            git(branch_dir, "worktree", "remove", "--force", str(worktree))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_branch")
    args = parser.parse_args()
    branch = Path(args.data_branch)
    publish(branch, branch / "feeds" / "site_check.json")


if __name__ == "__main__":
    main()
