"""Forward bounded public-feed health metadata to Claude on an eligible existing plan."""

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


KST = dt.timezone(dt.timedelta(hours=9))
TOKEN = re.compile(r"[a-z0-9_-]{1,55}")
STATUSES = {"ok", "http_error", "failed", "availability_only", "no_usable_links"}
DISALLOWED_ENV = (
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY", "ANTHROPIC_CUSTOM_HEADERS",
)
RECEIPT = "WMM-GOV-RADAR-QA-RECEIVED"
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["receipt", "assessment", "findings"],
    "properties": {
        "receipt": {"type": "string", "const": RECEIPT},
        "assessment": {"type": "string", "enum": ["review_needed", "no_new_issue"]},
        "findings": {"type": "array", "maxItems": 4, "items": {"type": "string", "maxLength": 320}},
    },
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
    os.replace(file.name, path)


def sanitize(data):
    if not isinstance(data, dict):
        raise ValueError("Expected a report object")
    if isinstance(data.get("sources"), list):
        sources = []
        for item in data["sources"][:32]:
            if not isinstance(item, dict):
                raise ValueError("Invalid source object")
            cat, owner, status = (item.get(k) for k in ("category", "owner", "status"))
            if not (isinstance(cat, str) and TOKEN.fullmatch(cat) and isinstance(owner, str)
                    and TOKEN.fullmatch(owner) and status in STATUSES and isinstance(item.get("items"), list)):
                raise ValueError("Invalid source category, group or status")
            sources.append({"category": cat, "owner": owner, "status": status, "item_count": len(item["items"])})
        return {"sources": sources, "claim_corroborated": False}
    if data.get("schema_version") == 1 and isinstance(data.get("checks"), list):
        checks = []
        for item in data["checks"][:40]:
            if not isinstance(item, dict) or not (isinstance(item.get("id"), str) and TOKEN.fullmatch(item["id"])):
                raise ValueError("Invalid feed identifier")
            state = item.get("state")
            if state not in {"PASS", "REVIEW", "BLOCKED"}:
                raise ValueError("Invalid feed state")
            age, count, limit = (item.get(k) for k in ("age_minutes", "count", "max_minutes"))
            checks.append({"id": item["id"], "state": state,
                           "age_minutes": age if type(age) in {int, float} and -10000 < age < 10000000 else None,
                           "max_minutes": limit if type(limit) is int and 0 < limit < 100000 else None,
                           "count": count if type(count) is int and 0 <= count <= 10000000 else None})
        return {"checks": checks, "claim_corroborated": False}
    raise ValueError("Unsupported report schema")


def invoke(command, input_text=None, timeout=20):
    return subprocess.run(command, input=input_text, capture_output=True, text=True, encoding="utf-8",
                          timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def review(report, output, use_included, *, config=None, local_date=None, attempt_dir=None):
    if report.stat().st_size > 4_000_000:
        raise ValueError("Oversize report")
    source = report.read_bytes()
    summary = sanitize(json.loads(source.decode("utf-8-sig")))
    digest = hashlib.sha256(source).hexdigest()
    day = local_date or dt.datetime.now(KST).date()
    if output.exists():
        previous = read_json(output)
        if previous.get("report_sha256") == digest and previous.get("review_date_kst") == day.isoformat():
            return previous
        raise ValueError("Output is already tied to a different report")
    result = {"schema_version": 1, "review_date_kst": day.isoformat(), "report_sha256": digest, "summary": summary}

    def finish(status, reason=None, **extra):
        result.update(status=status, **extra)
        if reason:
            result["reason"] = reason
        write_json(output, result)
        return result

    if not use_included:
        return finish("deterministic_only")
    if any(os.environ.get(key) for key in DISALLOWED_ENV):
        return finish("blocked", "alternate_billing_environment")
    try:
        local = read_json(config or Path.home() / ".claude.json")
        credits_disabled = local.get("cachedExtraUsageDisabledReason") == "org_level_disabled"
    except (OSError, ValueError, AttributeError):
        credits_disabled = False
    if not credits_disabled:
        return finish("blocked", "extra_usage_disable_unverified")
    exe = shutil.which("claude.exe") or shutil.which("claude")
    if not exe:
        return finish("blocked", "claude_cli_not_found")
    try:
        account = json.loads(invoke([exe, "auth", "status", "--json"]).stdout)
        if (account.get("loggedIn") is not True or account.get("authMethod") != "claude.ai"
                or account.get("apiProvider") != "firstParty" or account.get("subscriptionType") not in {"pro", "max", "ultra"}):
            return finish("blocked", "included_subscription_unverified")
    except (OSError, ValueError, AttributeError, subprocess.SubprocessError):
        return finish("blocked", "included_subscription_unverified")
    attempts = attempt_dir or output.parent
    attempts.mkdir(parents=True, exist_ok=True)
    try:
        with (attempts / f"claude-{day.isoformat()}.lock").open("x", encoding="utf-8") as stream:
            stream.write(digest + "\n")
    except FileExistsError:
        return finish("blocked", "daily_attempt_already_recorded")
    prompt = (
        f"GOV RADAR-{day:%Y%m%d}. Acknowledge with {RECEIPT}. Check the machine evidence below for stale "
        "official sources, duplicate publisher groups and missing verification. In Korean, return at most four "
        "plain-text findings and choose review_needed or no_new_issue. This is evidence for a draft site review, "
        "with no runtime actions, no access to source articles and no publication. Distinguish no alerts from "
        "failed retrieval. Judge staleness using each check's max_minutes, not a universal threshold. A null "
        "count means the document is not an item list. USGS and USGS-fast are a single publisher. Do not "
        "claim independent corroboration or test runs.\n"
        + json.dumps(summary, ensure_ascii=True, allow_nan=False)
    )
    command = [exe, "--print", "--safe-mode", "--tools", "", "--strict-mcp-config", "--setting-sources", "",
               "--no-session-persistence", "--model", "haiku", "--effort", "low",
               "--output-format", "json", "--json-schema", json.dumps(SCHEMA)]
    try:
        run = invoke(command, prompt, timeout=95)
        reply = json.loads(run.stdout)
        received = reply.get("structured_output")
        if (run.returncode or reply.get("is_error") or not isinstance(received, dict) or received.get("receipt") != RECEIPT
                or received.get("assessment") not in {"review_needed", "no_new_issue"}
                or not isinstance(received.get("findings"), list) or len(received["findings"]) > 4
                or any(not isinstance(f, str) or len(f) > 320 for f in received["findings"])):
            return finish("review_failed", "response_unverified")
        return finish("cross_review_completed", receipt=RECEIPT, assessment=received["assessment"],
                      findings=received["findings"])
    except (OSError, ValueError, AttributeError, subprocess.SubprocessError):
        return finish("review_failed", "response_unavailable")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--use-included-claude", action="store_true")
    parser.add_argument("--attempt-dir", type=Path)
    args = parser.parse_args()
    try:
        review(args.report, args.output, args.use_included_claude, attempt_dir=args.attempt_dir)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
