#!/bin/bash
# 사용: batch_go.sh c1  → 조사 반영 + 5개 언어 번역 + 빌드 + Cloudflare 게시
set -e
S=${SCRATCH:-/tmp/claude-0/-home-claude/8e1d9b9d-af77-5edb-96a7-c9e24190a4ed/scratchpad}
cd /home/claude/site
python3 tools/country_import.py $S/$1.json
python3 - "$S/${1}_tr.json" <<'PY'
import json,sys,subprocess,tempfile,os
t=json.load(open(sys.argv[1],encoding='utf-8'))
for L,v in t.items():
    p=tempfile.mktemp(suffix='.json'); json.dump(v,open(p,'w',encoding='utf-8'),ensure_ascii=False)
    subprocess.run(['python3','tools/tr_import.py',L,p],check=True,capture_output=True); os.remove(p)
print('tr', ','.join(t), sum(len(v) for v in t.values()))
PY
python3 build.py 2>&1 | tail -1
tools/publish_cf.sh "${2:-국가 조사 추가}" 2>&1 | tail -1
/home/claude/site/tools/publish_owner.sh
