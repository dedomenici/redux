#!/usr/bin/env python3
"""Smarter Nominatim retry by place-name, keep honest street pins, rematch
filmkh scenes by name, then remake all_rows + spots with tighter dedupe so
nearby Wayward Cloud landmarks stay separate."""
import csv, json, math, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo import geocode
from round2_harvest import city_of, TW, ROOT, dist, write_outputs, precision_for

CITY_RE = re.compile(
    r'(台北市|臺北市|新北市|基隆市|桃園市|新竹市|新竹縣|苗栗縣|台中市|臺中市|彰化縣|'
    r'南投縣|雲林縣|嘉義市|嘉義縣|台南市|臺南市|高雄市|屏東縣|宜蘭縣|花蓮縣|台東縣|臺東縣|澎湖縣|金門縣|連江縣)'
)

POI_OK_TYPES = {
    'hotel','motel','hostel','guest_house','restaurant','cafe','bar','pub','fast_food',
    'cinema','theatre','arts_centre','community_centre','library','museum','gallery',
    'attraction','theme_park','zoo','aquarium','viewpoint','memorial','monument',
    'artwork','place_of_worship','church','temple','chapel','shrine','monastery',
    'school','university','college','kindergarten','hospital','clinic','doctors',
    'police','fire_station','townhall','courthouse','embassy','prison',
    'station','halt','tram_stop','subway_entrance','ferry_terminal','bus_station','platform',
    'airport','terminal','harbour','marina','pier','ferry',
    'park','garden','nature_reserve','beach','peak','island','islet',
    'stadium','sports_centre','pitch','swimming_pool','track',
    'yes','house','apartments','building','ruins','historic','industrial','retail',
    'commercial','warehouse','cathedral','synagogue','mosque','cemetery',
    'marketplace','department_store','supermarket','bookstore','mall',
    'bridge','tower','lighthouse','castle','fort','palace','gate',
    'footway',  # only if name matches a named bridge
}

SKIP_NAME = re.compile(r'(民宅|住處|家$|遠眺|周邊$|附近|方向|一帶|主場景)')


def city_from_addr(addr):
    m = CITY_RE.search(addr or '')
    return (m.group(1).replace('台', '臺') if m else '')


def clean_name(n):
    n = re.sub(r'\s+', ' ', n or '').strip()
    n = re.sub(r'\s*[-–—]\s*\d+\s*$', '', n)
    n = re.sub(r'(舊址|遺址)$', '', n).strip()
    n = re.sub(r'^[^-]+ - ', '', n) if re.match(r'.+ - .+', n) and '市' in n else n
    return n.strip(' -')


def accept_poi(g, name, city):
    if not g or not TW(g['lat'], g['lng']):
        return False
    disp = g.get('display') or ''
    if city and city not in disp and city.replace('臺', '台') not in disp:
        # Penghu etc. may appear as 澎湖縣 or 馬公市
        if city == '澎湖縣' and '澎湖' not in disp and '馬公' not in disp and '西嶼' not in disp and '白沙' not in disp and '湖西' not in disp:
            return False
        elif city != '澎湖縣':
            return False
    n0 = disp.split(',')[0].strip()
    typ = (g.get('type') or '')
    core = re.sub(r'[\s\-（()）]', '', name)
    n0c = re.sub(r'[\s\-（()）]', '', n0)
    name_hit = (n0c and (n0c in core or core in n0c or (len(n0c) >= 2 and n0c[:2] in core)))
    if typ in POI_OK_TYPES and name_hit:
        return True
    if typ in POI_OK_TYPES and len(core) >= 2 and core[:2] in disp:
        return True
    if name_hit and typ not in ('administrative', 'city', 'suburb', 'town', 'village', 'county', 'state', 'postcode', 'peak') or typ in POI_OK_TYPES:
        # named building/amenity even if type is odd
        if typ in ('administrative', 'city', 'suburb', 'town', 'village', 'county', 'state', 'quarter'):
            return False
        if typ in ('residential', 'primary', 'secondary', 'tertiary', 'unclassified', 'living_street', 'service') and not name_hit:
            return False
        return name_hit
    return False


def geocode_fw_by_name(raw, already_kept_addrs):
    kept, miss = [], []
    seen = set(already_kept_addrs)
    for r in raw:
        addr = r['addr']
        if addr in seen:
            continue
        name = clean_name(r.get('place_zh') or r.get('place_en') or '')
        if not name or SKIP_NAME.search(name):
            miss.append((r.get('film_zh'), name or addr, 'skip-name'))
            continue
        # Don't use a pure road name here; those are handled as street-level separately
        if re.fullmatch(r'.*[路街巷段](\d+巷)?', name) and not re.search(r'(車站|公園|市場|碼頭|宮|廟|寺|橋|學校|國小|國中|高中|大學|飯店|酒店|戲院|館)', name):
            miss.append((r.get('film_zh'), name, 'road-name'))
            continue
        city = city_from_addr(addr)
        q = (name + (', ' + city if city else '')).strip(', ')
        g = geocode(q)
        if not accept_poi(g, name, city):
            # try name alone
            if city:
                g2 = geocode(name)
                if accept_poi(g2, name, city):
                    g = g2
                else:
                    miss.append((r.get('film_zh'), q, 'no-poi' if not g else 'reject:' + (g['display'][:70] if g else '')))
                    continue
            else:
                miss.append((r.get('film_zh'), q, 'no-poi' if not g else 'reject:' + g['display'][:70]))
                continue
        rec = dict(r)
        rec['lat'], rec['lng'] = g['lat'], g['lng']
        rec['coord_source'] = 'OpenStreetMap Nominatim (' + q + '): ' + g['display'][:120]
        rec['coord_conf'] = 'medium'
        rec['city'] = city_of(g['lat'], g['lng'])
        rec['shoot_date'] = rec.get('shoot_date') or ''
        if not rec.get('place_zh'):
            rec['place_zh'] = name
        kept.append(rec)
        seen.add(addr)
    return kept, miss


def street_rows_from_misses(fw_miss, raw_by_addr):
    """Promote honest street-only Nominatim hits (right road in the right district)."""
    out = []
    for film, addr, why in fw_miss:
        if not why.startswith('street-only:'):
            continue
        recs = raw_by_addr.get(addr) or []
        if not recs:
            continue
        g = geocode(addr)  # cached
        if not g or not TW(g['lat'], g['lng']):
            continue
        rec = dict(recs[0])
        rec['lat'], rec['lng'] = g['lat'], g['lng']
        rec['coord_source'] = 'OpenStreetMap Nominatim (' + addr + '): ' + g['display'][:120]
        rec['coord_conf'] = 'street-level'
        rec['city'] = city_of(g['lat'], g['lng'])
        rec['shoot_date'] = ''
        out.append(rec)
    return out


def fill_scenes_by_name():
    sc = json.load(open(ROOT / 'fk/scenes.json'))
    filled = 0
    for s in sc:
        if s.get('lat'):
            continue
        q = s['name'] + ', 高雄市'
        g = geocode(q)
        if accept_poi(g, s['name'], '高雄市'):
            s['lat'], s['lng'] = g['lat'], g['lng']
            s['coord_from'] = 'Nominatim of filmkh scene name: ' + g['display'][:120]
            filled += 1
    json.dump(sc, open(ROOT / 'fk/scenes.json', 'w'), ensure_ascii=False, indent=1)
    print('scene name fills', filled)
    return sc


def filter_kh(kh):
    drop = []
    keep = []
    for r in kh:
        tok = r['place_zh']
        disp = r['coord_source']
        # whole-district pins
        if re.fullmatch(r'.{1,3}區', tok) or tok in ('六龜區',):
            drop.append((tok, 'district-level'))
            continue
        # known bad snaps
        if '北嶺國小' in disp and '科學園區' in tok:
            drop.append((tok, 'wrong-poi'))
            continue
        if tok == '工協路' and '協和' in disp and '工協' not in disp:
            drop.append((tok, 'wrong-road'))
            continue
        if tok == '懷恩寶塔' and '懷恩堂' in disp:
            drop.append((tok, 'uncertain-alias'))
            continue
        if tok == '公園路' and '公園路' not in disp.split(':')[-1].split(',')[0]:
            drop.append((tok, 'not-the-road'))
            continue
        r['origin'] = 'Kaohsiung Film Commission (filmkh.org) — 來過高雄拍 (round 2 geocode retry)'
        keep.append(r)
    print('kh kept', len(keep), 'dropped', drop)
    return keep


def load_base_from_repo_csv():
    path = Path('/workspace/redux-movie-location-finder/data/taiwan/taiwan_film_locations.csv')
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f):
            rec = dict(r)
            rec['lat'] = float(rec['lat'])
            rec['lng'] = float(rec['lng'])
            rec['year'] = int(rec['year']) if rec.get('year') and str(rec['year']).isdigit() else (rec.get('year') or None)
            if rec['year'] == '':
                rec['year'] = None
            rows.append(rec)
    return rows


def names_close(a, b):
    def toks(s):
        s = re.sub(r'[（(][^）)]*[）)]', '', s or '')
        parts = re.split(r'[\s,，、/／·]+', s)
        out = set()
        for p in parts:
            p = p.strip()
            if len(p) >= 2:
                out.add(p)
        # CJK bigrams of the compacted string
        compact = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', s)
        for i in range(len(compact) - 1):
            if re.search(r'[\u4e00-\u9fff]', compact[i:i+2]):
                out.add(compact[i:i+2])
        return out
    A, B = toks(a), toks(b)
    if not A or not B:
        return False
    return bool(A & B)


def merge_tight(old, *news):
    """Same-film merge within 60 m, or within 150 m only if the place names overlap.
    Prefer richer scene text and tighter coordinate confidence."""
    rank = {'high': 0, 'medium': 1, 'street-level': 2}
    ded = list(old)
    added = 0
    for group in news:
        for r in group:
            key = (r['film_zh'] or r['film_en'] or '').lower()
            rname = r.get('place_zh') or r.get('place_en') or ''
            dup = None
            for d in ded:
                if (d['film_zh'] or d['film_en'] or '').lower() != key:
                    continue
                km = dist(d['lat'], d['lng'], r['lat'], r['lng'])
                dname = d.get('place_zh') or d.get('place_en') or ''
                if km < 0.06 or (km < 0.15 and names_close(rname, dname)):
                    dup = d
                    break
            if dup:
                if r.get('scene') and (not dup.get('scene') or len(str(r['scene'])) > len(str(dup.get('scene') or ''))):
                    dup['scene'] = r['scene']
                if rank.get(r.get('coord_conf'), 9) < rank.get(dup.get('coord_conf'), 9):
                    for k in ('lat', 'lng', 'coord_source', 'coord_conf', 'place_en', 'place_zh'):
                        if r.get(k):
                            dup[k] = r[k]
                if r.get('source') and r['source'] not in (dup.get('source') or ''):
                    dup['source2'] = ((dup.get('source2') or '') + ' ' + r['source']).strip()
                if r.get('origin') and 'Wayward' in (r.get('origin') or ''):
                    # keep the more specific WC research origin alongside the old one
                    if 'Wayward' not in (dup.get('origin') or ''):
                        dup['origin'] = (dup.get('origin') or '') + ' + ' + r['origin']
                continue
            ded.append(r)
            added += 1
    return ded, added


def wayward_rows():
    import csv as _csv
    path = Path('/workspace/wayward-cloud/wayward_cloud_locations.csv')
    rows = []
    with path.open() as f:
        for r in _csv.DictReader(f):
            cid = int(r['id'])
            if cid in (8, 9) or not r.get('lat') or not r.get('lon'):
                print('skip wayward', cid, r['name_en'])
                continue
            lat, lng = float(r['lat']), float(r['lon'])
            link = 'high' if cid in (1, 2, 7) else 'medium'
            coord = 'high' if cid in (1, 2) else 'medium'
            extras = re.findall(r'https?://[^\s;]+', r.get('source_note') or '')
            rows.append(dict(
                film_en='The Wayward Cloud', film_zh='天邊一朵雲', year=2005,
                kind='film', director='蔡明亮',
                place_zh=r['name_zh'], place_en=r['name_en'],
                lat=lat, lng=lng,
                coord_source=r['coord_source'], coord_conf=coord,
                scene=(r['scene'] or '')[:400],
                source=r['source_url'], source2=' '.join(extras),
                link_conf=link, city='Kaohsiung', shoot_date='',
                origin='Wayward Cloud location research (Nov 2026), sources linked per pin',
            ))
    return rows


def upgrade_pins():
    """Named-site upgrades that previously snapped to a road centreline."""
    specs = [
        ("Our Times", "我的少女時代", 2015, "Eslite Dunnan (closed 2020)", "敦南誠品（已熄燈）",
         ["敦化南路一段 245 號, 大安區, 臺北市", "Eslite Bookstore Dunnan, Taipei", "敦化南路一段245號 誠品"],
         "The famous Dunnan Eslite, closed 2020.",
         "https://stunning-asia.com/smart-travel/the-filming-locations-of-top-mandarin-movies/", "medium"),
        ("Cafe. Waiting. Love", "等一個人咖啡", 2014, "Waiting for Someone Café, Jingmei", "等一個人咖啡（景美店）",
         ["一壽街44巷, 文山區, 臺北市", "一壽街 44巷 1號, 文山區, 臺北市", "等一個人咖啡 景美本店"],
         "The café of the title (Jingmei main shop, 一壽街44巷1號).",
         "https://supertaste.tvbs.com.tw/pack/347636", "high"),
        ("The Boys from Fengkuei", "風櫃來的人", 1983, "Qixian Building, Yancheng", "七賢大樓",
         ["七賢大樓, 高雄市", "七賢三路269號, 鹽埕區, 高雄市"],
         "The Penghu boys are conned up to the rooftop of an unfinished building. FILMWALKER gives 七賢三路269號.",
         "https://islandtapestry.blogspot.com/2026/03/boysfromfengkuei.html", "high"),
    ]
    rows, miss = [], []
    for en, zh, yr, pen, pzh, queries, scene, src, conf in specs:
        g, used = None, ''
        for q in queries:
            cand = geocode(q)
            if cand and TW(cand['lat'], cand['lng']):
                # reject wrong city
                if zh != '風櫃來的人' and '臺北' not in cand['display'] and '台北' not in cand['display']:
                    continue
                if zh == '風櫃來的人' and '高雄' not in cand['display']:
                    continue
                g, used = cand, q
                # prefer a non-road result
                typ = cand.get('type') or ''
                if typ not in ('primary', 'secondary', 'tertiary', 'residential', 'unclassified'):
                    break
        if not g:
            miss.append((zh, pzh, queries[0]))
            continue
        typ = g.get('type') or ''
        cc = 'street-level' if typ in ('primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'living_street') and '巷' not in used else 'medium'
        # an alley (巷) is a tight enough site
        if '巷' in used:
            cc = 'medium'
        rows.append(dict(film_en=en, film_zh=zh, year=yr, kind='film', director='',
                         place_zh=pzh, place_en=pen, lat=g['lat'], lng=g['lng'],
                         coord_source='OpenStreetMap Nominatim (' + used + '): ' + g['display'][:120],
                         coord_conf=cc, scene=scene, source=src, source2='',
                         link_conf=conf, city=city_of(g['lat'], g['lng']), shoot_date='',
                         origin='Curated from web sources (round 2 pin upgrade)'))
    return rows, miss


def main():
    raw = json.load(open(ROOT / 'fw_raw.json'))
    already = json.load(open(ROOT / 'fw_rows.json'))
    already_addrs = {r['addr'] for r in already}
    print('=== FW place-name geocode ===', 'already', len(already))
    named, nmiss = geocode_fw_by_name(raw, already_addrs)
    print('new named', len(named), 'miss', len(nmiss))
    json.dump(named, open(ROOT / 'fw_named.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(nmiss, open(ROOT / 'fw_named_miss.json', 'w'), ensure_ascii=False, indent=1)

    fw_miss = json.load(open(ROOT / 'fw_geo_miss.json'))
    raw_by = {}
    for r in raw:
        raw_by.setdefault(r['addr'], []).append(r)
    streets = street_rows_from_misses(fw_miss, raw_by)
    print('street-level FW kept', len(streets))

    print('=== filmkh scenes by name ===')
    fill_scenes_by_name()
    # attach any newly filled scenes to remaining misses that match by name
    # (retry_misses already ran; do a light pass on leftover misses)
    from round2_harvest import retry_misses
    sc = json.load(open(ROOT / 'fk/scenes.json'))
    # restore leftover list from current kh_misses (already reduced)
    more, still = retry_misses(sc)
    # retry_misses rewrites based on original? It loads kh_misses.json which was already reduced to 118.
    # That's OK — it will try the remaining 118 again with newly filled scene GPS.
    print('extra kh from scene names', len(more), 'still', len(still))
    json.dump(still, open(ROOT / 'kh_misses.json', 'w'), ensure_ascii=False, indent=1)

    kh = filter_kh(json.load(open(ROOT / 'kh_retry.json')) + more)
    json.dump(kh, open(ROOT / 'kh_retry.json', 'w'), ensure_ascii=False, indent=1)

    print('=== Wayward Cloud + upgrades ===')
    wc = wayward_rows()
    print('wayward', len(wc), [r['place_en'] for r in wc])
    cur, cmiss = upgrade_pins()
    print('upgrades', len(cur), 'miss', cmiss)

    print('=== merge from original 352 ===')
    base = load_base_from_repo_csv()
    print('base', len(base))
    merged, added = merge_tight(base, already, named, streets, kh, wc, cur)
    print('added', added, 'total', len(merged))
    write_outputs(merged)
    print('done')

if __name__ == '__main__':
    main()
