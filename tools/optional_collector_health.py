#!/usr/bin/env python3
"""Report per-run optional collector exit states without publishing stale false-green data.

No source/API requests, no GitHub credentials, no customer data. This tool only
reads six fixed collector names and PASS/FAIL events in a runner-local TSV.
It does not assert that a provider returned fresh data; per-source freshness
and public readback must be validated separately.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys

EXPECTED = (
    "feed_intel", "feed_cty", "feed_official", "hz_disasters",
    "feed_econ", "feed_sanctions",
)


def report(raw):
    seen = {}
    invalid = False
    for line in raw.splitlines():
        cells = line.split("\t")
        if len(cells) != 2:
            invalid = True
            continue
        name, status = cells
        if name not in EXPECTED or status not in ("PASS", "FAIL") or name in seen:
            invalid = True
            continue
        seen[name] = status
    missing = [name for name in EXPECTED if name not in seen]
    failing = [name for name in EXPECTED if seen.get(name) == "FAIL"]
    state = "INCOMPLETE" if invalid or missing else ("DEGRADED" if failing else "PASS")
    return {
        "schema_version": 1,
        "scope": "OPTIONAL_COLLECTOR_PROCESS_EXIT_ONLY",
        "state": state,
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results": {name: seen.get(name, "NOT_RUN") for name in EXPECTED},
        "failed_collectors": failing,
        "not_run_collectors": missing,
        "invalid_or_duplicate_events": invalid,
        "source_freshness_verified": False,
        "public_site_readback_verified": False,
        "provider_access_verified": False,
        "customer_data_processed": False,
        "items_published_by_this_check": 0,
    }


def main(args):
    if len(args) not in (2, 3):
        raise SystemExit("usage: optional_collector_health.py report <tsv> <json> | gate <json>")
    mode = args[0]
    if mode == "report" and len(args) == 3:
        path, output = (Path(args[1]), Path(args[2]))
        try:
            raw = path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError, UnicodeError):
            raw = ""
        result = report(raw)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        # Both log and summary contain only fixed whitelisted collector names.
        print(json.dumps({"optional_collector_state": result["state"],
                          "failed_collectors": result["failed_collectors"],
                          "not_run_collectors": result["not_run_collectors"]},
                         ensure_ascii=False, sort_keys=True))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as fp:
                fp.write("\n## Optional collector exit status: " + result["state"] + "\n\n")
                fp.write("| Collector | Run result |\n|---|---|\n")
                for name, state in result["results"].items():
                    fp.write(f"| {name} | {state} |\n")
                fp.write("\nPASS means process exit 0, **not** provider freshness, official-item verification, or successful public deployment.\n")
        return 0
    if mode == "gate" and len(args) == 2:
        try:
            result = json.loads(Path(args[1]).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            print("BLOCKED: collector status artifact missing or invalid")
            return 1
        if (result.get("state") == "PASS" and
                set(result.get("results", {})) == set(EXPECTED) and
                all(result["results"].get(k) == "PASS" for k in EXPECTED)):
            print("PASS: six optional collector processes exited successfully; source freshness is a separate check")
            return 0
        print("DEGRADED: optional collector failures or incomplete run. Last-good data may still be displayed.")
        return 1
    raise SystemExit("invalid command")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
