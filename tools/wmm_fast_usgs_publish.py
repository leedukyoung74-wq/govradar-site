#!/usr/bin/env python3
"""Fast public USGS update for GOV RADAR's existing data/hz/official.json.

Updates ONLY sources.usgs/items.usgs, keeping all other official feeds intact.
This is a public USGS event feed, not an official tsunami/evacuation warning.
No customer data, credential collection, dark-web browsing, or paid feeds.
"""
import argparse
import datetime as dt
import json
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson'
UTC = dt.timezone.utc
KST = dt.timezone(dt.timedelta(hours=9))
HEARTBEAT_SECONDS = 15 * 60
MAX_READ = 2_000_000


def stamp(now):
    return now.astimezone(KST).strftime('%Y-%m-%dT%H:%M')


def safe_url(s):
    try:
        u = urllib.parse.urlsplit(s)
        return u.scheme == 'https' and u.netloc == 'earthquake.usgs.gov' and u.path.startswith('/earthquakes/eventpage/')
    except (ValueError, TypeError):
        return False


def fetch():
    req = urllib.request.Request(URL, headers={'User-Agent': 'WMM-GOV-RADAR/1.0 (public USGS data)'})
    with urllib.request.urlopen(req, timeout=25) as r:
        if urllib.parse.urlsplit(r.geturl()).hostname != 'earthquake.usgs.gov' or r.status != 200:
            raise ValueError('unexpected source or HTTP status')
        data = r.read(MAX_READ + 1)
    if len(data) > MAX_READ:
        raise ValueError('feed too large')
    return json.loads(data)


def quake_rows(obj):
    if not isinstance(obj, dict) or not isinstance(obj.get('features'), list):
        raise ValueError('USGS GeoJSON schema invalid')
    if len(obj['features']) > 5000:
        raise ValueError('USGS feed abnormal size')
    out = []
    seen = set()
    for feature in obj['features']:
        if not isinstance(feature, dict):
            continue
        prop = feature.get('properties') or {}
        geom = feature.get('geometry') or {}
        if not isinstance(prop, dict) or not isinstance(geom, dict):
            continue
        mag, ts = prop.get('mag'), prop.get('time')
        try:
            mag = float(mag)
            ms = int(ts)
            lon, lat = (geom.get('coordinates') or [])[:2]
            lon, lat = float(lon), float(lat)
        except (TypeError, ValueError, IndexError):
            continue
        if not (-180 <= lon <= 180 and -90 <= lat <= 90 and -2 <= mag <= 10):
            continue
        if mag < 5.5:
            continue
        source = prop.get('url') or ''
        if not safe_url(source) or source in seen:
            continue
        seen.add(source)
        day = dt.datetime.fromtimestamp(ms / 1000, UTC).strftime('%Y-%m-%d')
        title = ('M%.1f %s' % (mag, str(prop.get('place') or 'Earthquake')[:140])).strip()
        level = str(prop.get('alert') or '').lower()
        out.append((ms, {'k': 'quake', 't': title, 'date': day,
                         'lvl': level if level in ('orange', 'red') else '',
                         'url': source, 'x': lon, 'y': lat,
                         'src': 'USGS', 'mag': round(mag, 1)}))
    out.sort(key=lambda a: a[0], reverse=True)
    return [x[1] for x in out[:12]]


def heartbeat_due(last_checked, now):
    try:
        t = dt.datetime.strptime(last_checked, '%Y-%m-%dT%H:%M').replace(tzinfo=KST)
        return (now.astimezone(KST) - t).total_seconds() >= HEARTBEAT_SECONDS
    except (TypeError, ValueError):
        return True


def transform(old, raw, now, error=None):
    if not isinstance(old, dict) or not isinstance(old.get('sources'), dict) or not isinstance(old.get('items'), dict):
        raise ValueError('existing official.json is missing or invalid; refuse to overwrite')
    result = json.loads(json.dumps(old))
    prev = result['sources'].get('usgs') or {}
    old_items = result['items'].get('usgs') or []
    if error is not None:
        result['sources']['usgs'] = {**prev, 'ok': False,
                                      'err': type(error).__name__, 'n': len(old_items)}
        rows = old_items
    else:
        rows = quake_rows(raw)
        result['items']['usgs'] = rows
        result['sources']['usgs'] = {'ok': True, 'last_ok': stamp(now), 'n': len(rows)}
    changed = result['sources']['usgs'].get('ok') != prev.get('ok') or rows != old_items
    # Do not reset the aggregate 'checked' time. It belongs to the six-agency daily
    # collector; updating it on an USGS-only refresh would falsely freshen other agencies.
    last_fast = old.get('usgs_fast_checked') or old.get('checked')
    if changed or heartbeat_due(last_fast, now):
        result['usgs_fast_checked'] = stamp(now)
        return result, True
    return old, False


def save_atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '\n'
    fd, tmp = tempfile.mkstemp(prefix='.wmm-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def run(path, getter=fetch, now=None):
    now = now or dt.datetime.now(UTC)
    if not path.is_file():
        raise ValueError('existing official.json absent; refusing to create an incomplete feed')
    old = json.loads(path.read_text(encoding='utf-8-sig'))
    try:
        fresh = getter()
        result, changed = transform(old, fresh, now)
        state = 'ok'
    except (OSError, TimeoutError, ValueError, TypeError, json.JSONDecodeError) as exc:
        result, changed = transform(old, None, now, error=exc)
        state = 'delayed'
    if changed:
        save_atomic(path, result)
    print(json.dumps({'source': 'USGS', 'status': state, 'items': len(result['items'].get('usgs') or []),
                      'wrote': changed, 'checked': result.get('checked'),
                      'last_ok': (result['sources'].get('usgs') or {}).get('last_ok')}, ensure_ascii=False))
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('official_json', type=Path)
    args = parser.parse_args()
    run(args.official_json)
