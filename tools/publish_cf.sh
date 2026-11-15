#!/bin/bash
# 사이트 업데이트를 Cloudflare(live 브랜치)에만 올림 — Netlify 크레딧 0
set -e
cd /home/claude/site
python3 tools/signals_i18n.py || exit 1
python3 tools/welcome_i18n/build.py || exit 1
python3 tools/alerts_build.py || exit 1
python3 tools/cyber_build.py || exit 1
python3 tools/i18n_build.py || exit 1
python3 tools/hz_i18n.py || exit 1
python3 tools/cf_variant.py dist cf/public
python3 tools/lang_guard.py cf/public
python3 tools/asset_version.py cf/public
cd /home/claude/govradar-live
git fetch -q origin live && git reset -q --soft origin/live
rm -rf public functions && cp -a /home/claude/site/cf/public /home/claude/site/cf/functions .
git add -A
if git diff --cached --quiet; then echo "변경 없음"; exit 0; fi
git commit -qm "${1:-사이트 업데이트}

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NTgYhkF5aJdTG9EAqpbL7Z"
git push -q origin live && git log --oneline -1
