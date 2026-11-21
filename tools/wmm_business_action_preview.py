#!/usr/bin/env python3
"""Read-only, free preview of evidence-gated business review prompts from existing WMM NWS/CISA snapshots.

Inputs: already collected public-source JSON. No HTTP requests, no new data gathering, no user profiles.
Output: stdout JSON only. Do not publish, notify users, auto-patch or infer a business is affected.
This is a triage draft, not legal/medical/emergency response advice or a real-time incident feed.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

UTC = dt.timezone.utc
NWS_SOURCE = "https://api.weather.gov/alerts/active"
CISA_SOURCE = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
NWS_AGE_SECONDS = 180 * 60
CISA_AGE_SECONDS = 600 * 60
MAX_INPUT_BYTES = 2_000_000
MAX_PER_KIND = 12
CVE_RE = re.compile(r"^CVE-[0-9]{4}-[0-9]{4,19}$")
CONTROL = re.compile(r"[\x00-\x1f\x7f<>]")
ACTION_BY_WEATHER = (
    (("tornado", "hurricane", "flash flood", "tsunami"),
     "CHECK_SITE_SAFETY", "현지 공식 대피·안전 지침 및 직원 보호 계획 확인",
     "Check official local safety instructions and the personnel protection plan."),
    (("flood", "storm surge", "coastal flood"),
     "CHECK_ACCESS_LOGISTICS", "사업장 접근·물류 경로와 직원 안전을 공식 정보로 확인",
     "Review site access, logistics routes and worker safety against local official guidance."),
    (("heat", "cold", "winter storm", "blizzard", "ice storm"),
     "CHECK_WORKFORCE", "실외 작업·근무 일정·전력·난방/냉방 대비 점검",
     "Review exposed work, schedules and power/heating/cooling contingencies."),
)


def parse_utc(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        return None
    return result.astimezone(UTC) if result.tzinfo else None


def clean(value, limit=170):
    if not isinstance(value, str):
        return ""
    return CONTROL.sub(" ", value).strip()[:limit]


def is_official_nws_link(url):
    if not isinstance(url, str):
        return False
    try:
        p = urlsplit(url)
        return p.scheme == "https" and p.hostname == "api.weather.gov" and not (
            p.username or p.password or p.port or p.fragment)
    except (ValueError, TypeError):
        return False


def health_status(snapshot, now, max_age_seconds):
    """A saved item cannot be called active when its collector is stale/unknown."""
    h = snapshot.get("source_health")
    if not isinstance(h, dict) or h.get("ok") is not True or h.get("stale") is not False:
        return "SOURCE_UNVERIFIED"
    t = parse_utc(h.get("last_ok"))
    if t is None:
        return "SOURCE_UNVERIFIED"
    age = (now - t).total_seconds()
    if age < -300 or age > max_age_seconds:
        return "SOURCE_STALE"
    return "CURRENT_SNAPSHOT"


def weather_instruction(name):
    event = name.lower()
    for keys, code, ko, en in ACTION_BY_WEATHER:
        if any(key in event for key in keys):
            return code, ko, en
    return ("CHECK_LOCAL_GUIDANCE", "현지 공식 경보를 확인하고 사업장 대응 담당자와 업무 영향 검토",
            "Check local official alerts and ask the business continuity lead to assess impact.")


def weather_cards(snapshot, now):
    if not isinstance(snapshot, dict) or (
        snapshot.get("schema") != "wmm.nws.v1"
        or snapshot.get("kind") != "active_us_weather_alerts"
        or snapshot.get("source_url") != NWS_SOURCE
        or snapshot.get("coverage") != "United States only"
        or snapshot.get("not_global_all_clear") is not True
        or not isinstance(snapshot.get("items"), list)
    ):
        return {"source": "NWS", "state": "INVALID_SOURCE", "cards": [], "scope": "US only"}
    status = health_status(snapshot, now, NWS_AGE_SECONDS)
    if status != "CURRENT_SNAPSHOT":
        return {"source": "NWS", "state": status, "cards": [], "scope": "US only",
                "verification_url": NWS_SOURCE}
    cards, seen = [], set()
    for row in snapshot["items"][:250]:
        if not isinstance(row, dict) or row.get("src") != "NWS":
            continue
        if row.get("severity") not in {"Extreme", "Severe"}:
            continue
        expires = parse_utc(row.get("ends_at"))
        issued = parse_utc(row.get("issued_at"))
        if expires is None or expires <= now:
            continue
        if issued is None or issued > now + dt.timedelta(minutes=5):
            continue
        title, area = clean(row.get("title")), clean(row.get("area"))
        if not title or not area:
            continue
        url = row.get("url")
        url = url if is_official_nws_link(url) else NWS_SOURCE
        event = clean(row.get("event"), 100)
        key = (url, title, area)
        if key in seen:
            continue
        seen.add(key)
        action, ko, en = weather_instruction(event)
        cards.append({
            "kind": "WEATHER_LOCAL_REVIEW", "iso": "US", "region_text": area,
            "event": event, "title": title, "severity": row["severity"],
            "ends_at": row["ends_at"], "urgency": clean(row.get("urgency"), 24),
            "certainty": clean(row.get("certainty"), 24),
            "source_url": url, "action_code": action,
            "action_ko": ko, "action_en": en,
            "priority": "REVIEW_PROMPT" if row["severity"] == "Severe" else "URGENT_HUMAN_REVIEW",
            "client_impact_confirmed": False, "customer_geolocation_matched": False,
            "notification_allowed": False,
        })
        if len(cards) >= MAX_PER_KIND:
            break
    state = "PARTIAL_COVERAGE" if snapshot.get("partial_coverage") is True else "CURRENT_SNAPSHOT"
    return {"source": "NWS", "state": state, "scope": "US only", "cards": cards,
            "verification_url": NWS_SOURCE,
            "zero_cards_not_all_clear": True}


def kev_cards(snapshot, now):
    if not isinstance(snapshot, dict) or (
        snapshot.get("schema") != "wmm.cisa.kev.v1"
        or snapshot.get("kind") != "known_exploited_vulnerabilities"
        or snapshot.get("source_url") != CISA_SOURCE
        or snapshot.get("not_realtime_attack_feed") is not True
        or not isinstance(snapshot.get("items"), list)
        or not isinstance(snapshot.get("total_vulnerabilities"), int)
        or snapshot["total_vulnerabilities"] < 1000
    ):
        return {"source": "CISA_KEV", "state": "INVALID_SOURCE", "cards": []}
    status = health_status(snapshot, now, CISA_AGE_SECONDS)
    if status != "CURRENT_SNAPSHOT":
        return {"source": "CISA_KEV", "state": status, "cards": [],
                "verification_url": CISA_SOURCE}
    cards, seen = [], set()
    for row in snapshot["items"][:250]:
        if not isinstance(row, dict):
            continue
        cve = row.get("cve")
        if not isinstance(cve, str) or not CVE_RE.fullmatch(cve) or cve in seen:
            continue
        vendor, product = clean(row.get("vendor"), 80), clean(row.get("product"), 80)
        if not vendor or not product:
            continue
        try:
            added = dt.date.fromisoformat(row.get("date_added", ""))
        except (ValueError, TypeError):
            continue
        if not 0 <= (now.date() - added).days <= 45:
            continue
        seen.add(cve)
        cards.append({
            "kind": "VULNERABILITY_ASSET_REVIEW", "iso": None, "cve": cve,
            "vendor": vendor, "product": product, "date_added": str(added),
            "source_url": CISA_SOURCE, "action_code": "CHECK_ASSET_INVENTORY",
            "action_ko": "해당 제품 사용 여부 확인 → 제조사 권고·보완조치 검토 → 내부 변경관리로 우선순위 결정",
            "action_en": "Check asset inventory, review vendor guidance/mitigations and prioritize through change control.",
            "priority": "REVIEW_PROMPT", "business_affected_confirmed": False,
            "customer_uses_product_confirmed": False, "attack_confirmed": False,
            "due_date_is_universal_business_deadline": False,
            "notification_allowed": False,
        })
        if len(cards) >= MAX_PER_KIND:
            break
    return {"source": "CISA_KEV", "state": "CURRENT_SNAPSHOT", "cards": cards,
            "verification_url": CISA_SOURCE, "zero_cards_not_no_vulnerabilities": True}


def build_preview(nws=None, kev=None, now=None):
    now = now or dt.datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("timezone_aware_now_required")
    now = now.astimezone(UTC)
    modules = [weather_cards(nws, now) if nws is not None
               else {"source": "NWS", "state": "INPUT_NOT_PROVIDED", "cards": []},
               kev_cards(kev, now) if kev is not None
               else {"source": "CISA_KEV", "state": "INPUT_NOT_PROVIDED", "cards": []}]
    return {
        "schema": "wmm.business-action.review.v1",
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "INTERNAL_PREVIEW_ONLY",
        "customer_matching_performed": False,
        "customer_notifications_sent": False,
        "site_published": False,
        "paid_api_used": False,
        "disclaimer_ko": "공식 정보 기반 사전 점검 제안입니다. 특정 기업 피해·공격·규제 의무·대피 지시를 확인한 것이 아닙니다.",
        "cisa_due_note_ko": "CISA KEV 조치 기한은 미국 연방 민간행정기관에 적용되는 의무를 포함하며 모든 민간기업에 동일하게 적용되는 법적 기한이 아닙니다.",
        "source_modules": modules,
    }


def load_snapshot(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("snapshot_missing_or_too_large")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nws", type=Path, help="Existing public NWS snapshot (local file only)")
    ap.add_argument("--cisa", type=Path, help="Existing public CISA KEV snapshot (local file only)")
    ap.add_argument("--at", help="Optional ISO8601 UTC timestamp for deterministic review")
    args = ap.parse_args()
    if args.nws is None and args.cisa is None:
        ap.error("provide at least one existing local snapshot")
    at = parse_utc(args.at) if args.at else dt.datetime.now(UTC)
    if at is None:
        ap.error("--at must be timezone-aware ISO8601")
    preview = build_preview(load_snapshot(args.nws) if args.nws else None,
                            load_snapshot(args.cisa) if args.cisa else None, at)
    print(json.dumps(preview, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
