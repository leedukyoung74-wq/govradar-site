#!/bin/bash
# 매일 입찰 자동 수집 (AI 없음): 세계은행 공고를 모아 data 브랜치 feeds/tenders.json 으로 게시.
# 사이트 입찰 보드가 이 파일을 매일 불러와 표시한다. Netlify·main 브랜치는 건드리지 않는다.
set -e
G=https://github.com/leedukyoung74-wq/govradar-site
W=${1:-/tmp/feedrun}
rm -rf $W && mkdir -p $W && cd $W
git clone -q --depth 1 -b src $G site
git clone -q --depth 1 -b data $G site/data_branch
cd site && python3 tools/feed_tenders.py
cd data_branch && git add feeds
if git diff --cached --quiet; then echo "변경 없음"; exit 0; fi
git -c user.name="GOV RADAR bot" -c user.email="73036396@naver.com" commit -qm "Tender feed $(date +%F)"
git push -q origin HEAD:data && echo "입찰 자동 수집 게시 완료"
