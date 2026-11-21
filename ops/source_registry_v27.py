#!/usr/bin/env python3
"""WMM GOV RADAR: read-only 193-country / source provenance review gate.
No network requests, publishing, status updates, or paid APIs. Python stdlib only.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date
import ipaddress
import json
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED = {'government': 3, 'news': 3, 'environment': 1, 'weather': 1, 'emergency': 1}


def source_url_good(value):
    if not isinstance(value, str) or len(value) > 2048 or any(ord(x) < 32 for x in value):
        return False
    try:
        p = urlsplit(value)
        if p.scheme != 'https' or not p.hostname or p.username or p.password or p.fragment:
            return False
        if p.port not in (None, 443):
            return False
        try:
            ipaddress.ip_address(p.hostname)
            return False
        except ValueError:
            return '.' in p.hostname and not p.hostname.endswith('.')
    except (ValueError, TypeError):
        return False


def parse_date(s):
    try:
        if not isinstance(s, str) or len(s) != 10: return None
        day = date.fromisoformat(s)
        return day if day.isoformat() == s else None
    except ValueError:
        return None


def review_ok(row, as_of):
    review = row.get('verification')
    if not isinstance(review, dict) or row.get('status') != 'HUMAN_REVIEWED':
        return False
    day = parse_date(review.get('reviewed_at'))
    return bool(
        source_url_good(row.get('url')) and day and 0 <= (as_of - day).days <= 60
        and isinstance(review.get('reviewer'), str) and len(review['reviewer'].strip()) >= 3
        and all(review.get(k) is True for k in ('institution_ownership_confirmed', 'link_reachable', 'category_role_confirmed', 'editor_approved'))
        and source_url_good(review.get('evidence_url'))
    )


def analyze(root, source_doc, as_of):
    root = Path(root)
    if isinstance(as_of, str): as_of = parse_date(as_of)
    if not as_of: raise ValueError('as_of must be an ISO calendar date')
    countries = json.loads((root / 'data/countries.json').read_text(encoding='utf-8'))
    if not isinstance(countries, list) or len(countries) != 193: raise ValueError('expected 193 country records')
    codes = [x.get('iso') for x in countries]
    if len(set(codes)) != 193 or not all(isinstance(c,str) and len(c)==2 and c.isupper() for c in codes):
        raise ValueError('country ISO registry invalid or duplicate')
    profiles = {p.stem for p in (root / 'data/c').glob('??.json')}
    rows = source_doc.get('sources')
    if not isinstance(rows,list): raise ValueError('sources must be an array')
    seen = set(); candidates = defaultdict(lambda: Counter()); verified = defaultdict(lambda: Counter()); domains = defaultdict(set)
    errors = []
    for pos,row in enumerate(rows,1):
        if not isinstance(row,dict): errors.append(f'row {pos}: not an object'); continue
        iso, category, sid, url = (row.get(k) for k in ('iso','category','id','url'))
        if iso not in codes: errors.append(f'row {pos}: unknown country {iso}'); continue
        if category not in REQUIRED: errors.append(f'row {pos}: invalid category {category}'); continue
        if not sid or sid in seen: errors.append(f'row {pos}: duplicate/missing source id {sid}'); continue
        seen.add(sid)
        if not source_url_good(url): errors.append(f'row {pos}: invalid HTTPS source URL'); continue
        if row.get('status') not in ('CANDIDATE','HUMAN_REVIEWED'):
            errors.append(f'row {pos}: invalid status'); continue
        if not isinstance(row.get('publisher'),str) or not row['publisher'].strip():
            errors.append(f'row {pos}: missing publisher'); continue
        hostname=urlsplit(url).hostname.lower()
        if hostname.startswith("www."): hostname=hostname[4:]
        # Distinct domains matter for news-source independence, not duplicate paths.
        domain_key=(iso,category)
        if hostname in domains[domain_key]:
            errors.append(f'row {pos}: duplicate publisher domain {iso}/{category}/{hostname}'); continue
        domains[domain_key].add(hostname)
        candidates[iso][category]+=1
        if review_ok(row,as_of): verified[iso][category]+=1
    items=[]; ready=0
    for c in countries:
        iso=c['iso']; present=iso in profiles; v=verified[iso]; q=candidates[iso]
        category_met={k:v[k]>=count for k,count in REQUIRED.items()}
        finished=present and c.get('done') is True and all(category_met.values())
        ready+=int(finished)
        items.append({'iso':iso,'country_ko':c.get('names',{}).get('ko'), 'country_en':c.get('names',{}).get('en'),
            'profile_exists':present,'legacy_done_flag':c.get('done') is True,
            'candidate_sources':dict(q),'human_reviewed_sources':dict(v),
            'requirements_met':category_met,'operational_source_ready':finished,
            'next_action': 'CREATE_PROFILE_AND_VALIDATE_SOURCES' if not present else 'VERIFY_SOURCE_EVIDENCE'})
    if errors: raise ValueError('invalid source registry: '+'; '.join(errors))
    return {'as_of':as_of.isoformat(),'source_file_status':'REVIEW_ONLY_NOT_PUBLISHED',
        'country_total':len(countries),'profile_file_count':len(profiles.intersection(codes)),
        'missing_profile_count':sum(not x['profile_exists'] for x in items),
        'missing_profiles':[{'iso':x['iso'],'ko':x['country_ko'],'en':x['country_en']} for x in items if not x['profile_exists']],
        'candidate_source_count':sum(sum(x['candidate_sources'].values()) for x in items),
        'human_reviewed_source_count':sum(sum(x['human_reviewed_sources'].values()) for x in items),
        'source_ready_country_count':ready,
        'required_source_slots_per_country':REQUIRED,'missing_country_queue':len([x for x in items if not x['profile_exists']]),
        'countries':items,
        'warning':'CANDIDATE is a discovered URL only, not site operator verification, an official announcement, an active tender, or a live feed.'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--sources',type=Path,required=True)
    p.add_argument('--as-of',default=date.today().isoformat())
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    source_doc=json.loads(args.sources.read_text(encoding='utf-8'))
    result=analyze(args.repo_root,source_doc,args.as_of)
    target=args.output.resolve()
    # Require writing under audit-results, never inside data/ source tree.
    if 'audit-results' not in target.parts: raise ValueError('output path must contain audit-results')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('country_total','missing_profile_count','candidate_source_count','human_reviewed_source_count','source_ready_country_count')},ensure_ascii=False))


if __name__=='__main__': main()
