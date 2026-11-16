#!/usr/bin/env python3
"""Round 2 harvest: FILMWALKER addresses, filmkh scene-address retry, Wayward Cloud, pin upgrades."""
import json, re, html, math, csv, os, time
from pathlib import Path
from collections import Counter
from geo import geocode

ROOT = Path('/workspace/taiwan-film-locations')
TW = lambda la, ln: 21.8 < la < 25.5 and 119.2 < ln < 122.1
CITIES = [
    ('Pingtung City', 22.67, 120.49, 12), ('Kaohsiung', 22.63, 120.30, 40),
    ('Pingtung/Kenting', 22.2, 120.7, 45), ('Tainan', 23.0, 120.22, 30),
    ('Chiayi', 23.48, 120.45, 25), ('Taichung', 24.15, 120.67, 30),
    ('Changhua', 24.07, 120.54, 15), ('Hsinchu', 24.8, 120.98, 25),
    ('Taoyuan', 24.95, 121.25, 20), ('Keelung/Jiufen/Ruifang', 25.12, 121.8, 14),
    ('Taipei/New Taipei', 25.05, 121.52, 28), ('Yilan', 24.7, 121.75, 30),
    ('Hualien', 23.95, 121.55, 60), ('Miaoli', 24.55, 120.85, 30),
    ('Taitung', 22.8, 121.15, 50), ('Nantou', 23.9, 120.9, 40),
    ('Yunlin', 23.7, 120.45, 25),
    ('Penghu', 23.57, 119.58, 40),
]

def dist(a, b, c, d):
    return 6371 * 2 * math.asin(math.sqrt(
        math.sin(math.radians(c - a) / 2) ** 2
        + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(math.radians(d - b) / 2) ** 2
    ))

def city_of(la, ln):
    best = min(CITIES, key=lambda c: dist(la, ln, c[1], c[2]) / c[3])
    return best[0] if dist(la, ln, best[1], best[2]) <= best[3] else 'Taiwan (other)'

def body_text(html_src):
    m = re.search(r'<div[^>]+class="post-body[^"]*"(.*)', html_src, re.S)
    chunk = m.group(1) if m else html_src
    # cut at post-footer if present
    cut = re.search(r'<div class="post-footer', chunk)
    if cut:
        chunk = chunk[:cut.start()]
    text = html.unescape(re.sub(r'<script.*?</script>|<style.*?</style>', '', chunk, flags=re.S))
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = re.sub(r'</(p|h[1-6]|li|tr|div)>', '\n', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n[ \t]+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

TITLE_RE = re.compile(
    r'【電影拍攝場景】\s*《([^》]+)》\s*([^．.\n]*?)\s*[．.]\s*(?:導演[：:][^．.\n]*[．.]\s*)?(\d{4})?'
)
YEAR_RE = re.compile(r'(?:年|\.|．)\s*(19|20)\d{2}')

# Manual title/year for posts whose heading is irregular
MANUAL = {
    'threetimesruifang': ("Three Times", "最好的時光", 2005),
    'rebelsoftheneongod': ("Rebels of the Neon God", "青少年哪吒", 1992),
    'ahchung': ("Ah Chung", "忠仔", 1995),
    'blog-post_20': ("Darkness and Light", "黑暗之光", 1999),
    'blog-post_44': ("Intimate Encounter", "優雅的相遇", 2024),
    '0635': ("Betelnut Beauty", "愛你愛我", 2001),
    'blog-post_9': ("Blue Gate Crossing", "藍色大門", 2002),
    'ahometoofar': ("A Home Too Far", "異域", 1990),
    'requital': ("Requital", "五湖四海", 1992),
    'huayinst': ("Dragon Superman Series", "神龍飛俠系列", 1968),
    'chenggong': ("King of Snakes", "大蛇王", 1987),
    'blog-post_33': ("", "龍虎雙俠", 1966),
    'blog-post_77': ("The Chairman", "主席", 1969),
    'blog-post.html': ("Zegen", "女衒", 1989),
    'dashan': ("Rainy Dog", "極道黒社会", 1997),
}

SKIP_FILMS = {
    # Shot in Japan / not Taiwan locations
    'café lumière', 'cafe lumiere', '珈琲時光',
}

def parse_heading(title, text, url):
    slug = url.rstrip('/').rsplit('/', 1)[-1].replace('.html', '')
    if slug in MANUAL:
        return MANUAL[slug]
    # try first heading in text
    m = TITLE_RE.search(text) or TITLE_RE.search(title)
    if m:
        zh, en, year = m.group(1).strip(), m.group(2).strip(), m.group(3)
        en = re.sub(r'\s+', ' ', en).strip(' ．.·')
        return (en, zh, int(year) if year else None)
    # fallback: "Title EN" from our index
    # title field like "飲食男女 Eat Drink Man Woman"
    t = html.unescape(title)
    t = re.sub(r'&nbsp;', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    year = None
    ym = re.search(r'\b((?:19|20)\d{2})\b', t)
    if ym:
        year = int(ym.group(1))
        t = t[:ym.start()].strip()
    # split CJK / latin
    mm = re.match(r'^(.*?)([A-Za-z].*)$', t)
    if mm and re.search(r'[\u4e00-\u9fff]', mm.group(1)):
        return (mm.group(2).strip(), mm.group(1).strip(' ,，．.·'), year)
    if re.search(r'[\u4e00-\u9fff]', t):
        return ('', t, year)
    return (t, '', year)

# Addresses we will not pin: private homes, too vague, non-Taiwan
SKIP_ADDR = re.compile(r'(民宅|住處|男主角住處|女主角住處|巷內$|山區$|一帶$|方向$|附近$)')
JAPAN_OR_ABROAD = re.compile(r'(東京都|大阪府|京都府|北海道|神奈川|日本|香港|九龍|上海|北京|韓國|서울|Tokyo|Japan)')

ADDR_LINE = re.compile(
    r'場景地址[：:]\s*([^\n]+)'
)
PLACE_BLOCK = re.compile(
    r'▫️\s*\n([^\n]+)\n(.*?)(?=\n▫️|\Z)', re.S
)
COORDS = re.compile(r'(2[2-5]\.\d{3,8})\s*[,，]\s*(12[0-2]\.\d{3,8})')

def clean_addr(a):
    a = html.unescape(a)
    a = re.sub(r'\s+', ' ', a).strip(' 。；;，,')
    # drop trailing parenthetical comments
    a = re.sub(r'[（(][^）)]{0,40}[）)]$', '', a).strip()
    return a

def acceptable_addr(a):
    if not a or len(a) < 6:
        return False
    if JAPAN_OR_ABROAD.search(a):
        return False
    if not re.search(r'(台北市|臺北市|新北市|基隆市|桃園市|新竹|苗栗|台中市|臺中市|彰化|南投|雲林|嘉義|台南市|臺南市|高雄市|屏東|宜蘭|花蓮|台東|臺東|澎湖|金門|連江)', a):
        # allow if it still looks like a TW address starting with a county typo-free form
        if not re.search(r'(市|縣|區)', a):
            return False
    if SKIP_ADDR.search(a) and '號' not in a:
        return False
    # district-only (e.g. 新北市金山區) is too coarse
    if re.fullmatch(r'.{2,4}[縣市].{1,4}[區鄉鎮市]', a):
        return False
    # need a road/street/place noun
    if not re.search(r'(路|街|巷|段|號|里|村|公園|站|宮|廟|寺|橋|學校|國小|國中|高中|大學|飯店|酒店|市場|碼頭|港|夜市|戲院|電影|圖書館|博物館|園|池|堂|樓|廈|社區|新村|村)', a):
        return False
    return True

def precision_for(addr, nominatim):
    if re.search(r'\d+號', addr):
        return 'medium'  # named site / address
    if '十字路口' in addr or (addr.count('路') >= 2 and '、' in addr):
        return 'medium'
    n0 = (nominatim.get('display') or '').split(',')[0].strip() if nominatim else ''
    typ = (nominatim or {}).get('type') or ''
    cls = (nominatim or {}).get('cls') or ''
    if typ in ('yes', 'house', 'apartments', 'building', 'church', 'temple', 'school', 'university',
               'museum', 'library', 'theatre', 'cinema', 'hotel', 'hospital', 'station', 'bridge',
               'park', 'garden', 'memorial', 'attraction', 'place_of_worship') or cls in ('amenity', 'tourism', 'building', 'leisure'):
        return 'medium'
    if re.search(r'([路街巷]|[一二三四五六七八九]段)$', n0):
        return 'street-level'
    return 'medium'

def parse_fw():
    urls = json.load(open(ROOT / 'fw_urls.json'))
    rows = []
    skipped = []
    for rec in urls:
        fp = rec.get('file')
        if not fp or not Path(fp).exists():
            skipped.append((rec['url'], 'no file'))
            continue
        raw = Path(fp).read_text(errors='ignore')
        text = body_text(raw)
        en, zh, year = parse_heading(rec.get('title', ''), text, rec['url'])
        key = (en + ' ' + zh).lower()
        if any(s in key for s in SKIP_FILMS):
            skipped.append((rec['url'], 'skip film ' + zh or en))
            continue
        blocks = PLACE_BLOCK.findall(text)
        if not blocks:
            # fallback: just address lines
            for m in ADDR_LINE.finditer(text):
                blocks.append(('', '場景地址：' + m.group(1)))
        seen_addr = set()
        for name, body in blocks:
            name = re.sub(r'\s+', ' ', name).strip()
            am = ADDR_LINE.search(body)
            if not am:
                continue
            addr = clean_addr(am.group(1))
            if not acceptable_addr(addr):
                skipped.append((rec['url'], 'skip addr ' + addr))
                continue
            if addr in seen_addr:
                continue
            seen_addr.add(addr)
            sm = re.search(r'場景說明[：:]\s*([^\n]+)', body)
            scene = sm.group(1).strip() if sm else ''
            if len(scene) > 240:
                scene = scene[:237] + '…'
            cm = COORDS.search(body)
            rows.append(dict(
                film_en=en, film_zh=zh, year=year, kind='film', director='',
                place_zh=name if re.search(r'[\u4e00-\u9fff]', name) else '',
                place_en=name if name.isascii() else '',
                addr=addr,
                lat=float(cm.group(1)) if cm else None,
                lng=float(cm.group(2)) if cm else None,
                scene=scene, source=rec['url'], source2='',
                link_conf='high', origin='FILMWALKER (islandtapestry / taiwantravelforever) scene-address posts',
            ))
    return rows, skipped

def geocode_fw(rows):
    kept, miss = [], []
    for r in rows:
        if r['lat'] and TW(r['lat'], r['lng']):
            r['coord_source'] = 'coordinates published in FILMWALKER post'
            r['coord_conf'] = 'medium'
            r['city'] = city_of(r['lat'], r['lng'])
            r['shoot_date'] = ''
            kept.append(r)
            continue
        g = geocode(r['addr'])
        if not g or not TW(g['lat'], g['lng']):
            miss.append((r['film_zh'] or r['film_en'], r['addr'], 'nogeo'))
            continue
        prec = precision_for(r['addr'], g)
        if prec == 'street-level' and '號' not in r['addr'] and '十字路口' not in r['addr']:
            # a road-only pin — only keep if the address itself is a named site query that failed
            miss.append((r['film_zh'] or r['film_en'], r['addr'], 'street-only:' + g['display'][:80]))
            continue
        r['lat'], r['lng'] = g['lat'], g['lng']
        r['coord_source'] = 'OpenStreetMap Nominatim (' + r['addr'] + '): ' + g['display'][:120]
        r['coord_conf'] = 'street-level' if prec == 'street-level' else 'medium'
        r['city'] = city_of(r['lat'], r['lng'])
        r['shoot_date'] = ''
        if not r['place_zh']:
            r['place_zh'] = r['addr']
        kept.append(r)
    return kept, miss

def fill_scene_addresses():
    """Geocode official filmkh scene addresses that have no GPS, then retry misses."""
    sc = json.load(open(ROOT / 'fk/scenes.json'))
    filled = 0
    for s in sc:
        if s.get('lat') or not s.get('addr'):
            continue
        # skip overly vague addrs that are just the place name
        q = s['addr'] if re.search(r'(路|街|巷|號|區)', s['addr']) else s['name'] + ', 高雄市'
        g = geocode(q)
        if g and TW(g['lat'], g['lng']):
            # require the result to be in Kaohsiung (or nearby filmkh range)
            if 22.3 < g['lat'] < 23.5 and 120.1 < g['lng'] < 121.0:
                s['lat'], s['lng'] = g['lat'], g['lng']
                s['coord_from'] = 'Nominatim of official filmkh address: ' + g['display'][:120]
                filled += 1
            else:
                s['coord_from'] = 'rejected:' + g['display'][:80]
        else:
            s['coord_from'] = 'nogeo'
    json.dump(sc, open(ROOT / 'fk/scenes.json', 'w'), ensure_ascii=False, indent=1)
    print('filled scene GPS', filled)
    return sc

def retry_misses(sc):
    """Re-run kh_misses with filled scene GPS, better aliases and address queries."""
    misses = json.load(open(ROOT / 'kh_misses.json'))
    tm = {r['title'] if False else None for r in []}
    # We need film metadata (url, director, year, kind) for each miss.
    # Rebuild from teams + same filters as build_kh, but only for current miss tokens.
    teams = json.load(open(ROOT / 'fk/teams.json'))
    EN = {'461': ('BIG', 2023), '296': ('Incantation', 2022), '293': ('Coo-Coo 043', 2022), '291': ('Get the Hell Out', 2020),
          '290': ('Boluomi', 2019), '177': ('Dancing Mary', 2021), '288': ('Detention', 2019), '163': ('A Family Tour', 2018),
          '117': ('The Bold, the Corrupt, and the Beautiful', 2017), '277': ('Some Like It Hot', 2017), '272': ('Mr. Long', 2017),
          '274': ('The Great Buddha+', 2017), '159': ('Cities of Last Things', 2018), '275': ('Only the Ocean Knows', None),
          '276': ('Who Killed Cock Robin', 2017), '135': ('On Happiness Road', 2017), '284': ('The Village of No Return', 2017),
          '137': ('The Scoundrels', 2019), '287': ('Midnight Diner (Chinese version)', None), '478': ('Imperfect Us', None)}
    ZHFIX = {'117': '血觀音', '135': '幸福路上'}
    TV = {'287', '478', '134', '125', '122', '292', '136', '131', '124', '301', '132', '286', '123'}
    SKIP_TEAM = {'297'}
    # token -> list of team records
    from collections import defaultdict
    token_teams = defaultdict(list)
    for r in teams:
        if r['kind'] == '短片/學生製片' and r['id']:
            continue
        if r['kind'].startswith('電視') and r['id'] not in TV:
            continue
        if r['id'] in SKIP_TEAM:
            continue
        zh = ZHFIX.get(r['id'], r['title'])
        for tok in [x.strip() for x in re.split(r'[、，,；;]', r.get('scenes') or '') if x.strip()]:
            token_teams[(zh, tok)].append(r)

    ALIAS_Q = {
        '鼓山武德殿': '高雄市鼓山區登山街36號',
        '中都窯場': '高雄市三民區中華橫路220號',
        '楠梓消防教育訓練中心': '高雄市楠梓區旗楠路119號',
        '天主教救世主堂': '高雄市三民區建國一路271號',
        '高雄代天宮': '高雄市鼓山區鼓波街27號',
        '舊市議會': '高雄市議會舊址, 四維三路, 高雄市',
        '舊事議會': '高雄市議會舊址, 四維三路, 高雄市',
        '夏天19歲的肖像|舊市議會': '高雄市議會舊址, 四維三路, 高雄市',
        '建業新村': '建業新村, 鳳山區, 高雄市',
        '建業新村96號': '建業新村, 鳳山區, 高雄市',
        '高雄中學': '高雄市立高雄高級中學',
        '高雄女中': '高雄市立高雄女子高級中學',
        '義大皇家歌劇院': '義大皇家劇院, 高雄市',
        '高雄國際會議中心地下停車場': '高雄國際會議中心',
        '大同二路54號警察宿舍': '大同二路54號, 前金區, 高雄市',
        '美濃月光山隧道': '月光山隧道, 美濃區, 高雄市',
        '西甲郵局': '西甲郵局, 鳳山區, 高雄市',
        '一殯火化場': '高雄市立殯葬管理處第一殯儀館',
        '林園分局': '高雄市政府警察局林園分局',
        '左營四海派出所': '四海派出所, 左營區, 高雄市',
        '高雄客運自立站': '高雄客運自立站, 高雄市',
        '鹽埕示範市場': '鹽埕示範公有市場, 高雄市',
        '鹽埕區七賢一路及公園二路路口': '七賢一路, 公園二路, 鹽埕區, 高雄市',
        '左營區三角公園': '三角公園, 左營區, 高雄市',
        '三民區九如路橋': '九如路橋, 三民區, 高雄市',
        '中正技擊館天橋': '中正技擊館, 高雄市',
        '愛河湖畔(河東路)': '河東路, 前金區, 高雄市',
        '高雄港1號碼頭': '第一船渠, 哈瑪星, 高雄市',
        '阿蓮區化石涼亭': '化石園區, 阿蓮區, 高雄市',
        '懷恩寶塔': '懷恩堂, 高雄市',
        '金芭黎大舞廳': '金芭黎, 高雄市',
        '旗津沙灘': '旗津海水浴場, 高雄市',
        '壽山綠榕園': '綠榕園, 壽山, 鼓山區, 高雄市',
        '院子劇場': '院子劇場, 高雄市',
        '竹寮取水站': '竹寮取水站, 大樹區, 高雄市',
        '旗津118碼頭': '118號碼頭, 旗津區, 高雄市',
        '楠梓自由車場': '楠梓自行車場, 高雄市',
        '交通局智慧運輸中心': '高雄市交通局智慧運輸中心',
        '美濃第一戲院': '第一戲院, 美濃區, 高雄市',
        '大新百貨': '大新百貨, 高雄市',
        '鳳山鳳翔國中旁空地': '鳳翔國中, 鳳山區, 高雄市',
        '小港分局小港派出所': '小港派出所, 小港區, 高雄市',
        '和春戲院': '和春戲院, 高雄市',
        '邱外科診所': '邱外科醫院, 高雄市',
        '左營區百富酒窖': '百富威士忌酒廠, 左營區, 高雄市',  # may fail; will validate
        '路竹科學園區': '路竹科學園區, 高雄市',
        '田寮天后宮': '田寮天后宮, 田寮區, 高雄市',
        '路竹區三公宮': '三公宮, 路竹區, 高雄市',
        '彌陀區漁港/漁會製冰廠': '彌陀漁港, 高雄市',
        '中油興達站': '興達發電廠, 湖內區, 高雄市',  # careful
        '五福二路OPEN MTV': '五福二路, 新興區, 高雄市',
        '鳳山區五權南 路黃昏市場': '五權南路黃昏市場, 鳳山區, 高雄市',
        '前金區民生二路': '民生二路, 前金區, 高雄市',
        '前鎮區一心二路': '一心二路, 前鎮區, 高雄市',
        '小港區沿海一路': '沿海一路, 小港區, 高雄市',
        '高坪7路': '高坪七路, 小港區, 高雄市',
        '三民區十全二路': '十全二路, 三民區, 高雄市',
        '鳳山區瑞興路': '瑞興路, 鳳山區, 高雄市',
        '工協路': '工協路, 鳳山區, 高雄市',
        '鼓山區九如四路': '九如四路, 鼓山區, 高雄市',
        '前鎮區時代南一路': '時代南一路, 前鎮區, 高雄市',
        '小港區南星路': '南星路, 小港區, 高雄市',
        '盜命師|小港南星路': '南星路, 小港區, 高雄市',
        '新樂街': '新樂街, 鹽埕區, 高雄市',  # film is 幸福城市 in Yancheng context
        '公園路': '公園路, 鹽埕區, 高雄市',  # 春風愛河邊 more likely Yancheng Love River, not Gangshan
        '五福路': '五福路, 鹽埕區, 高雄市',
        '學城路': '學城路, 楠梓區, 高雄市',
        '鳳山區臨海路': '臨海路, 鳳山區, 高雄市',
    }

    # also match remaining no-lat / now-filled scenes by name
    def scene_for(tok):
        t = re.sub(r'\(.*?\)|（.*?）', '', tok).strip()
        best = None
        for s in sc:
            if not s.get('lat'):
                continue
            n = re.sub(r'\(.*?\)|（.*?）| — .*', '', s['name']).strip()
            for cand in [n] + n.split(' '):
                if len(cand) >= 2 and (cand == t or (len(t) >= 3 and t in cand) or (len(cand) >= 3 and cand in t)):
                    if best is None or abs(len(cand) - len(t)) < best[1]:
                        best = (s, abs(len(cand) - len(t)))
        return best[0] if best else None

    # skip still-vague or private
    SKIP_TOK = re.compile(r'(主場景|道路|路段|周邊|住處|民宅|單人房飯店|學生浴室|社宅事務所|男主角|女主角|出口區女子宿舍|3巷12號|639巷|603巷|15路|18路)$|^\d+巷$')

    out, still = [], []
    for zh, tok, why in misses:
        if SKIP_TOK.search(tok) or tok in ('中油', '香蕉園', '天宇鴿會', '字神補習班', 'SUM巨將車行', '綠洲西餐廳', '瓠仔貴', '哥雅美術社', '和新咖啡', '和好咖啡', '7-11昌富', '宏明門市', '藏愛婚紗', '觀海大廈(海邊路', '貝塔景觀套房(民宿', '大都會網咖華夏店', '穩發冷凍廠', '台華輪', '三輪車聚集地', '新樂園酒店', '道騰商務中心', '崇恩長照中心', '威秀影城'):
            # skip shops/homes we cannot uniquely identify, or keep trying a few of these below
            if tok not in ALIAS_Q and not scene_for(tok):
                still.append((zh, tok, why))
                continue
        teams_hit = token_teams.get((zh, tok), [])
        # choose meta
        if teams_hit:
            r0 = teams_hit[0]
            en, yr = EN.get(r0['id'], ('', None))
            kind = 'tv' if r0['id'] in TV else 'film'
            director = r0.get('director', '')
            src = r0['url']
            date = r0.get('date', '')
        else:
            en, yr, kind, director, src, date = '', None, 'film', '', '', ''

        # 1 scene match (now including newly filled GPS)
        s = scene_for(tok)
        # tighten: avoid weak substring matches like 一號 -> 哈瑪星一號船渠 for 高雄港1號碼頭? 1號碼頭 vs 一號船渠 is related but not certain.
        if s and not (tok in s['name'] or s['name'].split()[0] in tok or tok.replace('區', '') in s['name']):
            # allow alias-level if close
            if abs(len(s['name']) - len(re.sub(r'\(.*?\)|（.*?）', '', tok))) > 6 and tok not in s['name'] and s['name'] not in tok:
                s = None
        if s and s.get('lat'):
            src2 = s.get('url', '')
            csrc = s.get('coord_from') or ('filmkh scene database GPS: ' + s['name'])
            conf = 'high' if not s.get('coord_from', '').startswith('Nominatim') else 'medium'
            if s.get('coord_from', '').startswith('Nominatim'):
                csrc = 'filmkh official address geocoded via OSM Nominatim: ' + s['addr'] + ' — ' + s.get('coord_from', '')
            out.append(dict(film_en=en, film_zh=zh, year=yr, kind=kind, director=director,
                            place_zh=tok, place_en='', lat=s['lat'], lng=s['lng'],
                            coord_source=csrc, coord_conf=conf, scene='', source=src, source2=src2,
                            link_conf='high', city='Kaohsiung', shoot_date=date))
            continue

        q = ALIAS_Q.get(f'{zh}|{tok}') or ALIAS_Q.get(tok)
        if not q:
            # try the token plus city/district already in the name
            core = tok
            q = (core if '高雄' in core else core + ', 高雄市')
            # if it has a house number, great
            if re.search(r'(道路|路段|周邊道路|區道路)', tok) and '號' not in tok and '路口' not in tok:
                still.append((zh, tok, 'still-vague'))
                continue

        g = geocode(q)
        if not g or not (22.3 < g['lat'] < 23.5 and 120.1 < g['lng'] < 121.0):
            still.append((zh, tok, 'nogeo' if not g else 'out-of-range:' + g['display'][:60]))
            continue
        n0 = g['display'].split(',')[0].strip()
        # Accept if:
        # - official address query (ALIAS_Q and has 號)
        # - display name shares characters with the query core
        core = re.sub(r'^.{1,3}區', '', re.sub(r'\(.*?\)|（.*?）', '', tok)).strip()
        alias = tok in ALIAS_Q or f'{zh}|{tok}' in ALIAS_Q
        named_ok = n0 and (n0 in q or n0 in core or core in n0 or (len(n0) >= 2 and n0[:2] in core + q))
        # district check for roads: the display should contain the district if the token named one
        dist_m = re.match(r'(.{1,3}區)', tok)
        district_ok = True
        if dist_m:
            district_ok = dist_m.group(1) in g['display']
        if not district_ok:
            still.append((zh, tok, 'wrong-district:' + g['display'][:60]))
            continue
        if not (alias and re.search(r'號', q) or named_ok or alias):
            still.append((zh, tok, 'mismatch:' + g['display'][:60]))
            continue
        prec = 'street-level' if re.search(r'([路街巷]|路\d+巷)$', n0) and '號' not in (q + tok) and '路口' not in tok else 'medium'
        # Don't add yet more bare mid-road pins unless the miss was a mismatch we can now place in the right district
        if prec == 'street-level' and why.startswith('nogeo') and '路口' not in tok:
            # actually the task wants misses located; a correctly district-placed road is OK as street-level
            pass
        out.append(dict(film_en=en, film_zh=zh, year=yr, kind=kind, director=director,
                        place_zh=tok, place_en='', lat=g['lat'], lng=g['lng'],
                        coord_source='OpenStreetMap Nominatim (' + q + '): ' + g['display'][:120],
                        coord_conf=prec, scene='', source=src, source2='',
                        link_conf='high', city='Kaohsiung', shoot_date=date))
    return out, still

# Wayward Cloud + pin-upgrade curated rows.
# geocode query may start with @lat,lng|source
CURATED2 = [
    # Tsai himself told TAKAO he chose 春秋閣 for the musical love-song scenes.
    ("The Wayward Cloud", "天邊一朵雲", 2005, "Spring and Autumn Pavilions, Lotus Pond", "蓮池潭春秋閣",
     "@22.682287,120.292812|filmkh scene database GPS: 春秋閣 (春秋御閣)",
     "Tsai Ming-liang staged musical numbers at the Spring and Autumn Pavilions; he told the city he chose this 'Southeast Asian kitsch' landmark, a former dating spot, after first seeing it twenty years earlier.",
     "https://takao.kcg.gov.tw/article/1461", "high"),
    # Bridge of Light — Wikipedia photograph caption + TAKAO + Taipei Pictures.
    ("The Wayward Cloud", "天邊一朵雲", 2005, "Bridge of Light, Heti Community", "河堤社區光雕橋",
     "光雕橋, 三民區, 高雄市",
     "Watermelons float in the Love River under the light-art bridges of the Heti (Riverbank) Community; Wikipedia publishes a photograph of the Bridge of Light as a filming location.",
     "https://en.wikipedia.org/wiki/The_Wayward_Cloud", "high"),
    ("The Wayward Cloud", "天邊一朵雲", 2005, "Heti Community (riverside apartments)", "河堤社區",
     "河堤公園, 三民區, 高雄市",
     "Apartment and community scenes were shot in Zuoying/Sanmin's Heti riverside housing community (the specific building is not identified). Lee Kang-sheng has named Dragon and Tiger Pagodas, Lotus Pond and Heti Community as the Kaohsiung locations.",
     "https://star.ettoday.net/news/1833320", "high"),
    # Pin upgrades (named sites previously snapped to a road centreline)
    ("Our Times", "我的少女時代", 2015, "Eslite Dunnan (closed 2020)", "敦南誠品（已熄燈）",
     "敦化南路一段245號, 大安區, 台北市",
     "The famous Dunnan Eslite, closed 2020; previously pinned only to Dunhua South Road.",
     "https://stunning-asia.com/smart-travel/the-filming-locations-of-top-mandarin-movies/", "medium"),
    ("Cafe. Waiting. Love", "等一個人咖啡", 2014, "Waiting for Someone Café, Jingmei", "等一個人咖啡（景美店）",
     "台北市文山區一壽街44巷1號",
     "The café of the title (Jingmei main shop).",
     "https://supertaste.tvbs.com.tw/pack/347636",
     "high"),
]

def geocode_curated(entries):
    rows, miss = [], []
    for en, zh, yr, pen, pzh, q, scene, src, conf in entries:
        if q.startswith('@'):
            ll, why = q[1:].split('|', 1)
            la, ln = map(float, ll.split(','))
            g = dict(lat=la, lng=ln, display=why)
            csrc, cc = why, 'high' if 'filmkh scene database GPS' in why else 'medium'
        else:
            g = geocode(q)
            if not g or not TW(g['lat'], g['lng']):
                miss.append((zh, pzh, q))
                continue
            csrc = 'OpenStreetMap Nominatim (' + q + '): ' + g['display'][:120]
            n0 = g['display'].split(',')[0].strip()
            cc = 'street-level' if re.search(r'([路街巷]|[一二三四五六七八九]段)$', n0) and '號' not in q else 'medium'
        rows.append(dict(film_en=en, film_zh=zh, year=yr, kind='film', director='',
                         place_zh=pzh, place_en=pen, lat=g['lat'], lng=g['lng'],
                         coord_source=csrc, coord_conf=cc, scene=scene, source=src, source2='',
                         link_conf=conf, city=city_of(g['lat'], g['lng']), shoot_date='',
                         origin='Curated from web sources (round 2)'))
    return rows, miss

def merge(old, *news):
    ded = list(old)
    added = 0
    for group in news:
        for r in group:
            key = (r['film_zh'] or r['film_en'] or '').lower()
            dup = next((d for d in ded if (d['film_zh'] or d['film_en'] or '').lower() == key
                        and dist(d['lat'], d['lng'], r['lat'], r['lng']) < 0.15), None)
            if dup:
                if (not dup.get('scene')) and r.get('scene'):
                    dup['scene'] = r['scene']
                # prefer tighter coordinates
                rank = {'high': 0, 'medium': 1, 'street-level': 2}
                if rank.get(r.get('coord_conf'), 9) < rank.get(dup.get('coord_conf'), 9):
                    for k in ('lat', 'lng', 'coord_source', 'coord_conf', 'place_en', 'place_zh'):
                        if r.get(k):
                            dup[k] = r[k]
                srcs = ' '.join(x for x in [dup.get('source'), dup.get('source2'), r.get('source')] if x)
                # keep first source, stash extra
                if r.get('source') and r['source'] not in (dup.get('source') or ''):
                    dup['source2'] = ((dup.get('source2') or '') + ' ' + r['source']).strip()
                continue
            if 'origin' not in r:
                pass
            ded.append(r)
            added += 1
    return ded, added

def write_outputs(rows):
    for i, r in enumerate(rows, 1):
        r['id'] = i
        if not r.get('city'):
            r['city'] = city_of(r['lat'], r['lng'])
    json.dump(rows, open(ROOT / 'all_rows.json', 'w'), ensure_ascii=False, indent=1)
    F = ['id', 'city', 'film_en', 'film_zh', 'year', 'kind', 'director', 'place_en', 'place_zh',
         'lat', 'lng', 'scene', 'link_conf', 'coord_conf', 'coord_source', 'source', 'source2', 'origin', 'shoot_date']
    with open(ROOT / 'taiwan_film_locations.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=F)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') or '' for k in F})
    print(len(rows), 'rows', Counter(r['city'] for r in rows))
    print('films', len(set((r['film_zh'] or r['film_en']) for r in rows)))
    print('coord_conf', Counter(r['coord_conf'] for r in rows))

def main():
    print('=== FILMWALKER parse ===')
    fw_raw, fw_skip = parse_fw()
    print('parsed addresses', len(fw_raw), 'skipped', len(fw_skip))
    json.dump(fw_raw, open(ROOT / 'fw_raw.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(fw_skip, open(ROOT / 'fw_skipped.json', 'w'), ensure_ascii=False, indent=1)
    print('=== FILMWALKER geocode ===')
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

    print('=== curated round 2 ===')
    cur, cmiss = geocode_curated(CURATED2)
    print('curated', len(cur), 'miss', cmiss)

    print('=== merge ===')
    old = json.load(open(ROOT / 'all_rows.json'))
    # tag origin if missing
    merged, added = merge(old, fw_kept, kh_new, cur)
    print('added (non-duplicate) rows', added, 'total', len(merged))
    write_outputs(merged)
    print('done')

if __name__ == '__main__':
    main()
