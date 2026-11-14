#!/bin/bash
# 매일 자동 수집 (AI 없음): 세계은행 공고 → feeds/tenders.json, 공식 상황(USGS·GDACS·NASA·WHO·NOAA) → hz/official.json
# 사이트 입찰 보드가 이 파일을 매일 불러와 표시한다. Netlify·main 브랜치는 건드리지 않는다.
set -e
G=https://github.com/leedukyoung74-wq/govradar-site
W=${1:-/tmp/feedrun}
rm -rf $W && mkdir -p $W && cd $W
git clone -q --depth 1 -b src $G site
git clone -q --depth 1 -b data $G site/data_branch
cd site && python3 tools/feed_tenders.py
python3 tools/feed_official.py || echo "공식 상황 수집 일부 실패(이전 자료 유지)"
cd data_branch && git add feeds hz/official.json
if git diff --cached --quiet; then echo "변경 없음"; exit 0; fi
git -c user.name="GOV RADAR bot" -c user.email="73036396@naver.com" commit -qm "Tender + official situation feed $(date +%F)"
git push -q origin HEAD:data && echo "입찰 자동 수집 게시 완료"
