#!/usr/bin/env python3
"""Create a review-only delta bundle from canonical generated dist. NOT a website deploy.
No network operations, no secrets, no changes to main/data/hosting.
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUT = ROOT / "release-review"
LANGS = ("ko", "en", "es", "fr", "ar", "vi", "id")
files = [
    "quality/index.html", "review/index.html",
    "assets/review-status.js", "assets/wmm-resilience.js", "assets/wmm-resilience.css",
    "data/wmm-food-country-profiles.json",
    "data/wmm-food-primary-guidance-reviewed.json",
]
for lang in LANGS:
    files += [f"{lang}/prepare/index.html", f"{lang}/resilience/index.html"]

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
entries = []
for rel in files:
    source = DIST / rel
    if not source.is_file():
        raise RuntimeError(f"Missing generated artifact {rel}")
    content = source.read_bytes()
    if rel.endswith("/resilience/index.html"):
        text = content.decode("utf-8")
        assert "noindex, nofollow" in text, rel
        assert f'href="/{rel.split("/")[0]}/prepare/"' in text, rel
    if rel.endswith("/prepare/index.html"):
        text = content.decode("utf-8")
        assert "106.4L" in text and "84L" not in text, rel
    if rel in ("quality/index.html", "review/index.html"):
        assert "noindex,nofollow" in content.decode("utf-8"), rel
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    entries.append({
        "path": rel,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
    })

food = json.loads((OUT/"data/wmm-food-country-profiles.json").read_text(encoding="utf-8"))
guidance = json.loads((OUT/"data/wmm-food-primary-guidance-reviewed.json").read_text(encoding="utf-8"))
assert len(food) == 193
assert {x["iso"] for x in guidance["countries"]} == {"KR", "JP", "US"}
assert all(
    not p["local_official_guidance_verified"]
    and not p["retail_availability_verified"]
    and not p["shelf_life_verified"]
    for p in food
)
manifest = {
    "artifact_type": "WMM_GOV_RADAR_PARTIAL_REVIEW_ONLY",
    "safe_to_deploy_as_full_site": False,
    "does_not_publish": True,
    "does_not_certify_country_products": True,
    "languages": list(LANGS),
    "country_profile_count": len(food),
    "official_general_guidance_countries": ["KR", "JP", "US"],
    "verified_product_count": 0,
    "files": entries,
}
(OUT/"manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8"
)
(OUT/"READ_ME_FIRST.txt").write_text(
    "WMM GOV RADAR review-only delta package.\n"
    "This is NOT the complete site and MUST NOT be uploaded as a site root.\n"
    "Do not publish until the actual hosting project, production branch,"
    " release approval, rollback process, source and translation review are confirmed.\n"
    "The source of truth is src/build.py. Regenerate the complete dist/ for any release.\n"
    "This archive is read-only evidence, not an automated deployment.\n",
    encoding="utf-8"
)
print(f"PASS: review-only release evidence prepared: {len(entries)} files")
