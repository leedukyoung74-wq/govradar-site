#!/usr/bin/env python3
"""WMM official-only public NWS + CISA KEV collector.

NWS is an active US weather advisory feed, not a global all-clear signal.
CISA KEV is a vulnerability catalog, not evidence of a current attack incident.
Source failures keep last-good public items and set stale=true (fail-visible).
No authentication, sensitive information, dark-web content, or AI classification.
"""
import argparse
import datetime as dt
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

UTC = dt.timezone.utc
NWS_URL = 'https://api.weather.gov/alerts/active?limit=500'
CISA_PRIMARY = 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'
CISA_MIRROR = 'https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json'
NWS_HOSTS = {'api.weather.gov'}
CISA_HOSTS = {'www.cisa.gov', 'raw.githubusercontent.com'}
CVE = re.compile(r'^CVE-\d{4}-\d{4,19}$')
MAX_BYTES = 9_000_000


def iso(now):
    return now.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_time(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(str(s).replace('Z', '+00:00')).astimezone(UTC)
    except (ValueError, TypeError, OverflowError):
        return None


def official_url(s, domains):
    try:
        u = urllib.parse.urlsplit(s or '')
        return u.scheme == 'https' and u.hostname in domains and not u.username and not u.password
    except (ValueError, TypeError):
        return False


def fetch_json(url, hosts, max_bytes=MAX_BYTES):
    if not official_url(url, hosts):
        raise ValueError('source_not_allowlisted')
    req = urllib.request.Request(url, headers={
        'User-Agent': 'WMM-GOV-RADAR/1.0 (public official data; https://radar.wmm-hoa.com/)',
        'Accept': 'application/geo+json, application/json'
    })
    with urllib.request.urlopen(req, timeout=40) as response:
        if response.status != 200 or not official_url(response.geturl(), hosts):
            raise ValueError('source_redirect_or_http')
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError('source_too_large')
    return json.loads(data)


def nws_rows(pages, now):
    """NWS active feed is authoritative for US-only alerts at query time."""
    if not isinstance(pages, list) or not pages:
        raise ValueError('nws_empty_response')
    rows = []
    seen = set()
    total = 0
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get('features'), list):
            raise ValueError('nws_bad_schema')
        total += len(page['features'])
        for f in page['features']:
            if not isinstance(f, dict):
                continue
            p = f.get('properties') or {}
            if not isinstance(p, dict):
                continue
            if p.get('status') != 'Actual':
                continue
            sev = str(p.get('severity') or '').lower()
            if sev not in ('extreme', 'severe'):
                continue
            ends = parse_time(p.get('ends') or p.get('expires'))
            if ends is not None and ends < now:
                continue
            title = str(p.get('headline') or p.get('event') or '').strip()[:240]
            if not title or (p.get('messageType') or '').lower() in ('cancel', 'test'):
                continue
            url = str(f.get('id') or p.get('id') or '')
            if not official_url(url, NWS_HOSTS):
                url = 'https://www.weather.gov/alerts'
            eid = str(p.get('id') or f.get('id') or (title+str(p.get('sent'))))[:350]
            if eid in seen:
                continue
            seen.add(eid)
            rows.append({
                'title': title, 'event': str(p.get('event') or '')[:120],
                'area': str(p.get('areaDesc') or '')[:200],
                'severity': sev.capitalize(),
                'urgency': str(p.get('urgency') or 'Unknown')[:25],
                'certainty': str(p.get('certainty') or 'Unknown')[:25],
                'issued_at': str(p.get('sent') or '')[:40],
                'ends_at': str(p.get('ends') or p.get('expires') or '')[:40],
                'url': url, 'src': 'NWS',
            })
    rank = {'Extreme': 0, 'Severe': 1}
    rows.sort(key=lambda x: (rank.get(x['severity'], 2), x['ends_at'], x['title']))
    return {'items': rows[:100], 'filtered_count': len(rows),
            'source_active_records_scanned': total, 'display_limit': 100}


def nws_fetch(now):
    pages, next_url, visited = [], NWS_URL, set()
    partial = False
    for _ in range(6):
        if not official_url(next_url, NWS_HOSTS) or next_url in visited:
            raise ValueError('nws_pagination_not_allowlisted')
        visited.add(next_url)
        p = fetch_json(next_url, NWS_HOSTS)
        if not isinstance(p, dict):
            raise ValueError('nws_bad_schema')
        pages.append(p)
        candidate = (p.get('pagination') or {}).get('next')
        if not candidate:
            next_url = None
            break
        next_url = str(candidate)
    if next_url:
        partial = True
    result = nws_rows(pages, now)
    result.update({'schema': 'wmm.nws.v1', 'kind': 'active_us_weather_alerts',
                   'source': 'US National Weather Service',
                   'source_url': 'https://api.weather.gov/alerts/active',
                   'coverage': 'United States only', 'partial_coverage': partial,
                   'not_global_all_clear': True,
                   'disclaimer': 'Active weather alerts, not confirmed disaster impact. Consult NWS before acting.'})
    return result


def cisa_rows(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get('vulnerabilities'), list):
        raise ValueError('cisa_bad_schema')
    items = raw['vulnerabilities']
    n = raw.get('count')
    if not isinstance(n, int) or n != len(items) or n < 1000:
        raise ValueError('cisa_invalid_catalog_count')
    latest, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('cisa_invalid_record')
        cve = item.get('cveID')
        if not isinstance(cve, str) or not CVE.fullmatch(cve) or cve in seen:
            raise ValueError('cisa_invalid_or_duplicate_cve')
        seen.add(cve)
        latest.append({
            'cve': cve,
            'vendor': str(item.get('vendorProject') or '')[:120],
            'product': str(item.get('product') or '')[:130],
            'name': str(item.get('vulnerabilityName') or '')[:230],
            'date_added': str(item.get('dateAdded') or '')[:10],
            'due_date': str(item.get('dueDate') or '')[:10],
            'ransomware_use': str(item.get('knownRansomwareCampaignUse') or 'Unknown')[:18],
            'url': 'https://nvd.nist.gov/vuln/detail/' + cve,
        })
    latest.sort(key=lambda x: (x['date_added'], x['cve']), reverse=True)
    return {
        'schema': 'wmm.cisa.kev.v1', 'kind': 'known_exploited_vulnerabilities',
        'source': 'US CISA Known Exploited Vulnerabilities Catalog',
        'source_url': 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog',
        'catalog_version': str(raw.get('catalogVersion') or '')[:55],
        'catalog_released_at': str(raw.get('dateReleased') or '')[:50],
        'total_vulnerabilities': n, 'displayed': min(100, n),
        'items': latest[:100], 'not_realtime_attack_feed': True,
        'disclaimer': 'These CVEs are documented as exploited in the wild; the catalog is not a live attack incident feed.'
    }


def cisa_fetch(now):
    errors = []
    for url in (CISA_PRIMARY, CISA_MIRROR):
        try:
            result = cisa_rows(fetch_json(url, CISA_HOSTS))
            result['verified_download_url'] = url
            return result
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
            errors.append(type(e).__name__)
    raise ValueError('cisa_official_sources_unavailable')


def elapsed(s, now):
    t = parse_time(s)
    return float('inf') if t is None else (now-t).total_seconds()


def collect_one(path, kind, fn, min_interval_s, now):
    old = None
    if path.exists():
        try:
            old = json.loads(path.read_text(encoding='utf-8-sig'))
        except (ValueError, OSError):
            raise ValueError('prior_public_feed_corrupted')
    if old and old.get('source_health', {}).get('ok') and elapsed(old['source_health'].get('last_ok'), now) < min_interval_s:
        return {'kind': kind, 'status': 'skipped_recent_good', 'published': False}
    try:
        fresh = fn(now)
        if not isinstance(fresh, dict) or not isinstance(fresh.get('items'), list):
            raise ValueError('invalid_collector_output')
        result = fresh
        result['source_health'] = {
            'ok': True, 'last_ok': iso(now), 'checked_at': iso(now),
            'stale': False, 'last_error': None
        }
        status = 'ok'
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
        if old and isinstance(old.get('items'), list):
            result = dict(old)
        else:
            result = {'schema': 'wmm.'+kind+'.v1', 'kind': kind, 'items': []}
        previous_ok = (old or {}).get('source_health', {}).get('last_ok')
        result['source_health'] = {
            'ok': False, 'last_ok': previous_ok, 'checked_at': iso(now),
            'stale': True, 'last_error': type(e).__name__
        }
        status = 'delayed'
    if result != old:
        save_atomic(path, result)
        changed = True
    else:
        changed = False
    return {'kind': kind, 'status': status, 'items': len(result['items']), 'published': changed,
            'last_ok': result['source_health'].get('last_ok')}


def save_atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.wmm-', suffix='.json.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(obj, stream, ensure_ascii=False, separators=(',', ':'))
            stream.write('\n')
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data_directory', type=Path)
    args = ap.parse_args()
    now = dt.datetime.now(UTC)
    results = [
        collect_one(args.data_directory / 'hz' / 'nws_active.json', 'nws', nws_fetch, 14*60, now),
        collect_one(args.data_directory / 'hz' / 'cisa_kev.json', 'cisa_kev', cisa_fetch, 6*3600, now)
    ]
    print(json.dumps(results, ensure_ascii=False))


if __name__ == '__main__':
    main()
