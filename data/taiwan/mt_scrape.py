import re,json,time,urllib.request,html
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
def get(u):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=30).read().decode('utf8','ignore')
        except Exception as e: print('err',u,e); time.sleep(3)
    return ''
films=set(); regions={'/locations/taiwan'}; seen=set()
while regions:
    r=regions.pop()
    if r in seen: continue
    seen.add(r); t=get('https://metatake.net'+r); time.sleep(1)
    films|=set(re.findall(r'href="(/film/locations/[^"#?]+)"',t))
    regions|=set(x for x in re.findall(r'href="(/locations/taiwan[^"#?]*)"',t))
films|=set(open('mt/all58.txt').read().split())
print(len(seen),'regions',len(films),'films')
out=[]
for f in sorted(films):
    t=get('https://metatake.net'+f); time.sleep(1)
    movie=None; items=[]
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>',t,re.S):
        try: j=json.loads(m)
        except: continue
        if j.get('@type')=='Movie': movie=j
        if j.get('@type')=='ItemList': items=j['itemListElement']
    plain=html.unescape(re.sub(r'<[^>]+>','\n',t)); plain=re.sub(r'\n\s*\n+','\n',plain)
    for it in items:
        p=it['item']; g=p.get('geo') or {}
        nm=p['name']; idx=plain.find(nm); prec=''
        if idx>=0:
            mm=re.search(r'·\s*([a-z ]+)\n',plain[idx:idx+300]); prec=mm.group(1).strip() if mm else ''
        out.append(dict(film=movie.get('name') if movie else f, year=movie.get('datePublished') if movie else '', director=(movie or {}).get('director',{}).get('name','') if isinstance((movie or {}).get('director'),dict) else '', url='https://metatake.net'+f, place=nm, scene=p.get('description',''), lat=g.get('latitude'), lng=g.get('longitude'), precision=prec))
json.dump(out,open('mt/metatake.json','w'),ensure_ascii=False,indent=1)
tw=[o for o in out if o['lat'] and 21.8<o['lat']<26.5 and 118<o['lng']<122.2]
print(len(out),'items',len(tw),'in taiwan')
from collections import Counter; print(Counter(o['precision'] for o in tw))
