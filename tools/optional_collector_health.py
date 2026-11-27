#!/usr/bin/env python3
"""Report optional subprocess failures and per-provider status from runner-local data.

No network, no credential echo, no website publishing. PASS only proves that
six subprocesses exited 0 and 16 fixed source flags reported ok=true; it never
proves record-level correctness, source freshness or public CDN readback.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys

EXPECTED = ("feed_intel", "feed_cty", "feed_official",
            "hz_disasters", "feed_econ", "feed_sanctions")
PROVIDER_FEEDS = {
    "official": ("hz/official.json", "sources",
                 ("usgs", "gdacs", "eonet", "who", "cneos", "swpc")),
    "econ": ("feeds/econ.json", "src",
             ("pop", "gdp", "pc", "gr", "cpi", "fx")),
    "sanctions": ("feeds/sanctions.json", "src",
                  ("un", "us", "eu", "uk")),
}


def source_states(data_root):
    if data_root is None:
        return {}
    base = Path(data_root)
    result = {}
    for group, (rel, parent, sources) in PROVIDER_FEEDS.items():
        try:
            value = json.loads((base / rel).read_text(encoding="utf-8"))
            rows = value.get(parent) if isinstance(value, dict) else None
        except (OSError, ValueError, UnicodeError, TypeError):
            rows = None
        for name in sources:
            info = rows.get(name) if isinstance(rows, dict) else None
            ok = info.get("ok") if isinstance(info, dict) else None
            result[group + "." + name] = (
                "PASS" if ok is True else
                "FAIL" if ok is False else "NOT_REPORTED"
            )
    return result


def report(raw, data_root=None):
    seen = {}
    invalid = False
    for line in raw.splitlines():
        fields = line.split("\t")
        if len(fields) != 2:
            invalid = True
            continue
        name, status = fields
        if name not in EXPECTED or status not in ("PASS", "FAIL") or name in seen:
            invalid = True
            continue
        seen[name] = status
    missing = [k for k in EXPECTED if k not in seen]
    failed = [k for k in EXPECTED if seen.get(k) == "FAIL"]
    upstream = source_states(data_root)
    upstream_fail = [k for k, v in upstream.items() if v == "FAIL"]
    upstream_unknown = [k for k, v in upstream.items() if v == "NOT_REPORTED"]
    complete = len(upstream) == 16 and not upstream_unknown
    state = ("INCOMPLETE" if invalid or missing or not complete else
             "DEGRADED" if failed or upstream_fail else "PASS")
    return {
        "schema_version": 2,
        "scope": "PROCESS_EXIT_AND_PROVIDER_OK_FLAG_ONLY",
        "state": state,
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results": {k: seen.get(k, "NOT_RUN") for k in EXPECTED},
        "failed_collectors": failed,
        "not_run_collectors": missing,
        "invalid_or_duplicate_events": invalid,
        "provider_status_only": upstream,
        "provider_failure_sources": upstream_fail,
        "provider_not_reported_sources": upstream_unknown,
        "provider_status_complete": complete,
        "source_freshness_verified": False,
        "public_site_readback_verified": False,
        "provider_access_verified": False,
        "customer_data_processed": False,
        "items_published_by_this_check": 0,
    }


def main(args):
    if args[:1] == ["report"] and len(args) == 4:
        raw_file, output, data_root = map(Path, args[1:])
        try:
            raw = raw_file.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError, UnicodeError):
            raw = ""
        value = report(raw, data_root)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Only allowlisted fixed source names; do not copy error text or URLs.
        print(json.dumps({"optional_collector_state": value["state"],
                          "failed_collectors": value["failed_collectors"],
                          "not_run_collectors": value["not_run_collectors"],
                          "provider_failure_sources": value["provider_failure_sources"],
                          "provider_not_reported_sources": value["provider_not_reported_sources"]},
                         ensure_ascii=False, sort_keys=True))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as fp:
                fp.write("\n## Daily collector and official provider status: " + value["state"] + "\n\n")
                fp.write("| Collector process | Exit result |\n|---|---|\n")
                for name, state in value["results"].items():
                    fp.write(f"| {name} | {state} |\n")
                fp.write("\n| Official data source | Returned ok flag |\n|---|---|\n")
                for name, state in value["provider_status_only"].items():
                    fp.write(f"| {name} | {state} |\n")
                fp.write("\nProcess success and provider flags do **not** prove source freshness, individual notice validity or public CDN readback.\n")
        return 0
    if args[:1] == ["gate"] and len(args) == 2:
        try:
            value = json.loads(Path(args[1]).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            print("BLOCKED: collector status artifact missing or invalid")
            return 1
        if (value.get("state") == "PASS"
            and set(value.get("results", {})) == set(EXPECTED)
            and all(value["results"][k] == "PASS" for k in EXPECTED)
            and value.get("provider_status_complete") is True
            and len(value.get("provider_status_only") or {}) == 16
            and all(v == "PASS" for v in value["provider_status_only"].values())):
            print("PASS: six subprocesses and sixteen provider flags; source freshness is a separate check")
            return 0
        print("DEGRADED: optional collector or provider incomplete/failed; previous-good data may still be displayed")
        return 1
    raise SystemExit("usage: optional_collector_health.py report <events.tsv> <result.json> <data_branch> | gate <result.json>")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
