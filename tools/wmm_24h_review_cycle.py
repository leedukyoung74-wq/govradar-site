#!/usr/bin/env python3
"""Read-only 24-hour WMM review scheduler. No agents, deployment, payments or network.

GitHub Actions scheduled workflows run only from the repository DEFAULT branch.
This controller additionally requires an explicit enabled flag and a start time.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc
PHASES = (
    ("inventory", ("docs/WMM_GLOBAL_INTELLIGENCE_SOLUTION_OS_20261120.md",
                   "docs/WMM_24H_AUTONOMOUS_BUILD_RUNBOOK_20261120.md")),
    ("govradar-data", ("tools/check_export_inputs.py",
                       "tools/check_research_coverage.py",
                       "tools/check_build_consistency.py")),
    ("customer-intake", ("schemas/wmm_cross_site_intake_v1.schema.json",
                         "tests/test_wmm_intake_contract.py")),
    ("internationalization", ("pages3.py", "tests/test_tender_disclosure_generated.py")),
    ("release-safety", ("tools/check_public_fixture_leak.py",
                        "tests/test_publish_export_preflight.py")),
    ("handover-report", (".github/workflows/wmm_tender_disclosure_qa.yml",
                         "docs/WMM_GLOBAL_INTELLIGENCE_SOLUTION_OS_20261120.md")),
)

def utc_datetime(raw):
    value = dt.datetime.fromisoformat(str(raw).strip().replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("UTC offset required")
    return value.astimezone(UTC)

def evaluate(event, enabled, start_utc, now, requested_cycle=0):
    """Fail closed on schedule, allow harmless PR/manual preview without activation."""
    if event not in ("schedule", "pull_request", "workflow_dispatch"):
        return {"run": False, "reason": "unsupported_event", "cycle": None}
    if event != "schedule":
        if not isinstance(requested_cycle, int) or not 0 <= requested_cycle < 24:
            return {"run": False, "reason": "invalid_preview_cycle", "cycle": None}
        return {"run": True, "reason": "review_preview_only", "cycle": requested_cycle}
    if str(enabled).strip().lower() != "true":
        return {"run": False, "reason": "explicit_enable_required", "cycle": None}
    try:
        start = utc_datetime(start_utc)
        current = now.astimezone(UTC)
    except (ValueError, TypeError, AttributeError):
        return {"run": False, "reason": "invalid_utc_start", "cycle": None}
    hours = (current - start).total_seconds() / 3600
    if hours < 0:
        return {"run": False, "reason": "window_not_started", "cycle": None}
    if hours >= 24:
        return {"run": False, "reason": "window_expired", "cycle": None}
    return {"run": True, "reason": "scheduled_read_only_review", "cycle": int(hours)}

def phase_for_cycle(cycle):
    if not isinstance(cycle, int) or not 0 <= cycle < 24:
        raise ValueError("cycle must be between 0 and 23")
    return PHASES[cycle // 4]

def review(cycle, root=ROOT):
    """Metadata-only checklist; no actual code generation or runtime deployment."""
    name, paths = phase_for_cycle(cycle)
    present = [path for path in paths if (root / path).is_file()]
    absent = sorted(set(paths) - set(present))
    return {
        "kind": "WMM_REVIEW_ONLY_NO_DEPLOY",
        "cycleIndex": cycle,
        "phase": name,
        "checkedFiles": list(paths),
        "missingFiles": absent,
        "passed": not absent,
        "actualWork": "Static source presence and offline CI; not autonomous coding or 24h completion",
        "productionDeployment": False,
        "aiApiCalls": False,
        "customerDataCollection": False,
        "limitations": "The run does not verify live source data, browser QA or 193-country completeness.",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("gate", "report"))
    parser.add_argument("--cycle", type=int, default=int(os.getenv("WMM_CYCLE_INDEX", "0")))
    parser.add_argument("--output-dir", default="review-evidence")
    args = parser.parse_args()
    if args.action == "gate":
        gate = evaluate(
            os.getenv("GITHUB_EVENT_NAME", "workflow_dispatch"),
            os.getenv("WMM_24H_REVIEW_ENABLED", ""),
            os.getenv("WMM_24H_REVIEW_START_UTC", ""),
            dt.datetime.now(UTC), args.cycle,
        )
        print(json.dumps(gate, ensure_ascii=False))
        output = os.getenv("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf8") as handle:
                for key, value in (("run", "true" if gate["run"] else "false"),
                                   ("cycle", str(gate["cycle"] if gate["cycle"] is not None else "")),
                                   ("reason", gate["reason"])):
                    handle.write(key + "=" + value + "\n")
        return 0
    result = review(args.cycle)
    target = Path(args.output_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "cycle.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    summary = ("WMM 24h Review ONLY\n" +
               "Cycle: " + str(args.cycle) + " / 23\n" +
               "Phase: " + result["phase"] + "\n" +
               "Missing: " + (", ".join(result["missingFiles"]) or "none") + "\n" +
               "Operational deployment: NO\n")
    (target / "summary.txt").write_text(summary, encoding="utf8")
    print(summary)
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
