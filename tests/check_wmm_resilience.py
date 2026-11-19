#!/usr/bin/env python3
"""Read-only contract tests for WMM resilience review branch (no network required)."""
from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parents[1]
countries = json.loads((ROOT / "data/countries.json").read_text(encoding="utf-8"))
foods = json.loads((ROOT / "data/wmm-food-country-profiles.json").read_text(encoding="utf-8"))
assert len(countries) == 193, f"Expected 193 country records, got {len(countries)}"
assert len(foods) == 193, f"Expected 193 food profiles, got {len(foods)}"
ids = {c["iso"] for c in countries}
profiles = {f["iso"] for f in foods}
assert ids == profiles and len(ids) == 193, "Country food index must match country master exactly"
assert len({c["slug"] for c in countries}) == 193, "Country slugs must be unique"
for f in foods:
    assert f["status"] in ("pending","illustrative"), f
    assert f["local_official_guidance_verified"] is False, "No false official verification"
    assert f["retail_availability_verified"] is False, "No false retail availability"
    assert f["shelf_life_verified"] is False, "No unsupported shelf-life claims"
    assert len(f["examples"]) <= 8
for language in ("ko","en","es","fr","ar","vi","id"):
    content = (ROOT / language / "resilience/index.html").read_text(encoding="utf-8")
    assert f'<html lang="{language}"' in content
    assert "wmm-resilience.js" in content
    assert "wmm-resilience.css" in content
    assert "/ready/" in content or "/prepare/" in content
    assert 'noindex, nofollow' in content, "Review pages should not be indexed before approval"
js = (ROOT / "assets/wmm-resilience.js").read_text(encoding="utf-8")
css = (ROOT / "assets/wmm-resilience.css").read_text(encoding="utf-8")
assert 'fetch("/data/countries.json")' in js
assert "/data/wmm-food-country-profiles.json" in js
assert "localStorage" in js
assert "does not" in js.lower() or "never" in js.lower()
assert "grid-template-columns" in css and "@media" in css
assert "<h1>'+e(t.title)+'</h1>" in js, "Rendered page must retain a main H1"
assert "class=\\\"rs-result\\\" id=\\\"rs-out\\\" role=\\\"status\\\"" in js
assert "class=\\\"rs-result\\\" id=\\\"rs-pout\\\" role=\\\"status\\\"" in js
assert '.wmm-rs[dir=rtl] .rs-alert' in css, "RTL styles must target root direction"
assert 'x.toLocaleString(L,' in js, "Numbers should follow selected language"
assert not re.search(r'\bfetch\s*\([^)]*,\s*\{\s*method\s*:\s*["\']POST', js, re.I), "No POST of personal data"
print("PASS: 193 unique country profiles, status gates, seven locales, safe static references")
