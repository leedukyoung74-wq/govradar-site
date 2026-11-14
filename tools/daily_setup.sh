#!/bin/bash
# 예약 작업 시작용: 새 세션에서 작업 폴더를 복원한다. 사용: daily_setup.sh <master.key 내용>
set -e
G=https://github.com/leedukyoung74-wq/govradar-site
cd /home/claude
[ -d site/.git ] || git clone -q -b src $G site
[ -d govradar-live/.git ] || git clone -q --depth 1 -b live $G govradar-live
[ -d site/data_branch/.git ] || git clone -q --depth 1 -b data $G site/data_branch
mkdir -p site/private && printf '%s' "$1" > site/private/master.key
cd site && python3 tools/vault.py unpack && ls export/countries | wc -l
