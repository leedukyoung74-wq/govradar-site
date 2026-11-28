#!/usr/bin/env python3
"""WMM seven-language public home real-browser, mobile + RTL, NO CUSTOMER POST.

Explicit user-approved public read-only browser smoke. No browser cookies,
authentication, payment clicks, form submits, DNS or deployment.
Screenshots remain short-retention private workflow artifacts.
"""
import asyncio
import json
import os
from pathlib import Path

HOST = "https://radar.wmm-hoa.com"
LOCALES = ("ko", "en", "es", "fr", "ar", "vi", "id")
SIZES = ((390, 844), (1366, 768))
CAPTURES = Path("qa-artifacts")
COPY_MARKERS = {
    "ko": "조사·제안 아이디어 · 실시간 입찰 아님",
    "en": "Curated research ideas · not live tenders",
}


def classify(label, code, lang, direction, viewport, h1, main_count,
             overflow_px, denied_posts, copy_present=None):
    failures = []
    if code != 200:
        failures.append("HTML_NOT_HTTP_200")
    if lang != label:
        failures.append("WRONG_HTML_LANG")
    if direction != ("rtl" if label == "ar" else "ltr"):
        failures.append("WRONG_DOCUMENT_DIRECTION")
    if not viewport:
        failures.append("MISSING_VIEWPORT_META")
    if not h1 or main_count == 0:
        failures.append("MAIN_HEADING_NOT_VISIBLE")
    if overflow_px > 20:
        failures.append("MOBILE_HORIZONTAL_OVERFLOW")
    if denied_posts:
        failures.append("BACKGROUND_POST_BLOCKED")
    missing_copy = label in COPY_MARKERS and copy_present is False
    return {
        "status": "FAIL" if failures else "PASS",
        "failures": failures,
        "copy_review": "PENDING_NOT_DEPLOYED" if missing_copy else
                       "VISIBLE" if label in COPY_MARKERS else "NOT_APPLICABLE",
    }


async def run():
    # The import happens inside the real-browser function so synthetic policy
    # regression tests work without installing/launching Chromium.
    from playwright.async_api import async_playwright
    CAPTURES.mkdir(exist_ok=True)
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for lang in LOCALES:
            for width, height in ((SIZES[0],) if lang not in ("ko", "en") else SIZES):
                label = lang + ("-mobile" if width < 500 else "-desktop")
                ctx = await browser.new_context(
                    viewport={"width": width, "height": height},
                    device_scale_factor=1,
                    service_workers="block",
                    ignore_https_errors=False)
                blocked = []
                async def no_non_get(route):
                    if route.request.method.upper() != "GET":
                        blocked.append("BLOCKED_NON_GET")
                        await route.abort()
                    else:
                        await route.continue_()
                await ctx.route("**/*", no_non_get)
                page = await ctx.new_page()
                item = {"locale": lang, "viewport": label,
                        "http": None, "status": "FAIL",
                        "source_copy_deployed": None,
                        "customer_posts_allowed": 0}
                try:
                    res = await page.goto(
                        HOST + "/" + lang + "/?stay=1",
                        wait_until="domcontentloaded", timeout=38000)
                    await page.locator("main h1").first.wait_for(
                        state="visible", timeout=16000)
                    details = await page.evaluate("""() => ({
                        lang: document.documentElement.lang,
                        dir: getComputedStyle(document.documentElement).direction,
                        viewport: !!document.querySelector('meta[name="viewport"]'),
                        h1: !!document.querySelector('main h1')?.getClientRects().length,
                        mains: document.querySelectorAll('main').length,
                        overflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
                        body: document.body?.innerText?.slice(0, 35000) || ''
                    })""")
                    marker = COPY_MARKERS.get(lang)
                    copied = None if marker is None else marker in details["body"]
                    review = classify(
                        lang, res.status if res else None,
                        details["lang"], details["dir"], details["viewport"],
                        details["h1"], details["mains"], details["overflow"],
                        bool(blocked), copied)
                    item.update({
                        "http": res.status if res else None,
                        "status": review["status"],
                        "failures": review["failures"],
                        "copy_review": review["copy_review"],
                        "overflow_pixels": details["overflow"],
                        "source_copy_deployed": copied,
                    })
                    # No cookies, customer values or keys are captured in logs.
                    if item["status"] == "PASS":
                        await page.screenshot(
                            path=str(CAPTURES / (label + ".png")),
                            full_page=False)
                except Exception as exc:
                    item["failures"] = ["BROWSER_" + type(exc).__name__]
                finally:
                    results.append(item)
                    await ctx.close()
        await browser.close()
    failures = [x["viewport"] for x in results if x["status"] != "PASS"]
    pending_copy = [x["viewport"] for x in results
                    if x.get("copy_review") == "PENDING_NOT_DEPLOYED"]
    report = {
        "scope": "PUBLIC_SEVEN_LANGUAGE_REAL_CHROMIUM_READONLY",
        "result": "FAIL" if failures else
                  "PENDING_COPY_NOT_DEPLOYED" if pending_copy else "PASS",
        "locale_checks": len(results),
        "failed_viewports": failures,
        "reviewed_copy_not_deployed": pending_copy,
        "checks": results,
        "post_requests_allowed": 0,
        "signed_in_roles_verified": False,
        "paid_checkout_verified": False,
        "source_freshness_verified": False,
        "production_deployment_performed": False,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as fp:
            fp.write("\n## Seven-language real mobile/desktop browser QA: " +
                     report["result"] + "\n\n")
            fp.write("| Locale viewport | Browser | Copy state | Overflow px |\n|---|---|---|---:|\n")
            for item in results:
                fp.write("| " + item["viewport"] + " | " +
                         item["status"] + " | " +
                         str(item.get("copy_review", "-")) + " | " +
                         str(item.get("overflow_pixels", "-")) + " |\n")
            fp.write("\nNo customer POST, login, paid checkout or production deployment. "
                     "A passed public-browser check is not authenticated E2E.\n")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
