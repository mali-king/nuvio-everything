"""Validate a merged AIOMetadata config against 3.5.1's rules and live sources."""
import json, sys, time, urllib.request, urllib.parse
from collections import Counter
cfg_path, fp_index_path, mdb_check_path = sys.argv[1:4]
O = json.load(open(cfg_path))['config']
fp = json.load(open(fp_index_path))['index']['regions']
mdb_ok = json.load(open(mdb_check_path))
K, M = O['apiKeys']['tmdb'], O['apiKeys']['mdblist']
UA = {"User-Agent": "curl/8.7.1"}
TMDB_BUILTIN = {'tmdb.top', 'tmdb.trending', 'tmdb.top_rated', 'tmdb.airing_today', 'tmdb.year', 'tmdb.language'}
MAL_BUILTIN = {'mal.airing', 'mal.upcoming', 'mal.schedule', 'mal.seasons', 'mal.genres', 'mal.studios', 'mal.top_movies',
               'mal.top_series', 'mal.most_favorites', 'mal.most_popular', 'mal.top_anime', 'mal.season_top', 'mal.season_top_new'}
SECTION = {'movie': 'movies', 'series': 'series', 'all': 'overall'}
errors, warnings = [], []
cats = O['catalogs']
keys = Counter((c['id'], c['type']) for c in cats)
errors += [f'duplicate {k}' for k, n in keys.items() if n > 1]
names = Counter((c['name'], c['type']) for c in cats)
warnings += [f'same name+type twice: {k}' for k, n in names.items() if n > 1]
if sum(c['enabled'] for c in cats) > 200: errors.append('over 200 enabled')

def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25))

for c in cats:
    cid, typ = c['id'], c['type']
    for f in ('id', 'name', 'type', 'source', 'enabled', 'showInHome'):
        if f not in c: errors.append(f'{cid}: missing {f}')
    if cid.startswith('mdblist.'):
        n = cid.split('.')[1]
        if not n.isdigit(): errors.append(f'{cid}: bad id')
        if n not in mdb_ok:
            r = get(f'https://api.mdblist.com/lists/{n}?apikey={M}'); r = r[0] if isinstance(r, list) else r
            mdb_ok[n] = {k: r.get(k) for k in ('name', 'items', 'dynamic', 'updated', 'mediatype')}
            time.sleep(0.2)
        info = mdb_ok[n]
        if 'error' in info or not info.get('items'): errors.append(f'{cid} {c["name"]}: list unavailable {info}')
        want = 'movie' if typ == 'movie' else 'show'
        if info.get('mediatype') and info['mediatype'] != want:
            warnings.append(f'{cid} {c["name"]}/{typ}: list mediatype is {info["mediatype"]}')
    elif cid.startswith('flixpatrol.'):
        _, svc, country, sec = cid.split('.')[:4]
        slug = c.get('metadata', {}).get('countrySlug')
        if not slug: errors.append(f'{cid}: no countrySlug')
        avail = (fp.get(slug) or {}).get(svc) or {}
        if SECTION[sec] not in avail: errors.append(f'{cid}: FlixPatrol has no {SECTION[sec]} chart for {svc} in {slug} ({list(avail)})')
        if sec != typ: errors.append(f'{cid}: type {typ} != section {sec}')
    elif cid.startswith('tmdb.discover.'):
        d = c.get('metadata', {}).get('discover') or {}
        if d.get('version') != 2 or d.get('source') != 'tmdb': errors.append(f'{cid}: discover header')
        if d.get('mediaType') != ('movie' if typ == 'movie' else 'tv'): errors.append(f'{cid}: mediaType mismatch')
        p = d.get('params') or {}
        if 'sort_by' not in p: errors.append(f'{cid}: no sort_by')
        if p.get('with_watch_providers') and not p.get('watch_region'): errors.append(f'{cid}: providers without region')
        q = urllib.parse.urlencode({**{k: str(v).lower() if isinstance(v, bool) else v for k, v in p.items()}, 'api_key': K})
        r = get(f"https://api.themoviedb.org/3/discover/{d['mediaType']}?{q}")
        total = r.get('total_results', 0)
        c['_total'] = total
        if total < 20: warnings.append(f'{cid} {c["name"]}: only {total} titles')
    elif cid in TMDB_BUILTIN:
        pass
    elif cid in MAL_BUILTIN:
        if typ != 'anime': errors.append(f'{cid}: MAL catalogs are anime')
    else:
        errors.append(f'{cid}: unknown catalog kind')

print(f'{len(cats)} catalogs, {sum(c["enabled"] for c in cats)} enabled')
for c in cats:
    if '_total' in c: print(f'   discover {c["name"]:<26} {c["type"]:<6} {c["_total"]:>6} titles')
print('ERRORS', len(errors)); [print('  E', e) for e in errors]
print('WARNINGS', len(warnings)); [print('  W', w) for w in warnings]
json.dump(mdb_ok, open(mdb_check_path, 'w'), indent=1)
sys.exit(1 if errors else 0)
