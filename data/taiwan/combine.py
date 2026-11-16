import json,re,math,csv
from geo import geocode
from curated import C
def dist(a,b,c,d): return 6371*2*math.asin(math.sqrt(math.sin(math.radians(c-a)/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(math.radians(d-b)/2)**2))
TW=lambda la,ln: 21.8<la<25.4 and 119.2<ln<122.1
CITIES=[('Pingtung City',22.67,120.49,12),('Kaohsiung',22.63,120.30,40),('Pingtung/Kenting',22.2,120.7,45),('Tainan',23.0,120.22,30),('Chiayi',23.48,120.45,25),('Taichung',24.15,120.67,30),('Changhua',24.07,120.54,15),('Hsinchu',24.8,120.98,25),('Taoyuan',24.95,121.25,20),('Keelung/Jiufen/Ruifang',25.12,121.8,14),('Taipei/New Taipei',25.05,121.52,28),('Yilan',24.7,121.75,30),('Hualien',23.95,121.55,60),('Miaoli',24.55,120.85,30)]
def city(la,ln):
    best=min(CITIES,key=lambda c: dist(la,ln,c[1],c[2])/c[3])
    return best[0] if dist(la,ln,best[1],best[2])<=best[3] else 'Taiwan (other)'
rows=[]
# 1 Kaohsiung filmkh
for x in json.load(open('kh_filmkh.json')):
    x['origin']='Kaohsiung Film Commission (filmkh.org) — 來過高雄拍'; rows.append(x)
# 2 curated
miss=[]
for en,zh,yr,pen,pzh,q,scene,src,conf in C:
    if q.startswith('@'):
        ll,why=q[1:].split('|'); la,ln=map(float,ll.split(','))
        g=dict(lat=la,lng=ln,display=why); csrc=why; cc='medium'
    else:
        g=geocode(q)
        if not g or not TW(g['lat'],g['lng']): miss.append((zh,pzh,q)); continue
        csrc='OpenStreetMap Nominatim ('+q+'): '+g['display'][:110]
        n0=g['display'].split(',')[0].strip()
        cc='street-level' if re.search(r'([路街巷]|[一二三四五六七八九]段)$',n0) or n0 in ('景美',) else 'medium'
    rows.append(dict(film_en=en,film_zh=zh,year=yr,kind='film',director='',place_zh=pzh,place_en=pen,lat=g['lat'],lng=g['lng'],coord_source=csrc,coord_conf=cc,scene=scene,source=src,source2='',link_conf=conf,city='',shoot_date='',origin='Curated from web sources'))
print('curated geocode misses',miss)
# 3 metatake
ZHT={'A Brighter Summer Day':'牯嶺街少年殺人事件','A City of Sadness':'悲情城市','A Sun':'陽光普照','A Time to Live and a Time to Die':'童年往事','Cape No. 7':'海角七號','Dust in the Wind':'戀戀風塵','Goodbye, Dragon Inn':'不散','Happy Together':'春光乍洩','Life of Pi':'少年Pi的奇幻漂流','Millennium Mambo':'千禧曼波','Silence':'沉默','Taipei Story':'青梅竹馬','The Assassin':'聶隱娘','The River':'河流','Three Times':'最好的時光','Vive L\'Amour':'愛情萬歲','What Time Is It There?':'你那邊幾點','Yi Yi':'一一','Hill of No Return':'無言的山丘','He Never Gives Up':'汪洋中的一條船','A Foggy Tale':'大濛','The Spy Gone North':'공작','Lucy':'露西'}
drop=[]
for o in json.load(open('mt/metatake.json')):
    if not o['lat'] or not TW(o['lat'],o['lng']): continue
    # Metatake pins that land outside the district their own label names (checked by hand): skip rather than guess.
    if o['film']=='Yi Yi' and ('Heping East Rd' in o['place'] or '和平新生天橋' in o['place']): drop.append(o['place']+' [bad coords]'); continue
    first=o['place'].split(',')[0].strip()
    parts=[p.strip() for p in o['place'].split(',')]
    if re.fullmatch(r'(Taiwan|Taipei|Taichung|Kaohsiung|Tainan|Keelung|Jiufen|Hualien|Taoyuan|New Taipei( City)?|Pingtung|Yilan|Hsinchu|Miaoli( County)?|Ruifang( District)?|Kenting|Penghu|Taitung|Chiayi)',first) and len(parts)<=3:
        drop.append(o['place']); continue
    rows.append(dict(film_en=o['film'],film_zh=ZHT.get(o['film'],''),year=int(o['year']) if str(o['year']).isdigit() else None,kind='film',director=o.get('director',''),place_zh=first if re.search(r'[\u4e00-\u9fff]',first) else '',place_en=o['place'] if not re.search(r'[\u4e00-\u9fff]',first) else '',lat=o['lat'],lng=o['lng'],coord_source='Metatake geolocation',coord_conf='medium',scene=o['scene'],source=o['url'],source2='',link_conf='medium',city='',shoot_date='',origin='Metatake (metatake.net) film-location pages'))
print('metatake coarse dropped',len(drop))
for r in rows: r['city']='Kaohsiung' if r.get('origin','').startswith('Kaohsiung Film') else city(r['lat'],r['lng'])
# dedupe same film + within 150 m
ded=[]
for r in rows:
    key=(r['film_zh'] or r['film_en']).lower()
    dup=next((d for d in ded if (d['film_zh'] or d['film_en']).lower()==key and dist(d['lat'],d['lng'],r['lat'],r['lng'])<0.15),None)
    if dup:
        if not dup['scene'] and r['scene']: dup['scene']=r['scene']
        if r['source'] not in dup['source']: dup['source2']=(dup['source2']+' '+r['source']).strip()
        continue
    ded.append(r)
rows=ded
for i,r in enumerate(rows): r['id']=i+1
json.dump(rows,open('all_rows.json','w'),ensure_ascii=False,indent=1)
F=['id','city','film_en','film_zh','year','kind','director','place_en','place_zh','lat','lng','scene','link_conf','coord_conf','coord_source','source','source2','origin','shoot_date']
with open('taiwan_film_locations.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=F); w.writeheader()
    for r in rows: w.writerow({k:r.get(k,'') for k in F})
from collections import Counter
print(len(rows),'rows'); print(Counter(r['city'] for r in rows))
print('films',len(set((r['film_zh'] or r['film_en']) for r in rows)))
