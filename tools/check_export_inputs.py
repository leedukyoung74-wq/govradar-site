#!/usr/bin/env python3
"""Opt-in, local read-only input gate for GOV RADAR static builds.

Run BEFORE publishing: python tools/check_export_inputs.py --min-countries 20 --max-age-days 7
Thresholds are policy inputs, not evidence of complete country coverage.
No data is edited. A failure means HOLD, not delete or auto-publish.
"""
import argparse
import datetime as dt
import json
from pathlib import Path


def _date(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        # Country exporters usually use YYYY-MM-DD, some use ISO timestamps.
        text = value.strip()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return dt.date.fromisoformat(text[:10])
    except ValueError:
        pass
    return None


def audit_inputs(export_dir, *, min_countries=20, max_age_days=7, today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    files = sorted(Path(export_dir).glob("*.json"))
    usable = set()
    missing_date, stale, malformed, duplicate, future = [], [], [], [], []
    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(doc, dict):
                raise ValueError("export document must be an object")
            iso = doc.get("id") or path.stem[:2]
            if not isinstance(iso, str) or len(iso) != 2 or not iso.isupper() or not iso.isalpha():
                raise ValueError("expected two-letter ISO country id")
            payload = doc.get("data", doc)
            if not isinstance(payload, dict):
                raise ValueError("data must be an object")
            if iso in usable:
                duplicate.append(path.name)
            usable.add(iso)
            stamp = _date(payload.get("updated") or payload.get("asof") or doc.get("updated"))
            if stamp is None:
                missing_date.append(path.name)
            elif stamp > today:
                future.append(path.name)
            elif (today - stamp).days > max_age_days:
                stale.append(path.name)
        except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            malformed.append({"file": path.name, "reason": str(exc)[:160]})
    errors = []
    if len(usable) < min_countries:
        errors.append("INSUFFICIENT_COUNTRY_EXPORTS")
    if missing_date or stale or future:
        errors.append("UNVERIFIED_OR_STALE_EXPORT_DATES")
    if malformed or duplicate:
        errors.append("INVALID_OR_DUPLICATE_EXPORTS")
    return {
        "classification": "LOCAL_INPUT_FRESHNESS_GATE_ONLY",
        "passed": not errors,
        "countries": len(usable),
        "minCountries": min_countries,
        "maxAgeDays": max_age_days,
        "inputFiles": len(files),
        "missingDate": missing_date,
        "stale": stale,
        "futureDated": future,
        "malformed": malformed,
        "duplicate": duplicate,
        "errors": errors,
        "warning": "Input file dates and presence are not official source verification or live deadline confirmation.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-dir", default="export/countries")
    parser.add_argument("--min-countries", type=int, default=20)
    parser.add_argument("--max-age-days", type=int, default=7)
    parser.add_argument("--today", help="fixed UTC YYYY-MM-DD for test/reproducibility")
    options = parser.parse_args()
    if options.min_countries < 1 or options.max_age_days < 0:
        parser.error("invalid thresholds")
    try:
        day = dt.date.fromisoformat(options.today) if options.today else None
    except ValueError:
        parser.error("--today requires valid YYYY-MM-DD")
    report = audit_inputs(options.export_dir, min_countries=options.min_countries,
                          max_age_days=options.max_age_days, today=day)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
