#!/bin/bash
# 회원 전용 자료 암호화 + 운영자 전체 화면 + 작업용 금고(vault)를 GitHub data 브랜치에 올림 (Netlify 크레딧 0)
set -e
cd /home/claude/site
python3 tools/member.py encrypt >/dev/null
python3 tools/owner.py >/dev/null
python3 tools/vault.py pack >/dev/null
cd data_branch && git fetch -q origin data && git rebase -q --autostash origin/data 2>/dev/null || true
git add m feeds
if git diff --cached --quiet; then echo "data 변경 없음"; exit 0; fi
git -c user.name="GOV RADAR bot" -c user.email="73036396@naver.com" commit -qm "Member data, owner snapshot, vault $(date +%F)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NTgYhkF5aJdTG9EAqpbL7Z"
git push -q origin data && echo "data 브랜치 게시 완료"
