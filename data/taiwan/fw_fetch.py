#!/usr/bin/env python3
"""Download FILMWALKER posts (polite, cached)."""
import json, os, time, urllib.request
from pathlib import Path
DIR = Path('/workspace/taiwan-film-locations/fw')
DIR.mkdir(exist_ok=True)
urls = json.load(open('/workspace/taiwan-film-locations/fw_urls.json'))
UA = {'User-Agent': 'ReduxTaiwanHarvest/1.0 (research for dedomenici redux project; +https://github.com/dedomenici/redux-movie-location-finder)'}

def slug(url):
    return url.replace('https://','').replace('http://','').replace('/','_')[:180] + '.html'

for i, rec in enumerate(urls, 1):
    dest = DIR / slug(rec['url'])
    rec['file'] = str(dest)
    if dest.exists() and dest.stat().st_size > 2000:
        print(f'[{i}/{len(urls)}] cached {dest.name}')
        continue
    try:
        req = urllib.request.Request(rec['url'], headers=UA)
        data = urllib.request.urlopen(req, timeout=40).read()
        dest.write_bytes(data)
        print(f'[{i}/{len(urls)}] {len(data)} {rec["url"]}')
    except Exception as e:
        print(f'[{i}/{len(urls)}] ERR {rec["url"]} {e}')
    time.sleep(0.8)
json.dump(urls, open('/workspace/taiwan-film-locations/fw_urls.json','w'), ensure_ascii=False, indent=1)
print('done')
