"""One GOV RADAR work receipt for feed checks, ChatGPT intake and Claude QA."""

import argparse
import datetime as dt
from html import escape
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from claude.claude_qa import review
from pipeline.audit_feeds import KST, atomic_json, inspect


ROOT = Path(__file__).resolve().parent
MARKED_JSON = re.compile(r"\A\s*===JSON START===\s*(.*?)\s*===JSON END===\s*\Z", re.S)


def intake(source, repo, work, day):
    if source is None or not source.is_file():
        return {"state": "NODATA", "countries_passed": 0, "countries_failed": 0}
    try:
        if source.stat().st_size > 2_000_000:
            raise ValueError("research exceeds limit")
        raw = source.read_text(encoding="utf-8-sig").strip()
        if not raw.startswith("{"):
            block = MARKED_JSON.fullmatch(raw)
            if not block:
                raise ValueError("invalid JSON markers")
            raw = block[1]
        payload = json.loads(raw)
        if (not isinstance(payload, dict) or payload.get("kind") != "wmm_govradar_daily"
                or payload.get("date") != day.isoformat()
                or any(not isinstance(payload.get(key, {}), dict) for key in
                       ("country", "hazard", "official_directory_updates", "notes"))
                or not isinstance(payload.get("country", {}).get("countries", {}), dict)
                or len(payload.get("country", {}).get("countries", {})) > 16):
            raise ValueError("invalid research date, shape or scope")
        inputs = work / "input.json"
        atomic_json(inputs, payload)
        split_folder = work / "split"
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        for script, args in (
            ("gpt_daily_split.py", [inputs, split_folder]),
            ("inbox_check.py", [split_folder / "country", work / "checked", "--no-net"]),
        ):
            result = subprocess.run([sys.executable, "-X", "utf8", repo / "tools" / script, *args],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    timeout=30, creationflags=flags, check=False)
            if result.returncode:
                return {"state": "CHECK_FAILED", "countries_passed": 0, "countries_failed": 0}
        split = json.loads((split_folder / "split_report.json").read_text(encoding="utf-8"))
        day_report = work / "checked" / f"GPT_COUNTRY_{day:%Y%m%d}.report.json"
        checked = json.loads(day_report.read_text(encoding="utf-8")) if day_report.exists() else {}
        return {"state": "FORMAT_CHECKED" if split["status"] == "SPLIT_OK" else split["status"],
                "sha256": split["sha256"], "countries_passed": checked.get("pass", 0),
                "countries_failed": checked.get("fail", 0), "hazard_candidate": split["hazard"],
                "official_directory_candidates": split["directory"],
                "independent_claim_qa_required": True}
    except (AttributeError, OSError, ValueError, RecursionError, subprocess.SubprocessError):
        return {"state": "INVALID_INPUT", "countries_passed": 0, "countries_failed": 0}


def render_status(path, report, health):
    labels = {
        "usgs-fast": "USGS 지진 속보", "usgs": "USGS 지진", "nws": "미국 NWS 기상경보",
        "gdacs": "GDACS 재난", "cisa": "CISA 공개 권고", "tenders": "정부 입찰",
        "today": "오늘의 변경", "economy": "경제·환율", "sanctions": "공식 제재 목록",
    }
    states = {"PASS": "확인", "REVIEW": "지연·점검", "BLOCKED": "확인 실패"}
    rows = []
    for check in health["checks"]:
        age = check["age_minutes"]
        rows.append(f'<tr><th scope="row">{escape(labels.get(check["id"], check["id"]))}</th>'
                    f'<td>{escape(states[check["state"]])}</td>'
                    f'<td>{"미확인" if age is None else f"{age:g}분 전"}</td>'
                    f'<td>{"—" if check["count"] is None else check["count"]}</td></tr>')
    path.write_text(f"""<!doctype html>
<html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GOV RADAR 갱신 상태 · 검토본</title>
<style>
:root{{font:16px/1.55 system-ui,sans-serif;color:#162537;background:#f0f4f8}}
body{{margin:0}}main{{max-width:55rem;margin:auto;padding:3rem 1rem}}
h1{{margin:.15em 0;font-size:clamp(2rem,5.5vw,3.5rem);line-height:1.12}}
p{{max-width:42rem}} table{{text-align:left;width:100%;border-collapse:collapse;background:#fff;border-radius:.5rem}}
th,td{{padding:.68rem .5rem;border-bottom:1px solid #d4dce7}} thead{{background:#132b49;color:white}}
th{{font-weight:650}} @media(max-width:430px){{main{{padding:1.6rem .7rem}}th,td{{padding:.5rem .32rem}}}}
</style>
<main>
<p>GOV RADAR · 검토용</p><h1>데이터 갱신 상태</h1>
<p>{escape(report['task_id'])} · {escape(report['checked_at_kst'][:16].replace('T', ' '))} 한국시간</p>
<p>출처별 마지막 성공 시각을 기준으로 표시합니다. 지연이 있으면 담당 기관의 원문을 확인하세요.</p>
<table><thead><tr><th scope="col">출처 / 자료</th><th scope="col">상태</th><th scope="col">최근 확인</th><th scope="col">항목</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></main></html>""", encoding="utf-8")


def run(args):
    now = dt.datetime.now(KST)
    day = now.date()
    work = args.state_dir / f"GOVRADAR-{day:%Y%m%d}"
    work.mkdir(parents=True, exist_ok=True)
    attempt = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    research = args.research or (args.state_dir / "inbox" / f"GPT_DAILY_{day:%Y%m%d}.txt")
    health = inspect("daily", args.snapshot, now)
    atomic_json(attempt / "health.json", health)
    intake_result = intake(research, args.repo, attempt, day)
    qa_path = attempt / "claude.json"
    existing = work / "claude-receipt.json"
    use_claude = args.use_included_claude and health["status"] != "BLOCKED"
    if existing.exists():
        first = json.loads(existing.read_text(encoding="utf-8"))
        review_result = dict(first, evidence="earlier_same_day_snapshot")
    else:
        review_result = review(attempt / "health.json", qa_path, use_claude, attempt_dir=work)
        if review_result["status"] == "cross_review_completed":
            atomic_json(existing, review_result)
    report = {"schema_version": 1, "task_id": work.name, "checked_at_kst": now.isoformat(),
              "data_mode": "snapshot" if args.snapshot else "published",
              "health": {"status": health["status"], "findings": health["findings"],
                         "independence": health["independence"]},
              "research": intake_result,
              "claude": {k: review_result[k] for k in
                         ("status", "reason", "receipt", "assessment", "evidence", "findings", "report_sha256")
                         if k in review_result},
              "review": {"state": "PREVIEW_READY", "path": "index.html", "publish": "approval_required"},
              "evidence_dir": attempt.name}
    render_status(attempt / "index.html", report, health)
    atomic_json(work / "summary.json", report)
    atomic_json(args.state_dir / "latest.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, default=ROOT / "state")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--research", type=Path)
    parser.add_argument("--use-included-claude", action="store_true")
    args = parser.parse_args()
    result = run(args)
    if sys.stdout is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["health"]["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
