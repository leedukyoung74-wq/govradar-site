#!/usr/bin/env python3
"""WMM official USGS/NWS/CISA no-cost recovery freshness gate. READ ONLY."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path

UTC=dt.timezone.utc
KST=dt.timezone(dt.timedelta(hours=9))
USGS_LIMIT=35*60
NWS_LIMIT=75*60
CISA_LIMIT=8*3600
FAIL_RETRY=20*60
SKEW=5*60

def utc_stamp(s):
    try:
        if not isinstance(s,str) or not s: return None
        v=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
        return v.astimezone(UTC) if v.tzinfo else None
    except (TypeError,ValueError,OverflowError): return None

def kst_stamp(s):
    try:
        if not isinstance(s,str) or not s: return None
        v=dt.datetime.fromisoformat(s)
        return (v if v.tzinfo else v.replace(tzinfo=KST)).astimezone(UTC)
    except (TypeError,ValueError,OverflowError):return None

def age(stamp,now):
    return (now-stamp).total_seconds() if stamp else None

def due(stamp,now,limit):
    a=age(stamp,now)
    return a is None or a < -SKEW or a >= limit

def load(path):
    try:
        d=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        return d if isinstance(d,dict) else {}
    except (OSError,UnicodeError,TypeError,ValueError):return {}

def needs(data_root,now=None,force=False):
    now=now or dt.datetime.now(UTC)
    if now.tzinfo is None:raise ValueError('timezone-aware timestamp required')
    if force:return {'usgs':True,'nws_cisa':True,'reason':'OWNER_FORCED_OR_MANUAL_DRY_RUN'}
    folder=Path(data_root)/'hz'
    official=load(folder/'official.json')
    usgs=(official.get('sources') or {}).get('usgs') or {}
    fast=kst_stamp(official.get('usgs_fast_checked'))
    if usgs.get('ok') is True:
        usgs_due=due(fast,now,USGS_LIMIT)
    else:
        usgs_due=due(fast,now,FAIL_RETRY)
    def health_due(filename,limit):
        h=load(folder/filename).get('source_health') or {}
        if h.get('ok') is True and h.get('stale') is False:
            return due(utc_stamp(h.get('last_ok')),now,limit)
        return due(utc_stamp(h.get('checked_at')),now,FAIL_RETRY)
    nws_due=health_due('nws_active.json',NWS_LIMIT)
    cisa_due=health_due('cisa_kev.json',CISA_LIMIT)
    return {'usgs':bool(usgs_due),'nws_cisa':bool(nws_due or cisa_due),
            'nws':bool(nws_due),'cisa':bool(cisa_due),
            'usgs_age_minutes':None if fast is None else round(age(fast,now)/60,1),
            'reason':'PUBLIC_SOURCE_FRESHNESS_CHECK'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--force',action='store_true')
    x=p.parse_args()
    r=needs(x.data,force=x.force)
    print(json.dumps(r,ensure_ascii=False))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:
            f.write('usgs='+str(r['usgs']).lower()+'\n')
            f.write('nws_cisa='+str(r['nws_cisa']).lower()+'\n')

if __name__=='__main__':main()
