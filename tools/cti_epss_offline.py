#!/usr/bin/env python3
"""Internal-only CISA KEV + FIRST EPSS offline enrichment.

This tool makes ZERO network requests, touches no customer systems or private
records, and never authorizes publishing, paid CTI services or victim claims.
Inputs must be the existing normalized WMM CISA KEV JSON and an official FIRST
EPSS daily CSV (or CSV.GZ) already obtained through an approved process.
"""
import argparse
import csv
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
from pathlib import Path
import re

KEV_SCHEMA = "wmm-cti-safe-intake.v1"
KEV_URL = "https://raw.githubusercontent.com/cisagov/kev-data/refs/heads/develop/known_exploited_vulnerabilities.json"
EPSS_URL = "https://www.first.org/epss/data"
CVE = re.compile(r"^CVE-[0-9]{4}-[0-9]{4,19}$")
SCORE_HEADER = re.compile(r"^#model_version:[\w.-]{1,36},score_date:(\d{4}-\d{2}-\d{2})(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)?$")
KEV_FIELDS = {"id", "vendor", "product", "date_added", "ransomware_reported", "evidence_level",
              "source_url", "public_redistribution_approval", "enterprise_impact",
              "victim_or_outage_confirmed", "tlp"}
MAX_KEV_BYTES = 12_000_000
MAX_INPUT_BYTES = 60_000_000
MAX_UNCOMPRESSED_BYTES = 90_000_000
MAX_CSV_ROWS = 800_000
MAX_CSV_LINE = 350
MAX_DATA_AGE_HOURS = 48


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Missing KEV timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid KEV timestamp") from exc
    if dt.tzinfo is None:
        raise ValueError("KEV timestamp must be timezone-aware")
    return dt.astimezone(timezone.utc)


def score_fraction(value):
    if not isinstance(value, str) or len(value) > 30:
        raise ValueError("Invalid EPSS score text")
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid EPSS score") from exc
    if not number.is_finite() or not Decimal("0") <= number <= Decimal("1"):
        raise ValueError("Invalid EPSS score range")
    return float(number)


def score_age_check(day, now):
    try:
        score = date.fromisoformat(day)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid EPSS score date") from exc
    today = now.astimezone(timezone.utc).date()
    if score > today or (today - score).days > 2:
        raise ValueError("Stale/future EPSS score date")
    return score


def parse_epss(path, wanted, now=None, max_file_bytes=MAX_INPUT_BYTES):
    """Read bounded official-format daily CSV/CSV.GZ; return (date, selected scores)."""
    path = Path(path)
    now = now or datetime.now(timezone.utc)
    if path.suffixes[-2:] not in ([".csv", ".gz"],) and path.suffix != ".csv":
        raise ValueError("Only FIRST EPSS .csv or .csv.gz is supported")
    if path.stat().st_size > max_file_bytes:
        raise ValueError("EPSS compressed/source file too large")
    wanted = set(wanted)
    if len(wanted) > 5000 or any(not isinstance(v, str) or not CVE.fullmatch(v) for v in wanted):
        raise ValueError("Invalid requested CVE set")
    opener = gzip.open if path.suffix == ".gz" else open
    scores = {}
    seen = set()
    total_bytes = 0
    with opener(path, "rt", encoding="utf-8", errors="strict", newline="") as stream:
        def safe_line():
            nonlocal total_bytes
            line = stream.readline(MAX_CSV_LINE + 1)
            total_bytes += len(line.encode("utf-8"))
            if total_bytes > MAX_UNCOMPRESSED_BYTES or len(line) > MAX_CSV_LINE:
                raise ValueError("EPSS decoded stream exceeds limits")
            return line
        header = safe_line().strip()
        match = SCORE_HEADER.fullmatch(header)
        if not match:
            raise ValueError("Missing official EPSS model/score date header")
        score_date = match.group(1)
        # FIRST's current daily CSV uses a full UTC score timestamp; earlier
        # samples may contain only YYYY-MM-DD. Retain the calendar day for joins.
        published = header.rsplit("score_date:", 1)[-1]
        if "T" in published:
            released = datetime.fromisoformat(published.replace("Z", "+00:00"))
            if released > now.astimezone(timezone.utc) + timedelta(minutes=5):
                raise ValueError("Future EPSS score timestamp")
        score_age_check(score_date, now)
        columns = next(csv.reader([safe_line()]), [])
        if columns != ["cve", "epss", "percentile"]:
            raise ValueError("Unexpected EPSS CSV columns")
        count = 0
        while True:
            line = safe_line()
            if not line:
                break
            count += 1
            if count > MAX_CSV_ROWS:
                raise ValueError("EPSS row count exceeds limit")
            row = next(csv.reader([line]), [])
            if len(row) != 3 or not CVE.fullmatch(row[0]):
                raise ValueError("Invalid EPSS row or CVE ID")
            cve = row[0]
            if cve in seen:
                raise ValueError("Duplicate EPSS CVE")
            seen.add(cve)
            epss, percentile = score_fraction(row[1]), score_fraction(row[2])
            if cve in wanted:
                scores[cve] = (epss, percentile)
        if not count:
            raise ValueError("Empty EPSS CSV")
    return score_date, scores


def validate_kev(kev, now):
    if not isinstance(kev, dict) or kev.get("schema") != KEV_SCHEMA:
        raise ValueError("Invalid normalized CISA KEV schema")
    if kev.get("source") != KEV_URL:
        raise ValueError("Non-official KEV source")
    if any(kev.get(field) is not False for field in ("deployable", "public_release_allowed", "cti_vendor_connected")):
        raise ValueError("Unsafe KEV release/vendor flag")
    checked = timestamp(kev.get("checked_at_utc"))
    age = (now.astimezone(timezone.utc) - checked).total_seconds() / 3600
    if age < -0.1 or age > MAX_DATA_AGE_HOURS:
        raise ValueError("Stale/future KEV checked time")
    sha = kev.get("source_sha256")
    if not isinstance(sha, str) or not re.fullmatch("[a-f0-9]{64}", sha):
        raise ValueError("Invalid KEV evidence SHA256")
    rows = kev.get("records")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 5000 or kev.get("source_entries") != len(rows):
        raise ValueError("Invalid KEV record count")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != KEV_FIELDS:
            raise ValueError("Unsafe KEV fields")
        cve = row.get("id")
        if not isinstance(cve, str) or not CVE.fullmatch(cve) or cve in ids:
            raise ValueError("Invalid/duplicate KEV CVE")
        ids.add(cve)
        if (row.get("victim_or_outage_confirmed") is not False
                or row.get("public_redistribution_approval") != "REVIEW_REQUIRED"
                or row.get("enterprise_impact") != "NOT_ASSESSED"
                or row.get("tlp") != "CLEAR"
                or row.get("evidence_level") != "OFFICIAL_CISA_KEV"
                or not isinstance(row.get("ransomware_reported"), bool)):
            raise ValueError("Unsafe KEV evidence claim")
        if not isinstance(row.get("vendor"), str) or not isinstance(row.get("product"), str):
            raise ValueError("Invalid KEV vendor/product")
        if len(row["vendor"]) > 180 or len(row["product"]) > 180:
            raise ValueError("Oversized KEV text")
        try:
            added = date.fromisoformat(row["date_added"])
        except (TypeError, ValueError, KeyError) as exc:
            raise ValueError("Invalid KEV added date") from exc
        if added > now.date():
            raise ValueError("Future KEV added date")
    return rows


def analyze(kev, scores, score_date, now=None, limit=20):
    """Produce bounded internal-only CVE priority review; never infer customer impact."""
    now = now or datetime.now(timezone.utc)
    score_age_check(score_date, now)
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be 1..100")
    rows = validate_kev(kev, now)
    if not isinstance(scores, dict) or any(not CVE.fullmatch(cve) or len(values) != 2
                                          or any(not isinstance(v, (float, int)) or v != v or not 0 <= v <= 1 for v in values)
                                          for cve, values in scores.items()):
        raise ValueError("Unsafe EPSS score map")
    sample = []
    for row in rows:
        if row["id"] not in scores:
            continue
        epss, percentile = scores[row["id"]]
        sample.append({"cve": row["id"], "vendor": row["vendor"], "product": row["product"],
                       "date_added": row["date_added"], "epss": epss,
                       "percentile": percentile, "epss_score_date": score_date,
                       "confirmed_customer_impact": False, "product_version_check": "REQUIRED"})
    sample.sort(key=lambda x: (-x["epss"], x["cve"]))
    return {
        "schema": "wmm-cti-offline-epss-review.v1",
        "checked_at_utc": now.isoformat(),
        "kev_checked_at_utc": kev["checked_at_utc"],
        "kev_source": KEV_URL,
        "kev_source_sha256": kev["source_sha256"],
        "epss_source": EPSS_URL,
        "epss_score_date": score_date,
        "source_kev_entries": len(rows),
        "matched_count": len(sample),
        "missing_score_count": len(rows) - len(sample),
        "sample_priorities": sample[:limit],
        "status": "HUMAN_REVIEW_REQUIRED" if sample else "NO_SCORE_AVAILABLE",
        "public_release_allowed": False,
        "darkweb_vendor_connected": False,
        "customer_breaches_confirmed": False,
        "customer_vulnerabilities_confirmed": False,
        "customer_data_processed": False,
        "review_note": "KEV is known exploitation of a CVE; EPSS is global 30-day prediction, not customer compromise or asset impact. Match exact vendor advisories and versions before action.",
    }


def approved_path(path):
    path = Path(path).resolve()
    if {x.lower() for x in path.parts} & {"public", "dist", "data_branch", "site", "cf", "functions", "docs"}:
        raise ValueError("Refuse public/deployment output path")
    if path.exists():
        raise ValueError("Output exists; no overwrite")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kev", required=True, type=Path, help="Existing WMM normalized CISA KEV JSON")
    parser.add_argument("--epss", required=True, type=Path, help="Official FIRST EPSS daily CSV or CSV.GZ on disk")
    parser.add_argument("--out", required=True, type=Path, help="New internal/private JSON only")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.kev.stat().st_size > MAX_KEV_BYTES:
        raise ValueError("KEV input too large")
    kev = json.loads(args.kev.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    records = validate_kev(kev, now)
    score_date, scores = parse_epss(args.epss, {r["id"] for r in records}, now)
    report = analyze(kev, scores, score_date, now, args.limit)
    target = approved_path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"INTERNAL REVIEW ONLY: KEV={report['source_kev_entries']} EPSS matches={report['matched_count']} missing={report['missing_score_count']}. No public release, no customer claims.")


if __name__ == "__main__":
    main()
