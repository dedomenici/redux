import json,re
from geo import geocode
sc=json.load(open('fk/scenes.json')); tm=json.load(open('fk/teams.json'))
EN={'461':('BIG',2023),'296':('Incantation',2022),'293':('Coo-Coo 043',2022),'291':('Get the Hell Out',2020),'290':('Boluomi',2019),
'177':('Dancing Mary',2021),'288':('Detention',2019),'163':('A Family Tour',2018),'117':('The Bold, the Corrupt, and the Beautiful',2017),
'277':('Some Like It Hot',2017),'272':('Mr. Long',2017),'274':('The Great Buddha+',2017),'159':('Cities of Last Things',2018),
'275':('Only the Ocean Knows',None),'276':('Who Killed Cock Robin',2017),'135':('On Happiness Road',2017),'284':('The Village of No Return',2017),
'137':('The Scoundrels',2019),'287':('Midnight Diner (Chinese version)',None),'478':('Imperfect Us',None),'157':('',None)}
ZHFIX={'117':'血觀音','135':'幸福路上'}
TV={'287','478','134','125','122','292','136','131','124','301','132','286','123'}
SKIP_TEAM={'297'}
KH=(22.4,23.5,120.1,121.1)
def inkh(lat,lng): return KH[0]<lat<KH[1] and KH[2]<lng<KH[3]
def scene_match(tok):
    t=re.sub(r'\(.*?\)|（.*?）','',tok).strip()
    best=None
    for s in sc:
        if not s['lat']: continue
        n=re.sub(r'\(.*?\)|（.*?）| — .*','',s['name']).strip()
        for cand in [n]+n.split(' '):
            if len(cand)>=2 and (cand==t or (len(t)>=3 and t in cand) or (len(cand)>=3 and cand in t)):
                if best is None or abs(len(cand)-len(t))<best[1]: best=(s,abs(len(cand)-len(t)))
    return best[0] if best else None
ALIAS={'旗津砲台':('scene','旗後礮臺（旗後砲臺）'),'前金公有市場':('scene','前金第一公有市場(公有前金市場)'),'鳳山第二市場(民生路)':('scene','鳳山第二公有市場'),
'鼓山武德殿':('scene','高雄武德殿'),'中都窯場':('scene','中都唐榮磚窯廠'),'高雄代天宮':('scene','哈瑪星代天宮'),'路竹火車站':('scene','路竹車站'),
'打狗英國領事館及西子灣蓮海路':('scene','打狗英國領事館文化園區'),'果貿社區':('q','果貿, 左營區, 高雄市'),'左營果貿社區':('q','果貿, 左營區, 高雄市'),
'旗津老街':('q','廟前路, 旗津區, 高雄市'),'旗津天后宮':('q','旗後天后宮, 高雄市'),'高雄歷史博物館':('q','高雄市立歷史博物館'),'高雄火車站':('q','高雄車站'),'菜鳥:高雄火車站':('q','高雄車站'),
'舊市議會':('q','高雄市議會舊址'),'舊事議會':('q','高雄市議會舊址'),'中油宿舍宏毅一路4巷1號':('q','宏毅一路, 楠梓區, 高雄市'),'中油宏毅宿舍':('q','宏毅一路, 楠梓區, 高雄市'),
'中油宏南宿舍':('q','宏毅一路, 楠梓區, 高雄市'),'建業新村':('q','建業新村, 鳳山區, 高雄市'),'建業新村96號':('q','建業新村, 鳳山區, 高雄市'),'高雄中學':('q','高雄高級中學, 三民區, 高雄市'),
'高雄女中':('q','高雄女子高級中學, 高雄市'),'高雄市電影圖書館':('q','高雄市電影館'),'前鎮加工出口區':('q','前鎮加工出口區'),'小岡山':('q','小崗山, 高雄市'),
'中洲渡輪站':('q','中洲輪渡站, 高雄市'),'前鎮渡輪站':('q','前鎮輪渡站, 高雄市'),'香格里拉酒店':('q','高雄85大樓'),'柴山大自然':('q','柴山, 鼓山區, 高雄市'),
'長庚紀念醫  院':('q','長庚醫院, 鳥松區, 高雄市'),'楠梓消防教育訓練中心':('scene','高雄市消防訓練中心'),'西子灣 六龜區':('multi',['西子灣','六龜區'])}
out=[]; misses=[]
for r in tm:
    if r['kind']=='短片/學生製片' and r['id']: continue
    if r['kind'].startswith('電視') and r['id'] not in TV: continue
    if r['id'] in SKIP_TEAM: continue
    zh=ZHFIX.get(r['id'],r['title']); en,yr=EN.get(r['id'],('',None))
    toks=[x.strip() for x in re.split(r'[、，,；;]',r['scenes']) if x.strip()]
    toks2=[]
    for tok in toks:
        a=ALIAS.get(tok)
        if a and a[0]=='multi': toks2+=a[1]
        else: toks2.append(tok)
    for tok in toks2:
        a=ALIAS.get(tok)
        if a and a[0]=='scene':
            s=next((x for x in sc if x['name']==a[1] and x['lat']),None)
            if s:
                out.append(dict(film_en=en,film_zh=zh,year=yr,kind='tv' if r['id'] in TV else 'film',director=r['director'],place_zh=tok,place_en='',lat=s['lat'],lng=s['lng'],coord_source='filmkh scene database GPS: '+s['name'],coord_conf='high',scene='',source=r['url'],source2=s['url'],link_conf='high',city='Kaohsiung',shoot_date=r['date'])); continue
        if a and a[0]=='q':
            g=geocode(a[1])
            if g and inkh(g['lat'],g['lng']):
                out.append(dict(film_en=en,film_zh=zh,year=yr,kind='tv' if r['id'] in TV else 'film',director=r['director'],place_zh=tok,place_en='',lat=g['lat'],lng=g['lng'],coord_source='OpenStreetMap Nominatim ('+a[1]+'): '+g['display'][:110],coord_conf='medium',scene='',source=r['url'],source2='',link_conf='high',city='Kaohsiung',shoot_date=r['date'])); continue
            misses.append((zh,tok,'alias-nogeo')); continue
        if (re.fullmatch(r'.{1,3}區',tok) and not tok.endswith('社區')) or '主場景' in tok or re.search(r'道路|路段|周邊',tok) and len(tok)<4: misses.append((zh,tok,'vague')); continue
        if tok=='中油': misses.append((zh,tok,'vague')); continue
        s=scene_match(tok)
        if s:
            out.append(dict(film_en=en,film_zh=zh,year=yr,kind='tv' if r['id'] in TV else 'film',director=r['director'],place_zh=tok,place_en='',lat=s['lat'],lng=s['lng'],coord_source='filmkh scene database GPS: '+s['name'],coord_conf='high',scene='',source=r['url'],source2=s['url'],link_conf='high',city='Kaohsiung',shoot_date=r['date']))
            continue
        q=tok if '高雄' in tok else tok+', 高雄市'
        g=geocode(q)
        core=re.sub(r'^.{1,3}區','',re.sub(r'\(.*?\)|（.*?）','',tok)).strip()
        if g and inkh(g['lat'],g['lng']):
            n0=g['display'].split(',')[0].strip()
            if n0 and (n0 in core or core in n0 or (len(n0)>=3 and n0[:3] in core)) and not (re.search(r'[路街巷]$',n0) and not re.search(r'鹽埕|鼓山|前金|新興|苓雅|三民|前鎮|旗津|左營|鳳山|小港|楠梓|大寮',g['display'])):
                prec='street' if re.search(r'[路街巷]$|路\d+巷$',n0) else 'site'
                out.append(dict(film_en=en,film_zh=zh,year=yr,kind='tv' if r['id'] in TV else 'film',director=r['director'],place_zh=tok,place_en='',lat=g['lat'],lng=g['lng'],coord_source='OpenStreetMap Nominatim: '+g['display'][:120],coord_conf='medium' if prec=='site' else 'street-level',scene='',source=r['url'],source2='',link_conf='high',city='Kaohsiung',shoot_date=r['date']))
                continue
        misses.append((zh,tok,'nogeo' if not g else 'mismatch:'+g['display'][:50]))
json.dump(out,open('kh_filmkh.json','w'),ensure_ascii=False,indent=1)
json.dump(misses,open('kh_misses.json','w'),ensure_ascii=False,indent=1)
print(len(out),'geolocated',len(misses),'missed')
