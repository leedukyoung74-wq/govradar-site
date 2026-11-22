#!/usr/bin/env python3
"""P0 seven-language /prepare/ release guard, comparing exact live snapshot with a draft.

No login, secrets, deploy, remote writes or customer messages. A live HTTP probe is
optional, read-only, and reports drift separately from whether draft code is correct.
"""
import argparse
import concurrent.futures
import datetime as dt
import json
import urllib.error
import urllib.request
from pathlib import Path

LANGS = ("ko", "en", "es", "fr", "ar", "vi", "id")
HOSTS = ("https://radar.wmm-hoa.com", "https://wmm-radar.pages.dev")
COPY = {
    "ko": ("휴대용 버너와 연료 (실내 사용 시 환기)",
           "캠핑용 버너는 실외에서만 사용하세요. 실내·차고·텐트에서는 환기하더라도 사용하지 마세요."),
    "en": ("Camping stove and fuel (ventilate indoors)",
           "Camping fuel stoves: outdoors only, never indoors, in garages or tents, even with ventilation."),
    "es": ("Hornillo de camping y combustible (ventile en interiores)",
           "Hornillos de camping: solo al aire libre, nunca en casa, garaje ni tienda, aunque haya ventilación."),
    "fr": ("Réchaud de camping et combustible (aérer en intérieur)",
           "Réchaud de camping : uniquement dehors, jamais dans une habitation, un garage ou une tente, même ventilés."),
    "ar": ("موقد تخييم ووقود (مع التهوية داخل المباني)",
           "مواقد التخييم للاستخدام في الخارج فقط، وليس داخل المنازل أو المرائب أو الخيام حتى مع التهوية."),
    "vi": ("Bếp cắm trại và nhiên liệu (thông gió khi dùng trong nhà)",
           "Bếp cắm trại chỉ dùng ngoài trời; không dùng trong nhà, ga-ra hoặc lều kể cả khi có thông gió."),
    "id": ("Kompor kemah dan bahan bakar (pastikan ventilasi jika di dalam ruangan)",
           "Kompor camping hanya digunakan di luar ruangan; jangan gunakan di dalam rumah, garasi atau tenda meski ada ventilasi."),
}
MAX_BYTES = 1_500_000


def release_source_checks(baseline, patch):
    """Byte-exact diff: each locale changes its one old blackout panel item, nothing else."""
    checks = []
    for lang in LANGS:
        path = Path("public") / lang / "prepare" / "index.html"
        row = {"lang": lang, "relative_path": path.as_posix(), "checks": {}}
        old, new = COPY[lang]
        try:
            before = (Path(baseline) / path).read_text(encoding="utf-8")
            after = (Path(patch) / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as e:
            row["error_type"] = type(e).__name__
            row["pass"] = False
            checks.append(row)
            continue
        src, dst = "<li>" + old + "</li>", "<li>" + new + "</li>"
        row["checks"] = {
            "original_exactly_one_old_item": before.count(src) == 1,
            "candidate_no_old_item": old not in after,
            "candidate_one_safe_item": after.count(dst) == 1,
            "only_one_list_item_modified": before.replace(src, dst, 1) == after,
            "new_water_amount_preserved": "106.4" in before and "106.4" in after,
            "obsolete_84l_not_reintroduced": "84L" not in after,
            "no_script_or_stylesheet_change": before.count("<script") == after.count("<script")
            and before.count("<link") == after.count("<link"),
        }
        row["pass"] = all(row["checks"].values())
        checks.append(row)
    return checks


def http_probe_one(host, lang, opener=None):
    old, new = COPY[lang]
    url = host + "/" + lang + "/prepare/"
    result = {"url": url, "lang": lang, "host": host, "release_state": "UNKNOWN",
              "http_status": None, "error_type": None, "new_water_present": False,
              "unsafe_copy_present": None, "safe_copy_present": None}
    req = urllib.request.Request(url, headers={
        "User-Agent": "WMM-GOV-RADAR-SafeCopy-ReadOnly/1.0",
        "Cache-Control": "no-cache",
    }, method="GET")
    try:
        if opener is None:
            opener = urllib.request.urlopen
        with opener(req, timeout=12) as resp:
            # Fail visibly on upstream redirects; do not treat arbitrary content as official site.
            target = resp.geturl()
            if target != url:
                result["error_type"] = "UNEXPECTED_REDIRECT"
                result["release_state"] = "UNVERIFIED"
                return result
            result["http_status"] = getattr(resp, "status", None)
            raw = resp.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            result["error_type"] = "CONTENT_TOO_LARGE"
            result["release_state"] = "UNVERIFIED"
            return result
        body = raw.decode("utf-8", "replace")
        result["new_water_present"] = "106.4" in body
        result["unsafe_copy_present"] = old in body
        result["safe_copy_present"] = new in body
        if result["http_status"] == 200 and result["new_water_present"] and result["safe_copy_present"] and not result["unsafe_copy_present"] and "84L" not in body:
            result["release_state"] = "SAFE_PATCH_VISIBLE"
        elif result["http_status"] == 200 and result["unsafe_copy_present"]:
            result["release_state"] = "OLD_UNSAFE_COPY_VISIBLE"
        else:
            result["release_state"] = "VERSION_MISMATCH"
    except urllib.error.HTTPError as e:
        result["http_status"] = e.code
        result["error_type"] = "HTTP_ERROR"
        result["release_state"] = "UNREACHABLE_OR_RESTRICTED"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, UnicodeError) as e:
        result["error_type"] = type(e).__name__
        result["release_state"] = "UNREACHABLE_OR_RESTRICTED"
    return result


def run(baseline, patch, probe_live=False):
    source = release_source_checks(baseline, patch)
    probes = []
    if probe_live and all(x["pass"] for x in source):
        # 14 short, bounded, GET-only probes of two known hostnames.
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
            futures = [pool.submit(http_probe_one, host, lang)
                       for host in HOSTS for lang in LANGS]
            probes = [f.result() for f in futures]
    count = sum(x["release_state"] == "SAFE_PATCH_VISIBLE" for x in probes)
    result = {
        "schema": "wmm.prepbar.safe-release-gate.v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "READ_ONLY_REVIEW", "site_modified": False,
        "customer_messages_sent": False, "paid_api_used": False,
        "release_patch_source_ok": len(source) == 7 and all(x["pass"] for x in source),
        "source_checks": source,
        "live_probes_attempted": probe_live,
        "public_checks": probes,
        "public_patch_visible_count": count,
        "public_patch_visible_total": len(probes),
        "release_production_confirmed": probe_live and len(probes) == 14 and count == 14,
        "readiness": "PREVIEW_REQUIRED" if not probe_live else
                     ("PUBLIC_PATCH_VISIBLE" if count == 14 else "BLOCKED_PUBLIC_DRIFT"),
        "notes": [
            "All host probes are GET-only, fixed hosts and 7 paths; no authentication.",
            "Source code comparison is independent of current public deployment.",
            "Passing this gate does not prove Cloudflare preview, mobile, RTL, login or payment safety.",
            "A source check failure is a code review failure; a public version mismatch is a deployment-version finding.",
        ]
    }
    return result


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", required=True, type=Path)
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--probe-live", action="store_true")
    p.add_argument("--out", type=Path)
    args = p.parse_args(argv)
    result = run(args.baseline, args.candidate, args.probe_live)
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized + "\n", encoding="utf-8")
    print(json.dumps({
        "release_patch_source_ok": result["release_patch_source_ok"],
        "source_verified_languages": sum(x["pass"] for x in result["source_checks"]),
        "public_patch_visible": str(result["public_patch_visible_count"]) + "/" + str(result["public_patch_visible_total"]),
        "readiness": result["readiness"], "site_modified": False,
    }, ensure_ascii=False))
    return 0 if result["release_patch_source_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
