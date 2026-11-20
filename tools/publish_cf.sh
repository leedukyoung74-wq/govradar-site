#!/bin/bash
# 사이트 업데이트를 Cloudflare(live 브랜치)에만 올림 — Netlify 크레딧 0
set -e
cd /home/claude/site
# Guard (2026-11-17): never publish with country data older than the newest saved vault — a manual publish
# from a stale working folder rolled back the daily country refresh once. Fix: python3 tools/vault.py unpack
if [ -f data_branch/m/vault.json ] && git -C data_branch fetch -q origin data 2>/dev/null; then
  R=$(git -C data_branch show origin/data:m/vault.json 2>/dev/null | sha256sum | cut -d' ' -f1)
  if [ -n "$R" ] && [ "$R" != "$(cat private/.vault_sha 2>/dev/null)" ]; then
    echo "STOP: newer saved data exists (data branch m/vault.json). Run: git -C data_branch pull -q origin data && python3 tools/vault.py unpack, then rebuild."; exit 1; fi
fi
# Opt-in P0 release gate (disabled by default until export dates/coverage are approved).
# Set WMM_EXPORT_PREFLIGHT=required only after confirming actual collector schema and policy.
# This must run before any live-branch git operations or rendered-site writes.
case "${WMM_EXPORT_PREFLIGHT:-off}" in
  off)
    echo "INFO: export freshness preflight is OFF; live publication is NOT protected by this optional gate."
    ;;
  required)
    echo "INFO: validating local exported countries before publish"
    python3 tools/check_research_coverage.py --export-dir export/countries --metadata src/countries_meta.json --min-researched "${WMM_EXPORT_MIN_RESEARCHED:-1}" || { echo "STOP: no valid researched country coverage; nothing published."; exit 1; }
    python3 tools/check_export_inputs.py \
      --export-dir export/countries \
      --min-countries "${WMM_EXPORT_MIN_COUNTRIES:-20}" \
      --max-age-days "${WMM_EXPORT_MAX_AGE_DAYS:-7}" || {
        echo "STOP: country export freshness preflight failed; nothing published."
        exit 1
      }
    ;;
  *)
    echo "STOP: WMM_EXPORT_PREFLIGHT must be 'off' or 'required'."
    exit 1
    ;;
esac
python3 tools/signals_i18n.py || exit 1
python3 tools/orgs.py || exit 1   # one 'three entities' block for welcome + main
python3 tools/welcome_i18n/build.py || exit 1
python3 tools/alerts_build.py || exit 1
python3 tools/cyber_build.py || exit 1
python3 tools/i18n_build.py || exit 1
python3 tools/hz_i18n.py || exit 1
python3 tools/text_wrap.py || exit 1   # Korean line breaking on every page (after the page generators)
python3 tools/cf_variant.py dist cf/public
python3 tools/lang_guard.py cf/public
python3 tools/asset_version.py cf/public
# When explicitly enabled, the finished staging output must match the exported country source.
# Keep this after all overlays and before touching the live repository.
if [ "${WMM_EXPORT_PREFLIGHT:-off}" = "required" ]; then
  python3 tools/check_build_consistency.py --export-dir export/countries --public-dir cf/public --min-researched "${WMM_EXPORT_MIN_RESEARCHED:-1}" || {
    echo "STOP: generated pages do not match export data; nothing published."
    exit 1
  }
fi
# Mandatory release-output sanity check, even if optional country freshness gate is off.
python3 tools/check_public_fixture_leak.py cf/public || { echo "STOP: invalid or synthetic public assets; live branch unchanged."; exit 1; }
cd /home/claude/govradar-live
git fetch -q origin live && git reset -q --soft origin/live
rm -rf public functions && cp -a /home/claude/site/cf/public /home/claude/site/cf/functions .
git add -A
if git diff --cached --quiet; then echo "변경 없음"; exit 0; fi
git commit -qm "${1:-사이트 업데이트}

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NTgYhkF5aJdTG9EAqpbL7Z"
git push -q origin live && git log --oneline -1
