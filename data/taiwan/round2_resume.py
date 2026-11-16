#!/usr/bin/env python3
"""Resume interrupted harvest, fold in Wayward Cloud CSV, merge, rebuild spots."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from round2_harvest import (
    geocode_fw, fill_scene_addresses, retry_misses, geocode_curated,
    merge, write_outputs, city_of, ROOT, CURATED2
)

def wayward_rows():
    """High/medium pins from the dedicated Wayward Cloud research CSV.
    Skip unmapped / area-only rows the app cannot represent honestly.
    """
    path = Path('/workspace/wayward-cloud/wayward_cloud_locations.csv')
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f):
            cid = int(r['id'])
            conf_raw = r['confidence']
            # Skip wrap-only Taipei road and any unmapped rows (rental shop etc.)
            if cid in (9,) or not r.get('lat') or not r.get('lon'):
                print('skip wayward', cid, r['name_en'], 'unmapped or excluded')
                continue
            # Riverside Community is area-level only (exact building unknown).
            # The app has exact site / site / street — no area precision — and
            # street pins are hidden on near-you. Skip rather than drop a
            # doorbell-like pin on a whole housing estate.
            if cid == 8:
                print('skip wayward', cid, r['name_en'], 'area-level not supported')
                continue
            lat, lng = float(r['lat']), float(r['lon'])
            # link_conf: treat group-high / park-high as high; span/approx as medium
            if cid in (1, 2, 7):
                link = 'high'
            else:
                link = 'medium'
            # coord_conf: official named landmarks -> high (exact site);
            # park / spans / approximate shore -> medium (site)
            if cid in (1, 2):
                coord = 'high'
            else:
                coord = 'medium'
            src2 = ''
            # keep additional URLs mentioned in the note when they are real links
            note = r.get('source_note') or ''
            import re
            extras = re.findall(r'https?://[^\s;]+', note)
            src2 = ' '.join(extras)
            rows.append(dict(
                film_en='The Wayward Cloud', film_zh='天邊一朵雲', year=2005,
                kind='film', director='蔡明亮',
                place_zh=r['name_zh'], place_en=r['name_en'],
                lat=lat, lng=lng,
                coord_source=r['coord_source'],
                coord_conf=coord,
                scene=(r['scene'] or '')[:400],
                source=r['source_url'], source2=src2,
                link_conf=link, city='Kaohsiung', shoot_date='',
                origin='Wayward Cloud location research (Nov 2026), sources linked per pin',
            ))
    return rows

def curated_upgrades():
    # Keep only the non-Wayward upgrades from CURATED2 (Eslite, café)
    return [e for e in CURATED2 if e[1] not in ('天邊一朵雲',)]

def main():
    fw_raw = json.load(open(ROOT / 'fw_raw.json'))
    print('=== FILMWALKER geocode (resume, cache-aware) ===', len(fw_raw))
    fw_kept, fw_miss = geocode_fw(fw_raw)
    print('fw kept', len(fw_kept), 'fw geo miss', len(fw_miss))
    json.dump(fw_kept, open(ROOT / 'fw_rows.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(fw_miss, open(ROOT / 'fw_geo_miss.json', 'w'), ensure_ascii=False, indent=1)

    print('=== fill filmkh scene addresses ===')
    sc = fill_scene_addresses()
    print('=== retry kh misses ===')
    kh_new, still = retry_misses(sc)
    print('kh newly located', len(kh_new), 'still missed', len(still))
    json.dump(kh_new, open(ROOT / 'kh_retry.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(still, open(ROOT / 'kh_misses.json', 'w'), ensure_ascii=False, indent=1)

    print('=== Wayward Cloud CSV ===')
    wc = wayward_rows()
    print('wayward rows kept', len(wc), [r['place_en'] for r in wc])

    print('=== curated upgrades ===')
    cur, cmiss = geocode_curated(curated_upgrades())
    print('curated', len(cur), 'miss', cmiss)

    print('=== merge ===')
    old = json.load(open(ROOT / 'all_rows.json'))
    # If this file was already merged in a previous partial run it is still the
    # original 352-row snapshot (mtime before harvest wrote back).
    merged, added = merge(old, fw_kept, kh_new, wc, cur)
    print('added (non-duplicate) rows', added, 'total', len(merged))
    write_outputs(merged)
    print('done')

if __name__ == '__main__':
    main()
